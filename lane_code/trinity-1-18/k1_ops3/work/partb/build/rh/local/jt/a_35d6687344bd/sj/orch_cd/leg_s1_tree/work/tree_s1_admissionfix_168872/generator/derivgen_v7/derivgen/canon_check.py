"""Independent checks of a canonical (SPEC v3.8 calculator) row.

The checker reads the rendered target text, never the generator's numbers: it re-reads every
head readout against native GT, recomputes every calculator response from the printed point
values, verifies every arithmetic sentence, re-derives the decision from printed values only,
and gates the answer against the source label.
"""
import copy
import math
import re
from collections import Counter

import numpy as np
from scipy.ndimage import distance_transform_edt

from decimal import Decimal, localcontext, ROUND_HALF_EVEN

FORM = "spec-v3.8-calculator-v2"
def f2(x): return f"{round(float(x), 2) + 0.0:.2f}"
def wrap(x):
    value = (x + 180) % 360 - 180
    return 180 if value == -180 else value
from .common import Refusal, digest
from .bindings import (F17, UNITS, bind, gt_label, question, unit_policy, is_generic_label,
                       object_labels, label_typo_fixes, normalized_reviewed)
from .plan_contract import opening_text, enrich_opening, noun, plural, frame_look, join
from .replay import (native_reference, quantize, replay_move, replay_pose, replay_camera_turn, verify_depth,
                     audit_printed_calculator, verify_generated_gt, appearance_ids)

CALL = re.compile(r"<(depth_at|move|pose|dist|closest|cam_dist|angle|turn|area)((?: [^<>]*)?)><tool_response>(.*?)</tool_response>", re.S)
NUM = r"-?\d+\.\d\d"
POINT = re.compile(rf"(P\d+): cam(\d+) \(({NUM}), ({NUM}), ({NUM})\) m; f1 \(({NUM}), ({NUM}), ({NUM})\) m; spread (\d+\.\d\d)")
MOVE = re.compile(rf"dx = ([+-]\d+\.\d\d) m, dy = ([+-]\d+\.\d\d) m, dz = ([+-]\d+\.\d\d) m, distance = (\d+\.\d\d) m")
POSE = re.compile(rf"f1 centre \(({NUM}), ({NUM}), ({NUM})\) m, yaw (-?\d+) deg")
FULL_MIN_SLACK = 0.02


def require(ok, reason, detail=""):
    if not ok: raise Refusal(reason, detail)


def depth_limit(uv):
    require(len(uv) == 2 and all(type(x) is int and 20 <= x <= 980 for x in uv), "depth_click_border")
    return .10 if min(uv[0], uv[1], 1000-uv[0], 1000-uv[1]) <= 40 else .25


def args_of(name, raw):
    raw = raw.strip()
    if name == "depth_at":
        m = re.fullmatch(r"frame=(\d+)(?: image_frame=(\d+))? pts=(\[\[.*\]\])", raw)
        require(m is not None, "routing_syntax", raw)
        import json
        try: pts = json.loads(m.group(3))
        except ValueError: raise Refusal("routing_syntax")
        require(isinstance(pts, list) and 1 <= len(pts) <= 4 and all(isinstance(p, list) and len(p) == 2
                and all(type(x) is int and 0 <= x <= 1000 for x in p) for p in pts), "routing_syntax")
        require(json.dumps(pts, separators=(",", ":")) == m.group(3), "routing_syntax")
        return {"frame": int(m.group(1)), "image_frame": int(m.group(2)) if m.group(2) else None, "pts": pts}
    if name == "move" or name == "turn" and re.fullmatch(r"from=\d+ to=\d+", raw):
        m = re.fullmatch(r"from=(\d+) to=(\d+)", raw); require(m is not None, "routing_syntax", raw)
        return {"from": int(m.group(1)), "to": int(m.group(2))}
    if name == "pose":
        m = re.fullmatch(r"frame=(\d+)", raw); require(m is not None, "routing_syntax", raw)
        return {"frame": int(m.group(1))}
    if name == "dist":
        m = re.fullmatch(r"(P\d+) (P\d+)", raw); require(m is not None, "routing_syntax", raw)
        return {"pts": [m.group(1), m.group(2)]}
    if name == "cam_dist":
        require(re.fullmatch(r"P\d+(?:,P\d+)*", raw) is not None, "routing_syntax", raw)
        return {"pts": raw.split(",")}
    if name == "closest":
        m = re.fullmatch(r"A=(P\d+(?:,P\d+)*) B=(P\d+(?:,P\d+)*)", raw); require(m is not None, "routing_syntax", raw)
        return {"A": m.group(1).split(","), "B": m.group(2).split(",")}
    if name == "angle":
        m = re.fullmatch(r"S=(P\d+) F=(P\d+) Q=(P\d+) rule=(easy|medium|hard|turn)", raw); require(m is not None, "routing_syntax", raw)
        return {"S": m.group(1), "F": m.group(2), "Q": m.group(3), "rule": m.group(4)}
    if name == "turn":
        m = re.fullmatch(r"from=(P\d+) at=(P\d+) to=(P\d+)", raw); require(m is not None, "routing_syntax", raw)
        return {"from": m.group(1), "at": m.group(2), "to": m.group(3)}
    if name == "area":
        m = re.fullmatch(r"C=(P\d+(?:,P\d+)+)", raw); require(m is not None, "routing_syntax", raw)
        return {"C": m.group(1).split(",")}
    raise Refusal("unknown_tool", name)


DISTANCE_FAMILIES = {"object_abs_distance", "absolute_distance_object", "camera_obj_abs_dist"}


def numeric_ok(pred, gt, family, decimals):
    p, g = Decimal(str(pred)), Decimal(str(gt))
    require(p.is_finite() and g.is_finite(), "nonfinite_numeric_label")
    if family in DISTANCE_FAMILIES:
        return abs(p-g) <= Decimal("0.05")*abs(g)
    return quantize(p, decimals) == quantize(g, decimals)


