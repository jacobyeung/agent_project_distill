"""SPEC 6.2 printed-point calculator; standalone, standard-library-only vendoring unit.

PrintedPointRegistry.register(*, camera, f1, spread, requested_frame,
                              actual_frame=None, label=None) -> dict
    Accept only finite JSON numbers already rounded to two decimals. Return the
    allocated point, frame metadata and exact canonical response line. An optional
    label must be the next P label. Returned containers never alias the registry.
PrintedPointRegistry.execute(command: str) -> dict
    Parse one exact label-only SPEC command. Return named results, unwrapped text
    and injected_text (including tool_response markers) from the same computation.

Distances/minima use displayed two-decimal distances. All equal displayed minima
are retained; the first input-order witness only controls the printed min line.
Closest prints only that min line; its JSON result retains every computed pair.
It must never break a category tie. Angles use whole degrees and refuse rounded
categorical boundaries 0/90/135/180, as the producer does. There are no derived
labels, means, transforms, scalar rankings, option choices or external inputs.

When a point has no reference heading, its camera coordinates and vertical
coordinate are public. The registry retains its rounded metric operands privately
for invariant measurements. Horizontal components never enter injected text;
only the resulting formatted measurement reaches the language model.
"""
import math
import re
from decimal import Context, Decimal, DecimalException, InvalidOperation, ROUND_HALF_EVEN, localcontext
from functools import wraps

API_VERSION = "printed-point-calculator-v3"
SPEC_SHA256 = "b908ca9d8eac9f29122948f4523501a7b680c4056b376711c81e29483e7502ac"
_LABEL = r"P[1-9][0-9]*"
_LIST = _LABEL + r"(?:," + _LABEL + r")*"
_FORMS = (
    ("dist", rf"<dist ({_LABEL}) ({_LABEL})>"),
    ("closest", rf"<closest A=({_LIST}) B=({_LIST})>"),
    ("cam_dist", rf"<cam_dist ({_LIST})>"),
    ("angle", rf"<angle S=({_LABEL}) F=({_LABEL}) Q=({_LABEL}) rule=(easy|medium|hard|turn)>"),
    ("turn", rf"<turn from=({_LABEL}) at=({_LABEL}) to=({_LABEL})>"),
    ("area", rf"<area C=({_LIST})>"),
)


class CalculatorError(ValueError):
    """Fail-closed input/command refusal; reason is stable and machine readable."""
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _require(ok, reason):
    if not ok:
        raise CalculatorError(reason)


def _decimal_context(function):
    @wraps(function)
    def call(*args, **kwargs):
        # Isolate rounding and traps from an inference caller's Decimal context.
        # This precision covers finite float inputs and their squared products.
        with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):
            try:
                return function(*args, **kwargs)
            except DecimalException as exc:
                raise CalculatorError("calculator_numeric_range") from exc
    return call


def _q(x, places=2):
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)


def _number(x):
    _require(type(x) in (int, float), "invalid_printed_number")
    d = Decimal(str(x))
    _require(d.is_finite(), "nonfinite_printed_number")
    try:
        _require(d == _q(d), "unrounded_printed_number")
    except InvalidOperation as exc:
        raise CalculatorError("invalid_printed_number") from exc
    return d


def _vector(x):
    _require(isinstance(x, (list, tuple)) and len(x) == 3, "invalid_printed_vector")
    return tuple(_number(v) for v in x)


def _json(x):
    if isinstance(x, Decimal):
        value = float(x)
        _require(math.isfinite(value), "nonfinite_result")
        return value
    if isinstance(x, (list, tuple)):
        return [_json(v) for v in x]
    if isinstance(x, dict):
        return {k: _json(v) for k, v in x.items()}
    return x


def _vec_text(v):
    return "(" + ", ".join(f"{x:.2f}" for x in v) + ")"


def _distance(a, b):
    delta = tuple(x-y for x, y in zip(a, b))
    squares = tuple(_q(x*x, 4) for x in delta)
    sumsq = _q(sum(squares), 4)
    return {"delta": delta, "squares": squares, "sumsq": sumsq,
            "value": _q(sumsq.sqrt()), "unit": "m"}


