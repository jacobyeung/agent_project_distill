"""Opt-in faithful camera SFT and routing camera supervision."""
import copy
import re
from collections import Counter

import numpy as np
import torch

from . import carrier_c1_routing as routing
from .camera_targets import trajectory_scale
from generator.derivgen_v7.derivgen.materialize import materialize, MaterializeRefusal

CAMERA_TYPES = routing.CAMERA_MOTION


def validate(cfg):
    h = cfg.get('h1', {})
    if not isinstance(h, dict) or set(h) - {'faithful_own_camera_rows', 'routing_pose_targets',
                                           'camera_types', 'stop_after_step', 'metrics'}:
        raise ValueError('Unknown H1 configuration')
    for key in ('faithful_own_camera_rows', 'routing_pose_targets', 'metrics'):
        if key in h and type(h[key]) is not bool:
            raise ValueError('h1.' + key + ' must be boolean')
    if tuple(h.get('camera_types', CAMERA_TYPES)) != CAMERA_TYPES:
        raise ValueError('H1 camera_types must be the three camera motion types in canonical order')
    stop = h.get('stop_after_step')
    if stop is not None and (type(stop) is not int or not 1 <= stop <= cfg['recipe']['steps']):
        raise ValueError('h1.stop_after_step must be within the unchanged LR horizon')
    if h.get('faithful_own_camera_rows'):
        s = cfg['scheduled_sampling']
        if s['max_own_probability'] != .5 or s['force_from_step'] != 1:
            raise ValueError('H1 S1 requires max_own_probability=0.5 and force_from_step=1')
    return h


def camera(row, settings):
    return row.get('question_type') in settings.get('camera_types', CAMERA_TYPES)


def canonical_row(row):
    """Restore materializer metadata omitted by the sealed C1 row packing.

    v3.11 single-call camera programs have no frame-pair selection program. Their
    declared frame-gap rule can be reconstructed without changing the call.
    Other programs retain their metadata and fail closed in materialize.
    """
    raw = copy.deepcopy(row.get('routing', row))
    if 'routing' in row:
        raw.update(question=row['student_input']['question'],
                   options=row['student_input'].get('options') or [], target=row['target'])
    if raw.get('trace_revision') == '3.11' and raw.get('question_type') in CAMERA_TYPES:
        calls = [e for e in raw['events'] if e['kind'] == 'tool_call']
        if len(calls) == 1 and calls[0]['name'] in ('move', 'turn'):
            raw.setdefault('frame_pair_rule', 'frame_gap')
            raw.setdefault('frame_pair_turn', [])
            if raw['question_type'] == 'camera_movement_direction':
                # The packed row omits these deterministic GT printed-value margins.
                from decimal import Decimal, localcontext, Context
                event = next(e for e in raw['events'] if e['kind'] == 'tool_response')
                dx, _, dz = map(lambda x: Decimal(str(x)), event['values'][event['call_id']+'.delta']['value'])
                scores = dict(left=-dx, right=dx, forward=dz, backward=-dz)
                labels = [re.sub(r'^[A-Z][.)]\s*', '', o).lower() for o in raw['options']]
                with localcontext(Context(prec=1024)):
                    top, second = sorted((scores[o] for o in labels), reverse=True)[:2]
                    if top > 0:
                        raw.setdefault('margin_m', float(top-second))
                        raw.setdefault('margin_rel', float((top-second)/top))
    return raw


def printed_camera(row, target, spans):
    """Parse exactly the rounded response text emitted by the existing renderer."""
    responses = {e['call_id']: e for e in row['events'] if e['kind'] == 'tool_response'}
    printed = {}
    number = r'([+-]?\d+(?:\.\d+)?)'
    for span in spans:
        cid = span['call_id']; name = responses[cid]['name']
        text = target[span['start']:span['end']]
        text = text.removeprefix('<tool_response>').removesuffix('</tool_response>')
        if name == 'move':
            m = re.fullmatch(r'dx = '+number+r' m, dy = '+number+r' m, dz = '+number+r' m, distance = '+number+' m', text)
            if m is None:
                raise MaterializeRefusal('invalid_printed_move')
            values = list(map(float, m.groups()))
            printed[cid] = dict(delta=values[:3], distance=values[3])
        elif name == 'turn':
            m = re.fullmatch(r'turn = ([+-]?\d+) deg', text)
            if m is None:
                raise MaterializeRefusal('invalid_printed_turn')
            printed[cid] = dict(value=int(m[1]))
        else:
            raise MaterializeRefusal('non_camera_head')
    return printed


