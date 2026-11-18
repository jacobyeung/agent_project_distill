"""P3 routing traces inside the C1 trainer.

A routing row trains the language model on derivgen's canonical trace verbatim.
Injected tool outputs (`<tool_response>...</tool_response>`, delimiters included)
carry no language loss. Scheduled sampling replaces those outputs with values
from the model's own heads: one no-grad prefix forward reads pose, gravity and
point depth; a fixed, parameter-free layer turns them into derivgen's printed
numbers; the vendored printed-point calculator recomputes every calculator
response from the printed points. The model-authored text is unchanged.
"""
import copy
import hashlib
import json
import math
import random
import sqlite3
from pathlib import Path

import numpy as np
import torch

from . import p3_printed_calculator as calculator
from . import p3_printed_calculator_v2 as calculator_v2
from .camera_targets import rotation_from_xyzw
from .p3_provenance import file_pin, load, pinned, write
from . import ground_rows

ROUTING_SCHEMA = 'c1-routing-stream-v1'
V3_TRACE_REVISIONS = ('3.11', '3.12', '3.12.1', '3.12.2', '3.13', '3.14')
FORMS = ('spec-v3.8-calculator-v2',)
THINK = '<think>\n'
PATCH = 10.0
STENCIL = np.array([(dx, dy) for dx in np.linspace(-PATCH, PATCH, 5) for dy in np.linspace(-PATCH, PATCH, 5)])
FLIP = np.diag([1., -1., 1.])
HEAD_TOOLS = ('depth_at', 'pose', 'move', 'turn')
POSE_TOOLS = ('pose', 'move', 'turn')
# Dedicated tokenizer tokens for the head openers (SELF_ROUTING_DESIGN 1.1); arguments stay text.
OPENERS = ('<depth_at', '<move', '<pose', '<turn', '<box_3d')
SEGMENTS = ('plan', 'opener', 'arguments', 'calculator', 'prose', 'answer', 'tool')
# P3 v1 policy (SELF_ROUTING_DESIGN 1.3). route: plan-first trace (head calls where the family has
# them); direct: a reasoning trace without tool calls. Types outside the table are refused.
POLICY_VERSION = 'p3-v1-20261108'
POLICY = dict(
    route=('camera_displacement', 'camera_movement_direction', 'camera_rotation', 'object_abs_distance',
           'absolute_distance_object', 'object_rel_direction_medium', 'object_rel_direction_hard',
           'relative_direction_object', 'absolute_direction_object', 'object_rel_distance',
           'relative_distance_object', 'obj_appearance_order'),
    direct=('object_size_estimation', 'absolute_size_object', 'relative_size_object', 'room_size_estimation',
            'route_planning', 'object_rel_direction_easy', 'object_counting', 'absolute_count', 'relative_count',
            'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf',
            'obj_obj_relative_pos_ud', 'camera_obj_abs_dist', 'camera_obj_rel_dist', 'camera_obj_rel_dist_v1',
            'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3'))
# Final-run policies (POSE_ACCURACY_BRIDGE_20261108): camera motion always routes; the VSI geometry
# family routes only if night-1 heads pass break-even on held-out scenes; the rest answers directly.
CAMERA_MOTION = ('camera_displacement', 'camera_movement_direction', 'camera_rotation')
GEOMETRY = ('object_abs_distance', 'absolute_distance_object', 'object_rel_direction_medium',
            'object_rel_direction_hard', 'relative_direction_object', 'absolute_direction_object',
            'object_rel_distance', 'relative_distance_object', 'room_size_estimation')
ALL_TYPES = tuple(sorted(set(POLICY['route']) | set(POLICY['direct'])))
CP2_ROUTED = CAMERA_MOTION + ('object_abs_distance', 'absolute_distance_object', 'object_rel_direction_medium',
                              'object_rel_direction_hard', 'object_rel_distance', 'relative_distance_object',
                              'camera_obj_abs_dist')
POLICIES = {
    POLICY_VERSION: POLICY,
    'final-camera-geometry-20261108': dict(
        route=CAMERA_MOTION + GEOMETRY,
        direct=tuple(t for t in ALL_TYPES if t not in CAMERA_MOTION + GEOMETRY)),
    'final-camera-only-20261108': dict(
        route=CAMERA_MOTION, direct=tuple(t for t in ALL_TYPES if t not in CAMERA_MOTION)),
    'cp2-tool-mode-20261109': dict(
        route=CAMERA_MOTION + GEOMETRY + ('camera_obj_abs_dist',),
        direct=tuple(t for t in ALL_TYPES if t not in CAMERA_MOTION + GEOMETRY + ('camera_obj_abs_dist',))),
    # Without a prompt flag, the data alone says which types route: exactly the ten types that have v3.11 routed
    # traces, so a config route table built from it drops their direct VQA rows and keeps every other type direct.
    'cp2-routed-20261110': dict(
        route=CP2_ROUTED, direct=tuple(t for t in ALL_TYPES if t not in CP2_ROUTED)),
}
BOTH_TYPES = ('object_counting', 'object_size_estimation', 'absolute_size_object', 'object_rel_distance', 'relative_distance_object',
              'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
              'object_abs_distance', 'absolute_distance_object')
POLICIES['both-path-20261116'] = dict(route=CAMERA_MOTION, both=BOTH_TYPES,
    direct=tuple(t for t in ALL_TYPES if t not in CAMERA_MOTION + BOTH_TYPES))
EVENT_KINDS = ('plan', 'canonical_text', 'correction', 'canonical_paragraph', 'tool_call',
               'calculator_call', 'tool_response', 'calculator_response', 'decision')


class RenderError(ValueError):
    pass


def validate_tool_mode_flag(flag):
    if not isinstance(flag, str) or not flag.strip() or flag != flag.strip() or '\n' in flag or len(flag) > 200:
        raise ValueError('tool_mode_flag must be one non-empty stripped line of at most 200 characters')


def tool_mode(row, flag):
    """Dual-mode prompt: a routed row (category 'route') carries the flag line before its question.

    Direct rows never carry it, so a routed type keeps its direct rows; at decode the harness adds
    the same line exactly when the route table routes the item's type."""
    if not flag or (row.get('routing') or {}).get('category') != 'route':
        return row
    inputs = row['student_input']
    return {**row, 'student_input': {**inputs, 'question': flag + '\n' + inputs['question']}}


def r2(x):
    return round(float(x), 2) + 0.0


def f2(x):
    return f'{r2(x):.2f}'


def s2(x):
    return f'{r2(x):+.2f}'


def vec(p):
    return '(' + ', '.join(f2(x) for x in p) + ')'


def wrap(deg):
    return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180


def r8(a):
    return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0