def audit(record, scene, T, config, source, reviewed=None, exact_reference=False):
    reviewed = normalized_reviewed(source, reviewed)
    require(record.get("form") == FORM, "canonical_form")
    from .calculator import SPEC_SHA256
    require(config["spec"]["sha256"] == SPEC_SHA256, "canonical_spec_pin_mismatch")
    require(config.get("trace_form", "canonical_v38") == "canonical_v38", "canonical_configuration_epoch")
    require(record.get("schema") == "derivgen-row-v2" and record.get("readout_mode") == "gt"
            and record.get("answer_policy") == "trace_value", "unsupported_readout_or_answer_policy")
    require(bool(record.get("infrastructure_only")) == bool(scene.entry.get("infrastructure_only"))
            == bool(source.get("infrastructure_only")), "replay_infrastructure_mode")
    require(scene.entry.get("infrastructure_only") or bool(config.get("phrase_bank")), "missing_pinned_phrase_bank")
    require(record["qid"] == source["qid"], "source_qid_binding")
    q = question(source)
    require(record.get('label_typo_fixed', {}) == label_typo_fixes(source), 'label_typo_metadata')
    if label_typo_fixes(source):
        original = question(source, fix_typos=False)
        require(record.get('label_typo_original') == {"question": original["question"],
                "options": original["options"]}, 'label_typo_original_metadata')
    else:
        require('label_typo_original' not in record, 'label_typo_original_metadata')
    require(q["question_type"] not in ("room_size_estimation", "object_size_estimation", "absolute_size_object", "relative_size_object") or (
        scene.entry.get("infrastructure_only") and source.get("infrastructure_only") and config.get("infrastructure_only")),
        "p3_v1_direct_answer_required")
    plan = bind(q, T, reviewed)
    require(digest(record["private"]["bindings"]) == digest(plan), "replay_binding_mismatch")
    scene = copy.copy(scene)
    scene.referent_ids = plan.get("referent_ids", {})
    objects = object_labels(plan)
    for obj in objects:
        names = [obj] + [scene.native[i]["label"] for i in scene.ids(obj, many=True)]
        require(all(not is_generic_label(name) for name in names), "generic_label")
        for name in names:
            parts = set(re.findall(r"\b(ceiling|floor|wall)s?$", name.strip().lower()))
            asked = set(re.findall(r"\b(ceiling|floor|wall)s?\b", q["question"].lower()))
            require(parts <= asked, "structural_part_not_asked")
    require(all(label in q["question"] for label in object_labels(plan)), "binding_referent_not_in_question")
    require(record.get("trace_revision") == "3.11", "trace_revision")
    require(record.get("frame_pair_rule") == "frame_gap", "frame_pair_rule")
    require(record.get("frame_pair_turn") == [], "frame_pair_turn_metadata")
    require(record.get("image_size") == [scene.gt.W, scene.gt.H], "image_size")
    layout = config.get("head_layout", "paired_anchor")
    require(layout in ("paired_anchor", "per_frame") and record.get("head_layout") == layout, "head_layout")
    scene.head_layout = layout
    scene.anchors = [k for k in range(1 if layout == "per_frame" else 2,33,1 if layout == "per_frame" else 2) if scene.gt.has(k)]
    scene.allow_exact_reference = exact_reference
    require(record["private"]["gt"] == scene.entry["gt"] and record["private"]["frame_indices"] == scene.entry["frame_indices"], "replay_scene_binding")
    require(record["display"] == unit_policy(q, config, reviewed), "numeric_display_policy_mismatch")
    if "generated_gt" in record["private"]:
        evidence = record["private"]["generated_gt"]
        if evidence.get("method") == "native_source_reference_v1":
            from .canon_native import verify
            verify(evidence, scene, T, source, plan, record["display"])
        else:
            verify_generated_gt(evidence, scene, source, T)
    if source.get("generated_gt") is not None:
        require(record["private"].get("generated_gt") == source["generated_gt"], "generated_GT_provenance")
    require([i for i, e in enumerate(record["events"]) if e["kind"] == "plan"] == [0],
            "opening_plan_position")
    require(record["events"][0]["role"] == "assistant" and record["events"][0].get("format") == FORM,
            "opening_plan_metadata")
    for event in record["events"]:
        require(event["role"] in ("assistant", "tool") and event["target_loss"] == int(event["role"] == "assistant"), "tool_target_loss")
        if event['kind'] in ('tool_call', 'calculator_call'):
            reason = 'route_extra_claim' if q['question_type']=='route_planning' else 'call_prefix_extra_claim'
            require(event.get('prefix', '') in ('', ' '), reason)
        if event['kind'] in ('canonical_text', 'correction'):
            require('\n\n' not in event['text'], 'text_paragraph_boundary')
    published = audit_printed_calculator(record["events"])
    from .canon_render import render
    from .trace import loss_spans, remap_tool_spans
    projection = render(record["events"], record["answer"])
    original = record.get("original_target", record["target"])
    require(original == projection["target"], "readable_projection_mismatch")
    if "original_target" in record:
        from .review import rewrite_gate
        require(rewrite_gate(original, record["target"], record["private"]["style_evidence"]) == record["target"], "rewrite_not_preferred")
        expected_spans = remap_tool_spans(original, record["target"], projection["tool_output_spans"])
    else: expected_spans = projection["tool_output_spans"]
    require(record["tool_output_spans"] == expected_spans and record["loss_spans"] == loss_spans(record["target"], expected_spans), "printed_output_span_mismatch")
    require(record["private"]["source_question_sha256"] == digest(q), "question_binding_mismatch")
    require({k: record[k] for k in ("question", "options", "question_type")} == q, "visible_question_mismatch")
    text = record["target"]
    require(text.startswith("<think>\n") and text.count("\n</think>\n\n") == 1, "think_structure")
    body, answer = text[len("<think>\n"):].split("\n</think>\n\n")
    require(answer == str(record["answer"]), "target_answer_mismatch")
    paras = body.split("\n\n")
    require(len(paras) >= 3 and "<" not in paras[0], "plan_first")
    require(not re.search(r"\btimestamps?\b|\d+(?:\.\d+)? ?(?:s|sec|secs|seconds?)\b", body, re.I), "seconds_in_trace")
    for k in re.findall(r"\bframes? (\d+)(?![\d.])", body): require(1 <= int(k) <= 32, "visible_frame_range")
    spans = record["tool_output_spans"]
    found = [m for m in CALL.finditer(text)]
    require(text.count("<tool_response>") == text.count("</tool_response>") == len(found), "unpaired_tool_response")
    require(len(found) == len(spans) and all(text[s["start"]:s["end"]] == "<tool_response>" + m.group(3) + "</tool_response>"
                                             for s, m in zip(spans, found)), "tool_span_mismatch")
    clicks = {c["label"]: c for c in record["private"]["clicks"] if "label" in c}
    correction_replacements = {
        e["corrected_label"] for e in record["events"] if e["kind"] == "correction"}
    P, printed, calls = {}, set(), []
    calculator_calls = iter([e for e in record["events"] if e["kind"] == "calculator_call"])
    head_calls = iter([e for e in record["events"] if e["kind"] == "tool_call"])
    all_clicks = [c for c in record["private"]["clicks"] if "label" in c]
    require(len(clicks) == len(all_clicks), "duplicate_click_label")
    substitutions = {}
    n = 0
    for m in found:
        name, args, resp = m.group(1), args_of(m.group(1), m.group(2)), m.group(3)
        printed |= {x.lstrip("+") for x in re.findall(r"[+-]?\d+\.\d+", resp)}
        if name == "depth_at":
            k = args["image_frame"] or args["frame"]
            if args["image_frame"]:
                require(args["frame"] % 2 == 1 and args["image_frame"] == args["frame"] + 1, "invalid_depth_image_frame")
            require(exact_reference or layout == "per_frame" or k % 2 == 0, "unsupported_depth_frame")
            if args["image_frame"]: substitutions[args["frame"]] = k
            event = next(head_calls)
            actual_args = {key: value for key, value in args.items() if value is not None}
            require(event["name"] == name and event["arguments"] == actual_args and event["token"] == m.group(0).split("<tool_response>")[0], "head_call_binding")
            lines = resp.split("\n")
            require(1 <= len(args["pts"]) <= 4 and len(lines) == len(args["pts"]), "depth_batch")
            pose = replay_pose(scene, k, printed=False)
            for uv, line in zip(args["pts"], lines):
                pm = POINT.fullmatch(line)
                require(pm is not None, "depth_line_syntax", line)
                n += 1
                label = pm.group(1)
                require(label == f"P{n}" and int(pm.group(2)) == k, "point_label_sequence")
                c = clicks.get(label)
                require(c is not None and c["frame"] == k and c["uv"] == uv, "click_provenance")
                require(c["instance_id"] in scene.ids(c["object"], many=True), "click_referent_binding")
                camera, spread = verify_depth(scene, c["instance_id"], k, uv)
                cam = [float(pm.group(i)) for i in (3, 4, 5)]
                f1 = [float(pm.group(i)) for i in (6, 7, 8)]
                require(cam == [f2v(camera[0]), f2v(-camera[1]), f2v(camera[2])] and float(pm.group(9)) == f2v(spread), "replay_depth_readout")
                point = [sum(a * b for a, b in zip(row, camera)) + t for row, t in zip(pose["R"], pose["t"])]
                require(f1 == [f2v(x) for x in point], "replay_f1_readout")
                x, y = scene.gt.px([uv])
                dt = distance_transform_edt(scene.gt.inst[k - 1] == c["instance_id"])
                initial = c.get("correction_initial", False)
                limit = depth_limit(uv)
                require((spread > limit) if initial else (dt[y[0], x[0]] >= 3 and spread <= limit), "click_not_inside_eroded_mask")
                require(event.get("object") == c["object"], "click_object_event")
                P[label] = {"cam": cam, "f1": f1, "frame": k, "object": c["object"], "iid": c["instance_id"],
                            "uv": uv, "spread": float(pm.group(9)), "initial": initial}
                require(published["points"][label]["line"] == line, "point_line_format")
        elif name == "move":
            event = next(head_calls)
            require(event["name"] == name and event["arguments"] == args, "head_call_binding")
            require(exact_reference or layout == "per_frame" or all(k == 1 or k % 2 == 0 for k in args.values()), "unsupported_pose_frame")
            delta, dist, _ = replay_move(scene, args["from"], args["to"])
            delta[1] *= -1
            mm = MOVE.fullmatch(resp)
            require(mm is not None and [float(mm.group(i)) for i in (1, 2, 3)] == [f2v(x) for x in delta]
                    and float(mm.group(4)) == f2v(dist), "replay_move_value")
        elif name == "turn" and "at" not in args:
            event = next(head_calls)
            require(event["name"] == name and event["arguments"] == args, "head_call_binding")
            require(all(type(k) is int and 1 <= k <= 32 for k in args.values()), "frame_out_of_range")
            require(exact_reference or layout == "per_frame" or all(k == 1 or k % 2 == 0 for k in args.values()), "unsupported_pose_frame")
            turn = replay_camera_turn(scene,args["from"],args["to"])
            require(resp == f"turn = {turn:+d} deg", "replay_turn_value")
        elif name == "pose":
            event = next(head_calls)
            require(event["name"] == name and event["arguments"] == args, "head_call_binding")
            require(exact_reference or layout == "per_frame" or args["frame"] == 1 or args["frame"] % 2 == 0, "unsupported_pose_frame")
            pz = replay_pose(scene, args["frame"])
            pm = POSE.fullmatch(resp)
            require(pm is not None and [float(pm.group(i)) for i in (1, 2, 3)] == [f2v(x) for x in pz["t"]]
                    and int(pm.group(4)) == pz["yaw"], "replay_pose_value")
        else:
            event = next(calculator_calls)
            command = m.group(0).split("<tool_response>")[0]
            require(command == event["command"], "calculator_command_spelling")
            out = published["calculator_results"][event["call_id"]]
            if name == "closest":
                require(re.fullmatch(r"min P[1-9][0-9]*-P[1-9][0-9]* \d+\.\d{2} m", resp) is not None,
                        "closest_response_syntax")
            require(out["text"] == resp, "calculator_response_mismatch", name)
            r = out["result"]
            if name == "closest": value = (r["witness"]["a"], r["witness"]["b"], r["value"])
            elif name == "cam_dist": value = (r["witness"]["point"], r["value"], {x["point"]: x["value"] for x in r["points"]})
            elif name in ("angle", "turn"): value = (r["u"], r["v"], r["dot"], r["cross"], r["theta"], r["label"])
            else: value = r["value"]
            refs = [l for key, val in args.items() if key != "rule" for l in (val if isinstance(val, list) else [val])]
            require(all(not P[l]["initial"] for l in refs), "unreliable_point_in_calculation")

            calls.append((name, args, value))
        if name in ("move", "pose") or name == "turn" and "at" not in args: calls.append(("camera_turn" if name == "turn" else name, args, resp))
    prose = CALL.sub(" ", text)
    for a, b, raw, wrapped in re.findall(r"turn = (-?\d+) - \(?(-?\d+)\)? = (-?\d+) deg(?:, which wraps to (-?\d+) deg)?", prose):
        require(int(a) - int(b) == int(raw) and (wrapped == "" and wrap(int(raw)) == int(raw) or wrapped != "" and wrap(int(raw)) == int(wrapped)),
                "text_arithmetic", "turn")
    for line in re.findall(rf"= ({NUM}) \+ (\d+)/50 = ({NUM}) \+ ({NUM}) = ({NUM})", prose):
        d, t, d2, e, r = line
        require(d == d2 and f2(int(t) / 50) == e and f2(float(d) + float(e)) == r, "text_arithmetic", "pair rank")
        printed |= {e, r}
    for line in re.findall(rf"threshold = max\(0\.35, min\(({NUM}), ({NUM})\) / 2\) = ({NUM}) m", prose):
        require(f2(max(.35, round(min(float(line[0]), float(line[1])) / 2, 2))) == line[2], "text_arithmetic", "threshold")
        printed.add(line[2])
    for line in re.findall(r"ccw = (-?\d+) mod 360 = (\d+) deg", prose):
        require(int(line[0]) % 360 == int(line[1]), "text_arithmetic", "mod")
    require(set(P) == set(clicks) == set(record["points"]), "point_coverage")
    for label, point in P.items():
        require(record["points"][label] == {key: point[key] for key in ("object", "frame", "uv", "cam", "f1", "spread")}, "published_point_mismatch")
    verify_controls(record, scene, calls, P, plan, exact_reference)
    result = derive(record, scene, T, q, calls, P, prose, exact_reference)
    check_opening(record, q["question_type"], plan, calls, P, paras[0], config)
    if not record["display"]:
        check_conversion(record)
    else:
        # derive has independently checked the conversion before its result can
        # enter the prose number census.
        printed.add(result)
    if q['question_type'] in ('object_abs_distance', 'absolute_distance_object', 'object_rel_distance', 'relative_distance_object'):
        check_distance_prose(record, calls, plan, T, result)
    for x in re.findall(r"(?<![\w.\[,])-?\d+\.\d+", prose):
        require(x.lstrip("-") in {p.lstrip("-") for p in printed} or x in ("0.35", "0.25", "0.10", str((record.get("display") or {}).get("factor"))), "unprinted_number_in_text", x)
    t = q["question_type"]
    full_minimum(record, scene, calls, P, t)
    label = gt_label(source)
    require(record.get("gt_answer") == label, "source_gt_metadata")
    if t in F17:
        bound = copy.copy(scene)
        bound.referent_ids = record["private"]["bindings"].get("referent_ids", {})
        native = native_reference(bound, T, q, record["private"]["bindings"])
        require(record["private"].get("native_reference") == native, "native_reference_provenance")
        if record["display"]:
            require(quantize(label, record["display"]["decimals"]) == quantize(native["value"], record["display"]["decimals"]), "native_source_label_mismatch")
        else:
            require(T.letter_of(q["options"], native["value"]) == label, "native_source_label_mismatch")
    requested = ([plan["i"], plan["j"]] if q["question_type"] in ("camera_displacement", "camera_movement_direction", "camera_rotation")
                 else [plan["k"]] if "k" in plan else [c["frame"] for c in plan.get("floor_corners", [])])
    depth = q["question_type"] not in ("camera_displacement", "camera_movement_direction", "camera_rotation")
    expected_subs = {} if exact_reference or layout == "per_frame" else {k: k+1 for k in requested if k % 2}
    require({int(k): v for k, v in record["substitutions"].items()} == expected_subs, "substitution_binding")
    if depth: require(substitutions == expected_subs, "substitution_call_binding")
    require(bool(expected_subs) == ("exact_reference" in record["private"]), "missing_exact_frame_reference")
    if expected_subs:
        exact = record["private"]["exact_reference"]
        audit(exact, scene, T, config, source, reviewed, exact_reference=True)
        require(exact["answer"] == record["answer"], "odd_anchor_exact_reference_disagreement")
    if record["display"]:
        unit = record["display"]["unit"]
        require(str(result) == str(record["answer"]), "replay_answer_mismatch", f"{noun(result)} vs {record['answer']}")
        require(numeric_ok(record["answer"], label, t, record["display"]["decimals"]),
                "source_label_mismatch", f"{record['answer']} vs {label}")
    else:
        letter = T.letter_of(q["options"], result)
        require(letter is not None and letter == record["answer"], "replay_answer_mismatch", str(result))
        require(gt_label(source) == letter, "source_label_mismatch", f"{letter} vs {gt_label(source)}")
    decisions = [e for e in record["events"] if e["kind"] == "decision"]
    require(len(decisions) == 1, "decision_count")
    public_keys = {"cat", "a", "b", "target", "stand", "face", "query", "start", "goal", "plan",
                   "obj", "ref", "cands", "cats", "k", "i", "j", "M", "comparison"}
    require(decisions[0]["family"] == t and digest(decisions[0]["binding"]) == digest({k: v for k, v in plan.items() if k in public_keys})
            and decisions[0]["call_ids"] == [e["call_id"] for e in record["events"] if e["kind"] in ("tool_call", "calculator_call")],
            "decision_operand_binding")
    require(decisions[0]["result"] == result, "semantic_decision_mismatch")
    if record["display"]:
        g, v = Decimal(str(label)), Decimal(record["answer"])
        gap = abs(v-g)
        relative = gap/abs(g) if g else (Decimal(0) if not gap else None)
        expected = {"gt": str(g), "computed": str(v), "absolute_gap": str(gap),
                    "relative_gap": str(relative) if relative is not None else None,
                    "unit": unit, "decimals": record["display"]["decimals"],
                    "policy": "relative_0.05_no_floor" if t in DISTANCE_FAMILIES else "exact_declared_precision"}
        require(record["private"].get("numeric_contract") == record.get("numeric_contract") == expected, "numeric_contract_metadata")
        require(decisions[0].get("unit") == record["display"], "numeric_display_policy_mismatch")
    census = Counter()
    for event in record["events"]:
        if event["kind"] == "tool_response":
            census.update(v["unit"] for v in event["values"].values())
        elif event["kind"] == "calculator_response":
            census[event["response"]["result"]["unit"]] += 1
    return dict(census)


