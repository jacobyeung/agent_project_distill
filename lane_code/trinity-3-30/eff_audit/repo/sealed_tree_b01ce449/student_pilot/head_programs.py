"""Head programs (move response v2): the `point`, `pose` and `move` tools, their one formatter and parser, the call
schema, and the executor that derives every number from the PRINTED responses.

Views. A view is a temporal group g (0..15) named in text by the processor's pair label ("12.4 s"); its frame is the
heads' anchor, 1-based frame 2g + 2 (0-based sampled frame 2g + 1). Pixels are [x, y] on the [0, 1000] grid of that
frame, (0, 0) the top-left corner.

Level frame of a view: origin at its camera centre, +y down along gravity, +z the camera's optical axis projected on
the floor (horizontal forward), +x = y cross z (horizontal right). All tools answer in level frames, metres.

Tools (the readout function is shared by every source: the student's heads, GT geometry, a donor session):
  point(at, pixel)   the 3D point at `pixel` of view `at`: depth d along the optical axis, unprojected with a centred
                     principal point and the view's field of view, then rotated into `at`'s level frame.
  pose(from, to)     the step that maps view `from`'s level frame into view `to`'s:
                       x' = x cos t + z sin t + bx,  y' = y + dy,  z' = -x sin t + z cos t + bz,
                     t = yaw of `from`'s forward seen in `to`'s level frame (positive: `from` faces right of `to`),
                     (bx, dy, bz) = `from`'s camera centre in `to`'s level frame. dy carries the height change, so
                     cross-view 3D distances stay exact when the camera height changes.
  move(from, to)     the camera translation from view `from` to view `to` in `from`'s level frame (dx, dy, dz),
                     and its nonnegative Euclidean distance, computed from the same full-precision translation.

Printing (head-output-rounding): metres with 2 decimals, whole degrees for every angle (pose yaw, derived direction
angles), cos/sin with 2 decimals computed from the printed whole-degree yaw. Derived numbers are computed only from the
parsed printed values, every printed derived value is rounded before later steps use it, and every angle decision reads
the printed whole-degree value. Displacement answers copy the printed move distance; they never recompute a norm.
The explicitly named legacy v1 readers serve only retained P0/P1 artifacts; v2 admission refuses those strings.
"""
import json
import math
import re

import numpy as np

GROUPS = 16
GRID = 1000.0
TOOL_NAMES = ('point', 'pose', 'move')
POINT_RE = re.compile(r'^\(\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2})\s*\) m$')
POSE_RE = re.compile(r'^(?P<ax>\d+\.\d{2}) m (?P<lr>right|left), (?P<ay>\d+\.\d{2}) m (?P<ud>down|up), '
                     r'(?P<az>\d+\.\d{2}) m (?P<fb>forward|backward), facing (?P<at>\d+) degrees ?(?P<dir>right|left)? '
                     r'\(bx = (?P<bx>[+-]\d+\.\d{2}), dy = (?P<dy>[+-]\d+\.\d{2}), bz = (?P<bz>[+-]\d+\.\d{2}) m, '
                     r't = (?P<t>[+-]\d+) deg, cos t = (?P<c>[+-]\d\.\d{2}), sin t = (?P<s>[+-]\d\.\d{2})\)$')
LEGACY_MOVE_V1_RE = re.compile(r'^dx = ([+-]\d+\.\d{2}) m, dy = ([+-]\d+\.\d{2}) m, dz = ([+-]\d+\.\d{2}) m$')
MOVE_RE = re.compile(LEGACY_MOVE_V1_RE.pattern[:-1] + r', distance = (\d+\.\d{2}) m$')


class ProgramError(ValueError):
    """An invalid call, an unparseable response or a geometric degeneracy: the program has no answer."""


def r2(value):
    """Round to 2 decimals, never returning -0.0."""
    return round(float(value), 2) + 0.0


def f2(value):
    return f'{r2(value):.2f}'


def s2(value):
    return f'{r2(value):+.2f}'


def wrap_deg(angle):
    """Integer degrees in (-180, 180]."""
    a = int(round(float(angle))) % 360
    return a - 360 if a > 180 else a


