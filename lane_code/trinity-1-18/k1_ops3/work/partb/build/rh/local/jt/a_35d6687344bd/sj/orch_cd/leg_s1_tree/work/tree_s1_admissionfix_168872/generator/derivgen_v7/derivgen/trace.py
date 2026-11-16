"""Assistant arithmetic is evaluated on exactly the displayed operands."""
import math
import copy

import numpy as np

from .common import CONVENTION, SIGN, ProvenanceError, Refusal, encoded, rounded
from .calculator import CalculatorError, PrintedPointRegistry


def compute(op, a):
    if op == "mul": return a[0]*a[1]
    if op == "div": return np.asarray(a[0])/a[1]
    if op == "sqrt": return math.sqrt(a[0])
    if op == "mod": return a[0] % a[1]
    if op == "add": return np.asarray(a[0]) + a[1]
    if op == "sub": return np.asarray(a[0]) - a[1]
    if op == "matvec": return np.asarray(a[0]) @ a[1]
    if op == "local": return np.asarray(a[0]).T @ a[1]
    if op == "mean": return np.mean(a, axis=0)
    if op == "stack": return np.asarray(a)
    if op == "norm": return np.linalg.norm(a[0])
    if op == "abs": return abs(a[0])
    if op == "min": return min(a)
    if op == "max": return max(a)
    if op == "sum": return sum(a)
    if op == "scale": return np.asarray(a[0]) * a[1]
    if op == "x": return a[0][0]
    if op == "y": return a[0][1]
    if op == "z": return a[0][2]
    if op == "dot": return a[0][0]*a[1][0] + a[0][2]*a[1][2]
    if op == "cross": return a[0][0]*a[1][2] - a[0][2]*a[1][0]
    if op == "atan2": return math.degrees(math.atan2(a[0], a[1]))
    if op == "shoelace":
        p = np.asarray(a)
        return abs(float(np.dot(p[:, 0], np.roll(p[:, 2], -1))
                         - np.dot(p[:, 2], np.roll(p[:, 0], -1)))) / 2
    if op == "count": return len(a)
    raise Refusal("unknown_operation", op)


