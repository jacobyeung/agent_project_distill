"""Text protocol for the student's calls to its own heads.

A call sits inside the reasoning in Qwen3.5's native tool tokens, and the decode loop appends the head's answer
directly after the closing token:

  <tool_call>{"name": "depth", "frame": 4, "point": [412, 280]}</tool_call><tool_response>1.84 m</tool_response>
  <tool_call>{"name": "pose", "frame": 8}</tool_call><tool_response>position (0.32, 1.10, 0.05) m, heading 35 degrees
  left, pitch 12 degrees down</tool_response>

Conventions (shared with student_pilot.head_api, geo_stage1 and rung-1):
  frame  1-based index into the 32-frame student input, with pose origin at frame 1. Temporal group g (0..15) fuses
         frames 2g+1 and 2g+2 and describes frame 2g+2, so pose answers frames 1, 2, 4, ..., 32 and depth answers
         frames 2, 4, ..., 32. Odd frames 3..31 (and depth at frame 1) have no head output and raise CallError("frame").
  point  [x, y] integers on Qwen3.5's [0, 1000] grid, (0, 0) top-left, (1000, 1000) bottom-right
  depth  metres along the optical axis of that frame's camera to the first surface at the pixel
  pose   that frame's camera in the reference frame anchored at the camera of frame 1: x right, y forward
         (horizontal), z up, metres; heading is the yaw relative to frame 1 (left positive); pitch is the optical
         axis elevation above the horizontal (up positive); roll is the rotation about the optical axis
         (left = counterclockwise seen from behind the camera, i.e. its right side raised); view is the horizontal
         and vertical field of view in degrees (frames 2, 4, ..., 32; the pose head has no field of view for the
         origin frame 1). Position, heading, pitch, roll and view fix the camera ray of every grid point, so a depth
         response at a point turns into a 3D point the student can compute (headcall.derive).

Training text and decode-time insertion are byte-identical: the response starts right after </tool_call> with no
separator, so every token from <tool_response> through </tool_response> is inserted by the loop and masked from the
LM loss, and everything else is the model's own text.
"""
import ast
import json
import math
import re
from collections import namedtuple

CALL_OPEN, CALL_CLOSE = "<tool_call>", "</tool_call>"
RESPONSE_OPEN, RESPONSE_CLOSE = "<tool_response>", "</tool_response>"
EXPECTED_TRANSFORMERS_VERSION = "5.12.1"
FRAMES = 32
GROUPS = 16
FRAME_ORIGIN = 1
FRAME_ANCHORS = tuple(2 * g + 2 for g in range(GROUPS))
POSE_FRAMES = (FRAME_ORIGIN,) + FRAME_ANCHORS
DEPTH_FRAMES = FRAME_ANCHORS
ADDRESSING_MODES = ("frame", "group")
GRID = 1000
NAMES = ("depth", "pose")
NAME_ALIASES = {
    "depth": "depth", "point_depth": "depth", "get_depth": "depth", "depth_at": "depth", "depth_at_pixel": "depth",
    "pixel_depth": "depth", "depth_head": "depth",
    "pose": "pose", "camera_pose": "pose", "get_pose": "pose", "get_camera_pose": "pose", "pose_head": "pose",
    "camera": "pose",
}
FRAME_KEYS = ("frame", "frame_index", "frame_id", "frame_idx", "group", "group_index", "group_id", "group_idx")
POINT_KEYS = ("point", "pixel", "coords", "coordinate", "xy")

Call = namedtuple("Call", "name frame point")  # point is (x, y) for depth and None for pose
# position is (x, y, z) in metres; roll_deg left (counterclockwise) positive; view_deg (horizontal, vertical) or None
PoseValue = namedtuple("PoseValue", "position heading_deg pitch_deg roll_deg view_deg", defaults=(0.0, None))


def max_frame_index(addressing="frame"):
    if addressing == "frame":
        return FRAMES
    if addressing == "group":
        return GROUPS
    raise ValueError("addressing must be 'frame' or 'group', got %r" % (addressing,))