# --------------------------------------------------------------------------- rendering
def render_full(events, answer):
    """Byte-for-byte mirror of derivgen canon_render.render, plus segment ranges.

    Segments (character ranges of the target) tag trained tokens for per-segment CE:
    plan, opener (`<depth_at`, `<move`, ...), arguments, calculator command, prose,
    answer (`\n</think>\n\n` + answer) and tool (masked responses).
    """
    if ground_rows.is_ground(events):
        return ground_rows.render_ground(events, answer)
    parts, spans, segments, cursor = [], [], [], 0

    def emit(text, segment, index=None, call_id=None):
        nonlocal cursor
        start = cursor
        parts.append(text)
        cursor += len(text)
        segments.append((start, cursor, segment))
        if call_id is not None:
            spans.append({'start': start, 'end': cursor, 'call_id': call_id, 'event_index': index})

    emit(THINK, 'plan')
    for index, event in enumerate(events):
        kind = event['kind']
        if kind == 'plan':
            emit(event['text'] + '\n\n', 'plan')
        elif kind in ('canonical_text', 'correction'):
            emit(event['text'], 'prose')
        elif kind == 'canonical_paragraph':
            emit('\n\n', 'prose')
        elif kind == 'calculator_call':
            emit(event.get('prefix', '') + event['command'], 'calculator')
        elif kind == 'tool_call':
            prefix, token = event.get('prefix', ''), event['token']
            opener = next((o for o in (*OPENERS, '<ground', '<gap') if token.startswith(o)), None)
            if opener is None:
                raise RenderError('head call without a known opener')
            emit(prefix, 'prose')
            emit(opener, 'opener')
            emit(token[len(opener):], 'arguments')
        elif kind in ('tool_response', 'calculator_response'):
            text = event['response']['text'] if kind == 'calculator_response' else event['text']
            emit('<tool_response>' + text + '</tool_response>', 'tool', index, event['call_id'])
        elif kind != 'decision':
            raise RenderError('unknown event kind ' + str(kind))
    emit('\n</think>\n\n' + str(answer), 'answer')
    return ''.join(parts), spans, segments


def render(events, answer):
    target, spans, _ = render_full(events, answer)
    return target, spans


def check_row(row):
    """Admission of one derivgen-row-v2 routing row; the stored target must re-render exactly."""
    if row.get('form') in ground_rows.FORMS.values():
        if row.get('trace_contract') == 'next-leg-r2-v1' or row.get('r2_source_sha256'):
            from .r2_contract import event_row
            return event_row(row)
        return ground_rows.validate(row)
    if row.get('schema') != 'derivgen-row-v2' or row.get('form') not in FORMS:
        raise ValueError('Routing rows require derivgen-row-v2 canonical v3.8 form')
    if row.get('infrastructure_only') is not False:
        raise ValueError('Infrastructure-only rows cannot train')
    target, spans = render(row['events'], row['answer'])
    if target != row['target'] or not target.startswith(THINK):
        raise ValueError('Stored target differs from its events')
    require_training_think(target)
    stored = [(s['start'], s['end'], s['call_id']) for s in row['tool_output_spans']]
    if stored != [(s['start'], s['end'], s['call_id']) for s in spans]:
        raise ValueError('Stored tool spans differ from the rendered target')
    return target, spans


# --------------------------------------------------------------------------- fixed layer
def level_basis(rotation, down):
    forward = np.asarray(rotation, dtype=np.float64)[:, 2].copy()
    forward -= float(forward @ down) * down
    if np.linalg.norm(forward) < 1e-6:
        raise RenderError('vertical_camera_heading')
    forward /= np.linalg.norm(forward)
    right = np.cross(down, forward)
    return np.column_stack((right, down, forward))


