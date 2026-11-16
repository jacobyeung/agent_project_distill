"""Independent scalar replay, raster readout checks and semantic answer gates.

This module never calls the builder's arithmetic or decision functions.
"""
import math
import copy
import re
from collections import Counter, defaultdict
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext

import numpy as np

from .bindings import F17, NUMERIC, bind, gt_label, question, unit_policy
from .common import CONVENTION, Refusal, digest, rounded as raw_rounded


def rounded(v, places=2): return raw_rounded(v, places)

def require(ok, reason, detail=""):
    if not ok:
        raise Refusal(reason, detail)


def _printed_number(value):
    require(type(value) in (int, float), "calculator_invalid_printed_number")
    d = Decimal(str(value))
    require(d.is_finite() and d == quantize(value, 2), "calculator_unrounded_input")
    return d


def _replay_calculator(command, points):
    """Independent parser, Decimal arithmetic and formatter; no producer calls."""
    require(type(command) is str and command.startswith("<") and command.endswith(">"), "calculator_grammar")
    tokens = command[1:-1].split(" ")
    op, args = tokens[0], {}
    if op == "dist" and len(tokens) == 3:
        args = {"a": tokens[1], "b": tokens[2]}
    elif op == "closest" and len(tokens) == 3 and tokens[1].startswith("A=") and tokens[2].startswith("B="):
        args = {"A": tokens[1][2:].split(","), "B": tokens[2][2:].split(",")}
    elif op == "cam_dist" and len(tokens) == 2:
        args = {"points": tokens[1].split(",")}
    elif op == "angle" and len(tokens) == 5 and all(t.startswith(k+"=") for t, k in zip(tokens[1:], ("S", "F", "Q", "rule"))):
        args = {k: t[len(k)+1:] for t, k in zip(tokens[1:], ("S", "F", "Q", "rule"))}
        require(args["rule"] in ("easy", "medium", "hard", "turn"), "calculator_rule")
    elif op == "turn" and len(tokens) == 4 and all(t.startswith(k+"=") for t, k in zip(tokens[1:], ("from", "at", "to"))):
        args = {k: t[len(k)+1:] for t, k in zip(tokens[1:], ("from", "at", "to"))}
    elif op == "area" and len(tokens) == 2 and tokens[1].startswith("C="):
        args = {"C": tokens[1][2:].split(",")}
        require(len(args["C"]) >= 3, "calculator_area_cardinality")
    require(bool(args), "calculator_grammar")
    labels = [p for key, v in args.items() if key != "rule" for p in (v if isinstance(v, list) else [v])]
    require(all(re.fullmatch(r"P[1-9][0-9]*", p) for p in labels), "calculator_label_grammar")
    require(op == "turn" or len(set(labels)) == len(labels), "calculator_duplicate_reference")
    require(all(p in points for p in labels), "calculator_unknown_label")
    def q(d, places=2): return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    def coordinates(p, frame="f1"): return [Decimal(str(x)) for x in points[p][frame]]
    def vector_text(v): return "("+", ".join(format(x, ".2f") for x in v)+")"
    def distance(p, other=None):
        v = coordinates(p) if other is not None else coordinates(p, "camera")
        delta = [x-y for x, y in zip(v, coordinates(other))] if other is not None else v
        squares = [q(x**2, 4) for x in delta]
        total = q(sum(squares), 4)
        return {"delta": delta, "squares": squares, "sumsq": total, "value": q(total.sqrt()), "unit": "m"}
    if op == "dist":
        result = {"a": args["a"], "b": args["b"], **distance(args["a"], args["b"])}
        text = format(result["value"], ".2f")+" m"
    elif op in ("closest", "cam_dist"):
        if op == "closest":
            entries = [{"a": p, "b": other, **distance(p, other)} for p in args["A"] for other in args["B"]]
            witnesses = [{k: row[k] for k in ("a", "b")} for row in entries]
            names = [row["a"]+"-"+row["b"] for row in entries]
        else:
            entries = [{"point": p, **distance(p)} for p in args["points"]]
            witnesses = [{"point": row["point"]} for row in entries]
            names = [row["point"] for row in entries]
        best = min(row["value"] for row in entries)
        indices = [i for i, row in enumerate(entries) if row["value"] == best]
        minima = [witnesses[i] for i in indices]
        result = {"pairs" if op == "closest" else "points": entries, "value": best, "unit": "m",
                  "witness": minima[0], "minima": minima, "tied": len(indices) != 1}
        lines = ([name+" "+format(row["value"], ".2f")+" m" for name, row in zip(names, entries)]
                 if op == "cam_dist" else [])
        text = "\n".join(lines+["min "+names[indices[0]]+" "+format(best, ".2f")+" m"])
    elif op in ("angle", "turn"):
        if op == "angle":
            s, f, target = [coordinates(args[k]) for k in ("S", "F", "Q")]
            u, v = [[p[i]-s[i] for i in (0, 2)] for p in (f, target)]
        else:
            start, middle, end = [coordinates(args[k]) for k in ("from", "at", "to")]
            u = [middle[i]-start[i] for i in (0, 2)]
            v = [end[i]-middle[i] for i in (0, 2)]
        require(all(sum(x*x for x in heading) > Decimal("1e-12") for heading in (u, v)), "calculator_degenerate_heading")
        products = [x*y for x, y in zip(u, v)]
        dot = q(products[0]+products[1], 4)
        cross = q(u[0]*v[1]-v[0]*u[1], 4)
        require(dot != 0 or cross != 0, "calculator_degenerate_printed_angle")
        theta = round(180*math.atan2(float(cross), float(dot))/math.pi)
        require(theta != 0 if op == "turn" else abs(theta) not in (0, 90, 135, 180), "calculator_rounding_boundary")
        rule = "turn" if op == "turn" else args["rule"]
        label = "left" if theta > 0 else "right"
        if rule == "hard": label = ("front" if -90 < theta < 90 else "back")+"-"+label
        elif rule in ("medium", "turn"):
            if abs(theta) >= 135: label = "back"
            if rule == "turn": label = "Turn "+label.capitalize()
        result = {"u": u, "v": v, "dot": dot, "cross": cross, "theta": theta,
                  "unit": "degree", "rule": rule, "label": label}
        text = ("u "+vector_text(u)+"; v "+vector_text(v)+f"; dot {dot:.4f}; cross {cross:.4f}; "
                f"theta {theta} deg; {label}")
    else:
        polygon = [coordinates(p) for p in args["C"]]
        terms = []
        for i in range(len(polygon)):
            a, b = polygon[i], polygon[(i+1) % len(polygon)]
            terms.append(q(a[0]*b[2]-b[0]*a[2], 4))
        signed = q(sum(terms), 4)
        result = {"corners": args["C"], "terms": terms, "signed_sum": signed,
                  "value": q(abs(signed)*Decimal("0.5")), "unit": "m2"}
        text = f"area {result['value']:.2f} m^2"
    def plain(obj):
        if isinstance(obj, Decimal): return float(obj)
        if isinstance(obj, list): return [plain(v) for v in obj]
        if isinstance(obj, dict): return {k: plain(v) for k, v in obj.items()}
        return obj
    return plain({"api_version": "printed-point-calculator-v3",
                  "spec_sha256": "b908ca9d8eac9f29122948f4523501a7b680c4056b376711c81e29483e7502ac",
                  "command": command, "op": op, "arguments": args, "result": result, "text": text,
                  "injected_text": "<tool_response>"+text+"</tool_response>"})