def f2v(x):
    return float(f2(x))


def check_distance_prose(record, calls, plan, T, result):
    """Close the distance prose grammar after checking its observable evidence.

    An extra claim cannot hide in another sentence, event or routing prefix.
    Region/layout/visibility/correction sentences were independently checked.
    """
    allowed = set()
    measured = [(args, value) for name,args,value in calls if name=='closest']
    if record['question_type'] in ('object_abs_distance','absolute_distance_object'):
        _, value = measured[0]
        conclusion = f"The closest pair is {value[0]}-{value[1]}, so the shortest distance between the {noun(plan['a'])} and the {noun(plan['b'])} is {value[2]:.2f} m."
        policy = record['display']
        if policy['factor'] != 1:
            conclusion += f" {policy['unit']} = {value[2]:.2f} * {policy['factor']} = {record['answer']}."
    else:
        scores = {}
        for args,value in measured:
            obj=record['points'][args['B'][0]]['object']
            scores[obj]=min(scores.get(obj,float('inf')),value[2])
        listing=', '.join(f'{noun(obj)} {scores[obj]:.2f} m' for obj in plan['cands'])
        letter=T.letter_of(record['options'],result)
        conclusion=f"The closest-point distances to the {noun(plan['target'])} are {listing}; the smallest is the {noun(result)}. That matches option {letter}."
    allowed.add(conclusion)
    for event in record['events']:
        if event['kind'] in ('tool_call','calculator_call'):
            require(event.get('prefix','') in ('',' '), 'distance_extra_claim')
        elif event['kind'] == 'canonical_text' and not any(event.get(k) for k in ('image_region','common_layout','frame_look','selected_views','pair_context','pair_score','pair_pick','pair_skip','pair_reuse','candidate_group','click_object')):
            require(event['text'].strip() in allowed, 'distance_extra_claim')


def check_camera_distance_text(record, expected):
    actual = [e['text'].strip() for e in record['events'] if e['kind']=='canonical_text'
              and not e.get('click_object') and not e.get('substitution')]
    require(actual == expected,'camera_distance_reasoning_text')