# ---------------------------------------------------------------------------------------------------------- geometry

def level_rotation(r_cam_to_ref, up=(0.0, 0.0, 1.0)):
    """Rows (x_l, y_l, z_l) of a camera's level frame in the reference frame (ref -> level rotation).

    r_cam_to_ref: [3, 3] OpenCV camera-to-reference rotation; up: gravity up in the reference frame."""
    r = np.asarray(r_cam_to_ref, dtype=np.float64)
    up = np.asarray(up, dtype=np.float64)
    up = up / np.linalg.norm(up)
    forward = r[:, 2]
    horizontal = forward - float(np.dot(forward, up)) * up
    if np.linalg.norm(horizontal) < 1e-6:
        raise ProgramError('the camera looks along gravity: its level forward is undefined')
    z = horizontal / np.linalg.norm(horizontal)
    y = -up
    x = np.cross(y, z)
    return np.stack((x / np.linalg.norm(x), y, z), axis=0)


def camera_ray(pixel, fov_hw):
    """Optical-axis-depth-1 camera vector at a grid pixel, centred principal point; fov_hw = (vertical, horizontal) rad."""
    u, v = (float(c) for c in pixel)
    fov_h, fov_w = (float(a) for a in fov_hw)
    return np.array([(u / (GRID / 2) - 1.0) * math.tan(fov_w / 2), (v / (GRID / 2) - 1.0) * math.tan(fov_h / 2), 1.0])


def point_values(r_cam_to_ref, fov_hw, pixel, depth, up=(0.0, 0.0, 1.0)):
    """(x, y, z) of `pixel` at optical-axis `depth` in the view's level frame (full precision)."""
    if not (math.isfinite(depth) and depth > 0):
        raise ProgramError('depth is not a positive finite number')
    level = level_rotation(r_cam_to_ref, up)
    return tuple(float(v) for v in level @ (np.asarray(r_cam_to_ref, dtype=np.float64) @ (camera_ray(pixel, fov_hw) * depth)))


def pose_values(r_from, c_from, r_to, c_to, up=(0.0, 0.0, 1.0)):
    """{'bx', 'dy', 'bz', 't_deg'} of the step from view `from`'s level frame into view `to`'s (full precision)."""
    l_from, l_to = level_rotation(r_from, up), level_rotation(r_to, up)
    b = l_to @ (np.asarray(c_from, dtype=np.float64) - np.asarray(c_to, dtype=np.float64))
    sin_t = float(np.dot(l_from[2], l_to[0]))
    cos_t = float(np.dot(l_from[2], l_to[2]))
    return {'bx': float(b[0]), 'dy': float(b[1]), 'bz': float(b[2]), 't_deg': math.degrees(math.atan2(sin_t, cos_t))}


def move_values(r_from, c_from, c_to, up=(0.0, 0.0, 1.0)):
    """(dx, dy, dz): camera translation from `from` to `to` in `from`'s level frame (full precision)."""
    d = level_rotation(r_from, up) @ (np.asarray(c_to, dtype=np.float64) - np.asarray(c_from, dtype=np.float64))
    return tuple(float(v) for v in d)


# ------------------------------------------------------------------------------------------------ format and parse

def format_point(values):
    return '(' + ', '.join(f2(v) for v in values) + ') m'


def format_pose(values):
    bx, dy, bz, t = r2(values['bx']), r2(values['dy']), r2(values['bz']), wrap_deg(values['t_deg'])
    cos_t, sin_t = r2(math.cos(math.radians(t))), r2(math.sin(math.radians(t)))
    facing = 'facing 0 degrees' if t == 0 else f'facing {abs(t)} degrees {"right" if t > 0 else "left"}'
    return (f'{f2(abs(bx))} m {"right" if bx >= 0 else "left"}, {f2(abs(dy))} m {"down" if dy >= 0 else "up"}, '
            f'{f2(abs(bz))} m {"forward" if bz >= 0 else "backward"}, {facing} '
            f'(bx = {s2(bx)}, dy = {s2(dy)}, bz = {s2(bz)} m, t = {t:+d} deg, cos t = {s2(cos_t)}, sin t = {s2(sin_t)})')