def parse_command(command):
    """Return JSON {op, arguments}; accept only the six exact SPEC spellings."""
    _require(type(command) is str, "invalid_calculator_command")
    for op, pattern in _FORMS:
        match = re.fullmatch(pattern, command)
        if not match:
            continue
        a = match.groups()
        if op == "dist": args = {"a": a[0], "b": a[1]}
        elif op == "closest": args = {"A": a[0].split(","), "B": a[1].split(",")}
        elif op == "cam_dist": args = {"points": a[0].split(",")}
        elif op == "angle": args = dict(zip(("S", "F", "Q", "rule"), a))
        elif op == "turn": args = dict(zip(("from", "at", "to"), a))
        else:
            args = {"C": a[0].split(",")}
            _require(len(args["C"]) >= 3, "insufficient_area_points")
        refs = [p for key, v in args.items() if key != "rule"
                for p in (v if isinstance(v, list) else [v])]
        _require(op == "turn" or len(refs) == len(set(refs)), "duplicate_point_reference")
        return {"op": op, "arguments": args}
    raise CalculatorError("unsupported_calculator_command")


def format_command(op, **arguments):
    """Format strict named label arguments; validate by the same grammar as parsing."""
    keys = {"dist": {"a", "b"}, "closest": {"A", "B"}, "cam_dist": {"points"},
            "angle": {"S", "F", "Q", "rule"}, "turn": {"from", "at", "to"}, "area": {"C"}}
    _require(type(op) is str and op in keys and set(arguments) == keys[op],
             "unsupported_calculator_arguments")
    a = arguments
    def labels(key):
        _require(isinstance(a[key], (list, tuple)) and all(type(p) is str for p in a[key]),
                 "invalid_point_list")
        return ",".join(a[key])
    if op == "dist": command = f"<dist {a['a']} {a['b']}>"
    elif op == "closest": command = f"<closest A={labels('A')} B={labels('B')}>"
    elif op == "cam_dist": command = f"<cam_dist {labels('points')}>"
    elif op == "angle": command = f"<angle S={a['S']} F={a['F']} Q={a['Q']} rule={a['rule']}>"
    elif op == "turn": command = f"<turn from={a['from']} at={a['at']} to={a['to']}>"
    else: command = f"<area C={labels('C')}>"
    parse_command(command)
    return command