def derive(record, scene, T, q, calls, P, prose, exact=False):
    """Recompute the decision from printed values only."""
    t = q["question_type"]
    plan = record["private"]["bindings"]
    P = {label: point for label, point in P.items() if not point["initial"]}
    def effective(k, depth=False): return k if exact or record.get("head_layout") == "per_frame" or k % 2 == 0 else k+1
    by = lambda name: [c for c in calls if c[0] == name]
    if t in ('camera_rotation','camera_displacement','camera_movement_direction'):
        # Check requested and effective poses independently of producer admission.
        for i,j in {(plan['i'],plan['j']),(effective(plan['i']),effective(plan['j']))}:
            ri,ti = scene.gt.cam(i); rj,tj = scene.gt.cam(j)
            delta = np.asarray(tj)-np.asarray(ti)
            if t=='camera_rotation':
                a,b = np.asarray(ri)[:2,2],np.asarray(rj)[:2,2]
                yaw = math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0],float(a@b)))
                require(abs(yaw)<=175,'near_wrap')
            elif t=='camera_displacement': require(np.linalg.norm(delta)>=.10,'tiny_motion')
            else: require(math.hypot(float(delta[0]),float(delta[1]))>=.15,'tiny_motion')
    if t in ("object_abs_distance", "absolute_distance_object"):
        (_, args, value), = by("closest")
        require(all(P[l]["object"] == plan["a"] for l in args["A"]) and all(P[l]["object"] == plan["b"] for l in args["B"]), "distance_referents")
        return finish_numeric(record, value[2])
    if t in ("object_rel_distance", "relative_distance_object"):
        best = {}
        for _, args, value in by("closest"):
            obj = P[args["B"][0]]["object"]
            require(all(P[l]["object"] == plan["target"] for l in args["A"]) and all(P[l]["object"] == obj for l in args["B"]), "distance_referents")
            best[obj] = min(best.get(obj, 1e9), value[2])
        require(set(best) == set(plan["cands"]), "candidate_coverage")
        for obj in plan["cands"]:
            measured = [P[a["B"][0]]["iid"] for _, a, _ in by("closest") if P[a["B"][0]]["object"] == obj]
            ids = scene.ids(obj,many=True)
            require(len(ids) <= 2, "distance_category_too_many_instances")
            require(len(measured) == 1 and measured[0] in ids, "candidate_instance_coverage")
            target_point = P[by("closest")[0][1]["A"][0]]
            _, reference_pool = eroded_pool(scene,target_point['iid'],target_point['frame'])
            scores_by_id = []
            for iid in ids:
                visible = [k for k in scene.anchors if np.count_nonzero(scene.gt.inst[k-1]==iid) >= scene.programs.MIN_PX]
                visible.sort(key=lambda k:(-np.count_nonzero(scene.gt.inst[k-1]==iid),k))
                pools = [(k,eroded_pool(scene,iid,k)[1]) for k in visible]
                pool = next((pool for k,pool in pools if len(pool)>=3),None)
                require(pool is not None,"no_supported_visible_frame")
                scores_by_id.append((float(np.linalg.norm(np.median(pool,0)-np.median(reference_pool,0))),iid))
            require(measured[0] == min(scores_by_id)[1], "candidate_not_nearest_middle")
        scores = [best[c] for c in plan["cands"]]
        order = sorted(range(len(scores)), key=lambda i: scores[i])
        low, second = (Decimal(str(scores[i])) for i in order[:2])
        margin_m = second-low
        margin_rel = margin_m/second if second else Decimal(0)
        require(margin_m >= Decimal("0.10") and margin_rel >= Decimal("0.10"), "near_tie")
        require(record.get('margin_m') == float(margin_m) and record.get('margin_rel') == float(margin_rel), 'distance_margin_metadata')
        # Re-lift the actual operands without the public two-decimal readouts.
        raw_points = {label: np.asarray(scene.gt.lift(p['frame'], [p['uv']])[0][0], float)
                      for label, p in P.items()}
        raw_scores = [min(float(np.linalg.norm(raw_points[a]-raw_points[b]))
                          for a in args['A'] for b in args['B'])
                      for _, args, _ in by('closest')]
        low_raw, second_raw = sorted(Decimal(str(v)) for v in raw_scores)[:2]
        gap_raw = second_raw-low_raw
        require(second_raw > 0 and gap_raw >= Decimal('.10')
                and gap_raw >= Decimal('.10')*second_raw, 'near_tie')
        require(record.get('unrounded_margin_m') == float(gap_raw)
                and record.get('unrounded_margin_rel') == float(gap_raw/second_raw), 'distance_raw_margin_metadata')
        return plan["cands"][order[0]]
    if t in ("object_size_estimation", "absolute_size_object", "relative_size_object"):
        size = {}
        for _, args, value in by("dist"):
            obj = P[args["pts"][0]]["object"]
            size[obj] = max(size.get(obj, 0), value)
        if t != "relative_size_object": return finish_numeric(record, size[plan["a"]])
        require(size[plan["a"]] != size[plan["b"]], "size_tie")
        longer = plan["a"] if size[plan["a"]] > size[plan["b"]] else plan["b"]
        return longer if plan["comparison"] == "longer" else (plan["b"] if longer == plan["a"] else plan["a"])
    if t in ("object_counting", "absolute_count", "relative_count"):
        require(not calls, "count_unexpected_calculator")
        cats = [plan["a"],plan["b"]] if t == "relative_count" else [plan["cat"]]
        counts = {cat:len(scene.ids(cat,many=True)) for cat in cats}
        if t == "relative_count":
            a,b=counts[plan['a']],counts[plan['b']]
            result='more' if a>b else 'fewer' if a<b else 'equal number'
            final=(f"I count {a} {plural(plan['a'],a)} and {b} {plural(plan['b'],b)}; the counts are equal." if a==b else
                   f"I count {a} {plural(plan['a'],a)} and {b} {plural(plan['b'],b)}; {plural(plan['a'],2)} are {'less' if a<b else 'more'} numerous.")
            final+=f" That matches option {T.letter_of(q['options'],result)}."
        else:
            cat = plan['cat']
            count = counts[cat]
            floor = record['count_floor']
            require(count >= floor, "count_below_floor")
            final=f"Looking over the whole video, I count {count} {plural(cat,count)}, which is at least the floor of {floor}, so there {'is' if count == 1 else 'are'} {count}."
            result=finish_numeric(record,count)
        actual=[e['text'].strip() for e in record['events'] if e['kind']=='canonical_text' and not any(e.get(k) for k in ('count_scan','count_empty','count_floor','count_video','click_object'))]
        require(actual==[final], 'count_reasoning_text')
        return result
    if t.startswith("object_rel_direction") or t in ("relative_direction_object", "absolute_direction_object"):
        (_, args, value), = by("angle")
        require([P[args[k]]["object"] for k in ("S", "F", "Q")] == [plan["stand"], plan["face"], plan["query"]], "angle_referents")
        want = {"object_rel_direction_medium": "medium", "object_rel_direction_hard": "hard"}.get(t, "easy")
        require(args["rule"] == want, "angle_rule")
        require(min(np.linalg.norm(value[0]), np.linalg.norm(value[1])) >= .50, "direction_degenerate_floor")
        for role in ("stand","face","query"):
            obj = plan[role]
            ids = scene.ids(obj,many=True)
            require(obj.strip().lower() != "object" and all(scene.native[i]["label"].strip().lower() != "object" for i in ids), "direction_catch_all_object")
            categories = {scene.native[i]["label"].strip().lower() for i in ids}
            require(sum(x["label"].strip().lower() in categories for x in scene.native.values()) == 1, "direction_multiple_native_instances")
        from .replay import label_direction
        native = native_reference(scene,T,q,plan)["value"]
        native_label = native
        click_label = value[4] % 360 if t == "absolute_direction_object" else value[5]
        require(click_label == native_label, "click_centroid_label_disagree")
        require(record['private'].get('direction_centroid_label') == native_label,"centroid_label_metadata")
        boundaries = (0,180,-180,90,-90) if want == "hard" else (0,135,-135) if want == "medium" else (0,180,-180)
        margin = None if t == "absolute_direction_object" else min(abs(wrap(value[4]-b)) for b in boundaries)
        require(record.get('boundary_margin_deg') == margin and record.get('near_boundary') is (margin is not None and margin < 10),"direction_boundary_metadata")
        require(margin is None or margin >= 10, "near_boundary_refused")
        require(record.get("direction_roles") == [scene.entry["canonical"],plan["stand"],plan["face"],plan["query"]], "direction_roles")
        rule=("On the frame-1 floor (x right, z forward, y up) the calculator uses u = F - S and v = Q - S; "
              "cross = u_x*v_z - u_z*v_x > 0 means left and dot = u_x*v_x + u_z*v_z > 0 means front.")
        if want=='medium': rule+=' The question counts an object as behind when I would turn at least 135 degrees.'
        if t=='absolute_direction_object':
            angle=value[4]%360
            conclusion=(f"Counterclockwise seen from above is the positive (left) direction, so ccw = {value[4]} mod 360 = {angle} deg: "
                        f"I turn {angle} degrees counterclockwise to face the {noun(plan['query'])}.")
            result=finish_numeric(record,angle)
        else:
            result=value[5]
            conclusion=f"That matches option {T.letter_of(q['options'],result)}."
        plain=[e['text'].strip() for e in record['events'] if e['kind']=='canonical_text' and not any(e.get(k) for k in
               ('selected_views','frame_look','pair_context','pair_score','pair_pick','pair_skip','pair_reuse','candidate_group','click_object'))]
        require(plain==[rule,conclusion],'direction_reasoning_text')
        return result
    if t == "route_planning":
        objects = list(dict.fromkeys([plan["start"], plan["face"]] + [o for k, o in plan["plan"] if k == "go"]))
        require(len(P) == len(objects), "route_middle_coverage")
        labels = {}
        for obj in objects:
            matches = [l for l in P if P[l]["object"] == obj]
            require(len(matches) == 1, "route_landmark_binding")
            labels[obj] = matches[0]
        sequence = [c for c in calls if c[0] in ("angle", "turn")]
        contexts = []
        here, previous, turns, index, pending_turn = plan["start"], None, [], 0, False
        for i, (kind, obj) in enumerate(plan["plan"]):
            if kind == "go":
                require(obj != here, "route_degenerate_go")
                previous, here, pending_turn = here, obj, False
            else:
                require(not pending_turn and index < len(sequence), "route_sequence")
                nxt = next((o for k, o in plan["plan"][i+1:] if k == "go"), None)
                require(nxt is not None, "underspecified_route")
                op, arguments, value = sequence[index]
                if previous is None:
                    want = {"S": labels[here], "F": labels[plan["face"]], "Q": labels[nxt], "rule": "turn"}
                    require(op == "angle" and arguments == want, "route_heading_binding")
                    context = f"Blank {index+1}: I stand at the {noun(here)} facing the {noun(plan['face'])} and need to head to the {noun(nxt)}."
                else:
                    want = {"from": labels[previous], "at": labels[here], "to": labels[nxt]}
                    require(op == "turn" and arguments == want, "route_heading_binding")
                    context = f"Blank {index+1}: After the leg to the {noun(here)}, the incoming heading is from the {noun(previous)} to the {noun(here)}; I need to head to the {noun(nxt)}."
                contexts.append(context)
                turns.append(value[5]); index += 1; pending_turn = True
        require(index == len(sequence), "route_blanks")
        result = ", ".join(turns)
        check_route_prose(record, contexts, result, T.letter_of(q["options"], result))
        return result
    if t == "obj_appearance_order":
        firsts, seen = [], set()
        observations = [e for e in record['events'] if e.get('appearance_frame')]
        for k,e in enumerate(observations,1):
            g = e['appearance_frame']
            require(g['frame'] == k, "appearance_chronology")
            expected = [cat for cat in plan['cats'] if cat not in seen and appearance_ids(scene,cat,k)]
            require([o['object'] for o in g['firsts']] == expected, "appearance_observations")
            for o in g['firsts']:
                x,y = scene.gt.px([o['uv']])
                require(int(scene.gt.inst[k-1,y[0],x[0]]) in appearance_ids(scene,o['object'],k), "appearance_point")
                firsts.append((k,o['object'])); seen.add(o['object'])
            expected_text = (f"In frame {k}, I first spot " + join(f"the {noun(o['object'])} at {o['uv']}" for o in g['firsts'])+"." if expected
                             else f"In frame {k}, I find no new category from the question.")
            require(e['text'].strip() == expected_text, "appearance_text")
        require(not firsts or observations[-1]['appearance_frame']['frame'] == max(k for k,_ in firsts), "appearance_scan_end")
        require(sorted(c for _, c in firsts) == sorted(plan["cats"]), "appearance_coverage")
        require(len({k for k, _ in firsts}) == len(firsts), "appearance_tie")
        result=", ".join(c for _,c in sorted(firsts))
        conclusion='Sorting by first frame: '+', '.join(f"{noun(c)} ({k})" for k,c in sorted(firsts))+f". That matches option {T.letter_of(q['options'],result)}."
        plain=[e['text'].strip() for e in record['events'] if e['kind']=='canonical_text' and not e.get('appearance_frame')]
        require(plain==[conclusion],'appearance_reasoning_text')
        return result
    if t == "room_size_estimation":
        require(plan.get("floor_polygon_reviewed") and plan.get("floor_scope") == "whole_scene", "missing_reviewed_whole_scene_floor_corners")
        (_, args, value), = by("area")
        require(args["C"] == list(P) and len(P) == len(plan["floor_corners"]), "floor_click_coverage")
        for label, corner in zip(args["C"], plan["floor_corners"]):
            point = P[label]
            require(point["frame"] == effective(corner["frame"], True) and point["uv"] == corner["uv"]
                    and point["object"] == corner["object"] and scene.native[point["iid"]]["label"].lower() == "floor", "floor_corner_binding")
        validate_polygon([P[l]["f1"] for l in args["C"]])
        return finish_numeric(record, value)
    if t == "camera_rotation":
        (_,args,resp), = by("camera_turn")
        require(args == {"from":effective(plan["i"]),"to":effective(plan["j"])}, "camera_frames")
        value = int(re.fullmatch(r"turn = ([+-]\d+) deg",resp).group(1))
        conclusion = f"The camera rotation is {value} degrees; positive yaw means left."
        policy = record['display']
        if policy['factor'] != 1:
            conclusion += f" {policy['unit']} = {f2(value)} * {policy['factor']} = {record['answer']}."
        plain = [e['text'].strip() for e in record['events']
                 if e['kind']=='canonical_text' and not e.get('substitution')]
        require(plain==[conclusion], 'camera_turn_reasoning_text')
        return finish_numeric(record,value)
    if t in ("camera_displacement", "camera_movement_direction"):
        (_, args, resp), = by("move")
        mm = MOVE.fullmatch(resp)
        dx, dz, dist = float(mm.group(1)), float(mm.group(3)), float(mm.group(4))
        want = [effective(k) for k in (plan["i"], plan["j"])]
        require([args["from"], args["to"]] == want, "camera_frames")
        if t == "camera_displacement": return finish_numeric(record, dist)
        scores = {"forward": dz, "backward": -dz, "right": dx, "left": -dx}
        labels = [v.strip().lower() for v in T.option_texts(q["options"]).values()]
        ordered = sorted(labels, key=lambda l: -scores[l])
        require(scores[ordered[0]] > 0, "movement_no_positive_option")
        top,second = (Decimal(str(scores[l])) for l in ordered[:2])
        margin = top-second
        require(margin>=Decimal('.10') and margin>=Decimal('.10')*top,'near_tie')
        require(record.get('margin_m')==float(margin) and record.get('margin_rel')==float(margin/top),
                'camera_margin_metadata')
        for ri, rj in dict.fromkeys(((plan['i'], plan['j']), tuple(want))):
            rotation, start = scene.gt.cam(ri)
            delta = np.asarray(scene.gt.cam(rj)[1],dtype=float)-np.asarray(start,dtype=float)
            forward = np.asarray(rotation,dtype=float)[:, 2].copy()
            forward[2] = 0
            forward /= np.linalg.norm(forward)
            right = np.cross(np.array([0., 0., -1.]), forward)
            dx_raw, dz_raw = float(right@delta), float(forward@delta)
            raw_scores = dict(forward=dz_raw, backward=-dz_raw, right=dx_raw, left=-dx_raw)
            top_raw, second_raw = sorted((Decimal(str(raw_scores[l])) for l in labels), reverse=True)[:2]
            gap_raw = top_raw-second_raw
            require(top_raw > 0 and gap_raw >= Decimal('.10')
                    and gap_raw >= Decimal('.10')*top_raw, 'near_tie')
        require(math.isclose(record.get('unrounded_margin_m',math.nan),float(gap_raw),rel_tol=1e-12,abs_tol=1e-12)
                and math.isclose(record.get('unrounded_margin_rel',math.nan),float(gap_raw/top_raw),rel_tol=1e-12,abs_tol=1e-12),
                'camera_raw_margin_metadata')
        require('It is a narrow call' not in prose,'movement_margin_text')
        for label in labels:
            component = {"forward": "dz", "backward": "-dz", "right": "dx", "left": "-dx"}[label]
            require(f"{label} = {component} = {f2(scores[label])} m" in prose, "movement_scores")
        return ordered[0]
    k = effective(plan["k"], True)
    for l in P: require(P[l]["frame"] == k, "question_frame")
    def camera_instances(obj, labels):
        expected = {i for i in scene.ids(obj, many=True) if np.count_nonzero(scene.gt.inst[k-1] == i) >= scene.programs.MIN_PX}
        require({P[l]["iid"] for l in labels} == expected, "camera_instance_coverage")
    if t == "camera_obj_abs_dist":
        (_, args, best), = by("cam_dist")
        require(all(P[l]["object"] == plan["obj"] for l in args["pts"]), "camera_object_binding")
        camera_instances(plan["obj"], args["pts"])
        value = finish_numeric(record,best[1])
        instances = {P[l]['iid'] for l in args['pts']}
        expected = [f"In frame {k} I click the part of the {noun(plan['obj'])} nearest the camera."]*len(instances)
        final = f"The nearest clicked point of the {noun(plan['obj'])} is {best[0]} at {best[1]:.2f} m from the camera."
        policy = record['display']
        if policy['factor'] != 1: final += f" {policy['unit']} = {best[1]:.2f} * {policy['factor']} = {value}."
        check_camera_distance_text(record,expected+[final])
        return value
    if t.startswith("camera_obj_rel_dist"):
        scores = {}
        for _, args, best in by("cam_dist"):
            obj = P[args["pts"][0]]["object"]
            require(all(P[l]["object"] == obj for l in args["pts"]), "cam_dist_mixed_objects")
            camera_instances(obj, args["pts"])
            require(len(args["pts"]) <= 3, "camera_candidate_count")
            require(obj not in scores, "duplicate_camera_object_call")
            scores[obj] = best[1]
        require(set(scores) == set(plan["cands"]), "candidate_coverage")
        vals = [scores[c] for c in plan["cands"]]
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        require(round(vals[order[1]]-vals[order[0]],2) >= .05, "camera_distance_margin_under_0.05")
        result = plan["cands"][order[0]]
        expected = [f"I compare these near-side candidates for the {noun(c)}." for c in plan['cands']]
        final = "Nearest-point distances from the camera: " + ", ".join(f"{noun(c)} {scores[c]:.2f} m" for c in plan['cands']) + f"; the smallest is the {noun(result)}. That matches option {T.letter_of(q['options'],result)}."
        check_camera_distance_text(record,expected+[final])
        return result
    labels = list(P)
    require(len(labels) == 2 and [P[l]["object"] for l in labels] == [plan["a"], plan["ref"]], "obj_obj_points")
    a, r = (P[l] for l in labels)
    an,rn=noun(plan['a']),noun(plan['ref'])
    intro=f"In frame {k} I click near the middle of the {an} and of the {rn}."
    if t.endswith('_lr'):
        xa,xr=a['cam'][0],r['cam'][0]
        require(xa!=xr,'position_tie');result='left' if xa<xr else 'right'
        conclusion=f"In frame {k}'s view, larger x is further right. The middle of the {an} is at x {f2(xa)} and the middle of the {rn} at x {f2(xr)}, so the {an} lies to the {result}."
    elif t.endswith('_nf'):
        (_,operands,best),=by('cam_dist')
        require(operands['pts']==labels,'obj_obj_operand_coverage')
        da,dr=best[2][labels[0]],best[2][labels[1]]
        require(da!=dr,'position_tie');result='near' if da<dr else 'far'
        conclusion=f"The middle of the {an} is {f2(da)} m from the camera and the middle of the {rn} {f2(dr)} m, so the former is {'nearer' if da<dr else 'farther'}."
    else:
        ya,yr=a['f1'][1],r['f1'][1]
        require(ya!=yr,'position_tie');result='up' if ya>yr else 'down'
        conclusion=f"The pose head places the middle of the {an} at frame-1 height y {f2(ya)} and the middle of the {rn} at {f2(yr)}. With y up, the former is {'higher (up)' if ya>yr else 'lower (down)'}."
    conclusion+=f" That matches option {T.letter_of(q['options'],result)}."
    plain=[e['text'].strip() for e in record['events'] if e['kind']=='canonical_text' and not any(e.get(key) for key in ('click_object','substitution'))]
    require(plain==[intro,conclusion],'object_position_text')
    # These sentences name objects and coordinates rather than point labels.
    # Bind their implicit references to the readouts already shown at that event.
    shown = set()
    for event in record['events']:
        if event['kind']=='canonical_text' and event['text'].strip()==conclusion:
            require(set(labels) <= shown, 'comparison_before_readout')
        if event['kind']=='tool_response' and event['name']=='depth_at':
            shown.update(p['label'] for p in event['points'])
    return result