class Trace:
    def __init__(self):
        self.events, self.values, self.units = [], {}, {}
        self.point_registry = PrintedPointRegistry()
        self.add("assistant", "convention", text=CONVENTION + "; " + SIGN)

    def add(self, role, kind, **kw):
        e = {"role": role, "kind": kind, "target_loss": int(role == "assistant"), **kw}
        self.events.append(e)
        return e

    def tool(self, name, arguments, values):
        call = "t" + str(len(self.events))
        out = {}
        for key, (v, unit) in values.items():
            node = call + "." + key
            v = rounded(v, 0 if unit == "degree" else 2)
            out[node] = {"value": v, "unit": unit}
        extra = {}
        if name == "depth_at":
            pts = arguments.get("pts")
            if not isinstance(pts, list) or not 1 <= len(pts) <= 4:
                raise Refusal("invalid_depth_batch")
            registry = copy.deepcopy(self.point_registry)
            published = []
            try:
                for i in range(len(pts)):
                    prefix = "" if len(pts) == 1 else f"{i}."
                    get = lambda key: out[call+"."+prefix+key]["value"]
                    published.append(registry.register(camera=get("camera"), f1=get("f1"), spread=get("spread"),
                        requested_frame=arguments["frame"], actual_frame=arguments.get("image_frame", arguments["frame"])))
            except CalculatorError as exc:
                raise Refusal(exc.reason) from exc
            extra["points"] = published
            self.point_registry = registry
        for node, item in out.items():
            self.values[node], self.units[node] = item["value"], item["unit"]
        self.add("assistant", "tool_call", name=name, arguments=copy.deepcopy(arguments), call_id=call)
        self.add("tool", "tool_response", name=name, call_id=call, values=out, **extra)
        return {key: call + "." + key for key in values}

    def calculator(self, command):
        """Append a supervised label-only call and a masked exact calculator reply.

        Return the JSON response with named results/witnesses. This API does not
        migrate family decisions or add arithmetic nodes/derived point labels.
        """
        try:
            response = self.point_registry.execute(command)
        except CalculatorError as exc:
            raise Refusal(exc.reason) from exc
        call = "c" + str(len(self.events))
        self.add("assistant", "calculator_call", call_id=call, command=command)
        self.add("tool", "calculator_response", call_id=call, response=response)
        return copy.deepcopy(response)

    def calc(self, op, *args, unit, meaning="", places=None):
        # Expand compounds into individually printed products, sums and roots.
        if op == "norm":
            coordinates = [self.calc(axis, args[0], unit=unit) for axis in ("x", "y", "z")]
            squares = [self.calc("mul", c, c, unit="m2", places=4) for c in coordinates]
            total = self.calc("sum", *squares, unit="m2", places=4, meaning="sum of squares")
            return self.calc("sqrt", total, unit=unit, meaning=meaning)
        if op in ("dot", "cross"):
            ux, uz = [self.calc(axis, args[0], unit="m") for axis in ("x", "z")]
            vx, vz = [self.calc(axis, args[1], unit="m") for axis in ("x", "z")]
            a, b = (vx, vz) if op == "dot" else (vz, vx)
            p = self.calc("mul", ux, a, unit="m2", places=4)
            q = self.calc("mul", uz, b, unit="m2", places=4)
            return self.calc("add" if op == "dot" else "sub", p, q, unit="m2", places=4, meaning=meaning)
        if op == "shoelace":
            terms = []
            for i, p in enumerate(args):
                q = args[(i+1) % len(args)]
                px, pz = [self.calc(axis, p, unit="m") for axis in ("x", "z")]
                qx, qz = [self.calc(axis, q, unit="m") for axis in ("x", "z")]
                a = self.calc("mul", px, qz, unit="m2", places=4)
                b = self.calc("mul", qx, pz, unit="m2", places=4)
                terms.append(self.calc("sub", a, b, unit="m2", places=4))
            total = self.calc("sum", *terms, unit="m2", places=4)
            return self.calc("div", self.calc("abs", total, unit="m2", places=4), 2, unit="m2", meaning=meaning)
        node = "n" + str(len(self.events))
        operands = [self.values[x] if isinstance(x, str) else x for x in args]
        places = (0 if unit in ("degree", "count", "frame") else 2) if places is None else places
        value = rounded(compute(op, operands), places)
        self.values[node], self.units[node] = value, unit
        self.add("assistant", "arithmetic", id=node, op=op, args=list(args),
                 value=value, unit=unit, meaning=meaning, places=places)
        return node

    def distance(self, a, b):
        delta = self.calc("sub", a, b, unit="m", meaning="per-axis difference")
        return self.calc("norm", delta, unit="m", meaning="Euclidean norm")

    def angle(self, u, v):
        if min(np.linalg.norm(np.asarray(self.values[x])[[0, 2]]) for x in (u, v)) < 1e-6:
            raise Refusal("degenerate_heading")
        dot = self.calc("dot", u, v, unit="m2", meaning="floor dot")
        cross = self.calc("cross", u, v, unit="m2", meaning="floor cross; positive means left")
        if self.values[dot] == self.values[cross] == 0:
            raise Refusal("degenerate_printed_angle")
        self.last_cross = cross
        return self.calc("atan2", cross, dot, unit="degree", meaning=SIGN)


def loss_spans(target, output_spans):
    """Half-open Python character offsets; all non-output text receives loss 1."""
    result, cursor = [], 0
    for span in output_spans:
        start, end = span["start"], span["end"]
        if not cursor <= start < end <= len(target): raise Refusal("invalid_output_span")
        if cursor < start: result.append({"start": cursor, "end": start, "role": "assistant", "target_loss": 1})
        result.append({"start": start, "end": end, "role": "tool", "target_loss": 0, "call_id": span["call_id"]})
        cursor = end
    if cursor < len(target): result.append({"start": cursor, "end": len(target), "role": "assistant", "target_loss": 1})
    return result