def audit_printed_calculator(events):
    """Replay labels and calculator events from published depth values only.

    No scene or private GT input. Full row audit additionally retains all existing
    geometry, source, reference, rendering and loss-span gates.
    """
    with localcontext(Context(prec=1024, rounding=ROUND_HALF_EVEN)):
        try:
            return _audit_printed_calculator(events)
        except DecimalException as exc:
            raise Refusal("calculator_numeric_range") from exc


def _audit_printed_calculator(events):
    points, results, pending, seen = {}, {}, {}, set()
    for e in events:
        kind = e["kind"]
        if kind in ("tool_call", "calculator_call"):
            require(e["role"] == "assistant" and e["target_loss"] == 1, "calculator_call_role")
            call = e["call_id"]
            require(call not in seen, "calculator_duplicate_call")
            seen.add(call)
            if kind == "calculator_call":
                require(not pending, "calculator_pending_readout")
                # Resolve now so even a later registration cannot repair a forward reference.
                results[call] = _replay_calculator(e["command"], points)
            pending[call] = e
        elif kind in ("tool_response", "calculator_response"):
            require(e["role"] == "tool" and e["target_loss"] == 0, "calculator_response_role")
            call = e["call_id"]
            require(call in pending, "calculator_orphan_response")
            request = pending.pop(call)
            if kind == "calculator_response":
                require(request["kind"] == "calculator_call" and digest(e["response"]) == digest(results[call]),
                        "calculator_response_mismatch")
                continue
            require(request["kind"] == "tool_call" and request["name"] == e["name"], "calculator_head_call_mismatch")
            if e["name"] != "depth_at": continue
            a = request["arguments"]
            frame, actual = a["frame"], a.get("image_frame", a["frame"])
            require(all(type(k) is int and 1 <= k <= 32 for k in (frame, actual)), "calculator_frame")
            require(actual == frame or frame % 2 == 1 and actual == frame+1, "calculator_frame_substitution")
            pts = a.get("pts")
            require(isinstance(pts, list) and 1 <= len(pts) <= 4, "calculator_depth_batch")
            expected, keys = [], set()
            for i in range(len(pts)):
                prefix = "" if len(pts) == 1 else str(i)+"."
                readouts = {}
                for key, unit in (("camera", "m"), ("f1", "m"), ("spread", "1")):
                    node = call+"."+prefix+key
                    keys.add(node)
                    require(node in e["values"] and e["values"][node]["unit"] == unit, "calculator_depth_readout")
                    value = e["values"][node]["value"]
                    if key != "spread":
                        require(isinstance(value, list) and len(value) == 3, "calculator_point_shape")
                        readouts[key] = [float(_printed_number(v)) for v in value]
                    else: readouts[key] = float(_printed_number(value))
                require(readouts["spread"] >= 0, "calculator_point_spread")
                label = "P"+str(len(points)+1)
                fmt = lambda v: "("+", ".join(f"{x:.2f}" for x in v)+")"
                line = (f"{label}: cam{actual} {fmt(readouts['camera'])} m; f1 {fmt(readouts['f1'])} m; "
                        f"spread {readouts['spread']:.2f}")
                point = {"label": label, **readouts, "requested_frame": frame, "actual_frame": actual, "line": line}
                expected.append(point)
                points[label] = point
            require(keys == set(e["values"]) and digest(e.get("points")) == digest(expected), "calculator_point_publication")
    require(not pending, "calculator_missing_response")
    return {"points": points, "calculator_results": results}


def appearance_ids(scene, obj, k):
    raster = scene.gt.inst[k - 1]
    threshold = (raster.size + 499) // 500
    return {iid for iid in scene.ids(obj, many=True) if np.count_nonzero(raster == iid) >= threshold}


def check_appearance_click(scene, obj, event):
    k = event["frame"]
    expected = appearance_ids(scene, obj, k)
    observed = []
    for uv in event["points"]:
        x, y = scene.gt.px([uv])
        observed.append(int(scene.gt.inst[k-1, y[0], x[0]]))
    require(len(observed) == len(expected) and set(observed) == expected, "appearance_visibility_mismatch")


def vec(a, b, f):
    return [vec(x, y, f) for x, y in zip(a, b)] if isinstance(a, list) else f(a, b)


def norm(a): return math.sqrt(sum(x*x for x in a))
def sub(a, b): return [x-y for x, y in zip(a, b)]
def mean(a): return [sum(p[i] for p in a)/len(a) for i in range(len(a[0]))]
def mv(R, p): return [sum(x*y for x, y in zip(row, p)) for row in R]
def trans(R): return list(map(list, zip(*R)))
def dist(a, b):
    delta = rounded(sub(a, b))
    return rounded(math.sqrt(round(sum(round(x*x, 4) for x in delta), 4)))