class OwnGeometry:
    """Fixed, parameter-free unprojection and pose layer over own (or hybrid) head outputs.

    pose9: [F, 9], F in {32, 64} per-frame camera codes E_k = inv(C_k) C_1 (t, q xyzw, FoV vertical,
    FoV horizontal), frame 1 = slot 0. up: frame-1 OpenCV gravity-up vector (None means
    frame-1 camera -y). depth(frame, uv[n, 2]) -> optical-axis metric depth [n].
    Conventions match derivgen's GT layer: frame-1 level frame, public y up, p30 depth
    over a 5x5 +-10 stencil, spread (p80-p20)/max(p50, 1e-3), centred-FoV rays.
    The FoV that conditioned depth (pose slots 7:9) is the FoV used here: `fov` [F, 2]
    overrides pose9's slots when pose comes from GT but depth from the own head.
    depth None means GT clicks: `recorded` {label: (public camera, spread)} supplies them
    and the pose source places them in frame 1 (the reverse hybrid).
    Production refuses a missing gravity vector (require_up).
    """
    def __init__(self, pose9, up, depth, fov=None, recorded=None, require_up=True, readout=None, heading=None):
        self.readout = readout
        self.heading = heading
        self.p = np.asarray(pose9, dtype=np.float64)
        if self.p.shape not in ((32,9),(64,9)) or not np.isfinite(self.p).all():
            raise RenderError('own pose readout must be finite [32 or 64, 9]')
        if up is None and require_up:
            raise RenderError('gravity_unavailable')
        self.fov_override = None if fov is None else np.asarray(fov, dtype=np.float64)
        if self.fov_override is not None and (self.fov_override.shape != (len(self.p), 2) or not np.isfinite(self.fov_override).all()):
            raise RenderError('own FoV readout must be finite [F, 2]')
        self.recorded = recorded or {}
        up = np.array([0., -1., 0.]) if up is None else np.asarray(up, dtype=np.float64)
        if up.shape != (3,) or not np.isfinite(up).all() or np.linalg.norm(up) < 1e-6:
            raise RenderError('invalid own gravity')
        self.down = -up / np.linalg.norm(up)
        self.depth = depth
        self._bases = {}
        self._poses = {}
        self.to_l1  # Preserve construction-time validation in the active context.

    @property
    def to_l1(self):
        from trace_format.contracts import new_contracts, heading_plane_min
        key = (new_contracts(), heading_plane_min())
        if key not in self._bases:
            self._bases[key] = self._basis()
        return self._bases[key]

    def _basis(self):
        from trace_format.contracts import new_contracts
        try:
            basis = FLIP @ level_basis(np.eye(3), self.down).T
        except RenderError:
            if not new_contracts():
                raise
            # Private metric coordinates only. No horizontal component of this basis is published.
            right = np.array([1., 0., 0.])
            right -= (right @ self.down) * self.down
            right /= np.linalg.norm(right)
            basis = np.stack((right, -self.down, np.cross(right, self.down)))
        if new_contracts():
            from trace_format.contracts import heading_available, private_metric_basis
            if not heading_available(self):
                # Anchor hidden rounded operands independently of reference yaw.
                # These horizontal coordinates are never printed as public f1.
                private = private_metric_basis(lambda k: self.camera(k)[0], -self.down)
                if private is not None:
                    basis = private.T
        return basis

    def camera(self, k):
        if type(k) is not int or not 1 <= k <= len(self.p):
            raise RenderError('frame_out_of_range')
        if k == 1:
            return np.eye(3), np.zeros(3)
        q = self.p[k - 1, 3:7]
        if np.linalg.norm(q) < 1e-6:
            raise RenderError('zero quaternion')
        r_rel = rotation_from_xyzw(q / np.linalg.norm(q))
        rotation = r_rel.T
        return rotation, -rotation @ self.p[k - 1, :3]

    def fov(self, k):
        vertical, horizontal = self.p[k - 1, 7:9] if self.fov_override is None else self.fov_override[k - 1]
        if not (0 < vertical < math.pi and 0 < horizontal < math.pi):
            raise RenderError('invalid own FoV')
        return vertical, horizontal

    def camera_pose(self, k):
        rotation, centre = self.camera(k)
        return dict(camera_R_L1=r8(self.to_l1 @ rotation), camera_t_L1=r8(self.to_l1 @ centre))

    def pose(self, k):
        from trace_format.contracts import new_contracts, heading_plane_min
        key = (new_contracts(), heading_plane_min(), k)
        if key not in self._poses:
            rotation, centre = self.camera(k)
            level = r8(self.to_l1 @ level_basis(rotation, self.down))
            self._poses[key] = dict(camera_R_L1=r8(self.to_l1 @ rotation), camera_t_L1=r8(self.to_l1 @ centre),
                                  level_R_L1=level,
                                  yaw_degree=self.heading('yaw',level) if self.heading is not None else
                                  round(math.degrees(math.atan2(-level[0][2], level[2][2]))))
        return self._poses[key]

    def click(self, k, uv, label=None):
        from trace_format.contracts import new_contracts
        if self.depth is None:
            cam, spread = self.recorded[label]
            pose = self.camera_pose(k) if new_contracts() else self.pose(k)
            f1 = pose['camera_R_L1'] @ (np.asarray(cam, dtype=np.float64) * [1, -1, 1]) + pose['camera_t_L1']
            return list(cam), [r2(x) for x in f1], spread
        if self.readout is not None:
            result = self.readout(k, uv, self.fov(k))
            cam, spread = result['camera_point'].detach().cpu().numpy(), result['spread']
            pose = self.camera_pose(k) if new_contracts() else self.pose(k)
            f1 = pose['camera_R_L1'] @ cam + pose['camera_t_L1']
            return [r2(x*s) for x,s in zip(cam,(1,-1,1))], [r2(x) for x in f1], r2(spread)
        uv = np.asarray(uv, dtype=np.float64)
        points = np.clip(uv[None] + STENCIL, 0, 999.9)
        values = np.asarray(self.depth(k, points), dtype=np.float64)
        if values.shape != (len(STENCIL),) or not np.isfinite(values).all() or (values <= 0).any():
            raise RenderError('invalid own depth')
        p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / max(p50, 1e-3)
        vertical, horizontal = self.fov(k)
        ray = np.array([(uv[0] / 500 - 1) * math.tan(horizontal / 2), (uv[1] / 500 - 1) * math.tan(vertical / 2), 1.])
        cam = r8(ray * p30)
        pose = self.camera_pose(k) if new_contracts() else self.pose(k)
        f1 = pose['camera_R_L1'] @ cam + pose['camera_t_L1']
        return [r2(x * s) for x, s in zip(cam, (1, -1, 1))], [r2(x) for x in f1], r2(spread)

    def pose_text(self, k):
        from trace_format.contracts import heading_available, partial_f1, new_contracts
        if new_contracts() and k == 1:
            return 'f1 centre (0.00, 0.00, 0.00) m, yaw 0 deg'
        if not heading_available(self):
            p = self.camera_pose(k)
            return 'f1 centre '+partial_f1(p['camera_t_L1'], f2)+' m, yaw heading unavailable'
        if not heading_available(self, k):
            return 'f1 centre '+vec(self.camera_pose(k)['camera_t_L1'])+f' m, yaw heading unavailable (frame {k})'
        p = self.pose(k)
        return f"f1 centre {vec(p['camera_t_L1'])} m, yaw {p['yaw_degree']} deg"

    def move_text(self, i, j):
        from trace_format.contracts import heading_available, new_contracts
        if not heading_available(self, i):
            delta = self.camera(j)[1] - self.camera(i)[1]
            # Preserve the sealed distance's rounding at half-cent boundaries.
            # Exact vertical poses have no sealed level basis; their norm remains
            # available directly from the displacement.
            try:
                pi, pj = self.pose(i), self.camera_pose(j)
                distance = np.linalg.norm(pi['level_R_L1'].T @ (pj['camera_t_L1'] - pi['camera_t_L1']))
            except RenderError:
                distance = np.linalg.norm(delta)
            return (f'dx = heading unavailable (frame {i}), dy = {s2(-self.down @ delta)} m, '
                    f'dz = heading unavailable (frame {i}), distance = {f2(distance)} m')
        pi, pj = self.pose(i), self.camera_pose(j) if new_contracts() else self.pose(j)
        local = pi['level_R_L1'].T @ (pj['camera_t_L1'] - pi['camera_t_L1'])
        distance = float(np.linalg.norm(local))
        local[1] *= -1
        return f'dx = {s2(local[0])} m, dy = {s2(local[1])} m, dz = {s2(local[2])} m, distance = {f2(distance)} m'

    def turn_text(self, i, j):
        from trace_format.contracts import heading_available
        missing = [k for k in dict.fromkeys((i, j)) if not heading_available(self, k)]
        if missing:
            return 'turn = heading unavailable (frames '+','.join(map(str, missing))+')'
        if self.heading is not None:
            turn=self.heading('turn',self.pose(i)['level_R_L1'],self.pose(j)['level_R_L1'])
            return f'turn = {turn:+d} deg'
        a, b = (self.pose(k)['level_R_L1'][[0, 2], 2] for k in (i, j))
        turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))
        return f'turn = {turn:+d} deg'


class RecordedGeometry:
    """Replays the row's own GT printed values; the renderer's equivalence fixture."""
    def __init__(self, row):
        self.points = {p['label']: p for e in row['events'] if e['kind'] == 'tool_response'
                       and e['name'] == 'depth_at' for p in e['points']}
        self.calls = {e['call_id']: e for e in row['events'] if e['kind'] == 'tool_response'}

    def click_label(self, label):
        p = self.points[label]
        return p['camera'], p['f1'], p['spread']

    def response(self, call_id, name):
        e = self.calls[call_id]
        values = e.get('values', {})
        if name == 'pose':
            return f"f1 centre {vec(values[call_id + '.t']['value'])} m, yaw {values[call_id + '.yaw']['value']} deg"
        if name == 'move':
            d = values[call_id + '.delta']['value']
            return (f'dx = {s2(d[0])} m, dy = {s2(d[1])} m, dz = {s2(d[2])} m, '
                    f"distance = {f2(values[call_id + '.distance']['value'])} m")
        return f"turn = {values[call_id + '.turn']['value']:+d} deg"


def depth_queries(row):
    """Ordered (frame, uv) clicks of every depth_at call; the readout's query plan."""
    calls, queries = {}, []
    for e in row['events']:
        if e['kind'] == 'tool_call':
            calls[e['call_id']] = e
        elif e['kind'] == 'tool_response' and e['name'] == 'depth_at':
            pts = calls[e['call_id']]['arguments']['pts']
            if len(pts) != len(e['points']):
                raise RenderError('depth_at point count differs from its response')
            queries.extend((p['actual_frame'], [float(x) for x in uv]) for uv, p in zip(pts, e['points']))
    return queries


def calculator_for(row):
    return calculator if str(row.get('trace_revision')) in V3_TRACE_REVISIONS else calculator_v2