def check_opening(record, family, bound, calls, points, paragraph, config):
    """Use rebound source roles and validated operands, never branch metadata."""
    roles = {k: bound[k] for k in ("a", "b", "cat", "target", "stand", "face", "query", "start", "goal",
                                  "obj", "ref", "cands", "cats", "i", "j", "k") if k in bound}
    if family == "route_planning":
        roles["goal"] = bound.get("goal", next(o for k, o in reversed(bound["plan"]) if k == "go"))
    common_frame = None
    if family in ("object_abs_distance", "absolute_distance_object"):
        measured = [args for name, args, _ in calls if name == "closest"]
        require(len(measured) == 1, "opening_distance_call")
        frames = []
        for side, role in (("A", "a"), ("B", "b")):
            operands = [points[label] for label in measured[0][side]]
            require(operands and all(p["object"] == bound[role] for p in operands), "opening_distance_roles")
            actual = {p["frame"] for p in operands}
            require(1 <= len(actual) <= 3, "opening_distance_frames")
            frames.append(next(iter(actual)) if len(actual)==1 else None)
        if frames[0] is not None and frames[0] == frames[1]:
            common_frame = frames[0]
    expected = enrich_opening(opening_text(family, roles, common_frame=common_frame), family, record["private"]["frame_choices"], config, record["qid"], bool(points))
    require(record["events"][0]["text"] == paragraph == expected, "opening_plan_text")


def check_route_prose(record, contexts, result, letter):
    """Bind the complete ordered reasoning tail to replayed source transitions.

    Calls and responses have already been checked independently. Keeping each
    context beside its call also refuses a swap that preserves the claim census.
    """
    text = record["target"]
    matches = list(CALL.finditer(text))
    last_head = max(m.end() for m in matches if m.group(1) == "depth_at")
    turn_calls = [m.group(0) for m in matches if m.group(1) == "angle" or m.group(1) == "turn" and "at=" in m.group(2)]
    require(len(contexts) == len(turn_calls), "route_prose_context_count")
    rule = ("On the frame-1 floor (x right, z forward, y up) the calculator uses u = F - S and v = Q - S; "
            "cross = u_x*v_z - u_z*v_x > 0 means left and dot = u_x*v_x + u_z*v_z > 0 means front. "
            "Turn Back applies when |theta| >= 135 degrees.")
    turns = result.split(", ")
    conclusion = ("So the turn at the blank is " + turns[0].removeprefix("Turn ").lower() if len(turns) == 1 else "So the turns at the blanks are " + join(x.removeprefix("Turn ").lower() for x in turns)) + f", which matches option {letter}."
    expected = [rule] + [c + " " + call for c, call in zip(contexts, turn_calls)] + [conclusion, "</think>", str(record["answer"])]
    require(text[last_head:].split() == " ".join(expected).split(), "route_supervised_context")
    # A second claim before the reasoning tail is still supervised.
    prefix = CALL.sub(" ", text[:last_head])
    require(not re.search(r"\bblank\s+[^:.\n]+:|\bI (?:stand at|reached)\b|\bThe turns are\b|\bThat matches option\b", prefix, re.I),
            "route_extra_claim")
    # Admit only the fixed location preamble and visibility/correction text
    # already checked by verify_controls. A claim hidden in any other event or
    # call prefix must not add route context before the complete reasoning tail.
    last_event = max(i for i, e in enumerate(record["events"])
                     if e["kind"] == "tool_response" and e["name"] == "depth_at")
    allowed = ["<think>", record["events"][0]["text"]]
    allowed.extend(e["text"] for e in record["events"][1:last_event]
                   if any(e.get(k) for k in ("selected_views", "frame_look", "pair_context", "pair_score", "pair_pick", "pair_skip", "pair_reuse", "click_object")) or e["kind"] == "correction")
    require(prefix.split() == " ".join(allowed).split(), "route_extra_claim")


def converted_half_even(value, policy):
    """Convert the replayed measurement, independently of producer arithmetic."""
    with localcontext() as context:
        context.prec = 80
        converted = Decimal(str(value)) * Decimal(str(policy["factor"]))
        return format(converted.quantize(Decimal(1).scaleb(-policy["decimals"]),
                                         rounding=ROUND_HALF_EVEN), f".{policy['decimals']}f")


def check_conversion(record, value=None):
    """Census all unit claims and numeric products before accepting one sentence.

    The broad census deliberately accepts more spellings than the sentence
    grammar: malformed, exponent, Unicode or unknown-unit products must refuse,
    rather than disappear from a narrow arithmetic regex.
    """
    prose = CALL.sub(" ", record["target"])
    policy = record["display"]
    expected = bool(policy and policy["factor"] != 1)
    number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    sentence = re.compile(rf"\b([A-Za-z][\w²^]*) = ({NUM}) \* (\d+(?:\.\d+)?) = ({number})\.(?=\s|$)")
    claims = list(sentence.finditer(prose))
    require(len(claims) == int(expected), "conversion_sentence_count")
    if expected:
        claim, = claims
        unit, operand, factor, result = claim.groups()
        require(unit == policy["unit"] and operand == f2(value)
                and Decimal(factor) == Decimal(str(policy["factor"]))
                and result == converted_half_even(value, policy), "conversion_measurement_policy")
        prose = prose[:claim.start()] + " " + prose[claim.end():]
    # No unvalidated line can hide behind a spelling the sentence parser misses.
    units = "|".join(re.escape(u) for u in (*UNITS, "m²", "ft²"))
    unit_claim = rf"\b(?:{units})\s*(?:=|:|→)"
    product = rf"(?<!\w)(?:{number}|nan|inf)\s*(?:\*|×|·|x|times)\s*(?:{number}|nan|inf)(?!\w)"
    operation_claim = rf"\b[A-Za-z][\w²^]*\s*(?:=|:|→)\s*(?:{number}|nan|inf)\s*(?:[*×·/÷]|x\b|times\b)"
    require(not any(re.search(pattern, prose, re.I) for pattern in (unit_claim, product, operation_claim)), "extra_conversion_claim")


def finish_numeric(record, value):
    unit = record["display"]
    check_conversion(record, value)
    if unit["factor"] != 1:
        return converted_half_even(value, unit)
    return f"{value * unit['factor']:.{unit['decimals']}f}"


def _pool_percentiles(samples):
    """Use the ordinary quantile path only for fully finite sample columns."""
    finite = np.isfinite(samples).all(axis=0)
    percentiles = np.empty((4, samples.shape[1]), dtype=np.float64)
    if finite.any():
        percentiles[:, finite] = np.percentile(samples[:, finite], [20, 30, 50, 80], axis=0)
    if (~finite).any():
        percentiles[:, ~finite] = np.nanpercentile(samples[:, ~finite], [20, 30, 50, 80], axis=0)
    return percentiles


