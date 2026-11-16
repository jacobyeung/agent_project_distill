"""Add unique GT questions; retain every accepted source direction row."""
import itertools
import math
from collections import Counter

import numpy as np

from .common import Refusal, digest
from .replay import label_direction

DIRECTIONS = ("object_rel_direction_easy", "object_rel_direction_medium", "object_rel_direction_hard")


def targets(distribution, accepted, minimum=None):
    out = {}
    for t in DIRECTIONS:
        c = distribution[t]["content"]
        if any(type(n) is not int or n <= 0 for n in c.values()):
            raise ValueError("benchmark aggregate requires positive integer content counts")
        total = sum(c.values())
        observed = accepted.get(t, Counter())
        if set(observed)-set(c):
            raise ValueError("accepted direction label absent from benchmark aggregate")
        n = max([int((minimum or {}).get(t, 0)), sum(observed.values())]
                + [math.ceil(observed.get(label, 0)*total/count) for label, count in c.items()])
        out[t] = {label: max(observed.get(label, 0), math.ceil(n*count/total)) for label, count in c.items()}
    return out


def shortages(wanted, accepted):
    return {t: {label: max(0, n-accepted.get(t, {}).get(label, 0)) for label, n in c.items()}
            for t, c in wanted.items()}


def candidates(scene, alias, T, config):
    """Independent labels use native annotation centroids (canonical GT).

    These private reference values never replace observable point/depth readouts.
    A candidate survives only when its separate clicked-points program agrees.
    """
    labels, centres = [], {}
    for obj in sorted(set(scene.gt.labels)):
        try:
            iid, = scene.ids(obj)
            k = next(k for k in scene.anchors if scene.ground.masks(obj, k))
        except (Refusal, StopIteration, ValueError):
            continue
        native = scene.native[iid]
        centre = scene.basis.T @ (native["centroid"]-scene.origin)
        centre[1] = -centre[1]
        centres[obj] = {"point": centre.tolist(), "frame": k, "centroid_world": native["centroid"].tolist(),
                        "native_label": native["label"], "instance_id": iid}
        labels.append(obj)
    for t in DIRECTIONS:
        options = {"object_rel_direction_easy": ["left", "right"],
                   "object_rel_direction_medium": ["left", "right", "back"],
                   "object_rel_direction_hard": ["front-left", "front-right", "back-left", "back-right"]}[t]
        for stand, face, query in itertools.permutations(labels, 3):
            S, F, Q = [np.array(centres[x]["point"]) for x in (stand, face, query)]
            u, v = F-S, Q-S
            if min(np.linalg.norm(x[[0, 2]]) for x in (u, v)) < .01: continue
            dot, cross = u[0]*v[0]+u[2]*v[2], u[0]*v[2]-u[2]*v[0]
            theta = math.degrees(math.atan2(cross, dot))
            if any(abs(abs(theta)-b) < .6 for b in (0, 90, 135, 180)): continue
            label = label_direction(t, theta)
            suffix = ("left or right" if t.endswith("easy") else "left, right, or back" if t.endswith("medium")
                      else "front-left, front-right, back-left, or back-right")
            text = f"If I am standing by the {stand} and facing the {face}, is the {query} to my {suffix}?"
            if t.endswith("medium"): text += " Back means a turn of at least 135 degrees."
            qid = "gt-"+digest([scene.entry["physical_group"], scene.entry["canonical"], scene.entry["frame_indices"], t, text])[:32]
            yield {"qid": qid, "scene": alias, "question_type": t, "answer": chr(65+options.index(label)),
                   "student_input": {"question": text, "options": [f"{chr(65+i)}. {x}" for i, x in enumerate(options)],
                                     "frame_indices": scene.entry["frame_indices"]},
                   "infrastructure_only": bool(scene.entry.get("infrastructure_only")),
                   "generated_gt": {"method": "native_annotation_centroid_v1", "label": label,
                                    "theta_degree": theta, "dot_m2": dot, "cross_m2": cross,
                                    "objects": {x: centres[x] for x in (stand, face, query)},
                                    "native_annotations": scene.entry["native_annotations"],
                                    "source_box_convention": {key: scene.native_source.get(key) for key in ("box_convention", "provider_axesLengths", "released_boxes", "obb_estimator_used")},
                                    "gt": scene.entry["gt"]}}, label