def legacy_format_move_v1(values):
    """Render components for authentication of retained P1/P0 v1 artifacts only."""
    dx, dy, dz = values
    return f'dx = {s2(dx)} m, dy = {s2(dy)} m, dz = {s2(dz)} m'


def format_move(values):
    """Render v2 from three full-precision components, rounding only at the print boundary."""
    dx, dy, dz = (float(v) for v in values)
    if not all(math.isfinite(v) for v in (dx, dy, dz)):
        raise ProgramError('move needs finite components')
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if not math.isfinite(distance):
        raise ProgramError('move distance is not finite')
    return legacy_format_move_v1((dx, dy, dz)) + f', distance = {f2(distance)} m'


def parse_point(text):
    m = POINT_RE.match(text.strip())
    if not m:
        raise ProgramError(f'unparseable point response {text!r}')
    return tuple(float(g) for g in m.groups())


def parse_pose(text):
    """Printed (bx, dy, bz, t, cos t, sin t); the derivation uses exactly these numbers."""
    m = POSE_RE.match(text.strip())
    if not m:
        raise ProgramError(f'unparseable pose response {text!r}')
    return {'bx': float(m['bx']), 'dy': float(m['dy']), 'bz': float(m['bz']), 't_deg': int(m['t']),
            'cos_t': float(m['c']), 'sin_t': float(m['s'])}


def legacy_parse_move_v1(text):
    """Read only retained P0/P1 component-only responses; never use for v2 admission."""
    m = LEGACY_MOVE_V1_RE.fullmatch(text.strip())
    if not m:
        raise ProgramError(f'unparseable legacy move v1 response {text!r}')
    return tuple(float(g) for g in m.groups())


def parse_move(text):
    """Read v2 (dx, dy, dz, distance); preserve the printed distance for execution."""
    m = MOVE_RE.fullmatch(text.strip())
    if not m or '-0.00' in m.groups():
        raise ProgramError(f'unparseable move v2 response {text!r}')
    values = tuple(float(g) for g in m.groups())
    if not all(math.isfinite(v) for v in values):
        raise ProgramError('move needs finite printed values')
    return values


PARSERS = {'point': parse_point, 'pose': parse_pose, 'move': parse_move}


# P1 uses a separate executor: P0's ambiguous-direction error remains unchanged.
HP_KINDS = ('camera_displacement', 'camera_movement_direction')
CALL_SPAN = re.compile(r'<tool_call>(.*?)</tool_call>', re.S)
RESPONSE_SPAN = re.compile(r'<tool_response>(.*?)</tool_response>', re.S)


def question_frames(question):
    frames = [int(v) for v in re.findall(r'\bframe\s+(\d+)', question, re.I)]
    if len(frames) != 2 or any(not 1 <= f <= 32 for f in frames):
        raise ProgramError('camera question must name two frames of 32')
    return frames


def option_words(options):
    words = [re.sub(r'^[A-Z][.)]\s*', '', str(o)).strip() for o in options]
    if not words or len(set(words)) != len(words):
        raise ProgramError('direction options must be distinct')
    if any(w not in ('Forward', 'Backward', 'Right', 'Left', 'Up', 'Down') for w in words):
        raise ProgramError('unknown direction option')
    return words


def direction_components(response, options):
    dx, dy, dz, _ = parse_move(response)
    values = {'Forward': dz, 'Backward': -dz, 'Right': dx, 'Left': -dx, 'Up': -dy, 'Down': dy}
    return [(word, r2(values[word])) for word in option_words(options)]


def hp_answer(kind, options, response):
    parse_move(response)
    if kind == 'camera_displacement':
        return MOVE_RE.fullmatch(response.strip()).group(4)
    if kind == 'camera_movement_direction':
        components = direction_components(response, options)
        index = max(range(len(components)), key=lambda i: components[i][1])
        return chr(65 + index)
    raise ProgramError(f'unsupported HP kind {kind}')