def eroded_pool(scene, iid, frame):
    """Independently enumerate every representable stable eroded-mask pixel.

    Do not call GTScene.candidates, GT.lift, or generator arithmetic. Depth uses
    the same specified 5x5 grid and p30 definition, implemented here in bulk.
    """
    gt = scene.gt
    mask = gt.inst[frame-1] == iid
    interior = distance_transform_edt(mask) >= 3
    y, x = np.nonzero(interior)
    uv = np.unique(np.rint(np.column_stack(((x+.5)/gt.W*1000, (y+.5)/gt.H*1000))).astype(int), axis=0)
    x = np.minimum(gt.W-1, (uv[:, 0]/1000*gt.W).astype(int))
    y = np.minimum(gt.H-1, (uv[:, 1]/1000*gt.H).astype(int))
    keep = interior[y, x] & np.all((uv >= 20) & (uv <= 980), axis=1)
    uv, x, y = uv[keep], x[keep], y[keep]
    if not len(uv): return uv, np.empty((0, 3))
    samples = []
    for dx in (-10, -5, 0, 5, 10):
        for dy in (-10, -5, 0, 5, 10):
            xx = (np.clip(uv[:, 0]+dx, 0, 999.9)/1000*gt.W).astype(int)
            yy = (np.clip(uv[:, 1]+dy, 0, 999.9)/1000*gt.H).astype(int)
            samples.append(gt.depth[frame-1, yy, xx])
    samples = np.array(samples, float)
    samples[samples <= 0] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        percentiles = _pool_percentiles(samples)
        spread = np.round((percentiles[3]-percentiles[0])/np.maximum(percentiles[2], .001), 2)
    limits = np.where(np.min(np.minimum(uv, 1000-uv), axis=1) <= 40, .10, .25)
    keep = np.isfinite(percentiles[1]) & np.isfinite(spread) & (spread <= limits)
    K = gt.K if getattr(gt, "K_frames", None) is None else gt.K_frames[frame-1]
    camera = np.column_stack((x+.5, y+.5, np.ones(len(x)))) @ np.linalg.inv(K).T
    camera *= percentiles[1, :, None]
    pose = replay_pose(scene, frame, False)
    points = camera @ np.asarray(pose["R"]).T + pose["t"]
    return uv[keep], points[keep]


def validate_polygon(points):
    p = np.asarray(points)
    require(len(p) >= 3 and np.ptp(p[:, 1]) <= .1, "nonplanar_floor")
    xz = p[:, [0, 2]]
    require(len(np.unique(xz, axis=0)) == len(xz), "duplicate_floor_corner")
    cross = lambda a, b: a[0]*b[1]-a[1]*b[0]
    for i in range(len(xz)):
        a, b = xz[i], xz[(i+1) % len(xz)]
        for j in range(i+2, len(xz)):
            if i == 0 and j == len(xz)-1: continue
            c, d = xz[j], xz[(j+1) % len(xz)]
            require(not (cross(b-a, c-a)*cross(b-a, d-a) <= 0 and
                         cross(d-c, a-c)*cross(d-c, b-c) <= 0), "self_intersecting_floor_polygon")
    total = sum(cross(a, b) for a, b in zip(xz, np.roll(xz, -1, axis=0)))
    require(abs(total) > .0001, "zero_floor_area")


def event_paragraphs(events):
    """Group events at the same boundaries used by the public renderer."""
    paragraph = []
    for event in events:
        if event['kind'] in ('plan', 'canonical_paragraph'):
            if paragraph: yield paragraph
            paragraph = []
        else:
            paragraph.append(event)
    if paragraph: yield paragraph