def scalar_op(op, a):
    if op == "mul": return a[0]*a[1]
    if op == "div": return [x/a[1] for x in a[0]] if isinstance(a[0], list) else a[0]/a[1]
    if op == "sqrt": return math.sqrt(a[0])
    if op == "mod": return a[0] % a[1]
    if op == "add": return vec(a[0], a[1], lambda x, y: x+y)
    if op == "sub": return vec(a[0], a[1], lambda x, y: x-y)
    if op == "matvec": return mv(a[0], a[1])
    if op == "local": return mv(trans(a[0]), a[1])
    if op == "mean": return mean(a)
    if op == "stack": return a
    if op == "norm": return norm(a[0])
    if op == "abs": return abs(a[0])
    if op == "min": return min(a)
    if op == "max": return max(a)
    if op == "sum": return sum(a)
    if op == "scale":
        def scale(v): return [scale(x) for x in v] if isinstance(v, list) else v*a[1]
        return scale(a[0])
    if op in ("x", "y", "z"): return a[0][{"x": 0, "y": 1, "z": 2}[op]]
    if op == "dot": return a[0][0]*a[1][0]+a[0][2]*a[1][2]
    if op == "cross": return a[0][0]*a[1][2]-a[0][2]*a[1][0]
    if op == "atan2": return math.atan2(a[0], a[1])*180/math.pi
    if op == "shoelace":
        return abs(sum(a[i][0]*a[(i+1) % len(a)][2]-a[(i+1) % len(a)][0]*a[i][2]
                       for i in range(len(a))))/2
    if op == "count": return len(a)
    raise Refusal("replay_unknown_operation", op)


def close(a, b, tol=1.1e-8):
    if isinstance(a, list) or isinstance(b, list):
        return isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol


def quantize(value, places):
    try:
        d = Decimal(str(value))
        require(d.is_finite(), "nonfinite_answer")
        return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    except (ValueError, ArithmeticError) as exc:
        raise Refusal("invalid_numeric_answer", str(value)) from exc


def quantile(a, q):
    s = sorted(a)
    require(bool(s), "empty_depth_patch")
    x = (len(s)-1)*q/100
    i = int(x)
    return s[i] + (s[min(i+1, len(s)-1)]-s[i])*(x-i)


def verify_depth(scene, iid, k, uv):
    gt = scene.gt
    require(all(type(x) is int and 0 <= x <= 1000 for x in uv), "invalid_grid_click")
    x = min(gt.W-1, max(0, int(uv[0]/1000*gt.W)))
    y = min(gt.H-1, max(0, int(uv[1]/1000*gt.H)))
    require(int(gt.inst[k-1, y, x]) == iid, "replay_mask_membership")
    patch = []
    for dx in (-10, -5, 0, 5, 10):
        for dy in (-10, -5, 0, 5, 10):
            xx = int(min(999.9, max(0, uv[0]+dx))/1000*gt.W)
            yy = int(min(999.9, max(0, uv[1]+dy))/1000*gt.H)
            d = float(gt.depth[k-1, yy, xx])
            if d > 0: patch.append(d)
    depth = quantile(patch, 30)
    K = gt.K if getattr(gt, "K_frames", None) is None else gt.K_frames[k-1]
    ray = mv(np.linalg.inv(K).tolist(), [x+.5, y+.5, 1])
    camera = raw_rounded([v*depth for v in ray])
    spread = rounded((quantile(patch, 80)-quantile(patch, 20))/max(quantile(patch, 50), .001))
    return camera, spread


def replay_pose(scene, k, printed=True):
    # Reconstruct the level basis directly; do not call the builder's pose method.
    R1, origin = scene.gt.cam(1)
    f = [float(R1[0, 2]), float(R1[1, 2]), 0.]
    f = [x/norm(f) for x in f]
    B = trans([[f[1], -f[0], 0.], [0., 0., -1.], f])
    R, t = scene.gt.cam(k)
    heading = [float(R[0, 2]), float(R[1, 2]), 0.]
    heading = [x/norm(heading) for x in heading]
    L = trans([[heading[1], -heading[0], 0.], [0., 0., -1.], heading])
    Bt = trans(B)
    product = lambda A, C: trans([mv(A, col) for col in trans(C)])
    flip = lambda a: [a[0], [-v for v in a[1]], a[2]]
    t1 = mv(Bt, sub(t.tolist(), origin.tolist()))
    places = 2 if printed else 8
    level = raw_rounded(flip(product(Bt, L)))
    return {"R": rounded(flip(product(Bt, R.tolist())), places), "t": rounded([t1[0], -t1[1], t1[2]], places),
            "level_R": rounded(level, places), "yaw": round(math.atan2(-level[0][2], level[2][2])*180/math.pi)}


def replay_move(scene, i, j):
    pi, pj = replay_pose(scene, i, False), replay_pose(scene, j, False)
    delta = mv(trans(pi["level_R"]), sub(pj["t"], pi["t"]))
    return rounded(delta), rounded(norm(delta)), delta


def replay_camera_turn(scene, i, j):
    """Relative horizontal heading from native rotations, rounded only once."""
    headings = []
    for k in (i, j):
        rotation, _ = scene.gt.cam(k)
        headings.append([float(rotation[0, 2]), float(rotation[1, 2])])
    a, b = headings
    require(math.hypot(*a) > 1e-8 and math.hypot(*b) > 1e-8, "degenerate_camera_heading")
    value = round(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0], a[0]*b[0]+a[1]*b[1])))
    return 180 if value == -180 else value


def label_direction(t, theta):
    if t.endswith("hard"):
        return ("front" if -90 < theta < 90 else "back") + ("-left" if theta > 0 else "-right")
    if t.endswith("medium") and abs(theta) >= 135: return "back"
    return "left" if theta > 0 else "right"