def render_hp_target(kind, question, options, frames, labels, call, response):
    if list(frames) != question_frames(question) or len(labels) != GROUPS:
        raise ProgramError('frame mapping differs from question or label count')
    expected = {'name': 'move', 'from': frames[0], 'to': frames[1]}
    if call != expected or call['from'] == call['to']:
        raise ProgramError('move must address the question frames in order')
    parse_frame_call(frame_call_json(call))
    answer = hp_answer(kind, options, response)
    a, b = frames
    if kind == 'camera_displacement':
        plan = (f'Plan: read the camera translation from frame {a} to frame {b} in frame {a}\'s '
                'gravity-aligned frame with the move tool, and read the distance it reports.')
        derived = f'Distance: {answer} m.'
        final = answer
    elif kind == 'camera_movement_direction':
        plan = (f'Plan: read the camera translation from frame {a} to frame {b} in frame {a}\'s '
                'gravity-aligned frame with the move tool, and pick the option '
                'with the largest component.')
        expressions = {'Forward': 'dz', 'Backward': '-dz', 'Right': 'dx', 'Left': '-dx', 'Up': '-dy', 'Down': 'dy'}
        derived = 'Option components: ' + '; '.join(
            f'{word} = {expressions[word]} = {s2(value)} m' for word, value in direction_components(response, options)) + '.'
        final = option_words(options)[ord(answer) - 65]
        derived += f'\nLargest: {final}.'
    else:
        raise ProgramError(f'unsupported HP kind {kind}')
    mapping = (f'Frame {a} of 32 corresponds to the {labels[(a - 1) // 2]} view; '
               f'frame {b} of 32 corresponds to the {labels[(b - 1) // 2]} view.')
    return (f'<think>\n{plan}\n{mapping}\n<tool_call>{frame_call_json(call)}</tool_call>'
            f'<tool_response>{response}</tool_response>\n{derived}\nFinal answer: {final}\n</think>\n\n{answer}')


def audit_numbers(target, question, labels, response):
    spans = RESPONSE_SPAN.findall(target)
    if spans != [response]:
        raise ProgramError('target must contain exactly its recorded response')
    values = parse_move(response)
    allowed = {float(f) for f in question_frames(question)} | {32.0}
    allowed |= {float(re.search(r'\d+(?:\.\d+)?', label).group()) for label in labels}
    allowed |= set(values[:3]) | {-v for v in values[:3]} | {values[3]}
    outside = RESPONSE_SPAN.sub('', target)
    for number in re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', outside):
        if float(number) not in allowed:
            raise ProgramError(f'unlicensed number outside response: {number}')
    return True


def check_trace(kind, question, options, labels, text):
    calls, responses = CALL_SPAN.findall(text), RESPONSE_SPAN.findall(text)
    result = {'called': bool(calls), 'n_calls': len(calls), 'valid_call': False, 'right_frames': False,
              'executor_answer': None, 'model_answer': None, 'faithful': False, 'faithful_rel2': False}
    if '</think>' in text:
        tail = text.rsplit('</think>', 1)[1].strip()
        tail = re.split(r'<\|im_end\|>|<\|endoftext\|>', tail)[0].strip()
        result['model_answer'] = tail
    if len(calls) != 1:
        return result
    try:
        call = parse_frame_call(calls[0])
        result['valid_call'] = call['name'] == 'move'
        a, b = question_frames(question)
        result['right_frames'] = call == {'name': 'move', 'from': a, 'to': b}
        if len(responses) != 1 or not result['valid_call']:
            return result
        result['executor_answer'] = hp_answer(kind, options, responses[0])
        model = result['model_answer']
        if model is not None:
            result['faithful'] = (f2(float(model)) == result['executor_answer'] if kind == 'camera_displacement'
                                  else model == result['executor_answer'])
            if kind == 'camera_displacement':
                expected, actual = float(result['executor_answer']), float(model)
                result['faithful_rel2'] = math.isfinite(actual) and (
                    actual == 0.0 if expected == 0.0 else abs(actual - expected) <= .02 * abs(expected) + 1e-12)
            else:
                result['faithful_rel2'] = result['faithful']
    except (ProgramError, ValueError, TypeError):
        pass
    return result


