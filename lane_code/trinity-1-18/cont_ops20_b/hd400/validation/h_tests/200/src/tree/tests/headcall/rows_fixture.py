"""Templated head-call rows built the way the converters build them (calls, ⟦R⟧/⟦D⟧ template, derived items)."""
from headcall import derive as D
from headcall.protocol import Call, PoseValue, format_value, render_call


def record_of(index, call, value):
    if call.name == "depth":
        gt = {"depth_m": value}
    else:
        gt = {"position_m": list(value.position), "heading_deg": value.heading_deg, "pitch_deg": value.pitch_deg,
              "roll_deg": value.roll_deg, "view_deg": list(value.view_deg) if value.view_deg else None}
    return {"index": index, "name": call.name, "frame": call.frame, "point": list(call.point) if call.point else None,
            "gt": gt, "response": format_value(call.name, value), "source": {"kind": "object"}}


def build(lines, calls, derived, answer, category="object_abs_distance", options=(), qid="q1"):
    """lines: template lines where {c<i>} is call i's exchange and {d<k>} derived item k."""
    records = [record_of(i, call, value) for i, (call, value) in enumerate(calls)]
    exchanges = {"c%d" % i: render_call(call) + D.response_marker(i) for i, (call, _) in enumerate(calls)}
    marks = {"d%d" % k: D.marker("D", k) for k in range(len(derived))}
    think = "\n".join(line.format(**dict(exchanges, **marks)) for line in lines)
    template = "<think>\n" + think + "\n</think>\n\n" + answer
    texts, _ = D.evaluate(derived, D.values_of([r["name"] for r in records], [r["response"] for r in records]))
    for item, text in zip(derived, texts):
        item["text"] = text
    target = D.render(template, [r["response"] for r in records], texts)
    return {"qid": qid, "category": category, "answer": answer, "options": list(options), "target": target,
            "target_template": template, "head_calls": records, "head_derived": derived}


def distance_row(qid="q1"):
    calls = [(Call("pose", 4, None), PoseValue((0.12, -0.43, 0.3), -117.2, -12.6, 1.4, (58.0, 45.0))),
             (Call("depth", 4, (215, 529)), 0.862),
             (Call("pose", 10, None), PoseValue((0.80, 0.20, 0.25), 20.0, -5.0, 0.0, (58.0, 45.0))),
             (Call("depth", 10, (700, 120)), 3.415)]
    derived = [{"kind": "point", "pose": 0, "depth": 1, "at": [215, 529], "object": "chair"},
               {"kind": "point", "pose": 2, "depth": 3, "at": [700, 120], "object": "lamp"},
               {"kind": "distance", "points": [0, 1], "unit": "m"}]
    lines = ["Step 1: find the chair and the lamp.", "locate the chair: {c0} {c1} {d0}",
             "locate the lamp: {c2} {c3} {d1}", "Step 2: measure the distance between the located points: {d2}."]
    printed = build(lines, calls, [dict(d) for d in derived], "0", qid=qid)["head_derived"][2]["text"]
    return build(lines, calls, derived, printed[:-len(" m")], qid=qid)  # the GT answer equals the derived distance


def closest_row(qid="q3"):
    """Which of the lamp and the plant is closest to the chair (all on frame 2)."""
    view = (60.0, 46.0)
    calls = [(Call("pose", 2, None), PoseValue((0.0, 0.0, 0.0), 0.0, 0.0, 0.0, view)),
             (Call("depth", 2, (500, 500)), 2.0),
             (Call("depth", 2, (520, 500)), 2.2),
             (Call("depth", 2, (100, 300)), 4.0)]
    derived = [{"kind": "point", "pose": 0, "depth": 1, "at": [500, 500], "object": "chair", "role": "anchor"},
               {"kind": "point", "pose": 0, "depth": 2, "at": [520, 500], "object": "lamp", "role": "candidate"},
               {"kind": "point", "pose": 0, "depth": 3, "at": [100, 300], "object": "plant", "role": "candidate"},
               {"kind": "closest", "anchors": [0], "candidates": [["lamp", 1], ["plant", 2]], "unit": "m"}]
    lines = ["Step 1: find the chair and each candidate.", "locate the chair: {c0} {c1} {d0}",
             "locate the lamp: {c2} {d1}", "locate the plant: {c3} {d2}",
             "Step 2: measure the distance from the chair to each candidate's located point: {d3}."]
    return build(lines, calls, derived, "A", category="object_rel_distance", options=["A. lamp", "B. plant"], qid=qid)


def motion_row(qid="q4", category="camera_movement_direction"):
    """The camera between frames 2 and 8: 1.5 m forward and 0.4 m right of frame 2's heading."""
    view = (60.0, 46.0)
    calls = [(Call("pose", 2, None), PoseValue((0.10, 0.20, 0.0), 30.0, -5.0, 0.0, view)),
             (Call("pose", 8, None), PoseValue((0.10 - 1.5 * 0.5 + 0.4 * 0.8660254, 0.20 + 1.5 * 0.8660254 + 0.4 * 0.5,
                                                -0.05), 10.0, -3.0, 0.0, view))]
    derived = [{"kind": "ego_motion", "from": 0, "to": 1}]
    if category == "camera_movement_direction":
        derived.append({"kind": "movement_direction", "motion": 0})
        answer, options = "B", ["A. Left", "B. Forward", "C. Right"]
    else:
        derived.append({"kind": "displacement", "motion": 0, "unit": "m"})
        answer, options = "1.55", []
    lines = ["Step 1: read the camera pose at frames 2 and 8.", "camera at frame 2: {c0}", "camera at frame 8: {c1}",
             "Step 2: from frame 2 to frame 8, {d0}.", "{d1}."]
    return build(lines, calls, derived, answer, category=category, options=options, qid=qid)


def direction_row(qid="q2"):
    """Standing at the stool facing the desk, the plant is front-left (derived angle about +27 degrees)."""
    view = (60.0, 46.0)
    calls = [(Call("pose", 2, None), PoseValue((0.0, 0.0, 0.0), 0.0, 0.0, 0.0, view)),
             (Call("depth", 2, (500, 500)), 1.0),
             (Call("depth", 2, (500, 400)), 3.0),
             (Call("depth", 2, (300, 500)), 2.5)]
    derived = [{"kind": "point", "pose": 0, "depth": 1, "at": [500, 500], "object": "stool"},
               {"kind": "point", "pose": 0, "depth": 2, "at": [500, 400], "object": "desk"},
               {"kind": "point", "pose": 0, "depth": 3, "at": [300, 500], "object": "plant"},
               {"kind": "relative_direction", "points": [0, 1, 2]}]
    lines = ["Step 1: locate the stool, the desk and the plant.", "locate the stool: {c0} {c1} {d0}",
             "locate the desk: {c2} {d1}", "locate the plant: {c3} {d2}",
             "Step 2: standing at the stool and facing the desk, the plant lies {d3}.",
             "So the plant is at my front-left."]
    return build(lines, calls, derived, "A", category="object_rel_direction_hard",
                 options=["A. front-left", "B. front-right", "C. back-left", "D. back-right"], qid=qid)
