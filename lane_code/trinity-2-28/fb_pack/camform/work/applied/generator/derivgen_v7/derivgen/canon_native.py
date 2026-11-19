"""Independent native label evidence for externally supplied GT additions.

This is private label authority. No value here is a public head measurement.
The producer accepts an addition only after its separate observable trace agrees.
"""
import math
import numpy as np

from .bindings import F17, gt_label, question
from .common import Refusal, defer, digest
from .replay import argbest, native_reference, quantize, replay_move, replay_pose, require


def reference(scene, T, q, plan):
    family = q["question_type"]
    mapped = {"object_counting": "absolute_count", "object_size_estimation": "absolute_size_object",
              "object_abs_distance": "absolute_distance_object", "object_rel_distance": "relative_distance_object"}
    if family in F17 or family in mapped or family.startswith("object_rel_direction"):
        value = native_reference(scene, T, {**q, "question_type": mapped.get(family, family)}, plan)["value"]
    elif family in ("camera_rotation", "camera_displacement", "camera_movement_direction"):
        i, j = plan["i"], plan["j"]  # Source truth uses exact requested frames.
        if family == "camera_rotation":
            a, b = replay_pose(scene, i)["yaw"], replay_pose(scene, j)["yaw"]
            value = (b-a+180) % 360-180
            if value == -180: value = 180
        else:
            delta, distance, _ = replay_move(scene, i, j)
            if family == "camera_displacement": value = distance
            else:
                scores = {"forward": delta[2], "backward": -delta[2], "right": delta[0], "left": -delta[0]}
                labels = [s.strip().lower() for s in T.option_texts(q["options"]).values()]
                value = argbest([scores[s] for s in labels], labels, largest=True)
    elif family == "camera_obj_abs_dist" or family.startswith("camera_obj_rel_dist"):
        camera = scene.gt.cam(plan["k"])[1]
        def distance(obj):
            boxes = [{"centroid": scene.native[i]["centroid"], "axesLengths": scene.native[i]["lengths"],
                      "normalizedAxes": scene.native[i]["axes"]} for i in scene.ids(obj, many=True)]
            return T.point_obb_dist(camera, boxes)
        if family == "camera_obj_abs_dist": value = distance(plan["obj"])
        else: value = argbest([distance(o) for o in plan["cands"]], plan["cands"])
    elif family == "room_size_estimation":
        # A separate native whole-scene polygon is essential; the reviewed clicks
        # alone cannot act as both the measurement and its independent authority.
        polygon = scene.native_source.get("whole_scene_floor_polygon_world")
        if polygon is None: defer("missing_native_whole_scene_floor_polygon")
        xyz = np.asarray(polygon, float)
        require(xyz.ndim == 2 and xyz.shape[1] == 3 and len(xyz) >= 3 and np.isfinite(xyz).all(), "native_floor_polygon_schema")
        from .canon_check import validate_polygon
        validate_polygon(xyz[:, [0, 2, 1]].tolist())  # Native world is z up.
        value = abs(sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(xyz, np.roll(xyz, -1, axis=0))))/2
    elif family == "obj_appearance_order":
        from .replay import appearance_ids
        first = [next((k for k in range(1, 33) if appearance_ids(scene, o, k)), None) for o in plan["cats"]]
        require(None not in first and len(set(first)) == len(first), "native_appearance_tie")
        value = ", ".join(o for _, o in sorted(zip(first, plan["cats"])))
    elif family.startswith("obj_obj_relative_pos"):
        R, camera = scene.gt.cam(plan["k"])
        a, b = [scene.native[scene.ids(plan[key])[0]]["centroid"] for key in ("a", "ref")]
        if family.endswith("_nf"):
            value = argbest([np.linalg.norm(a-camera), np.linalg.norm(b-camera)], ["near", "far"])
        elif family.endswith("_lr"):
            value = argbest([(R.T @ (a-camera))[0], (R.T @ (b-camera))[0]], ["left", "right"])
        else: value = argbest([a[2], b[2]], ["up", "down"], largest=True)
    elif family == "route_planning":
        def centre(o):
            point = scene.native[scene.ids(o)[0]]["centroid"]
            return ((point-scene.origin) @ scene.basis)[[0, 2]]
        here, heading, turns = centre(plan["start"]), centre(plan["face"])-centre(plan["start"]), []
        for index, (kind, obj) in enumerate(plan["plan"]):
            if kind == "go":
                target = centre(obj); heading, here = target-here, target
            else:
                target = next((o for k, o in plan["plan"][index+1:] if k == "go"), None)
                require(target is not None, "underspecified_route")
                vector = centre(target)-here
                require(np.linalg.norm(heading) > 1e-6 and np.linalg.norm(vector) > 1e-6, "native_degenerate_heading")
                theta = math.degrees(math.atan2(heading[0]*vector[1]-heading[1]*vector[0], heading @ vector))
                require(abs(theta) > .5, "native_zero_turn")
                turns.append("Turn Back" if abs(theta) >= 135 else "Turn Left" if theta > 0 else "Turn Right")
                heading = vector
        value = ", ".join(turns)
    else: raise Refusal("unsupported_native_label_family", family)
    return {"method": "native_source_reference_v1", "question_sha256": digest(q), "bindings_sha256": digest(plan),
            "gt": scene.entry["gt"], "native_annotations": scene.entry["native_annotations"], "value": value,
            "source_box_convention": {k: scene.native_source.get(k) for k in
                ("box_convention", "provider_axesLengths", "released_boxes", "obb_estimator_used")}}


def verify(evidence, scene, T, source, plan, display):
    expected = reference(scene, T, question(source), plan)
    if evidence != expected:
        from .bindings import bind, label_typo_fixes, fix_label_typos
        require(bool(label_typo_fixes(source)), "generated_GT_native_reference")
        original = question(source, fix_typos=False)
        original_plan = bind(original, T)
        original_reference = reference(scene, T, original, original_plan)
        normalize = lambda v: fix_label_typos(v) if isinstance(v, str) else v
        require(evidence == original_reference and normalize(expected['value']) == normalize(original_reference['value']),
                "generated_GT_native_reference")
    if display:
        require(quantize(gt_label(source), display["decimals"]) == quantize(expected["value"]*display["factor"], display["decimals"]),
                "native_source_label_mismatch")
    else:
        require(T.letter_of(question(source)["options"], expected["value"]) == gt_label(source), "native_source_label_mismatch")