def angle(u, v):
    require(norm([u[0], u[2]]) > 1e-6 and norm([v[0], v[2]]) > 1e-6, "replay_degenerate_heading")
    dot, cross = round(round(u[0]*v[0], 4)+round(u[2]*v[2], 4), 4), round(round(u[0]*v[2], 4)-round(u[2]*v[0], 4), 4)
    theta = math.degrees(math.atan2(cross, dot))
    require(dot != 0 or cross != 0, "replay_degenerate_printed_angle")
    return round(theta)


def argbest(scores, labels, largest=False):
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=largest)
    require(len(order) > 1 and abs(scores[order[0]]-scores[order[1]]) >= 1e-6, "replay_tied_decision")
    return labels[order[0]]


def verify_generated_gt(reference, scene, source, T):
    require(reference.get("method") == "native_annotation_centroid_v1"
            and reference.get("gt") == scene.entry["gt"]
            and reference.get("native_annotations") == scene.entry["native_annotations"], "generated_GT_provenance")
    require(reference.get("source_box_convention") == {key: scene.native_source.get(key) for key in ("box_convention", "provider_axesLengths", "released_boxes", "obb_estimator_used")}, "generated_GT_box_convention")
    centres = []
    plan = bind(question(source), T)
    for obj in (plan["stand"], plan["face"], plan["query"]):
        item = reference["objects"][obj]
        iid, = scene.ids(obj)
        k = next((f for f in scene.anchors if scene.ground.masks(obj, f)), None)
        require(k is not None and item["instance_id"] == iid and item["frame"] == k, "generated_GT_binding")
        native = scene.native[iid]
        require(item["native_label"] == native["label"] and close(item["centroid_world"], native["centroid"].tolist()), "generated_GT_native_centroid")
        c = scene.basis.T @ (native["centroid"]-scene.origin)
        c[1] = -c[1]
        require(close(item["point"], c.tolist()), "generated_GT_centroid")
        centres.append(c)
    S, F, Q = centres
    u, v = F-S, Q-S
    dot, cross = u[0]*v[0]+u[2]*v[2], u[0]*v[2]-u[2]*v[0]
    theta = math.degrees(math.atan2(cross, dot))
    label = label_direction(source["question_type"], theta)
    require(close(reference["theta_degree"], theta) and close(reference["dot_m2"], dot)
            and close(reference["cross_m2"], cross) and reference["label"] == label
            and gt_label(source) == T.letter_of(question(source)["options"], label), "generated_GT_label")