# -------------------------------------------------------------------------------------------------- call schema

def parse_frame(value):
    """P1's 1-based sampled frame, never a pair-label view. P0 keeps resolve_label below."""
    if isinstance(value, str):
        match = re.fullmatch(r'\s*(?:frame\s+)?([0-9]+)\s*', value, re.I)
        if not match:
            raise ProgramError(f'frame {value!r} must be an integer or "frame N"')
        value = int(match[1])
    if type(value) is not int or not 1 <= value <= 32:
        raise ProgramError(f'frame {value!r} is outside integer frames 1..32')
    return value


def frame_call(call):
    if not isinstance(call, dict) or set(call) != {'name', 'from', 'to'} or call.get('name') != 'move':
        raise ProgramError('P1 move takes exactly "name": "move", "from" and "to"')
    a, b = parse_frame(call['from']), parse_frame(call['to'])
    if a == b:
        raise ProgramError('move needs two different frames')
    return {'name': 'move', 'from': a, 'to': b}


def parse_frame_call(text):
    """Parse P1 move JSON into a call with integer frames, independently of P0's view grammar."""
    def unique_fields(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ProgramError(f'duplicate call field {key!r}')
            data[key] = value
        return data
    try:
        data = json.loads(text, object_pairs_hook=unique_fields)
    except ValueError as exc:
        raise ProgramError(f'invalid frame call: {exc}') from None
    return frame_call(data)


def frame_call_json(call):
    call = frame_call(call)
    return json.dumps({'name': 'move', 'from': f'frame {call["from"]}', 'to': f'frame {call["to"]}'})


def call_json(call, labels):
    """Tool-call JSON text of a call dict {'name', 'at'|'from'/'to' (group), 'pixel'} with views as pair labels."""
    name = call['name']
    if name == 'point':
        return json.dumps({'name': 'point', 'at': labels[call['at']], 'pixel': [int(v) for v in call['pixel']]})
    if name in ('pose', 'move'):
        return json.dumps({'name': name, 'from': labels[call['from']], 'to': labels[call['to']]})
    raise ProgramError(f'unknown tool {name!r}')


def resolve_label(label, labels):
    """Group of a view label ('12.4 s', '<12.4 seconds>' or '12.4'); exact match on the printed 1-decimal value."""
    m = re.search(r'(\d+(?:\.\d+)?)', str(label))
    if not m:
        raise ProgramError(f'view label {label!r} has no time')
    value = f'{float(m.group(1)):.1f}'
    hits = [g for g, text in enumerate(labels) if re.search(r'(\d+(?:\.\d+)?)', text).group(1) == value]
    if len(hits) != 1:
        raise ProgramError(f'view label {label!r} names {len(hits)} views')
    return hits[0]


def parse_call(text, labels):
    """A model-written tool call (JSON) -> call dict with groups; raises ProgramError for any malformed field."""
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ProgramError(f'tool call is not JSON: {exc}') from None
    if not isinstance(data, dict) or data.get('name') not in TOOL_NAMES:
        raise ProgramError('tool call names no known tool')
    if data['name'] == 'point':
        if set(data) != {'name', 'at', 'pixel'}:
            raise ProgramError('point takes exactly "at" and "pixel"')
        return {'name': 'point', 'at': resolve_label(data['at'], labels), 'pixel': check_pixel(data['pixel'])}
    if set(data) != {'name', 'from', 'to'}:
        raise ProgramError(f'{data["name"]} takes exactly "from" and "to"')
    a, b = resolve_label(data['from'], labels), resolve_label(data['to'], labels)
    if a == b:
        raise ProgramError(f'{data["name"]} needs two different views')
    return {'name': data['name'], 'from': a, 'to': b}


def check_pixel(pixel):
    if (not isinstance(pixel, (list, tuple)) or len(pixel) != 2
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in pixel)
            or not all(0 <= v <= GRID for v in pixel)):
        raise ProgramError(f'pixel {pixel!r} is not [x, y] on the 0-1000 grid')
    return [int(round(v)) for v in pixel]


# --------------------------------------------------------------------------------------------- readout sources

