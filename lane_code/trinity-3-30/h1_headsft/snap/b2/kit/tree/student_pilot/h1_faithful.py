"""S1: faithful camera labels from the existing renderer's printed own values."""
import copy
import re
import torch
from . import carrier_c1_routing as routing
from generator.derivgen_v7.derivgen.materialize import materialize, MaterializeRefusal
CAMERA_TYPES = routing.CAMERA_MOTION


def validate(cfg):
    h = cfg.get('h1', {})
    flag = h.get('faithful_own_camera_rows', False)
    if type(flag) is not bool:
        raise ValueError('h1.faithful_own_camera_rows must be boolean')
    if flag:
        if tuple(h.get('camera_types', CAMERA_TYPES)) != CAMERA_TYPES:
            raise ValueError('S1 requires the three canonical camera types')
        schedule = cfg['scheduled_sampling']
        if schedule['max_own_probability'] != .5 or schedule['force_from_step'] != 1:
            raise ValueError('S1 requires max_own_probability=0.5 and force_from_step=1')


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