def rerender(row, geometry):
    """Re-render every head and calculator response; model-authored events stay verbatim."""
    if ground_rows.is_ground(row.get('events')):
        raise RenderError('Grounded own-value substitution requires a bound live grounding session')
    registry, calls, events = calculator_for(row).PrintedPointRegistry(), {}, []
    recorded = isinstance(geometry, RecordedGeometry)
    try:
        for event in row['events']:
            kind = event['kind']
            if kind not in EVENT_KINDS:
                raise RenderError('unknown event kind')
            if kind in ('tool_call', 'calculator_call'):
                calls[event['call_id']] = event
            if kind == 'tool_response':
                name, call = event['name'], calls[event['call_id']]
                if name not in HEAD_TOOLS:
                    raise RenderError('unknown head tool ' + str(name))
                from trace_format.contracts import heading_available, new_contracts
                if name == 'depth_at':
                    lines = []
                    for uv, p in zip(call['arguments']['pts'], event['points']):
                        cam, f1, spread = (geometry.click_label(p['label']) if recorded
                                           else geometry.click(p['actual_frame'], uv, p['label']))
                        lines.append(registry.register(camera=cam, f1=f1, spread=spread,
                                                       requested_frame=p['requested_frame'],
                                                       actual_frame=p['actual_frame'], label=p['label'],
                                                       **({'heading_defined': heading_available(geometry)}
                                                          if new_contracts() and not recorded else {}))['line'])
                    text = '\n'.join(lines)
                elif recorded:
                    text = geometry.response(event['call_id'], name)
                elif name == 'pose':
                    text = geometry.pose_text(call['arguments']['frame'])
                elif name == 'move':
                    text = geometry.move_text(call['arguments']['from'], call['arguments']['to'])
                else:
                    text = geometry.turn_text(call['arguments']['from'], call['arguments']['to'])
                event = {k: v for k, v in event.items() if k not in ('points', 'values')}
                event['text'] = text
            elif kind == 'calculator_response':
                event = {**event, 'response': registry.execute(calls[event['call_id']]['command'])}
            events.append(event)
    except (calculator.CalculatorError, calculator_v2.CalculatorError, KeyError, IndexError) as exc:
        raise RenderError(f'{type(exc).__name__}: {exc}') from exc
    return render_full(events, row['answer'])