class Readouts(object):
    """Answers calls for one video from per-view rotations, camera centres, fields of view and a depth function.

    r_cam_to_ref [16, 3, 3], c_ref [16, 3] (metres), fov_hw [16, 2] (vertical, horizontal; radians), depth(g, pixel) ->
    optical-axis metres, up: gravity up in the reference frame. HeadReadouts and GT readouts both go through here, so
    the tools have one readout function."""

    def __init__(self, r_cam_to_ref, c_ref, fov_hw, depth, up=(0.0, 0.0, 1.0), valid=None, r_origin=None):
        self.r, self.c = np.asarray(r_cam_to_ref, dtype=np.float64), np.asarray(c_ref, dtype=np.float64)
        self.fov, self.depth_fn, self.up = np.asarray(fov_hw, dtype=np.float64), depth, up
        self.valid = np.ones(GROUPS, bool) if valid is None else np.asarray(valid, dtype=bool)
        self.r_origin = None if r_origin is None else np.asarray(r_origin, dtype=np.float64)

    def _group(self, g):
        if type(g) is not int or not 0 <= g < GROUPS or not self.valid[g]:
            raise ProgramError(f'view {g!r} has no readout')
        return g

    def values(self, call):
        check_call(call)
        name = call['name']
        if name == 'point':
            g = self._group(call['at'])
            pixel = check_pixel(call['pixel'])
            return point_values(self.r[g], self.fov[g], pixel, float(self.depth_fn(g, pixel)), self.up)
        a, b = self._group(call['from']), self._group(call['to'])
        if a == b:
            raise ProgramError(f'{name} needs two different views')
        if name == 'pose':
            return pose_values(self.r[a], self.c[a], self.r[b], self.c[b], self.up)
        if name == 'move':
            return move_values(self.r[a], self.c[a], self.c[b], self.up)
        raise ProgramError(f'unknown tool {name!r}')

    def respond(self, call):
        """The printed response of a call (the only form a program may use)."""
        values = self.values(call)  # validates the call first
        return FORMATTERS[call['name']](values)


FORMATTERS = {'point': format_point, 'pose': format_pose, 'move': format_move}


def check_call(call):
    """Structure of a call dict: a known tool with exactly its fields, else ProgramError."""
    if not isinstance(call, dict) or call.get('name') not in TOOL_NAMES:
        raise ProgramError(f'not a call of a known tool: {call!r}')
    fields = {'name', 'at', 'pixel'} if call['name'] == 'point' else {'name', 'from', 'to'}
    if set(call) != fields:
        raise ProgramError(f'{call["name"]} call needs exactly {sorted(fields)}')


def head_readouts(session):
    """Readouts from a student_pilot.head_api.HeadSession (the student's own heads)."""
    from .head_api import FRAME_ANCHORS

    def depth(g, pixel):
        return session.depth(FRAME_ANCHORS[g], [float(pixel[0]), float(pixel[1])])
    return Readouts(session.r_grav, session.t_grav, session.fov_hw, depth, up=(0.0, 0.0, 1.0),
                    r_origin=getattr(session, 'r_origin', None))