def audit(record, scene, T, config, source, reviewed=None, exact_reference=False):
    if str(record.get("form", "")).startswith("spec-v3.") and record["form"] != "spec-v3.8-calculator-v2":
        raise Refusal("stale_canonical_form_use_frozen_producer")
    if record.get("form") == "spec-v3.8-calculator-v2":
        from .canon_check import audit as canonical_audit
        return canonical_audit(record, scene, T, config, source, reviewed, exact_reference)
    q = question(source)
    require(record.get("schema") == "derivgen-row-v1" and record.get("readout_mode") == "gt"
            and record.get("answer_policy") == "gt_and_faithful_equal", "unsupported_readout_or_answer_policy")
    require(bool(record.get("infrastructure_only")) == bool(scene.entry.get("infrastructure_only"))
            == bool(source.get("infrastructure_only")), "replay_infrastructure_mode")
    require(record["convention"] == CONVENTION, "convention_mismatch")
    require(record["private"]["source_question_sha256"] == digest(q), "question_binding_mismatch")
    require({k: record[k] for k in ("question", "options", "question_type")} == q, "visible_question_mismatch")
    plan = bind(q, T, reviewed)
    scene = copy.copy(scene)
    scene.referent_ids = plan.get("referent_ids", {})
    require(record["private"]["bindings"] == plan, "replay_binding_mismatch")
    require(record["private"]["gt"] == scene.entry["gt"] and record["private"]["frame_indices"] == scene.entry["frame_indices"], "replay_scene_binding")
    if "generated_gt" in record["private"]:
        verify_generated_gt(record["private"]["generated_gt"], scene, source, T)
    audit_printed_calculator(record["events"])
    values, units, calls, poses = {}, {}, {}, {}
    census = Counter()
    private_clicks = {p["camera_node"]: p for p in record["private"]["clicks"]}
    groups = {g["id"]: g for g in record["private"]["groups"]}
    obs, point_by_camera = defaultdict(list), {}
    spread_by_camera, click_events = {}, []
    merges, decision_events, correction_events = [], [], []
    last_click = None
    for e in record["events"]:
        require(e["target_loss"] == int(e["role"] == "assistant"), "tool_target_loss")
        if "frame" in e:
            k = e["frame"]
            require(type(k) is int and 1 <= k <= 32, "visible_frame_range")
        if e["kind"] == "click":
            last_click = e
            click_events.append(e)
        elif e["kind"] == "correction": correction_events.append(e)
        elif e["kind"] in ("calculator_call", "calculator_response"):
            # The independent published-value pass above verified these events.
            # Family decisions still use the existing semantic/source gates.
            continue
        elif e["kind"] == "tool_call":
            require(e["call_id"] not in calls, "duplicate_call_id")
            calls[e["call_id"]] = e
        elif e["kind"] == "tool_response":
            require(e["role"] == "tool" and e["call_id"] in calls, "orphan_tool_response")
            call = calls.pop(e["call_id"])
            name, args = call["name"], call["arguments"]
            require(e["name"] == name, "tool_name_mismatch")
            for node, item in e["values"].items():
                require(node not in values, "duplicate_value_id")
                values[node], units[node] = item["value"], item["unit"]
                require(close(item["value"], item["value"]), "nonfinite_evidence")
                census[item["unit"]] += 1
                expected_units = {"pose": {"R": "1", "t": "m", "level_R": "1", "yaw": "degree"},
                                  "depth_at": {"camera": "m", "f1": "m", "spread": "1"},
                                  "move": {"delta": "m", "distance": "m"}}
                require(name in expected_units and item["unit"] == expected_units[name].get(node.split(".")[-1]), "tool_unit_mismatch")
            get = lambda key: e["values"][e["call_id"]+"."+key]["value"]
            if name != "depth_at":
                require(set(e["values"]) == {e["call_id"]+"."+key for key in expected_units[name]}, "tool_readout_coverage")
            if name == "pose":
                k = args["frame"]
                if not exact_reference: require(k == 1 or k % 2 == 0, "unsupported_pose_frame")
                expected = replay_pose(scene, k)
                for key in expected: require(close(get(key), expected[key]), "replay_pose_value")
                poses[k] = {key: get(key) for key in expected}
            elif name == "depth_at":
                k = args.get("image_frame", args["frame"])
                pts = args.get("pts")
                require(isinstance(pts, list) and 1 <= len(pts) <= 4 and all(isinstance(p, list) and len(p) == 2 for p in pts), "invalid_depth_batch")
                require(last_click is not None and last_click["points"] == pts and last_click["frame"] == k, "depth_without_assistant_click")
                if "image_frame" in args:
                    require(not exact_reference and args["frame"] % 2 == 1 and k == args["frame"]+1
                            and any(x["kind"] == "substitution" and x["requested_frame"] == args["frame"] for x in record["events"]), "invalid_depth_image_frame")
                if not exact_reference: require(k % 2 == 0, "unsupported_depth_frame")
                require(k in poses, "missing_click_pose")
                expected_keys = set()
                for i, uv in enumerate(pts):
                    prefix = "" if len(pts) == 1 else f"{i}."
                    expected_keys.update(e["call_id"]+"."+prefix+key for key in ("camera", "f1", "spread"))
                    node = e["call_id"]+"."+prefix+"camera"
                    field = lambda key: get(prefix+key)
                    require(node in private_clicks, "missing_click_provenance")
                    pc = private_clicks[node]
                    require(pc["uv"] == uv and pc["frame"] == k and pc["object"] == last_click["object"], "click_provenance_mismatch")
                    require(pc["instance_id"] in scene.ids(pc["object"], many=True), "click_referent_binding")
                    camera, spread = verify_depth(scene, pc["instance_id"], k, uv)
                    if not pc["correction_initial"]:
                        from scipy.ndimage import distance_transform_edt
                        dt = distance_transform_edt(scene.gt.inst[k-1] == pc["instance_id"])
                        x, y = scene.gt.px([uv])
                        require(dt[y[0], x[0]] >= 3, "click_not_inward_from_edge")
                    require(close(field("camera"), rounded(camera)) and close(field("spread"), spread), "replay_depth_readout")
                    fixed = replay_pose(scene, k, printed=False)
                    point = rounded([a+b for a, b in zip(mv(fixed["R"], camera), fixed["t"])])
                    require(close(field("f1"), point), "replay_f1_readout")
                    point_by_camera[node], spread_by_camera[node] = point, spread
                    if not pc["correction_initial"]:
                        require(spread <= .25, "unresolved_spread")
                        obs[pc["group"]].append(point)
                    else: require(spread > .25, "stable_point_correction")
                require(set(e["values"]) == expected_keys, "batch_readout_coverage")
                last_click = None
            elif name == "first_seen":
                obj = args["object"]
                frame_clicks = [x for x in click_events if x["object"] == obj]
                require([x["frame"] for x in frame_clicks] == list(range(1, 33)), "incomplete_appearance_scan")
                visible = []
                for click in frame_clicks:
                    k = click["frame"]
                    check_appearance_click(scene, obj, click)
                    if click["points"]: visible.append(k)
                require(bool(visible) and get("first") == min(visible), "first_seen_mismatch")
            elif name == "move":
                delta, distance, raw = replay_move(scene, args["from"], args["to"])
                require(close(get("delta"), delta) and close(get("distance"), distance), "replay_move_value")
                module = getattr(scene, "l1", None)
                if module: require(e.get("p1_v2_text") == module.format_move(raw), "P1_v2_format_mismatch")
            else: raise Refusal("unbacked_tool", name)
        elif e["kind"] == "arithmetic":
            require(e["id"] not in values, "duplicate_value_id")
            args = [values[a] if isinstance(a, str) else a for a in e["args"]]
            expected_places = 0 if e["unit"] in ("degree", "count", "frame") else 4 if e["op"] in ("mul", "sum") or (e["unit"] == "m2" and e["op"] in ("add", "sub", "abs")) else 2
            require(e.get("places") == expected_places, "arithmetic_precision_mismatch")
            result = rounded(scalar_op(e["op"], args), expected_places)
            require(close(e["value"], result), "printed_arithmetic_mismatch", e["id"])
            require(e["unit"] in {"1", "m", "m2", "cm", "mm", "ft", "ft2", "inch", "degree", "count", "frame"}, "unknown_unit")
            if e["op"] in ("norm", "x", "y", "z", "min", "max", "mean", "add", "sub", "matvec", "local"):
                dimensional = [units[a] for a in e["args"] if isinstance(a, str) and units[a] != "1"]
                require(all(u == e["unit"] for u in dimensional), "arithmetic_unit_mismatch")
            operand_units = [units[a] for a in e["args"] if isinstance(a, str)]
            if e["op"] == "mul":
                require(e["unit"] == "m2" and operand_units == ["m", "m"], "product_unit_mismatch")
            elif e["op"] == "sum":
                require(e["unit"] == "m2" and all(u == "m2" for u in operand_units), "sum_unit_mismatch")
            elif e["op"] == "sqrt":
                require(e["unit"] == "m" and operand_units == ["m2"], "root_unit_mismatch")
            elif e["op"] == "mod":
                require(e["unit"] == "degree" and operand_units == ["degree"] and e["args"][1] == 360, "angle_modulo_unit_mismatch")
            elif e["op"] == "atan2":
                require(e["unit"] == "degree" and len(set(operand_units)) == 1 and operand_units[0] in ("m", "m2"), "angle_unit_mismatch")
            values[e["id"]], units[e["id"]] = result, e["unit"]
            census[e["unit"]] += 1
        elif e["kind"] == "merge": merges.append(e)
        elif e["kind"] == "decision": decision_events.append(e)
        elif e["kind"] == "substitution":
            require(config.get("odd_frame_policy") == "next_anchor_exact_gt_equality"
                    and e["requested_frame"] % 2 == 1 and e["effective_frame"] == e["requested_frame"]+1,
                    "invalid_anchor_substitution")
        elif e["kind"] == "frame_choice":
            ids = record["private"]["frame_bindings"][e["selection_id"]]
            require(len(ids) == len(e["objects"]) and all(i in scene.ids(obj, many=True) for obj, i in zip(e["objects"], ids)), "frame_choice_identity")
            visible = [[k for k in scene.anchors if int(np.sum(scene.gt.inst[k-1] == iid)) >= scene.programs.MIN_PX] for iid in ids]
            common = sorted(set.intersection(*map(set, visible)))
            if common:
                require(e["selected"] == [common[0]]*len(visible) and not e["candidates"], "common_frame_preference")
            else:
                require(len(visible) == 2, "invalid_frame_pair_choice")
                pairs = [(i, j) for i in visible[0] for j in visible[1]]
                require([tuple(c["frames"]) for c in e["candidates"]] == pairs, "frame_pair_census")
                scores = []
                for c in e["candidates"]:
                    i, j = c["frames"]
                    pi, pj = poses[i], poses[j]
                    delta = rounded(sub(pj["t"], pi["t"]))
                    distance = replay_move(scene, i, j)[1]
                    f = rounded(mv(trans(pi["level_R"]), rounded(mv(pj["level_R"], [0, 0, 1]))))
                    yaw = round(math.degrees(math.atan2(-f[0], f[2])))
                    score = rounded(distance+abs(yaw)/50)
                    require(close(values[c["distance"]], distance) and close(values[c["yaw"]], yaw)
                            and close(values[c["score"]], score), "frame_pair_rank_arithmetic")
                    scores.append((score, abs(i-j), i, j))
                best = min(scores)
                require(e["selected"] == list(best[2:]), "minimum_pose_frame_pair")
        elif e["kind"] not in ("convention", "plan"): raise Refusal("unknown_event_kind")
    require(not calls and set(private_clicks) == set(point_by_camera), "tool_or_click_accounting")
    branch = record["plan_branch"]
    require(branch["family"] == q["question_type"] and branch["argon_bank_integrated"] is False
            and branch["frames"] == sorted({e["frame"] for e in click_events})
            and branch["frame_choices"] == [e for e in record["events"] if e["kind"] == "frame_choice"]
            and branch["comparison"] == plan.get("comparison")
            and branch["decisions"] == decision_events
            and branch["corrections"] == len(correction_events), "plan_branch_event_mismatch")
    require(branch["referents"] == {k: plan[k] for k in ("cat", "a", "b", "target", "cands", "stand", "face", "query", "cats", "obj", "ref", "start", "goal") if k in plan}
            and branch["measurement_groups"] == [{k: g[k] for k in ("object", "frame", "purpose")} for g in record["private"]["groups"]]
            and branch["counting"] == [{"category": e["category"], "cluster": e["cluster"], "frame": e["frame"]} for e in merges]
            and branch["route_blanks"] == [i for i, (kind, _) in enumerate(plan.get("plan", [])) if kind == "turn"]
            and branch["substitutions"] == [{k: e[k] for k in ("requested_frame", "effective_frame")} for e in record["events"] if e["kind"] == "substitution"], "plan_branch_binding_mismatch")
    require(branch["requested_frames"] == {key: plan[key] for key in ("i", "j", "k") if key in plan}
            and branch["pose_frames"] == sorted({e["arguments"]["frame"] for e in record["events"] if e["kind"] == "tool_call" and e["name"] == "pose"}), "plan_branch_camera_frames_mismatch")
    require(branch["frame_strategy"] == ("cross_frame" if any(len(set(e["selected"])) > 1 for e in branch["frame_choices"]) else "common_or_single_frame"), "plan_branch_strategy_mismatch")
    purposes = {g["purpose"] for g in record["private"]["groups"]}
    require(branch["measurement_strategy"] == ("candidate_facing_pairs_minimum" if "facing" in purposes else "extreme_point_extent" if "extent" in purposes else "middle_points_or_rgb"), "plan_branch_measurement_mismatch")
    require(record["events"][0]["kind"] == "plan" and record["events"][0]["text"].startswith("PLAN:"), "plan_first")
    for node, pc in private_clicks.items():
        if pc["correction_initial"]:
            events = [e for e in correction_events if e["spread_node"] == pc["spread_node"]]
            require(len(events) == 1, "missing_correction_signal")
            e, = events
            require(values[e["spread_node"]] > .25 and e["initial"] == pc["uv"], "incorrect_correction_trigger")
            delta = sub(e["toward"], e["initial"])
            require(norm(delta) >= 30, "invalid_inward_direction")
            expected = [round(x+30*d/norm(delta)) for x, d in zip(e["initial"], delta)]
            require(expected == e["next"], "incorrect_correction_step")
            later = [p for p in private_clicks.values() if p["group"] == pc["group"] and not p["correction_initial"]]
            require(any(p["uv"] == e["next"] for p in later), "correction_missing_readout")
            from scipy.ndimage import distance_transform_edt
            dt = distance_transform_edt(scene.gt.inst[pc["frame"]-1] == pc["instance_id"])
            x, y = scene.gt.px([pc["uv"], e["next"]])
            require(dt[y[0], x[0]] <= 2 and dt[y[1], x[1]] > dt[y[0], x[0]], "correction_not_inward_from_edge")
    require(len(correction_events) == sum(p["correction_initial"] for p in private_clicks.values()), "correction_accounting")
    for gid, g in groups.items():
        require(2 <= len(obs[gid]) <= 4, "grounded_click_count")
        require(all(p["object"] == g["object"] and p["instance_id"] == g["instance_id"] and p["frame"] == g["frame"]
                    for p in private_clicks.values() if p["group"] == gid), "group_provenance_mismatch")

    def points(obj, purpose="middle", toward=None):
        allowed = scene.ids(toward, many=True) if toward else None
        found = [p for gid, g in groups.items() if g["object"] == obj and g["purpose"] == purpose
                 and (allowed is None or g["toward_id"] in allowed) for p in obs[gid]]
        require(bool(found), "missing_semantic_points", obj)
        return found

    def centre(obj): return rounded(mean(points(obj)))
    def closest(A, B): return min(rounded(dist(a, b)) for a in A for b in B)
    def effective(k, depth=False):
        return k if exact_reference or k % 2 == 0 or (k == 1 and not depth) else k+1

    t = q["question_type"]
    def counted(cat, run=0):
        clusters = []
        for e in [e for e in merges if e["category"] == cat and e["count_run"] == run]:
            k = e["frame"]
            candidate = []
            require(len(e["checks"]) == len(clusters), "merge_check_coverage")
            for i, c in enumerate(clusters):
                d = rounded(dist(values[e["detection"]], c["centre"]))
                threshold = max(.35, round(min(values[e["extent"]], c["extent"])*.5, 2))
                check = e["checks"][i]
                require(close(values[check["distance"]], d) and close(values[check["threshold"]], threshold), "merge_arithmetic")
                if d < threshold and k not in c["frames"]: candidate.append(i)
            require(len(candidate) <= 1, "ambiguous_instance_merge")
            j = candidate[0] if candidate else len(clusters)
            require(e["cluster"] == j+1, "merge_assignment")
            if not candidate: clusters.append({"points": [], "frames": set(), "extent": values[e["extent"]]})
            clusters[j]["points"].append(values[e["detection"]])
            clusters[j]["frames"].add(k)
            clusters[j]["centre"] = rounded(mean(clusters[j]["points"]))
        count = len(clusters)
        require(count == len(scene.ids(cat, many=True)), "count_identity_disagreement")
        return count

    if t in ("object_counting", "absolute_count"): result = counted(plan["cat"])
    elif t == "relative_count":
        a, b = counted(plan["a"], 0), counted(plan["b"], 1)
        result = "more" if a > b else "fewer" if a < b else "equal number"
    elif t == "relative_size_object":
        sizes = []
        for obj in (plan["a"], plan["b"]):
            P = points(obj, "extent")
            sizes.append(max(dist(a, b) for a in P for b in P))
        result = argbest(sizes, [plan["a"], plan["b"]], largest=plan["comparison"] == "longer")
    elif t in ("object_abs_distance", "absolute_distance_object"): result = closest(points(plan["a"], "facing", plan["b"]), points(plan["b"], "facing", plan["a"]))
    elif t in ("object_size_estimation", "absolute_size_object"):
        P = points(plan["a"], "extent"); result = max(rounded(dist(a, b)) for a in P for b in P)
    elif t == "room_size_estimation":
        P = [point_by_camera[p["camera_node"]] for p in private_clicks.values() if not p["correction_initial"]]
        require(len(P) == len(plan["floor_corners"]), "floor_click_coverage")
        result = rounded(scalar_op("shoelace", P))
    elif t in ("object_rel_distance", "relative_distance_object"):
        scores = [closest(points(plan["target"], "facing", obj), points(obj, "facing", plan["target"])) for obj in plan["cands"]]
        result = argbest(scores, plan["cands"])
    elif t.startswith("object_rel_direction") or t in ("relative_direction_object", "absolute_direction_object"):
        S, F, Q = [centre(plan[k]) for k in ("stand", "face", "query")]
        theta = angle(rounded(sub(F, S)), rounded(sub(Q, S)))
        if t == "absolute_direction_object": result = theta % 360
        elif t == "relative_direction_object":
            u, v = rounded(sub(F, S)), rounded(sub(Q, S))
            cross = round(round(u[0]*v[2], 4)-round(u[2]*v[0], 4), 4)
            require(cross != 0, "direction_tie")
            result = "left" if cross > 0 else "right"
        else:
            require(abs(theta) not in (0, 90, 135, 180), "rounding_boundary")
            result = label_direction(t, theta)
    elif t == "route_planning":
        here, face = centre(plan["start"]), centre(plan["face"])
        heading, turns = rounded(sub(face, here)), []
        for i, (kind, obj) in enumerate(plan["plan"]):
            if kind == "go":
                nxt = centre(obj); heading, here = rounded(sub(nxt, here)), nxt
            else:
                obj = next((o for kind, o in plan["plan"][i+1:] if kind == "go"), None)
                require(obj is not None, "underspecified_route")
                direction = rounded(sub(centre(obj), here)); theta = angle(heading, direction)
                require(abs(theta) not in (0, 90, 135, 180), "rounding_boundary")
                turns.append("Turn Back" if abs(theta) >= 135 else "Turn Left" if theta > 0 else "Turn Right")
                heading = direction
        result = ", ".join(turns)
    elif t == "obj_appearance_order":
        for obj in plan["cats"]:
            frames = [e for e in click_events if e["object"] == obj]
            require([e["frame"] for e in frames] == list(range(1, 33)), "incomplete_appearance_scan")
            for e in frames:
                k = e["frame"]
                check_appearance_click(scene, obj, e)
        firsts = {obj: next((k for k in range(1, 33) if appearance_ids(scene, obj, k)), None) for obj in plan["cats"]}
        require(None not in firsts.values() and len(set(firsts.values())) == len(firsts), "appearance_tie")
        result = ", ".join(sorted(firsts, key=firsts.get))
    elif t in ("camera_displacement", "camera_movement_direction", "camera_rotation"):
        pi, pj = [poses[effective(plan[k])] for k in ("i", "j")]
        local = rounded(mv(trans(pi["level_R"]), rounded(sub(pj["t"], pi["t"]))))
        local, distance, _ = replay_move(scene, effective(plan["i"]), effective(plan["j"]))
        if t == "camera_displacement": result = distance
        elif t == "camera_rotation":
            forward = rounded(mv(pj["level_R"], [0, 0, 1]))
            result = angle([0, 0, 1], rounded(mv(trans(pi["level_R"]), forward)))
        else:
            scores = {"forward": local[2], "backward": -local[2], "right": local[0], "left": -local[0]}
            labels = [s.strip().lower() for s in T.option_texts(q["options"]).values()]
            result = argbest([scores[s] for s in labels], labels, largest=True)
    else:
        k = effective(plan["k"], depth=True); pose = poses[k]; cam = pose["t"]
        if t == "camera_obj_abs_dist": result = min(rounded(dist(p, cam)) for p in points(plan["obj"], "facing"))
        elif t.startswith("camera_obj_rel_dist"):
            result = argbest([min(rounded(dist(p, cam)) for p in points(obj, "facing")) for obj in plan["cands"]], plan["cands"])
        else:
            a, b = centre(plan["a"]), centre(plan["ref"])
            if t.endswith("_nf"): scores, labels = [rounded(dist(p, cam)) for p in (a, b)], ["near", "far"]
            else:
                basis = pose["level_R"] if t.endswith("_ud") else pose["R"]
                axis = 1 if t.endswith("_ud") else 0
                scores = [rounded(mv(trans(basis), rounded(sub(p, cam))))[axis] for p in (a, b)]
                labels = ["up", "down"] if axis else ["left", "right"]
            result = argbest(scores, labels)
    if t in F17:
        native = native_reference(scene, T, q, plan)
        require(record["private"].get("native_reference") == native, "native_reference_provenance")
        if t in NUMERIC:
            policy = unit_policy(q, config, reviewed)
            require(quantize(gt_label(source), policy["decimals"]) == quantize(native["value"], policy["decimals"]), "native_source_label_mismatch")
        else:
            require(T.letter_of(q["options"], native["value"]) == gt_label(source), "native_source_label_mismatch")
    require(len(decision_events) == 1, "decision_count")
    claimed = decision_events[0]
    if t in NUMERIC:
        policy = unit_policy(q, config, reviewed)
        require(record["display"] == claimed.get("display") == policy, "numeric_display_policy_mismatch")
        result = rounded(result*policy["factor"], 0 if policy["unit"] in ("degree", "count") else 2)
        require(close(claimed["result"], result), "semantic_numeric_disagreement")
        expected = quantize(result, policy["decimals"])
        require(quantize(record["answer"], policy["decimals"]) == expected, "replay_answer_mismatch")
        require(quantize(gt_label(source), policy["decimals"]) == expected, "source_label_mismatch")
    else:
        require(claimed["result"] == result, "semantic_categorical_disagreement")
        labels = T.option_texts(q["options"])
        normtext = lambda x: " ".join(x.lower().rstrip(".").split())
        expected = [k for k, v in labels.items() if normtext(v) == normtext(result)]
        require(len(expected) == 1 and record["answer"] == expected[0], "replay_answer_mismatch")
        require(gt_label(source) == expected[0], "source_label_mismatch")
    require(record["target"].endswith("</think>\n\n"+str(record["answer"])), "target_answer_mismatch")
    # This checks serialization only. Arithmetic and the answer have already been
    # independently recomputed above, without calling the builder's formatter.
    from .trace import loss_spans, remap_tool_spans, render
    original = record.get("original_target", record["target"])
    projection = render(record["events"], record["answer"], include_spans=True)
    require(original == projection["target"], "readable_projection_mismatch")
    if "original_target" in record:
        from .review import rewrite_gate
        selected = rewrite_gate(original, record["target"], record["private"]["style_evidence"])
        require(selected == record["target"], "rewrite_not_preferred")
        expected_outputs = remap_tool_spans(original, record["target"], projection["tool_output_spans"])
    else: expected_outputs = projection["tool_output_spans"]
    require(record["tool_output_spans"] == expected_outputs and record["loss_spans"] == loss_spans(record["target"], expected_outputs), "printed_output_span_mismatch")
    substitutions = [e for e in record["events"] if e["kind"] == "substitution"]
    require(exact_reference or bool(substitutions) == ("exact_reference" in record["private"]), "missing_exact_frame_reference")
    if "exact_reference" in record["private"]:
        exact = record["private"]["exact_reference"]
        audit(exact, scene, T, config, source, reviewed, exact_reference=True)
        require(exact["answer"] == record["answer"], "odd_reference_disagreement")
    return dict(census)