def group_of_frame(frame):
    """Map a 1-based anchor frame 2g + 2 (2, 4, ..., 32) to its 0-based temporal group g (0..15)."""
    if type(frame) is not int or frame not in FRAME_ANCHORS:
        if type(frame) is int and 3 <= frame <= 31 and frame % 2:
            raise CallError(
                "frame",
                "frame %d has no head output; it shares temporal group %d with frame %d, which the heads answer"
                % (frame, (frame - 1) // 2, frame + 1),
            )
        raise CallError("frame", "frame %r is not an answerable 1-based anchor frame (2, 4, ..., 32)" % (frame,))
    return frame // 2 - 1


def anchor_candidates(frame, name="depth"):
    """Candidate answerable frames for a 1-based 32-frame index (1..32), in preference order.

    Pose answers frame 1 (origin) and even frames 2, 4, ..., 32; odd frame f in 3..31 maps to (f + 1,).
    Depth answers even frames 2, 4, ..., 32; frame 1 maps to (2,), even frame f maps to (f,), and odd frame f in
    3..31 tries f + 1 first (same temporal group) and then f - 1 (previous group's even frame).
    """
    if name not in NAMES:
        raise ValueError("unknown head %r; use depth or pose" % (name,))
    if type(frame) is not int or not 1 <= frame <= FRAMES:
        raise CallError("frame", "frame must be an integer from 1 to %d" % FRAMES)
    if name == "pose" and frame == FRAME_ORIGIN:
        return (FRAME_ORIGIN,)
    if frame % 2 == 0:
        return (frame,)
    if name == "depth" and frame >= 3:
        return (frame + 1, frame - 1)
    return (frame + 1,)


def anchor_frame(frame, name="depth"):
    """Map a 1-based 32-frame index (1..32) to the primary answerable frame of its temporal group.

    Pose answers frame 1 (origin) and even frames 2, 4, ..., 32; odd frame f in 3..31 maps to f + 1.
    Depth answers even frames 2, 4, ..., 32; odd frame f in 1..31 (including frame 1) maps to f + 1.
    """
    return anchor_candidates(frame, name)[0]


def frame_to_group(frame):
    """Map a 1-based anchor frame 2g + 2 (2, 4, ..., 32) to its 1-based 16-group index (1..16)."""
    return group_of_frame(frame) + 1


def group_to_frame(group):
    """Map a 1-based 16-group index (1..16) to its 1-based anchor frame 2 * group (2, 4, ..., 32)."""
    if type(group) is not int or not 1 <= group <= GROUPS:
        raise CallError("frame", "group must be an integer from 1 to %d" % GROUPS)
    return 2 * group


class CallError(ValueError):
    """A call the heads cannot answer; `code` names the failure for call-validity metrics."""

    def __init__(self, code, message):
        ValueError.__init__(self, message)
        self.code = code


class ParseResult(namedtuple("ParseResult", "call error repairs extra")):
    """call: a validated Call or None; error: CallError or None; repairs: fixes applied to reach valid JSON;
    extra: keys outside the schema (ignored)."""

    @property
    def valid(self):
        return self.call is not None

    @property
    def strict(self):
        """Valid with no repair and no extra key: what the training data teaches."""
        return self.call is not None and not self.repairs and not self.extra


# ---------------------------------------------------------------- rendering
def num(value):
    text = "%.2f" % value
    return "0.00" if text == "-0.00" else text


def turn(angle):
    """rung-1's heading text: '35 degrees left' (left positive), '0 degrees'."""
    angle = (angle + 180.0) % 360.0 - 180.0
    degrees = int(round(abs(angle)))
    if degrees == 0:
        return "0 degrees"
    return "%d degrees %s" % (degrees, "left" if angle > 0 else "right")


def tilt(angle):
    degrees = int(round(abs(angle)))
    if degrees == 0:
        return "0 degrees"
    return "%d degrees %s" % (degrees, "up" if angle > 0 else "down")


def call_json(call):
    body = {"name": call.name, "frame": call.frame}
    if call.name == "depth":
        body["point"] = [call.point[0], call.point[1]]
    return json.dumps(body)


def render_call(call, addressing="frame"):
    validate(call, addressing=addressing)
    return CALL_OPEN + call_json(call) + CALL_CLOSE


def render_response(text):
    if RESPONSE_OPEN in text or RESPONSE_CLOSE in text or CALL_OPEN in text or CALL_CLOSE in text:
        raise ValueError("A response may not contain tool tokens")
    return RESPONSE_OPEN + text + RESPONSE_CLOSE


def format_depth(metres):
    if not (isinstance(metres, (int, float)) and math.isfinite(metres) and metres > 0):
        raise ValueError("Depth must be a positive finite number of metres: %r" % (metres,))
    return "%s m" % num(metres)


def roll_text(angle):
    """'3 degrees left' (counterclockwise seen from behind the camera), '0 degrees'."""
    angle = (angle + 180.0) % 360.0 - 180.0
    degrees = int(round(abs(angle)))
    if degrees == 0:
        return "0 degrees"
    return "%d degrees %s" % (degrees, "left" if angle > 0 else "right")


def view_text(view):
    return "%d x %d degrees" % (int(round(view[0])), int(round(view[1])))


def format_pose(pose):
    x, y, z = pose.position
    values = (x, y, z, pose.heading_deg, pose.pitch_deg, pose.roll_deg) + tuple(pose.view_deg or ())
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Pose values must be finite")
    if pose.view_deg is not None and not all(0.0 < v < 180.0 for v in pose.view_deg):
        raise ValueError("The field of view must lie in (0, 180) degrees")
    text = "position (%s, %s, %s) m, heading %s, pitch %s, roll %s" % (
        num(x), num(y), num(z), turn(pose.heading_deg), tilt(pose.pitch_deg), roll_text(pose.roll_deg))
    if pose.view_deg is not None:
        text += ", view " + view_text(pose.view_deg)
    return text


def format_value(name, value):
    return format_depth(value) if name == "depth" else format_pose(value)


def format_error(error):
    return "error: " + str(error)


def exchange(call, value):
    """Call plus response text as it appears in a trace."""
    return render_call(call) + render_response(format_value(call.name, value))


# ---------------------------------------------------------------- reading responses back
_DEPTH = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*m\s*$")
_POSE = re.compile(r"^\s*position \((-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)\) m, "
                   r"heading (\d+) degrees(?: (left|right))?, pitch (\d+) degrees(?: (up|down))?"
                   r"(?:, roll (\d+) degrees(?: (left|right))?)?(?:, view (\d+) x (\d+) degrees)?\s*$")


def parse_response(name, text):
    """Value of a response text, or None for an error or unreadable response."""
    if name == "depth":
        match = _DEPTH.match(text)
        return float(match.group(1)) if match else None
    match = _POSE.match(text)
    if not match:
        return None
    heading = float(match.group(4)) * (-1.0 if match.group(5) == "right" else 1.0)
    pitch = float(match.group(6)) * (-1.0 if match.group(7) == "down" else 1.0)
    roll = float(match.group(8)) * (-1.0 if match.group(9) == "right" else 1.0) if match.group(8) else 0.0
    view = (float(match.group(10)), float(match.group(11))) if match.group(10) else None
    return PoseValue((float(match.group(1)), float(match.group(2)), float(match.group(3))), heading, pitch, roll, view)


# ---------------------------------------------------------------- parsing calls
def validate(call, addressing="frame"):
    limit = max_frame_index(addressing)
    if call.name not in NAMES:
        raise CallError("name", "unknown head %r; use depth or pose" % (call.name,))
    if type(call.frame) is not int or not 1 <= call.frame <= limit:
        raise CallError("frame", "frame must be an integer from 1 to %d" % limit)
    if addressing == "frame":
        if call.name == "pose" and call.frame not in POSE_FRAMES:
            raise CallError(
                "frame",
                "pose frame %d has no head output; valid frames are 1, 2, 4, ..., 32" % call.frame,
            )
        if call.name == "depth" and call.frame not in DEPTH_FRAMES:
            raise CallError(
                "frame",
                "depth frame %d has no head output; valid frames are 2, 4, ..., 32" % call.frame,
            )
    if call.name == "depth":
        if (not isinstance(call.point, tuple) or len(call.point) != 2
                or not all(type(v) is int and 0 <= v <= GRID for v in call.point)):
            raise CallError("point", "point must be [x, y] with integers from 0 to %d" % GRID)
    elif call.point is not None:
        raise CallError("point", "pose takes no point")
    return call


def _close_brackets(text):
    """Append the closers an unterminated JSON object needs (outside strings)."""
    stack, quote, escape = [], None, False
    for char in text:
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "{[":
            stack.append("}" if char == "{" else "]")
        elif char in "}]" and stack and stack[-1] == char:
            stack.pop()
    return text + (quote or "") + "".join(reversed(stack))


def _load_object(text, repairs):
    """Parse a JSON-like object with escalating repairs; returns a dict or raises CallError."""
    attempts = [(None, lambda s: s),
                ("closed_brackets", _close_brackets),
                ("trailing_comma", lambda s: re.sub(r",\s*([}\]])", r"\1", _close_brackets(s))),
                ("bare_keys", lambda s: re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z_0-9]*)\s*:", r'\1"\2":',
                                               re.sub(r",\s*([}\]])", r"\1", _close_brackets(s))))]
    for label, fix in attempts:
        try:
            value = json.loads(fix(text))
        except ValueError:
            continue
        if label:
            repairs.append(label)
        if isinstance(value, dict):
            return value
        raise CallError("json", "the call must be a JSON object")
    try:  # single quotes, Python literals (True/None), trailing commas
        value = ast.literal_eval(_close_brackets(text))
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        raise CallError("json", "the call is not valid JSON")
    if not isinstance(value, dict):
        raise CallError("json", "the call must be a JSON object")
    repairs.append("python_literal")
    return value