def verify_controls(record, scene, calls, points, plan, exact):
    events, text, family = record["events"], record["target"], record["question_type"]
    event_index = {id(e):i for i,e in enumerate(events)}
    printed_points = set()
    for event in events:
        if event['kind']=='canonical_text':
            references = set(re.findall(r'\bP\d+\b', event['text']))
            if event.get('common_layout'): references.update(event['common_layout'].values())
            if event.get('image_region'): references.add(event['image_region']['middle'])
            require(references <= printed_points, 'comparison_before_readout')
        if event['kind']=='tool_response' and event['name']=='depth_at':
            printed_points.update(p['label'] for p in event['points'])
    expected_branch = {"family": family, "frame_choices": [
        {key: choice[key] for key in ("objects", "frames", "kind")} for choice in record["private"]["frame_choices"]],
        "substitutions": record["substitutions"]}
    require(digest(record["plan_branch"]) == digest(expected_branch), "plan_branch_binding")
    choices = record["private"]["frame_choices"]
    distances = family in ("object_abs_distance", "absolute_distance_object", "object_rel_distance", "relative_distance_object")
    directions = family.startswith("object_rel_direction") or family in ("relative_direction_object", "absolute_direction_object")
    if distances:
        prose = CALL.sub(" ", text)
        ranking_claim = (r"(?:least|lowest|smallest|minimum|best|smaller|optimal)[^.!?\n]{0,120}(?:motion|frame pair|pair of (?:frames|views)|score|\br\b)|"
                         r"(?:pair|frames|views|score)[^.!?\n]{0,120}(?:least|lowest|minimum|optimal|smaller r)|"
                         r"(?:all|every|other)[^.!?\n]{0,60}(?:candidate pairs?|pair scores?)|"
                         r"(?:search|rank|compar)[^.!?\n]{0,80}(?:frames|views|pairs|motion)")
        uncontrolled = " ".join(e["text"] for e in events if e["kind"] == "canonical_text" and not e.get("pair_pick"))
        require(not re.search(ranking_claim, uncontrolled, re.I), "unshown_pair_ranking_claim")
        measured = [args for name, args, _ in calls if name == "closest"]
        require(len(choices) == len(measured), "frame_choice_coverage")
        require(not any(e.get("image_region") or e.get("common_layout") for e in events), "obsolete_distance_layout")
        for choice, operands in zip(choices, measured):
            a, b = points[operands["A"][0]], points[operands["B"][0]]
            require(choice["objects"] == [a["object"], b["object"]]
                    and choice["instance_ids"] == [a["iid"], b["iid"]]
                    and choice["frames"] == [a["frame"], b["frame"]], "frame_choice_operand_binding")
        if family in ("relative_distance_object","object_rel_distance"):
            require(all(a['A'] == measured[0]['A'] for a in measured),"reference_set_not_reused")
            operands = set(l for a in measured for side in ('A','B') for l in a[side])
            require(operands == {l for l,p in points.items() if not p['initial']},"unused_distance_click")
            for i,label in enumerate(sorted(operands)):
                p = points[label]
                for other in sorted(operands)[:i]:
                    q = points[other]
                    if (p['object'],p['iid']) == (q['object'],q['iid']):
                        require(p['frame'] == q['frame'],"distance_object_multiple_views")
                        gap = np.linalg.norm((np.asarray(p['uv'])-q['uv'])*[scene.gt.W/1000,scene.gt.H/1000])
                        require(gap >= 15,"distance_clicks_too_close")
    elif directions or family == "route_planning":
        objects = [plan[k] for k in ("stand", "face", "query")] if directions else list(dict.fromkeys(
            [plan["start"], plan["face"]]+[o for k, o in plan["plan"] if k == "go"]))
        require(len(choices) == 1 and choices[0]["objects"] == objects, "frame_choice_coverage")
    else: require(not choices, "unexpected_frame_choices")
    # Every response's structured head values must match its printed bytes.
    for event in events:
        if event["kind"] != "tool_response" or event["name"] == "depth_at": continue
        cid, values = event["call_id"], event["values"]
        if event["name"] == "move":
            m = MOVE.fullmatch(event["text"])
            expected = {cid+".delta": {"value": [float(m.group(i)) for i in (1, 2, 3)], "unit": "m"},
                        cid+".distance": {"value": float(m.group(4)), "unit": "m"}}
        elif event["name"] == "turn":
            m = re.fullmatch(r"turn = ([+-]\d+) deg",event["text"])
            require(m is not None,"turn_syntax")
            expected = {cid+".turn": {"value":int(m.group(1)),"unit":"degree"}}
        else:
            m = POSE.fullmatch(event["text"])
            expected = {cid+".t": {"value": [float(m.group(i)) for i in (1, 2, 3)], "unit": "m"},
                        cid+".yaw": {"value": int(m.group(4)), "unit": "degree"}}
        require(values == expected, "head_event_values")
    for i,e in enumerate(events):
        if e["kind"] == "tool_call" and e["name"] == "depth_at":
            announcement = i > 0 and events[i-1].get("click_object") == {"object": e["object"], "frame": e["arguments"].get("image_frame", e["arguments"]["frame"])}
            previous = events[i-2] if i >= 2 else {}
            continuation = (i >= 2 and events[i-1]['kind'] == 'tool_response' and previous.get('kind') == 'tool_call'
                            and previous.get('name') == 'depth_at' and previous.get('object') == e['object']
                            and previous['arguments']['frame'] == e['arguments']['frame']
                            and previous['arguments'].get('image_frame') == e['arguments'].get('image_frame')
                            and len(previous['arguments']['pts']) == 4)
            require(announcement or continuation, "missing_click_announcement")
    seen = []
    for point in points.values():
        for other in seen:
            if point['frame'] != other['frame']: continue
            delta = np.asarray(point['uv'])-other['uv']
            require(np.linalg.norm(delta*[scene.gt.W/1000, scene.gt.H/1000]) >= 15
                    and np.linalg.norm(delta) >= 15, 'click_spacing')
        seen.append(point)
    corrected = set()
    for event in events:
        if event["kind"] != "correction": continue
        old, new = points[event["initial_label"]], points[event["corrected_label"]]
        require(old["initial"] and old["spread"] > depth_limit(old["uv"]) and not new["initial"] and new["spread"] <= depth_limit(new["uv"]),
                "correction_trigger")
        require((old["object"], old["iid"], old["frame"]) == (new["object"], new["iid"], new["frame"]), "correction_identity")
        scale = np.array([scene.gt.W, scene.gt.H])/1000
        for point in points.values():
            if point['initial'] or (point['object'], point['iid'], point['frame']) != (old['object'], old['iid'], old['frame']): continue
            delta = np.asarray(point['uv'])-old['uv']
            require(np.linalg.norm(delta*scale) >= 40 and np.linalg.norm(delta) >= 40, 'reclick_exclusion')
            if depth_limit(old['uv']) == .10:
                require(min(*point['uv'], *(1000-x for x in point['uv'])) > min(*old['uv'], *(1000-x for x in old['uv'])), 'reclick_border')
        require(event["initial"] == old["uv"] and event["next"] == new["uv"] and event["frame"] == old["frame"], "correction_click_binding")
        require(int(event["corrected_label"][1:]) == int(event["initial_label"][1:])+1, "correction_sequence")
        require(int(digest([record['qid'],old['object'],old['frame']]),16)%10==0, 'correction_hash_selection')
        references = set()
        for n,a,_ in calls:
            if n in ('move','pose','camera_turn'): continue
            for key,val in a.items():
                if key != 'rule': references.update(val if isinstance(val,list) else [val])
        # Middle clicks also feed the printed layout or direct x/y comparison.
        for e in events:
            if e.get('common_layout'): references.update(e['common_layout'].values())
        if family.startswith('obj_obj_relative_pos'):
            references.update(l for l,p in points.items() if not p['initial'])
        if family in ('object_counting','absolute_count','relative_count'):
            references.update('P'+str(int(a['pts'][0][1:])-1) for n,a,_ in calls if n=='dist')
        require(event['corrected_label'] in references, 'correction_replacement_unused')
        old_response = next(e for e in events if e["kind"] == "tool_response" and
                            any(p["label"] == event["initial_label"] for p in e.get("points", [])))
        new_response = next(e for e in events if e["kind"] == "tool_response" and
                            any(p["label"] == event["corrected_label"] for p in e.get("points", [])))
        index = next(i for i, p in enumerate(old_response["points"]) if p["label"] == event["initial_label"])
        prefix = "" if len(old_response["points"]) == 1 else str(index)+"."
        require(event["spread_node"] == old_response["call_id"]+"."+prefix+"spread", "correction_spread_node")
        require(event_index[id(old_response)] < event_index[id(event)] < event_index[id(new_response)], "correction_sequence")
        near = family == 'camera_obj_abs_dist' or family.startswith('camera_obj_rel_dist')
        require(event.get('goal') == 'replacement', 'correction_goal')
        goal = f"another point on the {noun(old['object'])}"
        expected_text = f"The spread is {old['spread']:.2f}, above {depth_limit(old['uv']):.2f}, so this click is probably on an edge; I click {goal}, at {new['uv']}."
        require(event["text"].strip() == expected_text, "correction_text")
        corrected.add(event["initial_label"])
    require(corrected == {l for l, p in points.items() if p["initial"]}, "unresolved_spread")

    require(not any(e.get("grounding") for e in events), "visibility_inventory")
    prose = CALL.sub(" ", text)
    require(not re.search(r"Visibility for|Absent in|No checked|Scan for|innermost|30 grid units|clearest", prose, re.I), "visibility_inventory")
    def visible(iid):
        return [k for k in scene.anchors if np.count_nonzero(scene.gt.inst[k-1] == iid) >= scene.programs.MIN_PX]
    usable_counts = {}
    def usable(iid,k):
        key = (iid,k)
        if key not in usable_counts:
            usable_counts[key] = len(eroded_pool(scene,iid,k)[0]) >= 3
        return usable_counts[key]
    def ranked(A,B):
        scores = []
        for i in A:
            for j in B:
                scores.append([abs(i-j),0,0,i,j])
        return sorted(scores,key=lambda c:(c[0],abs(c[3]-c[4]),c[3],c[4]))
    expected_rankings = []
    for choice in choices:
        objects,frames,kind = choice['objects'],choice['frames'],choice['kind']
        ids = choice.get('instance_ids') or [scene.ids(o)[0] for o in objects]
        require(len(objects) == len(frames) == len(ids), 'frame_choice_cardinality')
        for o,i,k in zip(objects,ids,frames):
            require(i in scene.ids(o,many=True) and k in visible(i), 'frame_choice_identity')
            require(any(p['object']==o and p['iid']==i and p['frame']==k for p in points.values()), 'frame_choice_readout')
        common = set.intersection(*(set(visible(i)) for i in ids))
        if kind == 'surface_views':
            require(family in ('object_abs_distance','absolute_distance_object'), 'surface_view_family')
            wanted = []
            for i in ids:
                ks = []
                for k in sorted(visible(i),key=lambda k:(-np.count_nonzero(scene.gt.inst[k-1]==i),k)):
                    if len(eroded_pool(scene,i,k)[0]) >= 3: ks.append(k)
                    if len(ks) == 3: break
                wanted.append(sorted(ks))
            # Reconstruct the view pruning from GT pools, independently of recorded clicks.
            from scipy.spatial import cKDTree
            while True:
                pools = [[eroded_pool(scene,i,k) for k in ks] for i,ks in zip(ids,wanted)]
                clouds = [np.concatenate([p for uv,p in side]) for side in pools]
                ds, nn = cKDTree(clouds[1]).query(clouds[0])
                witness = int(nn[int(ds.argmin())]); view_index = 0
                while witness >= len(pools[1][view_index][0]):
                    witness -= len(pools[1][view_index][0]); view_index += 1
                indices = [[int(cKDTree(clouds[1-side]).query(p)[0].argmin()) for uv,p in group]
                           for side,group in enumerate(pools)]
                indices[1][view_index] = witness
                retained = []
                for iid,ks,group,ix in zip(ids,wanted,pools,indices):
                    keep, positions = [], []
                    order = sorted(range(len(ks)), key=lambda v:(-np.count_nonzero(scene.gt.inst[ks[v]-1]==iid),ks[v]))
                    for v in order:
                        k,(_,cloud),index = ks[v],group[v],ix[v]
                        point = cloud[index]
                        if all(np.linalg.norm(point-other) >= .05 for other in positions):
                            keep.append(k); positions.append(point)
                    retained.append(sorted(keep))
                if retained == wanted: break
                wanted = retained
            require(choice.get('views') == wanted and frames == [ks[0] for ks in wanted], 'surface_view_selection')
            for o,i,ks in zip(objects,ids,wanted):
                require(sorted(p['frame'] for p in points.values() if p['object']==o and p['iid']==i and not p['initial']) == ks,
                        'surface_view_coverage')
            from .plan_contract import qwen_tokens
            require(qwen_tokens(record['target']) <= 3000, 'surface_view_token_limit')
        elif kind == 'common':
            require(len(set(frames)) == 1 and frames[0] in common, 'common_frame_choice')
        elif kind in ('pair','reference_pair'):
            require(len(ids)==2 and (not common if kind=='pair' else frames[0] not in visible(ids[1])), 'pair_when_common_available')
            scores = ranked(visible(ids[0]) if kind=='pair' else [frames[0]],visible(ids[1]))
            require(choice['candidates']==scores, 'pair_minimum_or_tie_rule')
            expected_rankings.append((scores,choice['shown'],frames,[(ids[0],0),(ids[1],1)]))
        elif kind == 'anchor':
            require(not common, 'anchor_when_common_available')
            available = set.union(*(set(visible(i)) for i in ids))
            anchor = min(available,key=lambda k:(-sum(k in visible(i) for i in ids),
                -min(np.count_nonzero(scene.gt.inst[k-1]==i) for i in ids if k in visible(i)),k))
            require(choice['anchor']==anchor, 'anchor_choice')
            rs = iter(choice['rankings'])
            for o,i,k in zip(objects,ids,frames):
                if anchor in visible(i): require(k==anchor, 'anchor_object_frame')
                else:
                    r=next(rs); scores=ranked([anchor],visible(i))
                    require(r['object']==o and r['candidates']==scores, 'anchor_object_minimum')
                    operands=[(ii,0) for ii in ids if anchor in visible(ii)]+[(i,1)]
                    expected_rankings.append((scores,r['shown'],[anchor,k],operands))
            require(next(rs,None) is None, 'extra_anchor_ranking')
        else: raise Refusal('unknown_frame_choice')
    picks = [e for e in events if e.get('pair_pick')]
    require(len(picks)==len(expected_rankings),'pair_comparison_coverage')
    expected_pairs, expected_turns, reused = [], [], []
    for (scores,shown,selected,operands),pick in zip(expected_rankings,picks):
        eligible = []
        for c in scores:
            if all(usable(iid,c[3+side]) for iid,side in operands): eligible.append(c)
            if len(eligible) == 2: break
        require(bool(eligible), 'no_supported_visible_frame_pair')
        i,j = eligible[0][3:]
        require(shown == sorted(c[3:] for c in eligible), 'candidate_pair_coverage')
        require(pick['pair_pick'] == {'pairs':shown,'selected':selected,'skipped':[],'rule':'frame_gap'}, 'pair_pick_binding')
        require(selected == [i,j], 'frame_gap_minimum')
        expected_pick = f"I use frames {i} and {j}: among usable visible pairs, they have the smallest frame separation, with ties settled by the lower first frame, then the second."
        require(pick['text'].strip() == expected_pick, 'pair_pick_text')
    require(record.get('frame_pair_turn') == expected_turns and 'frame_pair_r' not in record, 'frame_pair_turn_metadata')
    require(not any(e.get(k) for e in events for k in ('pair_skip','pair_context','pair_score')), 'obsolete_pair_prose')
    require([(e['pair_reuse']['from'],e['pair_reuse']['to']) for e in events if e.get('pair_reuse')] == reused, 'pair_reuse_coverage')
    if distances or directions or family=='route_planning':
        require(not any(n=='move' for n,a,r in calls), 'pair_move_coverage')
        require([(a['from'],a['to']) for n,a,r in calls if n=='camera_turn'] == expected_pairs, 'pair_turn_coverage')
    groups = [e for e in events if e.get('candidate_group')]
    require([e['candidate_group']['object'] for e in groups] == (plan['cands'] if family in ('relative_distance_object','object_rel_distance') else []), 'candidate_group_coverage')
    if groups:
        controls = [e for e in events if e.get('pair_pick') or e.get('frame_look')]
        require(len(controls) == len(groups), 'candidate_group_control_coverage')
        for n,(group,control) in enumerate(zip(groups,controls)):
            lo,hi = event_index[id(group)],event_index[id(control)]
            require(lo < hi and (n+1 == len(groups) or hi < event_index[id(groups[n+1])]), 'candidate_group_order')
            if control.get('frame_look'):
                require(group['candidate_group']['object'] in control['frame_look']['objects'], 'candidate_group_binding')
    expected_substitutions = Counter((int(i),j) for i,j in record['substitutions'].items())
    explanations = Counter((e['substitution']['from'],e['substitution']['to']) for e in events if e.get('substitution'))
    require(explanations==expected_substitutions, 'substitution_explanation_coverage')
    for e in events:
        for key in ('frame_look','selected_views','pair_reuse','candidate_group','click_object','substitution'):
            if not e.get(key): continue
            g=e[key]
            if key in ('frame_look','selected_views'):
                if len(set(g['frames'])) > 1:
                    prior=events[:event_index[id(e)]]
                    chosen_frames={k for x in prior if x.get('pair_pick') for k in x['pair_pick']['selected']}
                    require(set(g['frames']) <= chosen_frames,'frame_named_before_measurement')
                require(any(g=={'objects':c['objects'],'frames':c['frames']} for c in choices),'frame_sentence_binding')
                expected=frame_look(g['objects'],g['frames']) if key=='frame_look' else 'I use '+join(f"the {noun(o)} in frame {k}" for o,k in zip(g['objects'],g['frames']))+'.'
            elif key=='click_object':
                expected=f"I click the {noun(g['object'])} in frame {g['frame']}."
                index=event_index[id(e)]
                preceding = events[index-1] if index else {}
                covered = (preceding.get('kind') == 'correction' and preceding.get('frame') == g['frame']
                           or family == 'camera_obj_abs_dist' and preceding.get('text', '').strip() ==
                           f"In frame {g['frame']} I click the part of the {noun(g['object'])} nearest the camera.")
                require(bool(e.get('click_covered')) == bool(covered), 'duplicate_click_sentence')
                if covered: expected = ""
                index=event_index[id(e)]
                if distances or directions or family=='route_planning':
                    observed = any((c['kind']=='common' and g['object'] in c['objects'] and g['frame'] in c['frames']) or
                                   (c['kind']=='surface_views' and g['object'] in c['objects'] and
                                    g['frame'] in c['views'][c['objects'].index(g['object'])]) for c in choices)
                    selected = any(x.get('pair_pick') and g['frame'] in x['pair_pick']['selected'] for x in events[:index])
                    require(observed or selected,'frame_named_before_measurement')
                require(index+1<len(events) and events[index+1]['kind']=='tool_call' and events[index+1]['name']=='depth_at' and events[index+1]['object']==g['object'] and events[index+1]['arguments'].get('image_frame',events[index+1]['arguments']['frame'])==g['frame'],'click_announcement')
            elif key=='substitution':
                i,j=g['from'],g['to']
                require(record['head_layout']=='paired_anchor' and {int(k):v for k,v in record['substitutions'].items()}.get(i)==j,'substitution_text_binding')
                expected=f"The heads read out one frame per temporal pair, the even one, so for frame {i} I use frame {j}."
            elif key == 'candidate_group':
                expected = f"For the {noun(g['object'])}:"
            else:
                i,j = g['from'],g['to']
                prior = events[:event_index[id(e)]]
                require(any(x['kind']=='tool_call' and x['name']=='turn' and x['arguments']==g and
                            any(y['kind']=='tool_response' and y['call_id']==x['call_id'] for y in prior) for x in prior), 'reuse_before_readout')
                expected = f"I reuse the printed turn for frames {i} and {j}."
            require(e['text'].strip()==expected,key+'_text')

    if family in ("object_size_estimation", "absolute_size_object", "relative_size_object"):
        wanted = [plan["a"], plan["b"]] if family == "relative_size_object" else [plan["a"]]
        measured = set()
        for op, args, _ in calls:
            if op != "dist": continue
            a, b = [points[l] for l in args["pts"]]
            require(a["object"] == b["object"] and a["iid"] == b["iid"] and a["object"] in wanted, "size_endpoint_identity")
            delta = np.asarray(b["f1"])-a["f1"]
            delta[1] *= -1
            world = scene.basis @ delta
            components = np.abs(scene.native[a["iid"]]["axes"] @ world)
            require(np.count_nonzero(components > .04) == 1, "size_diagonal_not_side")
            measured.add(a["object"])
        require(measured == set(wanted), "size_coverage")
    if family.startswith("object_rel_direction") or family in ("relative_direction_object", "absolute_direction_object", "route_planning"):
        correction_labels = {e["corrected_label"] for e in events if e["kind"] == "correction"}
        for label, point in points.items():
            if point["initial"]: continue
            uv, pool = eroded_pool(scene, point["iid"], point["frame"])
            require(len(pool) >= 3, "middle_pool_empty")
            centre = np.median(pool, axis=0) if directions else np.mean(pool, axis=0)
            if directions:
                index = np.flatnonzero(np.all(uv == point['uv'],axis=1))
                require(len(index)==1 and np.linalg.norm(pool[index[0]]-centre) <= np.linalg.norm(pool-centre,axis=1).min()+1e-7,"operand_not_median_proxy")
            require(np.linalg.norm(np.asarray(point["f1"])-centre) <= np.linalg.norm(pool-centre, axis=1).min()+.025,
                    "operand_not_middle")
    if family in ("object_counting", "absolute_count", "relative_count"):
        verify_counting(record, scene, points, plan)