def native_reference(scene, T, q, plan):
    """Private independent label check; never a public head value or operand."""
    t = q["question_type"]
    def ids(obj, many=False): return scene.ids(obj, many=many)
    def boxes(obj, many=False):
        return [{"centroid": scene.native[i]["centroid"], "axesLengths": scene.native[i]["lengths"],
                 "normalizedAxes": scene.native[i]["axes"]} for i in ids(obj, many)]
    def size(obj): return float(max(scene.native[ids(obj)[0]]["lengths"]))
    def closest(a, b): return T.obb_closest(boxes(a, True), boxes(b, True))
    if t in ("object_counting", "absolute_count"): value = len(ids(plan["cat"], True))
    elif t == "relative_count":
        a, b = len(ids(plan["a"], True)), len(ids(plan["b"], True))
        value = "more" if a > b else "fewer" if a < b else "equal number"
    elif t == "absolute_size_object": value = size(plan["a"])
    elif t == "relative_size_object":
        value = argbest([size(plan["a"]), size(plan["b"])], [plan["a"], plan["b"]], largest=plan["comparison"] == "longer")
    elif t == "absolute_distance_object": value = closest(plan["a"], plan["b"])
    elif t == "relative_distance_object":
        value = argbest([closest(plan["target"], obj) for obj in plan["cands"]], plan["cands"])
    else:
        centres = []
        for key in ("stand", "face", "query"):
            c = scene.basis.T @ (scene.native[ids(plan[key])[0]]["centroid"]-scene.origin)
            centres.append([float(c[0]), float(-c[1]), float(c[2])])
        S, F, Q = centres
        u, v = sub(F, S), sub(Q, S)
        require(norm([u[0], u[2]]) > 1e-6 and norm([v[0], v[2]]) > 1e-6, "native_degenerate_heading")
        theta = math.degrees(math.atan2(u[0]*v[2]-u[2]*v[0], u[0]*v[0]+u[2]*v[2]))
        value = round(theta) % 360 if t == "absolute_direction_object" else label_direction(t, theta)
    return {"method": "independent_native_annotation_v1", "value": value,
            "native_annotations": scene.entry["native_annotations"]}