def _xml_function(body):
    """Qwen3.5's chat-template form: <function=depth><parameter=frame>3</parameter>...</function>."""
    match = re.match(r"\s*<function=([^>\s]+)>(.*?)(?:</function>\s*)?$", body, re.S)
    if not match:
        return None
    params = {"name": match.group(1)}
    for key, value in re.findall(r"<parameter=([^>\s]+)>(.*?)</parameter>", match.group(2), re.S):
        value = value.strip()
        try:
            params[key] = json.loads(value)
        except ValueError:
            params[key] = value
    return params


def _integer(value, code, what):
    if isinstance(value, bool):
        raise CallError(code, what)
    if isinstance(value, str):
        value = value.strip()
        try:
            value = float(value)
        except ValueError:
            raise CallError(code, what)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CallError(code, what)
        return int(round(value)), value != round(value)
    if isinstance(value, int):
        return value, False
    raise CallError(code, what)


def _point(params, repairs):
    raw = None
    for key in POINT_KEYS:
        if key in params:
            raw = params[key]
            break
    if raw is None and "x" in params and "y" in params:
        raw = [params["x"], params["y"]]
        repairs.append("separate_xy")
    if isinstance(raw, str):
        numbers = re.findall(r"-?\d+(?:\.\d+)?", raw)
        raw = [float(n) for n in numbers] if numbers else raw
        repairs.append("point_string")
    if isinstance(raw, dict) and "x" in raw and "y" in raw:
        raw = [raw["x"], raw["y"]]
        repairs.append("point_dict")
    what = "point must be [x, y] with integers from 0 to %d" % GRID
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise CallError("point", what)
    point = []
    for value in raw:
        number, rounded = _integer(value, "point", what)
        if rounded:
            repairs.append("rounded_point")
        if not 0 <= number <= GRID:
            raise CallError("point", what)
        point.append(number)
    return tuple(point)