# --------------------------------------------------------------------------- tokens
def suffix_mask(tokenizer, suffix, target, spans):
    """Token ids of the assistant suffix and the True-where-trained mask.

    The generation prompt already ends with the opening '<think>\\n'; suffix char i is
    target char i + len(THINK). Every token inside a tool span, delimiters included,
    is excluded; '<tool_response>' and '</tool_response>' are single special tokens,
    so no token straddles a span edge (checked).
    """
    if not target.startswith(THINK) or not suffix.startswith(target[len(THINK):]):
        raise ValueError('Assistant suffix does not continue the generation prompt with the target')
    encoded = tokenizer(suffix, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = encoded['input_ids'], encoded['offset_mapping']
    if ids != tokenizer.encode(suffix, add_special_tokens=False):
        raise ValueError('Offset tokenization differs from the trainer tokenization')
    shift = len(THINK)
    ranges = [(s['start'] - shift, s['end'] - shift) for s in spans]
    train = []
    for a, b in offsets:
        inside = [lo <= a and b <= hi for lo, hi in ranges]
        overlap = [a < hi and lo < b for lo, hi in ranges]
        if any(overlap) and not any(inside):
            raise ValueError('A token straddles a tool-output span edge')
        train.append(not any(inside))
    masked = ''.join(suffix[a:b] for (a, b), keep in zip(offsets, train) if not keep)
    if masked != ''.join(target[s['start']:s['end']] for s in spans):
        raise ValueError('Masked tokens differ from the tool-output spans')
    # Parity with inference: a response tokenized alone equals its slice of the whole suffix.
    for lo, hi in ranges:
        inside = [i for i, (a, b) in enumerate(offsets) if lo <= a and b <= hi]
        if [ids[i] for i in inside] != tokenizer.encode(suffix[lo:hi], add_special_tokens=False):
            raise ValueError('A tool response tokenized alone differs from its whole-suffix slice')
    return ids, train, offsets


def suffix_tokens(processor, row, target, spans):
    require_training_think(target)
    from .batches import training_text
    inputs = row['student_input']
    _, suffix = training_text(processor, inputs['question'], inputs.get('options') or [], target)
    return suffix_mask(processor.tokenizer, suffix, target, spans)


def segment_ids(offsets, segments):
    """Segment index of every suffix token (by its first character in the target)."""
    shift, result, j = len(THINK), [], 0
    for a, _ in offsets:
        while j + 1 < len(segments) and segments[j][1] <= a + shift:
            j += 1
        result.append(SEGMENTS.index(segments[j][2]) if segments[j][0] <= a + shift < segments[j][1]
                      else SEGMENTS.index('answer'))
    return result


def finish(batch, ids, train, row, target, spans, mode, offsets=None, segments=None, faithful=False):
    if not faithful and mode != 'gt' and spans and offsets is not None:
        # Own values with GT-authored prose: never train text after the first own-value response
        # (orchestrator 14:44Z fallback until the faithful materializer re-derives the prose).
        cut = spans[0]['end'] - len(THINK)
        train = [keep and a < cut for keep, (a, _) in zip(train, offsets)]
    labels = batch['labels'][0]
    supervised = torch.where(labels != -100)[0]
    start = int(supervised[0])
    if (len(supervised) != len(ids) or int(supervised[-1]) != start + len(ids) - 1
            or batch['input_ids'][0, start:start + len(ids)].tolist() != ids):
        raise ValueError('Assistant suffix tokens differ from the encoded batch')
    labels[start:start + len(ids)][~torch.tensor(train)] = -100
    batch['aux_suffix_start'] = torch.tensor([start], device=labels.device)
    if segments is not None:
        tags = torch.full_like(batch['input_ids'], -1)
        tags[0, start:start + len(ids)] = torch.tensor(segment_ids(offsets, segments))
        batch['aux_segments'] = tags
    if batch['input_ids'].shape[1] > 16384:
        raise ValueError('Complete routing row exceeds 16384 tokens; no truncation')
    return batch, dict(qid=row['routing']['qid'], values=mode, suffix_tokens=len(ids),
                       trained_tokens=int(sum(train)), tool_spans=len(spans),
                       target_sha256=hashlib.sha256(target.encode()).hexdigest())


def encode(processor, row, carrier_placement, training_mode, frame_layout, gap, geometry_online=None):
    """GT-valued routing row: native video/carrier encoding, tool outputs masked."""
    from . import carrier_c1_data as data
    target, spans, segments = render_full(row['routing']['events'], row['routing']['answer'])
    ids, train, offsets = suffix_tokens(processor, row, target, spans)
    batch, _, _ = data.encode(processor, {**row, 'target': target}, {}, 'vqa', carrier_placement,
                              training_mode, frame_layout, gap, geometry_online=geometry_online)
    return finish(batch, ids, train, row, target, spans, 'gt', offsets, segments)


def encode_own(processor, row, gt_batch, target, spans, segments=None, mode='own', faithful=False):
    """Own-valued routing row: splice the re-rendered suffix after the unchanged prompt."""
    ids, train, offsets = suffix_tokens(processor, row, target, spans)
    batch = splice(gt_batch, ids, processor.tokenizer.pad_token_id)
    return finish(batch, ids, train, row, target, spans, mode, offsets, segments, faithful=faithful)


def splice(batch, ids, pad_id):
    """Replace the assistant suffix of an encoded GT batch; video, carriers and prompt stay."""
    start = int(batch['aux_suffix_start'][0])
    length = start + len(ids)
    padded = math.ceil(length / 8) * 8
    out = dict(batch)
    head = batch['input_ids'][:, :start]
    out['input_ids'] = torch.cat((head, head.new_tensor([ids]), head.new_full((1, padded - length), pad_id)), 1)
    out['attention_mask'] = (torch.arange(padded, device=head.device) < length)[None].to(batch['attention_mask'].dtype)
    if 'mm_token_type_ids' in batch:
        out['mm_token_type_ids'] = torch.cat((batch['mm_token_type_ids'][:, :start],
                                              batch['mm_token_type_ids'].new_zeros((1, padded - start))), 1)
    labels = torch.full_like(out['input_ids'], -100)
    labels[:, start:length] = out['input_ids'][:, start:length]
    out['labels'] = labels
    return out


def prefix_batch(batch):
    """The question-independent video+carrier prefix the heads read."""
    end = int(batch['aux_video_prefix_end'][0]) + 1
    out = {k: v for k, v in batch.items() if k not in ('labels', 'aux_suffix_start', 'aux_segments')}
    for key in ('input_ids', 'attention_mask', 'mm_token_type_ids'):
        if key in out:
            out[key] = out[key][:, :end]
    return out


# --------------------------------------------------------------------------- sampling
SCHEDULE_NUMBERS = ('max_own_probability', 'pose_open_deg', 'pose_full_deg', 'fov_open_deg', 'depth_open_absrel',
                    'exposure_probability')


def validate_schedule(schedule):
    """Per-head gates (SELF_ROUTING_DESIGN 1.2); force_from_step opens both at max p (test run)."""
    keys = set(SCHEDULE_NUMBERS) | {'seed', 'ema_steps', 'force_from_step', 'exposure_from_step'}
    if not isinstance(schedule, dict) or set(schedule) != keys:
        raise ValueError('scheduled_sampling keys: ' + ', '.join(sorted(keys)))
    if (any(type(schedule[k]) not in (int, float) or not math.isfinite(schedule[k]) or schedule[k] < 0
            for k in SCHEDULE_NUMBERS) or not schedule['max_own_probability'] <= 1
            or not schedule['pose_full_deg'] < schedule['pose_open_deg']
            or type(schedule['seed']) is not int or type(schedule['ema_steps']) is not int or schedule['ema_steps'] < 1
            or any(not (schedule[k] is None or (type(schedule[k]) is int and schedule[k] >= 0))
                   for k in ('force_from_step', 'exposure_from_step'))
            or not schedule['exposure_probability'] <= schedule['max_own_probability']):
        raise ValueError('Invalid scheduled_sampling values')
    return schedule


class Gates:
    """Own-value gates from all-reduced pose-stream EMAs; identical on every rank.

    Depth opens when the depth head starts from the Stage-1 V-C artifact and the FoV
    error EMA is below fov_open_deg, otherwise when the depth AbsRel EMA is below
    depth_open_absrel; then p = max. Pose opens below pose_open_deg and its p ramps
    linearly to max as the rotation EMA falls to pose_full_deg. Exposure floor: from
    exposure_from_step both heads draw own values with at least exposure_probability,
    whatever the gates say, so the model has seen its own values before it must use them.
    """
    METRICS = ('rotation_deg', 'fov_deg', 'depth_absrel')

    def __init__(self, schedule, stage1_depth, ema=None):
        self.schedule, self.stage1_depth = validate_schedule(schedule), bool(stage1_depth)
        self.ema = dict(ema or {})

    def update(self, metrics):
        alpha = 2. / (self.schedule['ema_steps'] + 1)
        for key in self.METRICS:
            value = metrics.get(key)
            if value is None or not math.isfinite(value):
                continue
            self.ema[key] = value if key not in self.ema else (1 - alpha) * self.ema[key] + alpha * value

    def state(self, step):
        s, ema = self.schedule, self.ema
        top = s['max_own_probability']
        forced = s['force_from_step'] is not None and step >= s['force_from_step']
        if self.stage1_depth:
            # V-C trained on 16 fused-pair groups; the AbsRel EMA must also hold in this layout.
            depth_open = ('fov_deg' in ema and ema['fov_deg'] < s['fov_open_deg']
                          and ema.get('depth_absrel', float('inf')) < s['depth_open_absrel'])
        else:
            depth_open = 'depth_absrel' in ema and ema['depth_absrel'] < s['depth_open_absrel']
        rotation = ema.get('rotation_deg')
        pose = 0. if rotation is None or rotation >= s['pose_open_deg'] else \
            top * min(1., (s['pose_open_deg'] - rotation) / (s['pose_open_deg'] - s['pose_full_deg']))
        floor = s['exposure_probability'] if (s['exposure_from_step'] is not None
                                              and step >= s['exposure_from_step']) else 0.
        return dict(p_depth=top if (forced or depth_open) else floor, p_pose=top if forced else max(pose, floor),
                    forced=forced, exposure_floor=floor, ema=dict(ema))

    def decide(self, step, microstep):
        state = self.state(step)
        seed = int(hashlib.sha256(f"{self.schedule['seed']}:{step}:{microstep}".encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        u_depth, u_pose = rng.random(), rng.random()
        return u_depth < state['p_depth'], u_pose < state['p_pose']


def row_geometry(row, readout, queries, index, depth_own, pose_own):
    """Choose the value source per head for one routing row (None: train the GT row).

    Rows with pose calls stay GT until pose is own. Depth-only rows use own depth with
    GT pose (gt_pose9/gt_up) while pose is closed; pose-own rows with GT depth place
    the recorded GT clicks with own pose (the reverse hybrid).
    """
    names = {e['name'] for e in row['events'] if e['kind'] == 'tool_response'}
    if not names:
        return None, 'no_head_calls'
    if names & set(POSE_TOOLS) and not pose_own:
        return None, 'pose_gate_closed'
    depth_used = 'depth_at' in names and depth_own
    if not depth_used and not pose_own:
        return None, 'gates_closed'
    own_pose = readout['pose'][0].double().cpu().numpy()
    if pose_own:
        if readout.get('gravity') is None:
            raise RenderError('gravity_unavailable')
        pose9, up = own_pose, readout['gravity'][0].double().cpu().numpy()
    else:
        if 'gt_pose9' not in row or 'gt_up' not in row:
            return None, 'gt_pose_missing'
        pose9, up = np.asarray(row['gt_pose9'], dtype=np.float64), np.asarray(row['gt_up'], dtype=np.float64)
    recorded = {p['label']: (p['camera'], p['spread']) for e in row['events']
                if e['kind'] == 'tool_response' and e['name'] == 'depth_at' for p in e['points']}
    if depth_used:
        geometry = own_geometry(readout, queries, index)
        return OwnGeometry(pose9, up, geometry.depth, fov=own_pose[:, 7:9]), \
            ('own' if pose_own else 'own_depth_gt_pose')
    return OwnGeometry(pose9, up, None, recorded=recorded), ('own' if 'depth_at' not in names else 'own_pose_gt_depth')


def query_tensor(queries, k_max=None, *, frame_count=32):
    """[F, K, 2] stencil queries and each click's (frame, slot) index."""
    if type(frame_count) is not int or frame_count not in (32, 64):
        raise RenderError("unsupported_frame_count")
    per_frame, index = [[] for _ in range(frame_count)], []
    for frame, uv in queries:
        if type(frame) is not int or not 1 <= frame <= frame_count:
            raise RenderError('frame_out_of_range')
        stencil = np.clip(np.asarray(uv)[None] + STENCIL, 0, 999.9)
        index.append((frame, len(per_frame[frame - 1])))
        per_frame[frame - 1].extend(stencil.tolist())
    k = max([len(p) for p in per_frame] + [1])
    k = max(k, k_max or 0)
    uv = np.full((frame_count, k, 2), 500., dtype=np.float32)
    for f, points in enumerate(per_frame):
        if points:
            uv[f, :len(points)] = points
    return torch.from_numpy(uv), index


def own_geometry(readout, queries, index, require_up=True):
    pose = readout['pose'][0].double().cpu().numpy()
    up = None if readout.get('gravity') is None else readout['gravity'][0].double().cpu().numpy()
    depth = None if readout.get('depth') is None else readout['depth'].double().cpu().numpy()
    lookup = {}
    for (frame, uv), (f, slot) in zip(queries, index):
        lookup[(frame, tuple(uv))] = (f, slot)

    def depth_fn(frame, points):
        if depth is None:
            raise RenderError('own depth head unavailable')
        uv = tuple(float(x) for x in points[len(STENCIL) // 2])
        f, slot = lookup[(frame, uv)]
        return depth[f - 1, slot:slot + len(STENCIL)]
    return OwnGeometry(pose, up, depth_fn, require_up=require_up)


# --------------------------------------------------------------------------- tokens
def add_routing_tokens(processor, *, include_ground=False):
    """Add the head-opener tokens; record each one's plain-text constituents for init."""
    from transformers import AddedToken
    tokenizer = processor.tokenizer
    if any(o in tokenizer.get_vocab() for o in OPENERS):
        raise ValueError('Routing openers already exist in the tokenizer')
    constituents = {o: tokenizer.encode(o, add_special_tokens=False) for o in OPENERS}
    tokenizer.add_tokens([AddedToken(o, normalized=False, special=False) for o in OPENERS])
    ids = {o: tokenizer.convert_tokens_to_ids(o) for o in OPENERS}
    processor._routing_tokens = dict(ids=ids, constituents=constituents)
    if include_ground:
        from .mdg_decode_tokens import add_ground_tokens
        add_ground_tokens(processor)
    return processor._routing_tokens


def init_routing_embeddings(model, tokens):
    """Input and output rows of each opener = mean of its constituent tokens' rows."""
    rows = model.get_input_embeddings().weight
    head = model.get_output_embeddings().weight
    if max(tokens['ids'].values()) >= min(rows.shape[0], head.shape[0]):
        raise ValueError('Routing opener ids exceed the embedding rows')
    with torch.no_grad():
        for opener, index in tokens['ids'].items():
            parts = tokens['constituents'][opener]
            rows[index] = rows[parts].float().mean(0).to(rows.dtype)
            head[index] = head[parts].float().mean(0).to(head.dtype)


# --------------------------------------------------------------------------- stream build
def c1_row(row, rgb, path_map=None):
    """derivgen row + its RGB manifest -> the C1 row layout (student input is RGB only).

    The manifest supplies frames [{path, sha256, source_index}], fps and total_num_frames.
    path_map {old_prefix: new_prefix} relocates frame paths to the logical /data2 names the
    training job maps with STUDENT_FRAME_ROOT_MAP (as the VQA/pointing streams do); bytes stay pinned.
    """
    target, spans = check_row(row)
    frames = rgb['frames']
    if len(frames) not in (32, 64) or [f['source_index'] for f in frames] != row['provenance']['frame_indices']:
        raise ValueError('RGB manifest differs from the trace frame selection')
    missing = [k for k in ('fps', 'total_num_frames') if k not in rgb]
    if missing:
        raise ValueError('RGB manifest lacks ' + ', '.join(missing))
    fps = rgb['fps']

    def relocate(path):
        for old, new in (path_map or {}).items():
            if path.startswith(old):
                return new + path[len(old):]
        return path
    canonical = row['provenance']['canonical']
    source_identity = {}
    source_sha = row['provenance'].get('source_row_sha256')
    if source_sha is None and row.get('form') in ground_rows.FORMS.values():
        from .p3_provenance import digest
        source_sha = digest(row)
        source_identity = dict(source_identity_kind='generated_record', source_record_sha256=source_sha)
    if source_sha is None:
        raise ValueError('Routing row lacks source identity')
    # Division and exclusion keys use the rung-1 alias token, as every C1 stream does.
    dataset, scene = (row['provenance'].get('alias') or alias_of(canonical)).split('/', 1)
    return dict(qid=row['qid'], dataset=dataset, scene=scene, category='routing_trace',
                student_input=dict(frames=[dict(path=relocate(f['path']), sha256=f['sha256']) for f in frames],
                                   frame_indices=[f['source_index'] for f in frames],
                                   timestamps=[f['source_index'] / fps for f in frames], fps=fps,
                                   total_num_frames=rgb['total_num_frames'],
                                   question=row['question'], options=row.get('options') or [],
                                   **({'geometry_dense': rgb['geometry_dense']} if 'geometry_dense' in rgb else {})),
                target=target,
                # Preserve the audited source fields through the native store layout.
                **{k:row[k] for k in ('source_qid','candidate_id','question','question_type','answer',
                                     'gt_answer','ground_record','provenance','tool_output_spans') if k in row},
                routing=dict(qid=row['qid'], question_type=row['question_type'], form=row['form'],
                             events=row['events'], answer=row['answer'], gt_answer=row['gt_answer'],
                             tool_output_spans=row['tool_output_spans'],
                             physical_group=row['provenance'].get('physical_group'), canonical=canonical,
                             source_row_sha256=source_sha, **source_identity,
                             category=row.get('category', 'direct' if not row['tool_output_spans'] else 'route'),
                             head_layout=row.get('head_layout', 'paired_anchor'),
                             **{k: row[k] for k in ('gt_pose9', 'gt_up', 'trace_revision', 'ground_record',
                                                    'candidate_id', 'training_admitted') if k in row}))


ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3')
NATIVE = dict(scannet='scannet', scannetpp='scannetppv2', scannetppv2='scannetppv2', arkitscenes='arkitscenes')


def alias_of(canonical):
    """Division key 'dN/v<12 hex>' = 'v' + sha256('rung1 scene ' + native_dataset + '/' + scene)[:12]."""
    dataset, scene = canonical.split('/', 1)
    token = 'v' + hashlib.sha256(f'rung1 scene {NATIVE[dataset]}/{scene}'.encode()).hexdigest()[:12]
    return ALIAS[dataset] + '/' + token


def camera_filter(raw):
    """TRACE_POOL_V2_READ rules for camera rows (None keeps the row).

    Every row: no frame substitution. Movement: the winning horizontal component is >= 0.15 m,
    above |dy| and >= 0.10 m ahead of the runner-up. Rotation: |turn| < 165 deg.
    """
    events = raw['events']
    if any(p['requested_frame'] != p['actual_frame'] for e in events if e['kind'] == 'tool_response'
           and e['name'] == 'depth_at' for p in e['points']):
        return 'frame_substitution'
    if any(e['kind'] == 'tool_call' and 'image_frame' in e.get('arguments', {}) for e in events):
        return 'frame_substitution'
    qtype = raw['question_type']
    values = {k: v['value'] for e in events if e['kind'] == 'tool_response' for k, v in e.get('values', {}).items()}
    if qtype == 'camera_movement_direction':
        deltas = [v for k, v in values.items() if k.endswith('.delta')]
        if not deltas:
            return 'movement_without_move'
        dx, dy, dz = deltas[-1]
        win, runner = sorted((abs(dx), abs(dz)), reverse=True)
        if win < .15 or win <= abs(dy) or win - runner < .10:
            return 'movement_margin'
    if qtype == 'camera_rotation':
        turns = [v for k, v in values.items() if k.endswith('.turn') or k.endswith('.yaw')]
        if any(abs(t) >= 165 for t in turns if isinstance(t, (int, float))):
            return 'rotation_near_180'
    return None


def load_exclusions(pin):
    """Benchmark-scene exclusion names (schema benchmark_scene_exclusions_v1): listed scenes ('dN/sceneX'),
    room groups ('scannet/sceneNNNN', 'arkitscenes/venueN') and rung-1 tokens ('dN/v...').
    A KEEP contamination check (orchestrator 11-08)."""
    if pin is None:
        return set()
    data = load(pinned(pin))
    if data.get('schema') == 'scene-exclusions-v1':
        return set(data['names'])
    if data.get('schema') != 'benchmark_scene_exclusions_v1':
        raise ValueError('Exclusions must use schema benchmark_scene_exclusions_v1 or scene-exclusions-v1')
    return set(alias_names(data))


def alias_key(key):
    """'scannet/scene0078' -> 'd1/scene0078'; alias keys pass through."""
    if not key or '/' not in key:
        return key
    dataset, rest = key.split('/', 1)
    return f'{ALIAS.get(dataset, dataset)}/{rest}'


def alias_names(data):
    """All exclusion names in alias form only (dN/...), the shippable form of the list."""
    return sorted({alias_key(k) for k in data['scenes']} | {alias_key(k) for k in data.get('physical_groups', [])}
                  | {'/'.join(t) for t in data.get('rung1_tokens', [])})


def excluded(names, *keys):
    """True when any key (division alias, 'dN/scene', canonical, room group) is listed."""
    return bool(names) and any(k in names for k in keys if k)


def canonical_keys(canonical, group=None):
    keys = [alias_key(group)] if group else []
    if canonical and '/' in canonical:
        keys.append(alias_key(canonical))
    return keys


def require_training_think(target):
    """Legacy training targets must contain an explicit reasoning body."""
    if (not isinstance(target, str) or not target.startswith(THINK)
            or '</think>' not in target
            or not target[len(THINK):target.index('</think>')].strip()):
        raise ValueError('LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED')


def direct_row(raw):
    """Pack a concrete direct trace while preserving its exact target bytes."""
    target = raw.get('target')
    require_training_think(target)
    inputs = dict(raw['student_input'])
    count = len(inputs['frames'])
    if count not in (32, 64) or len(inputs['frame_indices']) != count:
        raise ValueError('Direct rows require 32 or 64 pinned native frames')
    from .r2_grammar import validate_direct
    answer = validate_direct(target, inputs['question'], count)
    if answer != str(raw['answer']):
        raise ValueError('Direct trace answer differs from its declared answer')
    suffix = '\n</think>\n\n' + answer
    if not target.endswith(suffix):
        raise ValueError('Direct trace target does not match the training renderer')
    body = target[len(THINK):-len(suffix)]
    inputs['timestamps'] = [k / inputs['fps'] for k in inputs['frame_indices']]
    dataset, scene = (alias_of(raw['canonical']) if 'canonical' in raw
                      else raw['dataset'] + '/' + raw['scene']).split('/', 1)
    events = [dict(kind='canonical_text', text=body)]
    return dict(qid=raw['qid'], dataset=dataset, scene=scene, category='routing_trace', student_input=inputs,
                target=target, routing=dict(qid=raw['qid'], question_type=raw['question_type'], form='direct_trace',
                                            canonical=raw.get('canonical'),
                                            events=events, answer=raw['answer'], gt_answer=raw['answer'],
                                            tool_output_spans=[], category='direct', head_layout='n/a'))


def build_routing_stream(source, rgb_index, division_pin, output, processor_root, max_suffix_tokens=9600,
                         verify_frames=True, allow_paired_anchor=False, policy=None, scene_role='train',
                         direct_source=None, exclusions=None, report_exclusions=None):
    """CPU parent data job: derivgen JSONL + RGB manifests -> immutable SQLite + receipt.

    rgb_index: JSON {"manifests": {rgb_manifest_sha256: local manifest path},
    "path_map": {old_frame_prefix: new_frame_prefix}}. Every
    frame is pinned when verify_frames; the trainer pins them again at read time.
    Rows whose assistant suffix exceeds max_suffix_tokens are refused here, because
    the trainer never truncates (16,384 tokens include ~6k video tokens and carriers).
    The P3 v1 policy table decides each type's form: route rows are plan-first traces
    (v3.9 `head_layout: per_frame` unless allow_paired_anchor, for interim pools);
    direct rows carry a reasoning trace without tool calls (never an empty think).
    """
    from .common import binding  # logical frame paths resolve through STUDENT_FRAME_ROOT_MAP
    verified = set()
    from .decoupled_v_run import processor_for
    processor = processor_for(processor_root)
    tokens = add_routing_tokens(processor)
    policy_name = policy or POLICY_VERSION
    policy = POLICIES[policy_name]
    benchmark = load_exclusions(exclusions)
    reported, overlap = load_exclusions(report_exclusions), {}
    division = load(pinned(division_pin))
    if division.get('schema') != 'diagnostic-whole-scene-division-v1' or division.get('training_only') is not True:
        raise ValueError('Routing rows require the inherited training-only division')
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    if scene_role not in ('train', 'heldout'):
        raise ValueError('scene_role must be train or heldout')
    index = load(pinned(rgb_index))
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    conn = sqlite3.connect(out / 'rows.sqlite')
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    seen, scenes, types, count, refused, layouts, replay_rows = set(), set(), {}, 0, {}, {}, []
    try:
        with pinned(source).open() as handle:
            for line in handle:
                raw = json.loads(line)
                manifest = raw['provenance']['rgb_manifest']
                entry = index['manifests'][manifest['sha256']]
                # A string names the producer's manifest bytes; a {path, sha256} pin substitutes a manifest
                # of the same frames (frame identity is checked by c1_row and pinned again at read time).
                rgb = load(pinned(entry if isinstance(entry, dict) else dict(path=entry, sha256=manifest['sha256'])))
                row = c1_row(raw, rgb, index.get('path_map'))
                key = row['dataset'] + '/' + row['scene']
                qtype = raw['question_type']
                calls = bool(raw['tool_output_spans'])
                both = qtype in policy.get('both', ())
                kind = ('route' if calls else 'direct') if both else ('route' if qtype in policy['route'] else 'direct' if qtype in policy['direct'] else None)
                gate_reason = None
                if 'both' in policy:
                    from .routing_type_gate import refusal
                    gate_reason = refusal(qtype, 'routed' if calls else 'direct', policy)
                    row['answer_form'] = 'routed' if calls else 'direct'
                row['routing']['category'] = kind
                ids, _, _ = suffix_tokens(processor, row, row['target'], render(raw['events'], raw['answer'])[1])
                reason = ('duplicate_qid' if row['qid'] in seen else
                          'benchmark_scene' if excluded(benchmark, key, *canonical_keys(
                              row['routing'].get('canonical'), row['routing'].get('physical_group'))) else
                          'scene_outside_training_division' if scene_role == 'train' and (key not in train or key in heldout) else
                          'scene_outside_heldout_division' if scene_role == 'heldout' and key not in heldout else
                          gate_reason if gate_reason else
                          'type_without_policy' if kind is None else
                          'direct_policy_row_has_tool_calls' if kind == 'direct' and calls else
                          # This legacy policy admits direct traces through --direct-source.
                          'direct_policy_reasoning_row' if kind == 'direct' and not both else
                          camera_filter(raw) if qtype in CAMERA_MOTION else
                          'paired_anchor_layout' if (kind == 'route' and calls and not allow_paired_anchor
                                                     and row['routing']['head_layout'] != 'per_frame') else
                          'over_length' if len(ids) > max_suffix_tokens else None)
                if reason:
                    refused[reason] = refused.get(reason, 0) + 1
                    continue
                if verify_frames:
                    for frame in row['student_input']['frames']:
                        # Rows share frames (one clip per pose row, many rows per recording): hash each once.
                        if (frame["path"], frame["sha256"]) not in verified:
                            binding(frame["path"], frame["sha256"])
                            verified.add((frame["path"], frame["sha256"]))
                seen.add(row['qid'])
                scenes.add(key)
                if excluded(reported, key, *canonical_keys(row['routing'].get('canonical'),
                                                          row['routing'].get('physical_group'))):
                    overlap[qtype] = overlap.get(qtype, 0) + 1
                if 'gt_pose9' in raw and len(replay_rows) < 2000:
                    replay_rows.append(raw)
                types[qtype + ':' + kind] = types.get(qtype + ':' + kind, 0) + 1
                layouts[row['routing']['head_layout']] = layouts.get(row['routing']['head_layout'], 0) + 1
                conn.execute('INSERT INTO rows VALUES (?,?,?)', (count, json.dumps(row), '{}'))
                count += 1
        if direct_source is not None:
            with pinned(direct_source).open() as handle:
                for line in handle:
                    raw = json.loads(line)
                    row = direct_row(raw)
                    key = row['dataset'] + '/' + row['scene']
                    qtype = raw['question_type']
                    reason = ('duplicate_qid' if row['qid'] in seen else
                              'benchmark_scene' if excluded(benchmark, key,
                                                            *canonical_keys(row['routing'].get('canonical'))) else
                              'scene_outside_training_division' if scene_role == 'train' and (key not in train or key in heldout) else
                              'scene_outside_heldout_division' if scene_role == 'heldout' and key not in heldout else
                              'direct_row_for_route_type' if qtype not in policy['direct'] + policy.get('both', ()) else None)
                    if 'both' in policy:
                        row['answer_form'] = 'direct'
                    if reason:
                        refused['direct:' + reason] = refused.get('direct:' + reason, 0) + 1
                        continue
                    suffix_tokens(processor, row, row['target'], [])
                    if verify_frames:
                        for frame in row['student_input']['frames']:
                            binding(frame["path"], frame["sha256"])
                    seen.add(row['qid'])
                    scenes.add(key)
                    types[qtype + ':direct'] = types.get(qtype + ':direct', 0) + 1
                    conn.execute('INSERT INTO rows VALUES (?,?,?)', (count, json.dumps(row), '{}'))
                    count += 1
        if not count:
            raise ValueError('Empty routing stream')
        conn.commit()
    finally:
        conn.close()
    receipt = dict(schema=ROUTING_SCHEMA, stream='routing', count=count, scenes=len(scenes), types=types,
                   refused=refused, direct_source=direct_source, exclusions=exclusions,
                   report_exclusions=report_exclusions, reported_overlap_rows=overlap,
                   excluded_names=len(benchmark), policy_version=policy_name, policy=policy,
                   head_layouts=layouts, allow_paired_anchor=allow_paired_anchor, routing_tokens=tokens['ids'],
                   scene_role=scene_role, gt_replay=gt_replay(replay_rows), source=source, rgb_index=rgb_index, division=division_pin,
                   database=file_pin(out / 'rows.sqlite'), heldout_overlap=0 if scene_role == 'train' else None,
                   calculator_sha256=hashlib.sha256(Path(calculator.__file__).read_bytes()).hexdigest())
    write(out / 'receipt.json', receipt)
    return receipt


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build the C1 routing stream from derivgen rows (CPU job).')
    parser.add_argument('--source', required=True, help='JSON pin {path, sha256} of the derivgen POOL/rows JSONL')
    parser.add_argument('--rgb-index', required=True, help='JSON pin of {manifests: {sha: path}, path_map: {...}}')
    parser.add_argument('--division', required=True, help='JSON pin of the training-only scene division')
    parser.add_argument('--processor', required=True, help='Qwen3.5 processor directory')
    parser.add_argument('--output', required=True, help='New output directory')
    parser.add_argument('--max-suffix-tokens', type=int, default=9600)
    parser.add_argument('--allow-paired-anchor', action='store_true', help='Interim pools (v1) only')
    parser.add_argument('--direct-source', help='JSON pin of concrete direct traces (JSONL)')
    parser.add_argument('--exclusions', help='JSON pin of the TEST-split scene exclusion list (rows dropped)')
    parser.add_argument('--report-exclusions', help='JSON pin of a wider overlap list (counted only)')
    parser.add_argument('--policy', choices=sorted(POLICIES), default=POLICY_VERSION)
    parser.add_argument('--scene-role', choices=('train', 'heldout'), default='train',
                        help='heldout builds the canary set from the division\'s held-out scenes')
    args = parser.parse_args()
    receipt = build_routing_stream(json.loads(args.source), json.loads(args.rgb_index), json.loads(args.division),
                                   args.output, args.processor, args.max_suffix_tokens,
                                   allow_paired_anchor=args.allow_paired_anchor, scene_role=args.scene_role,
                                   direct_source=json.loads(args.direct_source) if args.direct_source else None,
                                   exclusions=json.loads(args.exclusions) if args.exclusions else None,
                                   report_exclusions=json.loads(args.report_exclusions) if args.report_exclusions else None,
                                   policy=args.policy)
    print(json.dumps({k: receipt[k] for k in ('count', 'scenes', 'types', 'refused', 'database')}, indent=1))


if __name__ == '__main__':
    main()


def gt_replay(rows):
    """E2 check: GT pose/gravity and GT clicks through the fixed layer reproduce derivgen's targets.

    Uses rows that carry gt_pose9/gt_up; returns the byte-equal fraction and the first diffs.
    """
    done, equal, diffs = 0, 0, []
    for row in rows:
        if 'gt_pose9' not in row or 'gt_up' not in row:
            continue
        recorded = {p['label']: (p['camera'], p['spread']) for e in row['events']
                    if e['kind'] == 'tool_response' and e['name'] == 'depth_at' for p in e['points']}
        done += 1
        try:
            target = rerender(row, OwnGeometry(row['gt_pose9'], row['gt_up'], None, recorded=recorded))[0]
        except RenderError as exc:
            diffs.append(dict(qid=row['qid'], error=str(exc)))
            continue
        if target == row['target']:
            equal += 1
        elif len(diffs) < 20:
            i = next(i for i, (a, b) in enumerate(zip(target, row['target'])) if a != b)
            diffs.append(dict(qid=row['qid'], ours=target[max(0, i-60):i+60], theirs=row['target'][max(0, i-60):i+60]))
    return dict(rows=done, byte_equal=equal, fraction=equal / done if done else None, diffs=diffs)


def shippable_exclusions(source, output):
    """Write the alias-only list (no corpus words) that jobs read on the training site."""
    data = json.loads(Path(source).read_text())
    raw = (json.dumps(dict(schema='scene-exclusions-v1', names=alias_names(data),
                           source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest()),
                      indent=0, sort_keys=True) + '\n').encode()
    Path(output).write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()