def verify_counting(record, scene, points, plan):
    """Rebuild scan coverage, median clicks and temporal prose from GT, without generator helpers."""
    layout = record['head_layout']
    anchors = list(range(1,33) if layout=='per_frame' else range(2,33,2))
    require(list(scene.anchors)==anchors, 'missing_count_anchor_depth_pose')
    family = record['question_type']
    cats = [plan['a'],plan['b']] if family=='relative_count' else [plan['cat']]
    expected, floors = [], {}
    for cat in dict.fromkeys(cats):
        ids = scene.ids(cat,many=True)
        require(cat.strip().lower()!='object' and all(scene.native[i]['label'].strip().lower()!='object' for i in ids), 'count_catch_all_object')
        sightings = {}
        for k in anchors:
            seen = []
            for iid in ids:
                if np.count_nonzero(scene.gt.inst[k-1]==iid)*200 < scene.gt.H*scene.gt.W: continue
                uv,pool = eroded_pool(scene,iid,k)
                require(len(uv)>=3, 'unclickable_visible_instance')
                _,_,axes = np.linalg.svd(uv-uv.mean(0),full_matrices=False)
                proj = (uv-uv.mean(0))@axes[0]
                if np.linalg.norm(pool[int(proj.argmax())]-pool[int(proj.argmin())]) < .10: continue
                index = int(np.argmin(np.linalg.norm(pool-np.median(pool,axis=0),axis=1)))
                seen.append((iid,uv[index].tolist()))
            seen.sort(key=lambda item:(item[1][0],item[1][1],item[0]))
            sightings[k] = seen
            if not seen: continue
            para = []
            for start in range(0,len(seen),4):
                batch = seen[start:start+4]
                para.extend([('click',cat,k),('depth',cat,k,batch),('response',cat,k,batch)])
            para.append(('scan',cat,k,len(seen)))
            expected.append(para)
        empty = [k for k in anchors if not sightings[k]]
        if empty:
            spans = []
            groups = [[empty[0]]]
            for k in empty[1:]:
                if k-groups[-1][-1] == (1 if layout=='per_frame' else 2): groups[-1].append(k)
                else: groups.append([k])
            for g in groups: spans.append(str(g[0]) if len(g)==1 else f'{g[0]}-{g[-1]}')
            span = spans[0] if len(spans)==1 else ', '.join(spans[:-1])+' and '+spans[-1]
            text = f"{'Frame' if len(empty)==1 else 'Frames'} {span} {'shows' if len(empty)==1 else 'show'} no {noun(cat)}."
            expected.append([('text',text,'count_empty',{'object':cat,'frames':empty})])
        floor = max(len(seen) for seen in sightings.values())
        floors[cat] = floor
        require(len(ids)>=floor,'count_below_floor')
        k = next(k for k in anchors if len(sightings[k])==floor)
        expected.append([('text',f"The most {plural(cat,2)} visible together is {floor}, in frame {k}, so there {'is' if floor == 1 else 'are'} at least {floor}.",
                          'count_floor',{'object':cat,'count':floor,'frame':k})])
        video = f"Looking over the whole video, I count {len(ids)} {plural(cat,len(ids))}, which is at least the floor of {floor}, so there {'is' if len(ids) == 1 else 'are'} {len(ids)}."
        expected.append([('text',video,'count_video',{'object':cat,'count':len(ids)})] if family=='relative_count' else [('final',video)])
    require(record.get('count_branch')=='floor_then_video' and record.get('count_floor')==(floors if family=='relative_count' else floors[plan['cat']]), 'count_floor_metadata')
    if family=='relative_count': expected.append([('comparison',)])
    actual = list(event_paragraphs(record['events']))
    require(len(actual)==len(expected),'count_reasoning_paragraph')
    all_labels = []
    for para, want in zip(actual,expected):
        para = [e for e in para if e['kind']!='decision']
        require(len(para)==len(want),'count_reasoning_paragraph')
        for e,item in zip(para,want):
            kind = item[0]
            if kind=='click':
                _,cat,k = item
                require(e['kind']=='canonical_text' and e.get('click_object')=={'object':cat,'frame':k} and e['text'].strip()==f"I click the {noun(cat)} in frame {k}.", 'count_click_announcement')
            elif kind in ('depth','response'):
                _,cat,k,batch = item
                if kind=='depth':
                    require(e['kind']=='tool_call' and e.get('name')=='depth_at' and e.get('object')==cat and e['arguments']=={'frame':k,'pts':[uv for _,uv in batch]}, 'count_detection_coverage')
                else:
                    require(e['kind']=='tool_response' and e.get('name')=='depth_at' and len(e['points'])==len(batch), 'count_detection_coverage')
                    for printed,(iid,uv) in zip(e['points'],batch):
                        label = printed['label']; point = points[label]; all_labels.append(label)
                        require((point['object'],point['frame'],point['iid'],point['uv'],point['initial'])==(cat,k,iid,uv,False),'count_operand_not_median_proxy')
            elif kind=='scan':
                _,cat,k,n = item
                require(e['kind']=='canonical_text' and e.get('count_scan')=={'object':cat,'frame':k,'count':n} and e['text'].strip()==f"Frame {k} shows {n} {plural(cat,n)}.", 'count_scan_after_clicks')
            elif kind=='text':
                _,text,key,value = item
                require(e['kind']=='canonical_text' and e['text'].strip()==text and e.get(key)==value, 'count_reasoning_text')
            elif kind=='final':
                require(e['kind']=='canonical_text' and e['text'].strip()==item[1], 'count_reasoning_text')
            else:
                require(e['kind']=='canonical_text', 'count_reasoning_text')
    require(set(all_labels)==set(points) and len(all_labels)==len(points),'count_click_coverage')


def full_minimum(record, scene, calls, P, t):
    """The printed minimum of every closest/cam_dist call equals the complete eroded-pool minimum of its views."""
    from scipy.spatial import cKDTree

    def pool(label):
        iid, k = P[label]["iid"], P[label]["frame"]
        _, c = eroded_pool(scene, iid, k)
        require(len(c) >= 2, "insufficient_stable_points")
        return iid, k, c
    distance = t in ("object_abs_distance", "absolute_distance_object", "object_rel_distance", "relative_distance_object")
    camera = t == "camera_obj_abs_dist" or t.startswith("camera_obj_rel_dist")
    for name, args, value in calls:
        if name == "closest" and distance:
            ia, ka, A = pool(args["A"][0])
            ib, kb, B = pool(args["B"][0])
            multi = any(c['kind']=='surface_views' for c in record['private']['frame_choices'])
            if any(P[l]["iid"] != ia or (not multi and P[l]["frame"] != ka) for l in args["A"]) or any(P[l]["iid"] != ib or (not multi and P[l]["frame"] != kb) for l in args["B"]):
                raise Refusal("mixed_minimum_operand_identity")
            if multi:
                A = np.concatenate([pool(l)[2] for l in args['A']])
                B = np.concatenate([pool(l)[2] for l in args['B']])
            for side in ('A','B'):
                require(1 <= len(args[side]) <= (6 if t in ('object_rel_distance','relative_distance_object') and side=='A' else 3) and len({(P[l]['frame'],*P[l]['uv']) for l in args[side]}) == len(args[side]),'distance_candidate_count')
            full = float(cKDTree(B).query(A)[0].min())
            require(abs(value[2] - full) <= FULL_MIN_SLACK, "not_complete_eroded_minimum", f"{value[2]} vs {full:.3f}")
        elif name == "cam_dist" and camera:
            require(len(args['pts']) <= (6 if t=='camera_obj_abs_dist' else 3),'camera_candidate_count')
            if len(args['pts']) > 3:
                require(len({P[l]['iid'] for l in args['pts']}) == len(args['pts']),'camera_padding_candidates')
            require(args['pts'] == sorted(args['pts'], key=lambda l:digest([record['qid'],P[l]['iid'],P[l]['frame'],P[l]['uv']])),"camera_candidate_order")
            for iid, k in {(P[l]["iid"], P[l]["frame"]) for l in args["pts"]}:
                mine_labels=[l for l in args['pts'] if P[l]['iid']==iid and P[l]['frame']==k]
                require(1 <= len(mine_labels) <= 3 and len({tuple(P[l]['uv']) for l in mine_labels}) == len(mine_labels),'camera_candidate_count')
                _, _, C = pool(mine_labels[0])
                cam = np.asarray(replay_pose(scene, k, printed=False)["t"])
                full = float(np.linalg.norm(C - cam, axis=1).min())
                mine = min(value[2][l] for l in args["pts"] if P[l]["iid"] == iid and P[l]["frame"] == k)
                require(abs(mine - full) <= FULL_MIN_SLACK, "not_complete_eroded_minimum", f"{mine} vs {full:.3f}")