def parse_call(body, addressing="frame"):
    """Parse the text between <tool_call> and </tool_call> into a validated Call, never raising."""
    repairs, extra = [], []
    limit = max_frame_index(addressing)
    try:
        if not isinstance(body, str):
            raise CallError("json", "the call is not text")
        text = body.strip()
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
        if fence:
            text = fence.group(1)
            repairs.append("code_fence")
        params = _xml_function(text)
        if params is not None:
            repairs.append("xml_function")
        else:
            start = text.find("{")
            if start < 0:
                raise CallError("json", "the call is not a JSON object")
            if start > 0 or (text.rfind("}") not in (-1, len(text) - 1)):
                repairs.append("surrounding_text")
            end = text.rfind("}")
            params = _load_object(text[start:end + 1] if end > start else text[start:], repairs)
        nested = params.get("function")
        if isinstance(nested, dict):  # OpenAI style {"function": {"name": ..., "arguments": ...}}
            params = dict(nested, **{k: v for k, v in params.items() if k != "function"})
            repairs.append("function_wrapper")
        for key in ("arguments", "parameters", "args"):
            inner = params.get(key)
            if isinstance(inner, str):
                try:
                    inner = json.loads(inner)
                except ValueError:
                    inner = None
            if isinstance(inner, dict):
                params = dict({k: v for k, v in params.items() if k != key}, **inner)
                repairs.append("arguments_wrapper")
                break
        raw_name = params.get("name", params.get("tool", params.get("head")))
        if not isinstance(raw_name, str):
            raise CallError("name", "the call needs a name: depth or pose")
        name = NAME_ALIASES.get(raw_name.strip().lower())
        if name is None:
            raise CallError("name", "unknown head %r; use depth or pose" % raw_name)
        if name != raw_name:
            repairs.append("name_alias")
        frame_key = next((key for key in FRAME_KEYS if key in params), None)
        if frame_key is None:
            raise CallError("frame", "frame must be an integer from 1 to %d" % limit)
        if frame_key != "frame":
            repairs.append("frame_key")
        what = "frame must be an integer from 1 to %d" % limit
        frame, rounded = _integer(params[frame_key], "frame", what)
        if rounded or not 1 <= frame <= limit:
            raise CallError("frame", what)
        if not isinstance(params[frame_key], int):
            repairs.append("frame_type")
        point = _point(params, repairs) if name == "depth" else None
        known = {"name", "tool", "head", frame_key}
        if name == "depth":
            known |= set(POINT_KEYS) | {"x", "y"}
        extra = sorted(k for k in params if k not in known)
        call = validate(Call(name, frame, point), addressing=addressing)
    except CallError as error:
        return ParseResult(None, error, tuple(repairs), tuple(extra))
    except Exception:  # a decode loop must survive any text the model writes
        return ParseResult(None, CallError("json", "the call is not valid JSON"), tuple(repairs), tuple(extra))
    return ParseResult(call, None, tuple(repairs), tuple(extra))


# ---------------------------------------------------------------- traces
EXCHANGE = re.compile(re.escape(CALL_OPEN) + r"(.*?)" + re.escape(CALL_CLOSE)
                      + r"(?:" + re.escape(RESPONSE_OPEN) + r"(.*?)" + re.escape(RESPONSE_CLOSE) + r")?", re.S)


def exchanges(text):
    """(call_start, call_end, response_end, body, response_text_or_None) for every call in a trace."""
    out = []
    for match in EXCHANGE.finditer(text):
        out.append((match.start(), match.start() + len(CALL_OPEN) + len(match.group(1)) + len(CALL_CLOSE),
                    match.end(), match.group(1), match.group(2)))
    return out


def strip_exchanges(text):
    """The trace without its calls and responses (for no-call ablations and fidelity checks)."""
    return EXCHANGE.sub("", text)