class FrameReadouts:
    """P1 frame poses layered over P0's unmodified view readouts in the frame-1 gravity reference.

    The 32 samples are uniformly spaced, so missing odd frames use centre and rotation midpoints (weight 0.5).
    The offline readout pass checks timestamp uniformity within 5% of the mean sample step before any forward.
    """
    def __init__(self, readouts):
        self.readouts = readouts

    def pose(self, frame):
        frame = parse_frame(frame)
        source = self.readouts
        if frame == 1:
            if source.r_origin is None:
                raise ProgramError('frame 1 requires the origin camera rotation in the gravity reference')
            return source.r_origin.copy(), np.zeros(3, dtype=np.float64)
        g = source._group(frame // 2 - 1)
        if frame % 2 == 0:
            return source.r[g].copy(), source.c[g].copy()
        # For frame 2g+1, g >= 1, these are the anchors at frames 2g and 2g+2.
        next_g = source._group(g + 1)
        from .camera_targets import quaternion_xyzw, rotation_from_xyzw
        q0, q1 = quaternion_xyzw(source.r[g]), quaternion_xyzw(source.r[next_g])
        if np.dot(q0, q1) < 0:
            q1 = -q1
        # Normalizing q0+q1 is exactly shortest-arc SLERP at t=0.5, including coincident rotations.
        rotation = rotation_from_xyzw(q0 + q1)
        centre = (source.c[g] + source.c[next_g]) / 2.0
        return rotation, centre

    def values(self, call):
        call = frame_call(call)
        r_from, c_from = self.pose(call['from'])
        _, c_to = self.pose(call['to'])
        return move_values(r_from, c_from, c_to, self.readouts.up)

    def respond(self, call):
        return format_move(self.values(call))


# --------------------------------------------------------------------------------------------------- executor

def _transform(p, step):
    """A printed point (x, y, z) of view `from` in view `to` via a printed pose step; each coordinate printed at 2 dp."""
    x, y, z = p
    c, s = step['cos_t'], step['sin_t']
    return (r2(x * c + z * s + step['bx']), r2(y + step['dy']), r2(-x * s + z * c + step['bz']))


def _dist(a, b=(0.0, 0.0, 0.0)):
    return r2(math.sqrt(sum((u - v) ** 2 for u, v in zip(a, b))))


def _option_index(options, value):
    keys = [o.split('. ', 1)[1].strip().lower() if '. ' in o else o.strip().lower() for o in options]
    value = value.lower()
    if value not in keys:
        raise ProgramError(f'derived answer {value!r} is not an option')
    return keys.index(value)


def _letter(index):
    return chr(65 + index)


def execute(program, responses):
    """Derive the answer of a program from its printed responses.

    program: {'kind', 'calls': [...], 'options': [...], ...} (tools/hp_p0_build.py); responses: one printed response
    per call. Returns {'answer': float or option letter, 'lines': [derived lines]}; raises ProgramError when a response
    is missing or unparseable or the geometry is degenerate (that row then has no answer and scores 0)."""
    try:
        return _execute(program, responses)
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ProgramError(f'malformed program or response: {exc!r}') from None


def execute_legacy_v1(program, responses):
    """Execute retained P0 v1 artifacts with their original rounded-component semantics."""
    try:
        return _execute(program, responses, legacy_v1=True)
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ProgramError(f'malformed program or response: {exc!r}') from None


def _execute(program, responses, legacy_v1=False):
    calls = program['calls']
    if not isinstance(responses, (list, tuple)) or len(responses) != len(calls):
        raise ProgramError('a call has no response')
    if any(not isinstance(r, str) for r in responses):
        raise ProgramError('a response is missing')
    parsers = {**PARSERS, 'move': legacy_parse_move_v1} if legacy_v1 else PARSERS
    vals = [parsers[c['name']](r) for c, r in zip(calls, responses)]
    kind, options, lines = program['kind'], program.get('options') or [], []

    def in_view(i_point, i_pose):
        """Point call i_point expressed in the program's target view (via pose call i_pose, or as is)."""
        p = vals[i_point]
        if i_pose is None:
            return p
        q = _transform(p, vals[i_pose])
        lines.append(f'{format_point(p)} -> {format_point(q)}')
        return q

    if kind == 'camera_displacement':
        d = _dist(vals[0]) if legacy_v1 else vals[0][3]
        lines.append(f'd = {f2(d)} m')
        return {'answer': d, 'lines': lines}
    if kind == 'camera_movement_direction':
        dx, _, dz = vals[0][:3]
        component = {'forward': dz, 'backward': -dz, 'right': dx, 'left': -dx}
        scores = []
        for o in options:
            key = o.split('. ', 1)[1].strip().lower()
            if key not in component:
                raise ProgramError(f'option {o!r} is not a horizontal direction')
            scores.append(component[key])
        best = max(range(len(scores)), key=lambda k: (scores[k], -k))
        if sum(1 for s in scores if s == scores[best]) > 1:
            raise ProgramError('two options have the same component')
        return {'answer': _letter(best), 'lines': lines}
    if kind == 'camera_obj_abs_dist':
        d = _dist(vals[0])
        return {'answer': d, 'lines': [f'd = {f2(d)} m']}
    if kind == 'camera_obj_rel_dist':
        ds = [_dist(v) for v in vals]
        best = min(range(len(ds)), key=lambda k: (ds[k], k))
        if ds.count(ds[best]) > 1:
            raise ProgramError('two candidates are equally near')
        return {'answer': _letter(best), 'lines': [' '.join(f2(d) for d in ds)]}
    if kind == 'obj_obj_relative_pos_nf':
        da, db = _dist(vals[0]), _dist(vals[1])
        if da == db:
            raise ProgramError('both objects are equally far')
        return {'answer': _letter(_option_index(options, 'near' if da < db else 'far')), 'lines': [f'{f2(da)} {f2(db)}']}
    if kind == 'obj_obj_relative_pos_ud':
        ya, yb = vals[0][1], vals[1][1]
        if ya == yb:
            raise ProgramError('both objects are at the same height')
        return {'answer': _letter(_option_index(options, 'up' if ya < yb else 'down')), 'lines': []}
    if kind == 'object_abs_distance':
        a = vals[0]
        b = in_view(1, program['pose_index'])
        d = _dist(a, b)
        lines.append(f'd = {f2(d)} m')
        return {'answer': d, 'lines': lines}
    if kind == 'object_rel_distance':
        ref = vals[0]
        ds = []
        for i_point, i_pose in program['candidates']:
            ds.append(_dist(in_view(i_point, i_pose), ref))
        best = min(range(len(ds)), key=lambda k: (ds[k], k))
        if ds.count(ds[best]) > 1:
            raise ProgramError('two candidates are equally near')
        return {'answer': _letter(best), 'lines': lines + [' '.join(f2(d) for d in ds)]}
    if kind.startswith('object_rel_direction'):
        (i_s, _), (i_f, pose_f), (i_q, pose_q) = program['roles']
        s, f, q = vals[i_s], in_view(i_f, pose_f), in_view(i_q, pose_q)
        u = (r2(f[0] - s[0]), r2(f[2] - s[2]))
        v = (r2(q[0] - s[0]), r2(q[2] - s[2]))
        if u == (0.0, 0.0) or v == (0.0, 0.0):
            raise ProgramError('the standing point coincides with the facing or query point')
        dot = r2(u[0] * v[0] + u[1] * v[1])
        cross = r2(u[0] * v[1] - u[1] * v[0])
        if dot == 0.0 and cross == 0.0:
            raise ProgramError('degenerate direction')
        # Every direction decision reads the printed whole-degree angle (user ruling 2026-11-04: angles print as
        # integers because the pose head errs ~13 deg), never the signs of dot and cross.
        angle = wrap_deg(math.degrees(math.atan2(cross, dot)))
        lines.append(f'u = ({f2(u[0])}, {f2(u[1])}), v = ({f2(v[0])}, {f2(v[1])}), dot = {f2(dot)}, '
                     f'cross = {f2(cross)}, angle = {angle:+d} deg')
        if kind.endswith('hard'):
            if angle in (0, 90, -90, 180):
                raise ProgramError('the query lies on a quadrant boundary')
            label = ('front' if abs(angle) < 90 else 'back') + '-' + ('left' if angle > 0 else 'right')
        elif kind.endswith('medium'):
            if abs(angle) >= 135:  # 'Back' means rotating at least 135 degrees
                label = 'back'
            elif angle == 0:
                raise ProgramError('the query lies straight ahead')
            else:
                label = 'left' if angle > 0 else 'right'
        else:
            if angle in (0, 180):
                raise ProgramError('the query lies on the facing line')
            label = 'left' if angle > 0 else 'right'
        return {'answer': _letter(_option_index(options, label)), 'lines': lines}
    if kind == 'object_size_estimation':
        length = _dist(vals[0], vals[1])
        cm = int(round(length * 100))
        return {'answer': float(cm), 'lines': [f'length = {f2(length)} m = {cm} cm']}
    raise ProgramError(f'unknown program kind {kind!r}')