class PrintedPointRegistry:
    """One registry per trace; only register publishes new immutable P labels."""
    def __init__(self):
        self._points = {}

    @_decimal_context
    def register(self, *, camera, f1, spread, requested_frame, actual_frame=None, label=None, heading_defined=True):
        actual_frame = requested_frame if actual_frame is None else actual_frame
        _require(all(type(k) is int and 1 <= k <= 32 for k in (requested_frame, actual_frame)),
                 "invalid_point_frame")
        _require(actual_frame == requested_frame or
                 (requested_frame % 2 == 1 and actual_frame == requested_frame+1),
                 "invalid_point_frame_substitution")
        expected = "P" + str(len(self._points)+1)
        if label is not None:
            _require(type(label) is str and re.fullmatch(_LABEL, label) is not None, "malformed_point_label")
            _require(label not in self._points, "duplicate_point_label")
            _require(label == expected, "nonsequential_point_label")
        cam, point, reliability = _vector(camera), _vector(f1), _number(spread)
        _require(reliability >= 0, "invalid_point_spread")
        from .contracts import partial_f1
        public_f1 = _vec_text(point) if heading_defined else partial_f1(point, lambda x: f'{x:.2f}')
        line = (f"{expected}: cam{actual_frame} {_vec_text(cam)} m; f1 {public_f1} m; "
                f"spread {reliability:.2f}")
        point = {"label": expected, "camera": cam, "f1": point, "spread": reliability,
                 "requested_frame": requested_frame, "actual_frame": actual_frame, "line": line}
        if not heading_defined:
            point["heading_defined"] = False
        published = _json(point)
        self._points[expected] = point
        return published

    @_decimal_context
    def execute(self, command):
        parsed = parse_command(command)
        op, a = parsed["op"], parsed["arguments"]
        refs = [p for key, v in a.items() if key != "rule"
                for p in (v if isinstance(v, list) else [v])]
        _require(all(p in self._points for p in refs), "unknown_point_label")
        points = self._points
        if op == "dist":
            result = {"a": a["a"], "b": a["b"], **_distance(points[a["a"]]["f1"], points[a["b"]]["f1"])}
            text = f"{result['value']:.2f} m"
        elif op in ("closest", "cam_dist"):
            if op == "closest":
                rows = [{"a": p, "b": q, **_distance(points[p]["f1"], points[q]["f1"])}
                        for p in a["A"] for q in a["B"]]
                names = [r["a"]+"-"+r["b"] for r in rows]
                witnesses = [{"a": r["a"], "b": r["b"]} for r in rows]
            else:
                rows = [{"point": p, **_distance(points[p]["camera"], (Decimal(0),)*3)} for p in a["points"]]
                names = [r["point"] for r in rows]
                witnesses = [{"point": r["point"]} for r in rows]
            minimum = min(r["value"] for r in rows)
            indices = [i for i, r in enumerate(rows) if r["value"] == minimum]
            minima = [witnesses[i] for i in indices]
            result = {"pairs" if op == "closest" else "points": rows, "value": minimum, "unit": "m",
                      "witness": minima[0], "minima": minima, "tied": len(minima) > 1}
            text = f"min {names[indices[0]]} {minimum:.2f} m"
            if op == "cam_dist":
                text = "\n".join(f"{name} {r['value']:.2f} m" for name, r in zip(names, rows)) + "\n" + text
        elif op in ("angle", "turn"):
            if op == "angle":
                s, f, q = (points[a[key]]["f1"] for key in ("S", "F", "Q"))
                u, v = [tuple(p[i]-s[i] for i in (0, 2)) for p in (f, q)]
            else:
                origin, at, target = (points[a[key]]["f1"] for key in ("from", "at", "to"))
                u = tuple(at[i]-origin[i] for i in (0, 2))
                v = tuple(target[i]-at[i] for i in (0, 2))
            _require(all(sum(x*x for x in p) > Decimal("0.000000000001") for p in (u, v)),
                     "degenerate_heading")
            dot, cross = _q(u[0]*v[0]+u[1]*v[1], 4), _q(u[0]*v[1]-u[1]*v[0], 4)
            _require(dot != 0 or cross != 0, "degenerate_printed_angle")
            theta = round(math.degrees(math.atan2(float(cross), float(dot))))
            _require(theta != 0 if op == "turn" else abs(theta) not in (0, 90, 135, 180), "rounding_boundary")
            side = "left" if theta > 0 else "right"
            rule = "turn" if op == "turn" else a["rule"]
            if rule == "hard": label = ("front-" if abs(theta) < 90 else "back-") + side
            elif rule == "medium": label = "back" if abs(theta) >= 135 else side
            elif rule == "turn": label = "Turn Back" if abs(theta) >= 135 else "Turn " + side.title()
            else: label = side
            result = {"u": u, "v": v, "dot": dot, "cross": cross, "theta": theta,
                      "unit": "degree", "rule": rule, "label": label}
            text = (f"u {_vec_text(u)}; v {_vec_text(v)}; dot {dot:.4f}; "
                    f"cross {cross:.4f}; theta {theta} deg; {label}")
        else:
            corners = [points[p]["f1"] for p in a["C"]]
            terms = [_q(p[0]*corners[(i+1) % len(corners)][2]-p[2]*corners[(i+1) % len(corners)][0], 4)
                     for i, p in enumerate(corners)]
            total = _q(sum(terms), 4)
            result = {"corners": a["C"], "terms": terms, "signed_sum": total,
                      "value": _q(abs(total)/2), "unit": "m2"}
            text = f"area {result['value']:.2f} m^2"
        return _json({"api_version": API_VERSION, "spec_sha256": SPEC_SHA256, "command": command,
                      **parsed, "result": result, "text": text,
                      "injected_text": "<tool_response>"+text+"</tool_response>"})