def faithful(row, geometry):
    raw = canonical_row(row)
    target, spans, _ = routing.rerender(raw, geometry)
    result = materialize(raw, printed_camera(raw, target, spans))
    target, spans, segments = routing.render_full(result['events'], result['answer'])
    if target != result['target']:
        raise MaterializeRefusal('faithful_render_mismatch')
    return result, target, spans, segments


def own_values(model, rows, batch, audit, index, decision, device):
    """Every rank joins a requested readout; only camera pose draws change labels."""
    from .carrier_c1_run import move
    row, _ = rows.row('routing', index)
    raw = row['routing']
    kind = raw.get('question_type', 'unknown')
    info = dict(type=kind, values='gt', refused=None, answer_differs=False)
    audit = {**audit, 'h1': info}
    if not any(decision):
        return batch, audit
    # Keep the readout collective aligned even for ground/gap or closed pose gates.
    uv, slots = routing.query_tensor([])
    with torch.no_grad():
        readout = model(move(routing.prefix_batch(batch), device), {'uv': uv.to(device)}, stream='readout')
    if not camera(raw, rows.h1) or not decision[1]:
        return batch, audit
    try:
        geometry, source = routing.row_geometry(raw, readout, [], slots, False, True)
        if geometry is None:
            raise routing.RenderError(source)
        result, target, spans, segments = faithful(row, geometry)
        new, changed = routing.encode_own(rows.processor, row, batch, target, spans, segments,
                                          source, faithful=True)
        info.update(values='own', answer_differs=str(result['answer']) != str(raw['answer']),
                    answer=result['answer'])
        return new, {**audit, **changed, 'h1': info}
    except (MaterializeRefusal, routing.RenderError) as exc:
        info['refused'] = getattr(exc, 'reason', str(exc))
        return batch, {**audit, 'own_refusal': info['refused']}


def pose_targets(row, batch, settings):
    """Reuse the pose stream target contract, masking missing camera labels."""
    raw = row.get('routing', row)
    valid = camera(raw, settings) and 'gt_pose9' in raw and 'gt_up' in raw
    reason = None if valid else ('missing_gt_fields' if camera(raw, settings) else 'non_camera')
    p = np.asarray(raw['gt_pose9'], dtype=np.float32) if valid else np.tile([0,0,0,0,0,0,1,1,1], (32,1))
    up = np.asarray(raw['gt_up'], dtype=np.float32) if valid else np.array([0,-1,0], dtype=np.float32)
    if p.shape != (32,9) or up.shape != (3,) or not np.isfinite(p).all() or not np.isfinite(up).all():
        raise ValueError('H1 routing GT must be finite gt_pose9[32,9] and gt_up[3]')
    if valid and (not np.allclose(np.linalg.norm(p[:,3:7], axis=1), 1, atol=1e-4)
                  or not np.isclose(np.linalg.norm(up), 1, atol=1e-4)):
        raise ValueError('H1 routing GT quaternion and gravity must be unit vectors')
    positions = batch['aux_camera_positions']
    if positions.shape != (1,32) or (valid and not (positions >= 0).all()):
        raise ValueError('H1 pose targets require all 32 frame carriers')
    mask = np.full(32, valid)
    targets = dict(aux_camera_target=torch.tensor(p, dtype=torch.float32)[None],
                   aux_camera_mask=torch.tensor(mask)[None],
                   aux_camera_scale=torch.tensor([trajectory_scale(p, mask) if valid else 0.]),
                   aux_gravity_target=torch.tensor(up, dtype=torch.float32)[None],
                   aux_gravity_mask=torch.tensor([valid]), h1_pose=torch.tensor(True))
    return targets, dict(supervised=int(valid), missing=int(reason == 'missing_gt_fields'), reason=reason)


def summarize(shapes):
    out = {}
    for row in shapes:
        h = row.get('h1')
        if h is None:
            continue
        d = out.setdefault(h['type'], dict(own=0, gt=0, refused=0, refusal_reasons={},
                                          answer_differs=0, pose_supervised=0, pose_missing=0, segments={}))
        d[h['values']] += 1
        if h.get('refused'):
            d['refused'] += 1
            r = h['refused']; d['refusal_reasons'][r] = d['refusal_reasons'].get(r, 0) + 1
        d['answer_differs'] += int(h.get('answer_differs', False))
        pose = row.get('h1_pose', {})
        d['pose_supervised'] += pose.get('supervised', 0)
        d['pose_missing'] += pose.get('missing', 0)
        for name, (loss, n) in row.get('segments', {}).items():
            sums = d['segments'].setdefault(name, [0., 0]); sums[0] += loss; sums[1] += n
    for d in out.values():
        d['faithful_answer_differs_from_gt_rate'] = d['answer_differs']/d['own'] if d['own'] else None
        d['segment_ce'] = {k: loss/n for k, (loss,n) in d['segments'].items() if n}
    return out