def remap_tool_spans(original, rewritten, spans):
    """Shift a byte-identical programmatic body after a plan-only rewrite."""
    old_plan, sep, old_body = original.partition("\n\n")
    new_plan, new_sep, new_body = rewritten.partition("\n\n")
    if not sep or not new_sep or old_body != new_body:
        raise Refusal("rewrite_programmatic_body_changed")
    delta = len(new_plan)-len(old_plan)
    if any(s["start"] < len(old_plan)+2 for s in spans): raise Refusal("output_span_inside_plan")
    return [{**s, "start": s["start"]+delta, "end": s["end"]+delta} for s in spans]


def render(events, answer, *, include_spans=False):
    """SPEC L1 tokens inline in prose; structured events retain loss boundaries."""
    if events and events[0].get("format") == "spec-v3.8-calculator-v2":
        from .canon_render import render as canonical_render
        projection = canonical_render(events, answer)
        return projection if include_spans else projection["target"]
    paragraphs, calls, printed = [], {}, {}

    class Fragment(str):
        def __new__(cls, text, role, index, call_id=None):
            obj = str.__new__(cls, text)
            obj.role, obj.index, obj.call_id = role, index, call_id
            return obj

    class Sentences(list):
        def append(self, text, role=None):
            super().append(Fragment(text, role or e["role"], event_index, e.get("call_id")))

    sentence = Sentences()

    def flush():
        if sentence:
            paragraphs.append(list(sentence))
            sentence.clear()

    def value(v, places=2):
        if isinstance(v, list): return "(" + ", ".join(value(x, places) for x in v) + ")"
        return f"{v:.{places}f}" if isinstance(v, (int, float)) else str(v)

    def expression(op, a):
        if op in ("add", "sub", "scale", "mul", "div", "mod"):
            symbol = {"add": "+", "sub": "-", "scale": "*", "mul": "*", "div": "/", "mod": "mod"}[op]
            return f"{a[0]} {symbol} {a[1]}"
        if op == "sum": return " + ".join(a)
        if op in ("x", "y", "z"): return f"{a[0]}[{dict(x=0,y=1,z=2)[op]}]"
        return f"{op}({', '.join(a)})"

    for event_index, e in enumerate(events):
        kind = e["kind"]
        if kind == "substitution": continue
        if kind in ("plan", "convention", "frame_choice"):
            flush()
            paragraphs.append([Fragment(e.get("text", e.get("reason", "")), e["role"], event_index)])
        elif kind == "click":
            flush()
            if e["points"]:
                sentence.append(f"I locate the {e['object']} at {e['points']} in frame {e['frame']}.")
            else:
                sentence.append(f"I do not see the {e['object']} in frame {e['frame']}.")
        elif kind == "correction":
            flush()
            sentence.append("My click may be on the edge; clicking closer to the middle. "
                            f"The printed spread exceeds 0.25, so I move 30 grid units toward {e['toward']} "
                            f"and re-click {e['next']} in frame {e['frame']}.")
        elif kind == "tool_call":
            calls[e["call_id"]] = e
        elif kind == "calculator_call":
            calls[e["call_id"]] = e
        elif kind == "calculator_response":
            call = calls[e["call_id"]]
            sentence.append(call["command"], role="assistant")
            sentence.append(e["response"]["text"])
        elif kind == "tool_response":
            call = calls[e["call_id"]]
            args, name = call["arguments"], call["name"]
            get = lambda key: value(e["values"][e["call_id"]+"."+key]["value"])
            for node, item in e["values"].items():
                places = 0 if item["unit"] == "degree" else 2
                printed[node] = value(item["value"], places)
            if name == "depth_at":
                import json
                k = args.get("image_frame", args["frame"])
                image = f" image_frame={k}" if "image_frame" in args else ""
                pts = json.dumps(args["pts"], separators=(",", ":"))
                sentence.append(f"<depth_at frame={args['frame']}{image} pts={pts}>", role="assistant")
                sentence.append("\n".join(p["line"] for p in e["points"]))
            elif name == "pose":
                k = args["frame"]
                sentence.append(f"<pose frame={k}>", role="assistant")
                sentence.append(f"gives f1 centre {get('t')} m ({e['call_id']}.t), "
                                f"camera-to-f1 matrix {get('R')} ({e['call_id']}.R), and "
                                f"L_{k}-to-f1 matrix {get('level_R')} ({e['call_id']}.level_R); "
                                f"yaw {value(e['values'][e['call_id']+'.yaw']['value'], 0)} degrees ({e['call_id']}.yaw), positive to the left.")
            elif name == "move":
                sentence.append(f"<move from={args['from']} to={args['to']}>", role="assistant")
                delta = e["values"][e["call_id"]+".delta"]["value"]
                sentence.append(f"dx = {delta[0]:+.2f} m, dy = {delta[1]:+.2f} m, dz = {delta[2]:+.2f} m, "
                                f"distance = {get('distance')} m (L_{args['from']}, dy positive down; "
                                f"{e['call_id']}.delta; {e['call_id']}.distance).")
            else: raise Refusal("unbacked_tool", name)
        elif kind == "arithmetic":
            args = [printed[a] if isinstance(a, str) else str(a) for a in e["args"]]
            printed[e["id"]] = value(e["value"], e["places"])
            flush()
            sentence.append(f"{e['id']} = {expression(e['op'], args)} = {printed[e['id']]} {e['unit']}")
        elif kind == "merge":
            sentence.append(f"The printed centre distances and merge thresholds {encoded(e['checks'])} assign detection "
                            f"{e['detection']} to observable instance {e['cluster']}.")
        elif kind == "decision":
            flush()
            if e["mode"] == "numeric":
                d = e["display"]
                sentence.append(f"Rounding {e['nodes'][0]} in {d['unit']} to {d['decimals']} decimal places gives {answer} {d['unit']}.")
            elif e["mode"] == "direction":
                sentence.append(f"The signed angle {e['nodes'][0]} places the object {e['result']}, which matches option {answer}.")
            elif e["mode"] == "route":
                sentence.append(f"The signed turns give {e['result']}, which matches option {answer}.")
            else:
                sentence.append(f"Comparing the printed values {[printed[n] for n in e['nodes']]} gives {e['result']}, which matches option {answer}.")
        if sum(len(s) for s in sentence) > 1400:
            flush()
    flush()
    parts, spans, cursor = [], [], 0

    def emit(text, role="assistant", index=None, call_id=None):
        nonlocal cursor
        if role == "tool":
            text = "<tool_response>" + str(text) + "</tool_response>"
        start = cursor
        parts.append(str(text)); cursor += len(text)
        if role == "tool":
            spans.append({"start": start, "end": cursor, "call_id": call_id, "event_index": index,
                          "event_id": "event:"+str(index), "target_loss": 0})

    emit("<think>\n")
    for p, fragments in enumerate(paragraphs):
        if p: emit("\n\n")
        for i, fragment in enumerate(fragments):
            if i: emit(" ")
            emit(fragment, fragment.role, fragment.index, fragment.call_id)
    emit("\n</think>\n\n"); emit(str(answer))
    target = "".join(parts)
    if not include_spans: return target
    return {"target": target, "tool_output_spans": spans, "loss_spans": loss_spans(target, spans)}


def render_with_spans(events, answer):
    """P3 API: text plus offsets recorded during construction, without searching."""
    return render(events, answer, include_spans=True)
