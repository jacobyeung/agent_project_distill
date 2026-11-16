"""SPEC v3.8 canonical derivations from native GT.

Each row is a natural plan paragraph followed by one paragraph per step. Every number the
student reads comes from a printed head readout (labelled depth_at points, move, pose) or
from the fixed calculator layer (dist, closest, cam_dist, angle, area, turn) applied to
point labels. Text keeps only the plan, the click choices, comparisons, unit lines and
the final option choice.
"""
import math
import re
from collections import OrderedDict

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull, cKDTree

from .bindings import (F17, bind, question, unit_policy, is_generic_label, object_labels,
                       label_typo_fixes, normalized_reviewed)
from .calculator import CalculatorError, PrintedPointRegistry, format_command
from .common import Refusal, defer, digest
from .camera_policy import direction_margins, motion_reason
from .plan_contract import opening_text, enrich_opening, noun, plural, frame_look

FORM = "spec-v3.8-calculator-v2"
MIN_POOL = 3
SIGN_RULE = ("On the frame-1 floor (x right, z forward, y up) the calculator uses u = F - S and v = Q - S; "
             "cross = u_x*v_z - u_z*v_x > 0 means left and dot = u_x*v_x + u_z*v_z > 0 means front.")


def r2(x): return round(float(x), 2) + 0.0
def r4(x): return round(float(x), 4) + 0.0
def f2(x): return f"{r2(x):.2f}"
def f4(x): return f"{r4(x):.4f}"
def s2(x): return f"{r2(x):+.2f}"
def vec(p): return "(" + ", ".join(f2(x) for x in p) + ")"
def wrap(deg): return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180


def boundary_margin(theta, rule):
    if rule == "absolute": return None
    boundaries = (0, 90, -90, 180) if rule == "hard" else (0, 135, -135) if rule == "medium" else (0, 180)
    return min(abs(wrap(theta-boundary)) for boundary in boundaries)


def spread_limit(uv):
    return .10 if min(*uv, *(1000-x for x in uv)) <= 40 else .25


def innermost_uv(gt, mask):
    """Return the visible-mask point farthest from its outline, including the image border."""
    y, x = np.unravel_index(int(np.argmax(ndimage.distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1])), mask.shape)
    return [int(round((x+.5)/gt.W*1000)), int(round((y+.5)/gt.H*1000))]


def image_region(uv, middle):
    horizontal = "left" if uv[0] < middle[0] else "right" if uv[0] > middle[0] else "same column"
    vertical = "upper" if uv[1] < middle[1] else "lower" if uv[1] > middle[1] else "same row"
    return horizontal + ", " + vertical


class Fixed:
    """Adapter over the shared printed-point-calculator-v3.

    All point arithmetic, including waypoint turns, uses the shared calculator.
    """

    def __init__(self, requested=()):
        self.reg, self.requested, self.f1 = PrintedPointRegistry(), set(requested), {}
        self.last_point = None

    def register(self, label, cam, f1, spread, requested_frame, actual_frame):
        try:
            point = self.reg.register(camera=cam, f1=f1, spread=spread, requested_frame=requested_frame,
                                      actual_frame=actual_frame, label=label)
        except CalculatorError as e:
            raise Refusal("calculator_" + e.reason) from e
        self.last_point = point
        self.f1[label] = f1
        return point["line"]

    def run(self, name, args):
        keys = {"dist": lambda a: {"a": a["pts"][0], "b": a["pts"][1]}, "closest": lambda a: {"A": a["A"], "B": a["B"]},
                "cam_dist": lambda a: {"points": a["pts"]}, "angle": lambda a: {k: a[k] for k in ("S", "F", "Q", "rule")},
                "area": lambda a: {"C": a["C"]}, "turn": lambda a: a}
        try:
            command = format_command(name, **keys[name](args))
            out = self.reg.execute(command)
        except CalculatorError as e:
            raise Refusal("calculator_" + e.reason, name) from e
        self.last = out
        r = out["result"]
        if name == "dist": value = float(r["value"])
        elif name == "closest": value = (r["witness"]["a"], r["witness"]["b"], float(r["value"]))
        elif name == "cam_dist": value = (r["witness"]["point"], float(r["value"]), {x["point"]: float(x["value"]) for x in r["points"]})
        elif name in ("angle", "turn"): value = (tuple(r["u"]), tuple(r["v"]), float(r["dot"]), float(r["cross"]), int(r["theta"]), r["label"])
        else: value = float(r["value"])
        return command, out["text"], value


def token(name, args):
    if name == "depth_at":
        image = f" image_frame={args['image_frame']}" if "image_frame" in args else ""
        pts = "[" + ",".join(f"[{u},{v}]" for u, v in args["pts"]) + "]"
        return f"<depth_at frame={args['frame']}{image} pts={pts}>"
    if name == "turn" and "at" not in args: return f"<turn from={args['from']} to={args['to']}>"
    if name == "move": return f"<move from={args['from']} to={args['to']}>"
    if name == "pose": return f"<pose frame={args['frame']}>"
    if name == "dist": return f"<dist {args['pts'][0]} {args['pts'][1]}>"
    if name == "closest": return f"<closest A={','.join(args['A'])} B={','.join(args['B'])}>"
    if name == "cam_dist": return f"<cam_dist {','.join(args['pts'])}>"
    if name == "angle": return f"<angle S={args['S']} F={args['F']} Q={args['Q']} rule={args['rule']}>"
    if name == "turn": return f"<turn from={args['from']} at={args['at']} to={args['to']}>"
    if name == "area": return f"<area C={','.join(args['C'])}>"
    raise Refusal("unknown_tool", name)


class Writer:
    def __init__(self):
        self.paras, self.calls = [[]], []

    def say(self, text, **metadata):
        self.paras[-1].append(("text", text, metadata))

    def call(self, name, args, response, meta=None, text=None):
        call_id = "c" + str(len(self.calls) + 1)
        text = text or token(name, args)
        self.calls.append({"kind": "tool_call", "call_id": call_id, "name": name, "arguments": args, "token": text,
                           "response": response, **(meta or {})})
        self.paras[-1].append(("call", text, response, call_id))
        return call_id

    def para(self):
        if self.paras[-1]: self.paras.append([])

    def render(self, answer):
        from .canon_render import render
        events = []
        calls = {c["call_id"]: c for c in self.calls}
        for i, para in enumerate(p for p in self.paras if p):
            if i: events.append({"role": "assistant", "kind": "canonical_paragraph", "target_loss": 1})
            for j, seg in enumerate(para):
                prefix = " " if j else ""
                if seg[0] == "text":
                    events.append({"role": "assistant", "kind": "canonical_text", "target_loss": 1,
                                   "text": prefix + seg[1] if seg[1] else "", **seg[2]})
                else:
                    c = calls[seg[3]]
                    calc = c["name"] in ("dist", "closest", "cam_dist", "angle", "turn", "area") and not (c["name"] == "turn" and "at" not in c["arguments"])
                    call = {"role": "assistant", "target_loss": 1, "call_id": c["call_id"], "prefix": prefix}
                    if calc:
                        events.append({**call, "kind": "calculator_call", "command": c["token"]})
                        events.append({"role": "tool", "target_loss": 0, "kind": "calculator_response",
                                       "call_id": c["call_id"], "response": c["data"]})
                    else:
                        events.append({**call, "kind": "tool_call", "name": c["name"], "arguments": c["arguments"],
                                       "token": c["token"], "object": c.get("object")})
                        events.append({"role": "tool", "target_loss": 0, "kind": "tool_response",
                                       "call_id": c["call_id"], "name": c["name"], "text": c["response"], **c["data"]})
        self.events = events
        projection = render(events, answer)
        return projection["target"], projection["tool_output_spans"]


def poss(name):
    return noun(name) + ("'" if name.endswith("s") else "'s")


def join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


class Canon:
    def __init__(self, scene, T, config, row, reviewed=None, exact=False):
        reviewed = normalized_reviewed(row, reviewed)
        self.scene, self.T, self.config, self.row, self.exact = scene, T, config, row, exact
        self.fixed = Fixed(config.get("requested_bindings", ()))
        self.q = question(row)
        self.t = self.q["question_type"]
        self.plan = bind(self.q, T, reviewed)
        self.reviewed = reviewed
        self.scene = scene
        self.scene.referent_ids = self.plan.get("referent_ids", {})
        self.w = Writer()
        self.P, self.n = {}, 0
        self.raw_P = {}
        self.pools, self.private = {}, {"clicks": [], "frame_choices": [], "gt_reference": {}}
        self.gt = scene.gt
        self.layout = config.get("head_layout", "paired_anchor")
        if self.layout not in ("paired_anchor", "per_frame"): raise Refusal("head_layout")
        self.scene.head_layout = self.layout
        self.anchors = [k for k in range(1 if self.layout == "per_frame" else 2, 33, 1 if self.layout == "per_frame" else 2) if self.gt.has(k)]
        self.scene.anchors = self.anchors
        self.substituted = {}
        self.corrected = set()
        self.rejected_pixels = {}
        self.measured_pairs = set()

    # ------------------------------------------------------------------ GT-side selection
    def area(self, iid, k):
        areas = self.scene.__dict__.setdefault("_canon_areas", {})
        if k not in areas:
            ids, counts = np.unique(self.gt.inst[k - 1], return_counts=True)
            areas[k] = {int(i): int(c) for i, c in zip(ids, counts)}
        return areas[k].get(int(iid), 0)

    def f1_of_world(self, world):
        c = (np.asarray(world, float) - self.scene.origin) @ self.scene.basis
        c[..., 1] *= -1
        return c

    def pool(self, iid, k):
        pools = self.scene.__dict__.setdefault("_canon_pools", OrderedDict())
        key = (int(iid), k)
        if key not in pools:
            try:
                uv, world = self.scene.candidates(iid, k, complete=True, canonical=True)
            except Refusal:
                pools[key] = None
            else:
                pools[key] = (np.asarray(uv), self.f1_of_world(world)) if len(uv) >= MIN_POOL else None
            while len(pools) > 256: pools.popitem(last=False)
        pools.move_to_end(key)
        return pools[key]

    def visible(self, iid, frames=None):
        return [k for k in (frames or self.anchors) if self.area(iid, k) >= self.scene.programs.MIN_PX]

    def usable(self, iid, k):
        return self.area(iid, k) >= self.scene.programs.MIN_PX and self.pool(iid, k) is not None

    def best_frame(self, iid):
        for k in sorted(self.visible(iid), key=lambda k: (-self.area(iid, k), k)):
            if self.usable(iid, k): return k
        raise Refusal("no_supported_visible_frame", str(iid))

    def middle_uv(self, iid, k):
        uv, P = self.pool(iid, k)
        return uv[int(np.argmin(np.linalg.norm(P - (np.median(P, axis=0) if self.t.startswith("object_rel_direction") or self.t in ("relative_direction_object", "absolute_direction_object") else P.mean(0)), axis=1)))].tolist()

    def facing_uv(self, iid, k, oid, ok, n=3):
        uv, P = self.pool(iid, k)
        _, Q = self.pool(oid, ok)
        d = cKDTree(Q).query(P)[0]
        order = np.argsort(d, kind="stable")
        band = order[:max(n, (len(order)+2)//3)]
        return self.spaced_pixels(uv[band], d[band], n, k=k), float(d.min())

    def near_camera_uv(self, iid, k, n=3):
        uv, P = self.pool(iid, k)
        cam = self.scene.pose(k)["camera_t_L1"]
        d = np.linalg.norm(P - np.asarray(cam), axis=1)
        order = np.argsort(d, kind="stable")
        band = order[:max(n, (len(order)+2)//3)]
        chosen = self.spaced_pixels(uv[band], d[band], n, k=k)
        chosen.sort(key=lambda p: digest([self.row["qid"], iid, k, p]))
        return chosen, float(d.min())

    @staticmethod
    def spread_candidates(uv, distances, n):
        # Keep the actual minimum, then cover the nearest-side band in image space.
        order = np.argsort(distances, kind="stable")
        band = order[:max(n, (len(order)+2)//3)]
        chosen = [int(order[0])]
        while len(chosen) < min(n, len(band)):
            gap = np.min(np.linalg.norm(uv[band, None]-uv[chosen], axis=2), axis=1)
            index = int(band[np.argmax(gap)])
            if index in chosen: break
            chosen.append(index)
        
        return [uv[i].tolist() for i in chosen]

    def count_extent_uv(self, iid, k):
        uv, P = self.pool(iid, k)
        _, _, axes = np.linalg.svd(uv-uv.mean(0), full_matrices=False)
        projection = (uv-uv.mean(0)) @ axes[0]
        lo, hi = int(projection.argmin()), int(projection.argmax())
        return [uv[lo].tolist(), uv[hi].tolist()], float(np.linalg.norm(P[hi]-P[lo]))

    def extent_uv(self, iid, k):
        # Native axes choose a side, never a public length. Both public endpoints
        # still come from the complete stable visible surface and depth readouts.
        uv, points = self.pool(iid, k)
        axes = np.asarray(self.scene.native[iid]["axes"]).reshape(3, 3)
        native = self.scene.native[iid]
        world = points.copy(); world[:, 1] *= -1
        world = world @ self.scene.basis.T + self.scene.origin
        local = (world - native["centroid"]) @ axes.T
        def pair(axis):
            other = [j for j in range(3) if j != axis]
            # A narrow strip through the face gives paired endpoints of one side.
            centre = local[np.argmin(np.linalg.norm(local - np.median(local, axis=0), axis=1))]
            allowed = np.flatnonzero(np.max(np.abs(local[:, other]-centre[other]), axis=1) <= .015)
            if len(allowed) < 2: raise Refusal("missing_visible_side_endpoints")
            lo, hi = allowed[np.argmin(local[allowed, axis])], allowed[np.argmax(local[allowed, axis])]
            if lo == hi: raise Refusal("missing_visible_side_endpoints")
            return [uv[lo].tolist(), uv[hi].tolist()], float(np.linalg.norm(points[hi]-points[lo]))
        axis = int(np.argmax(native["lengths"]))
        ends, length = pair(axis)
        vertical_axis = int(np.argmax(np.abs(axes[:, 2])))
        vertical, height = pair(vertical_axis) if vertical_axis != axis else (ends, 0.)
        return ends, vertical, length, height

    # ------------------------------------------------------------------ printed tools
    def eff(self, k, depth=True):
        if type(k) is not int or not 1 <= k <= 32: raise Refusal("frame_out_of_range")
        if self.exact or self.layout == "per_frame" or k % 2 == 0: return k
        self.substituted[k] = k + 1
        return k + 1

    def replacement_pixels(self, iid, k, pts):
        required = len(pts) if self.t in ('object_size_estimation', 'absolute_size_object', 'relative_size_object') else 1
        scale = np.array([self.gt.W, self.gt.H])/1000
        for initial in self.rejected_pixels.get((iid, k), []):
            def allowed(point):
                delta = np.asarray(point)-initial
                return (np.linalg.norm(delta*scale) >= 40 and np.linalg.norm(delta) >= 40
                        and (spread_limit(initial) != .10 or min(*point, *(1000-x for x in point))
                             > min(*initial, *(1000-x for x in initial))))
            pts = [point for point in pts if allowed(point)]
        if len(pts) < required: raise Refusal("reclick_exclusion")
        return pts

    def depth_at(self, obj, iid, k, pts, requested=None, evidence=False, announce=True, _continuation=False):
        if not evidence:
            pts = self.replacement_pixels(iid, k, pts)
        if not evidence and (iid, k) not in self.corrected:
            self.corrected.add((iid, k))
            selected = int(digest([self.row["qid"], obj, k]), 16) % 10 == 0
            if selected and self.config.get("edge_correction") and not self.exact:
                correction = self.scene.edge_example(iid, k, [pts[0]], canonical=True)
                if correction:
                    initial = correction[0]
                    self.rejected_pixels.setdefault((iid, k), []).append(initial)
                    pts = self.replacement_pixels(iid, k, pts)
                    first = self.depth_at(obj, iid, k, [initial], requested, evidence=True, announce=announce)[0]
                    spread_node = self.w.calls[-1]["call_id"]+".spread"
                    goal = f"another point on the {noun(obj)}"
                    self.w.say(f"The spread is {f2(self.P[first]['spread'])}, above {f2(spread_limit(initial))}, so this click is probably on an edge; I click {goal}, at {pts[0]}.",
                               kind="correction", initial=initial, next=pts[0],
                               initial_label=first, corrected_label=f"P{self.n+1}", frame=k, spread_node=spread_node, goal="replacement")
                    announce = False
        if len(pts) > 4:
            return [label for start in range(0, len(pts), 4)
                    for label in self.depth_at(obj, iid, k, pts[start:start+4], requested, evidence,
                                               announce=announce and start == 0, _continuation=start > 0)]
        # Preserve the binding event even when another sentence already states the click.
        if not announce and not _continuation:
            self.w.say("", click_object={"object": obj, "frame": k}, click_covered=True)
        if announce:
            self.w.say(f"I click the {noun(obj)} in frame {k}.", click_object={"object": obj, "frame": k})
        self.check_click_spacing(k, pts)
        pose = self.scene.pose(k)
        lines, labels, published, values = [], [], [], {}
        call_id = "c" + str(len(self.w.calls) + 1)
        for uv in pts:
            if not all(20 <= x <= 980 for x in uv): raise Refusal("depth_click_border")
            v = self.scene.readout(iid, k, uv)
            if v["spread"] > spread_limit(uv) and not evidence: raise Refusal("unstable_measurement_click")
            x, y = self.gt.px([uv])
            if not evidence and ndimage.distance_transform_edt(self.gt.inst[k-1] == iid)[y[0], x[0]] < 3:
                raise Refusal("click_not_inside_eroded_mask")
            if evidence and v["spread"] <= spread_limit(uv): raise Refusal("correction_trigger")
            f1 = np.asarray(pose["camera_R_L1"]) @ np.asarray(v["camera"]) + np.asarray(pose["camera_t_L1"])
            self.n += 1
            label = f"P{self.n}"
            self.raw_P[label] = np.asarray(self.gt.lift(k, [uv])[0][0], dtype=float)
            cam, f1 = [r2(x*s) for x, s in zip(v["camera"], (1, -1, 1))], [r2(x) for x in f1]
            self.P[label] = {"object": obj, "frame": k, "uv": [int(uv[0]), int(uv[1])], "cam": cam, "f1": f1, "spread": r2(v["spread"])}
            self.private["clicks"].append({"label": label, "object": obj, "instance_id": int(iid), "frame": k, "uv": self.P[label]["uv"], "correction_initial": evidence})
            lines.append(self.fixed.register(label, cam, f1, r2(v["spread"]), requested or k, k))
            published.append(self.fixed.last_point)
            prefix = "" if len(pts) == 1 else str(len(labels))+"."
            for key, value, unit in (("camera", cam, "m"), ("f1", f1, "m"), ("spread", r2(v["spread"]), "1")):
                values[call_id+"."+prefix+key] = {"value": value, "unit": unit}
            labels.append(label)
        args = {"frame": requested or k, "pts": [[int(u), int(v)] for u, v in pts]}
        if requested and requested != k: args["image_frame"] = k
        self.w.call("depth_at", args, "\n".join(lines), {"object": obj, "data": {"points": published, "values": values}})
        return labels

    def camera_admission(self, i, j):
        ri, ti = self.gt.cam(i)
        rj, tj = self.gt.cam(j)
        delta = np.asarray(tj) - np.asarray(ti)
        a, b = np.asarray(ri)[:2,2], np.asarray(rj)[:2,2]
        yaw = math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0], float(a@b)))
        reason = motion_reason(self.t, distance=float(np.linalg.norm(delta)),
                               horizontal=float(np.linalg.norm(delta[:2])), yaw=yaw)
        if reason:
            raise Refusal(reason)

    def move(self, i, j):
        pi, pj = self.scene.pose(i), self.scene.pose(j)
        local = np.asarray(pi["level_R_L1"]).T @ (np.asarray(pj["camera_t_L1"]) - np.asarray(pi["camera_t_L1"]))
        dist = float(np.linalg.norm(local))
        local[1] *= -1
        text = f"dx = {s2(local[0])} m, dy = {s2(local[1])} m, dz = {s2(local[2])} m, distance = {f2(dist)} m"
        l1 = getattr(self.scene, "l1", None)
        # P1 formats a vector in its caller's representation. Supply public y up;
        # retain exact comparison of all components and the fixed-layer norm.
        if l1 is not None and l1.format_move(local) != text: raise Refusal("p1_v2_move_format_mismatch")
        cid = "c" + str(len(self.w.calls)+1)
        self.w.call("move", {"from": i, "to": j}, text, {"data": {"values": {
            cid+".delta": {"value": [r2(x) for x in local], "unit": "m"},
            cid+".distance": {"value": r2(dist), "unit": "m"}}}})
        return {"dx": r2(local[0]), "dy": r2(local[1]), "dz": r2(local[2]), "distance": r2(dist)}

    def pose(self, k):
        p = self.scene.pose(k)
        cid = "c" + str(len(self.w.calls)+1)
        self.w.call("pose", {"frame": k}, f"f1 centre {vec(p['camera_t_L1'])} m, yaw {p['yaw_degree']} deg", {"data": {"values": {
            cid+".t": {"value": [r2(x) for x in p["camera_t_L1"]], "unit": "m"},
            cid+".yaw": {"value": int(p["yaw_degree"]), "unit": "degree"}}}})
        return {"t": [r2(x) for x in p["camera_t_L1"]], "yaw": int(p["yaw_degree"])}

    def calc(self, name, **args):
        command, text, value = self.fixed.run(name, args)
        self.w.call(name, args, text, {"data": self.fixed.last}, text=command)
        return value

    # ------------------------------------------------------------------ frame choice
    def pair_rank(self, i, j):
        # Preserve the private census tuple's frame offsets without reading a head.
        return abs(i-j), 0, 0

    def turn_value(self, i, j):
        a, b = (np.asarray(self.scene.pose(k)["level_R_L1"])[[0, 2], 2] for k in (i, j))
        return wrap(round(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0], float(a@b)))))

    def camera_turn(self, i, j):
        turn = self.turn_value(i, j)
        cid = "c"+str(len(self.w.calls)+1)
        self.w.call("turn", {"from": i, "to": j}, f"turn = {turn:+d} deg",
                    {"data": {"values": {cid+".turn": {"value": turn, "unit": "degree"}}}})
        return turn

    def ranked_views(self, A, B, operands=None):
        ranked = sorted((self.pair_rank(i, j)+(i, j) for i in A for j in B),
                        key=lambda c: (c[0], c[3], c[4]))
        # Only the first two usable pairs can affect the winner or the view prose.
        eligible = []
        for c in ranked:
            if operands is None or operands(*c[3:]): eligible.append(c)
            if len(eligible) == 2: break
        if not eligible: raise Refusal("no_supported_visible_frame_pair")
        i, j = eligible[0][3:]
        shown = sorted(eligible, key=lambda c: (c[3],c[4]))
        self.w.say(f"I use frames {i} and {j}: among usable visible pairs, they have the smallest frame separation, with ties settled by the lower first frame, then the second.",
                   pair_pick={"pairs": [list(c[3:]) for c in shown], "selected": [i,j], "skipped": [], "rule": "frame_gap"})
        self.last_pair = (i, j)
        return ranked, shown

    def choose_pair(self, a, ia, b, ib):
        A, B = self.visible(ia), self.visible(ib)
        common = sorted(set(A)&set(B), key=lambda k: (-min(self.area(ia,k), self.area(ib,k)), k))
        for k in common:
            if self.usable(ia,k) and self.usable(ib,k):
                choice = {"objects": [a,b], "instance_ids": [int(ia),int(ib)], "frames": [k,k], "kind": "common"}
                self.private["frame_choices"].append(choice)
                self.w.say(frame_look([a,b], [k,k]), frame_look={"objects": [a,b], "frames": [k,k]})
                return k,k
        if common: raise Refusal("common_frame_unclickable")
        ranked, shown = self.ranked_views(A,B, lambda i,j: self.usable(ia,i) and self.usable(ib,j))
        i,j = self.last_pair
        if not (self.usable(ia,i) and self.usable(ib,j)): raise Refusal("best_pair_unclickable")
        choice = {"objects": [a,b], "instance_ids": [int(ia),int(ib)], "frames": [i,j], "kind": "pair",
                  "candidates": [list(c) for c in ranked], "shown": [list(c[3:]) for c in shown]}
        self.private["frame_choices"].append(choice)
        if len(shown) > 1:
            self.w.say(f"I use the {noun(a)} in frame {i} and the {noun(b)} in frame {j}.",
                       selected_views={"objects": [a,b], "frames": [i,j]})
        return i,j

    def one_id(self, obj):
        return self.scene.ids(obj)[0]

    # ------------------------------------------------------------------ programs
    def side_words(self, a, pa, b, pb):
        A, B = self.P[pa]["f1"], self.P[pb]["f1"]
        dx, dz = B[0] - A[0], B[2] - A[2]
        lateral = "to the right" if dx > 0 else "to the left" if dx < 0 else "at the same x"
        depth = "ahead" if dz > 0 else "behind" if dz < 0 else "at the same z"
        main = f"{lateral} (x {f2(B[0])} vs {f2(A[0])}) and {depth} (z {f2(B[2])} vs {f2(A[2])})"
        if abs(dz) > abs(dx):
            main = f"{depth} (z {f2(B[2])} vs {f2(A[2])}) and {lateral} (x {f2(B[0])} vs {f2(A[0])})"
        return f"In frame-1 coordinates (x right, z forward), relative to the {poss(a)} middle {pa}, the {poss(b)} middle {pb} is {main}."

    def closest_pair(self, a, ia, b, ib, reuse=None):
        if getattr(self,'surface_search',False) and ia != ib:
            return self.surface_pair(a,ia,b,ib)
        ka, kb = self.choose_pair(a, ia, b, ib)
        if getattr(self,'single_view_limit',False):
            self.private['frame_choices'][-1]['single_view_limit'] = True
        self.w.para()
        ua, _ = self.facing_uv(ia, ka, ib, kb)
        ub, _ = self.facing_uv(ib, kb, ia, ka)
        auv, ap = self.pool(ia,ka)
        buv, bp = self.pool(ib,kb)
        distances, neighbours = cKDTree(bp).query(ap)
        witness = buv[int(neighbours[int(distances.argmin())])].tolist()
        if witness not in ub: ub = [witness]+ub[:2]
        A = self.depth_at(a, ia, ka, ua)
        B = self.depth_at(b, ib, kb, ub)
        best = self.calc("closest", A=A, B=B)
        _, Pa = self.pool(ia, ka)
        _, Pb = self.pool(ib, kb)
        self.private["gt_reference"].setdefault("eroded_min_m", []).append(float(cKDTree(Pb).query(Pa)[0].min()))
        return best, A[0]

    def surface_pair(self, a, ia, b, ib):
        """Compare one complete-pool minimum witness from each of up to three views."""
        views = []
        for iid in (ia,ib):
            selected = []
            for k in sorted(self.visible(iid),key=lambda k:(-self.area(iid,k),k)):
                if self.usable(iid,k): selected.append(k)
                if len(selected) == 3: break
            views.append(selected)
        if any(not ks for ks in views): raise Refusal('no_supported_visible_frame')
        views = [sorted(ks) for ks in views]
        while True:
            pools = [[self.pool(iid,k) for k in ks] for iid,ks in zip((ia,ib),views)]
            unions = [np.concatenate([p for uv,p in ps]) for ps in pools]
            distances, neighbours = cKDTree(unions[1]).query(unions[0])
            witness = int(neighbours[int(distances.argmin())])
            b_view = 0
            while witness >= len(pools[1][b_view][0]):
                witness -= len(pools[1][b_view][0]); b_view += 1
            indices = [[int(cKDTree(other).query(pool)[0].argmin()) for uv,pool in ps]
                       for ps,other in zip(pools,reversed(unions))]
            indices[1][b_view] = witness
            retained = []
            for iid,ks,ps,ix in zip((ia,ib),views,pools,indices):
                kept, positions = [], []
                for v in sorted(range(len(ks)), key=lambda v:(-self.area(iid,ks[v]),ks[v])):
                    k,(_,pool),index = ks[v],ps[v],ix[v]
                    point = pool[index]
                    if any(np.linalg.norm(point-old) < .05 for old in positions): continue
                    kept.append(k); positions.append(point)
                retained.append(sorted(kept))
            if retained == views: break
            views = retained
        labels = []
        for side,(obj,iid,ks,ps,other) in enumerate(zip((a,b),(ia,ib),views,pools,reversed(unions))):
            selected = []
            tree = cKDTree(other)
            for view_index,(k,(uv,pool)) in enumerate(zip(ks,ps)):
                index = int(tree.query(pool)[0].argmin())
                if side == 1 and view_index == b_view: index = witness
                self.w.para()
                selected += self.depth_at(obj,iid,k,[uv[index].tolist()])
            labels.append(selected)
        self.private['frame_choices'].append({'objects':[a,b], 'instance_ids':[int(ia),int(ib)],
            'frames':[ks[0] for ks in views], 'kind':'surface_views', 'views':views})
        best = self.calc('closest',A=labels[0],B=labels[1])
        self.private['gt_reference'].setdefault('eroded_min_m',[]).append(float(cKDTree(unions[1]).query(unions[0])[0].min()))
        return best,labels[0][0]

    def relative_distances(self, target, candidates):
        """Measure a shared reference set once; keep all closest-pair witnesses."""
        it = self.one_id(target)
        kt = self.best_frame(it)
        selected = []
        for obj in candidates:
            self.w.para()
            self.w.say(f"For the {noun(obj)}:", candidate_group={"object": obj})
            ids = self.scene.ids(obj, many=True)
            if len(ids) > 2: raise Refusal("distance_category_too_many_instances")
            options = []
            for iid in ids:
                k = self.best_frame(iid)
                _, pool = self.pool(iid, k)
                _, target_pool = self.pool(it, kt)
                options.append((float(np.linalg.norm(np.median(pool,0)-np.median(target_pool,0))), iid))
            iid = min(options)[1]
            # Fix the reference frame across all candidates while measuring alternatives.
            visible = self.visible(iid)
            if kt in visible and self.usable(iid,kt):
                k = kt
                choice = {"objects":[target,obj], "instance_ids":[int(it),int(iid)], "frames":[kt,k], "kind":"common"}
                self.w.say(frame_look([target,obj],[kt,k]), frame_look={"objects":[target,obj],"frames":[kt,k]})
            else:
                ranks, shown = self.ranked_views([kt], visible, lambda i,j: self.usable(it,i) and self.usable(iid,j))
                _, k = self.last_pair
                choice = {"objects":[target,obj], "instance_ids":[int(it),int(iid)], "frames":[kt,k], "kind":"reference_pair",
                          "candidates":[list(c) for c in ranks], "shown":[list(c[3:]) for c in shown]}
            self.private["frame_choices"].append(choice)
            selected.append((obj,iid,k))
        uv, pool = self.pool(it,kt)
        indices = []
        for obj,iid,k in selected:
            _, other = self.pool(iid,k)
            idx = int(cKDTree(other).query(pool)[0].argmin())
            if idx not in indices: indices.append(idx)
        # Real image pixels, not the normalized 0..1000 grid.
        scale = np.array([self.gt.W,self.gt.H])/1000
        self.check_click_spacing(kt, [uv[i] for i in indices])
        if len(indices) > 6: raise Refusal("too_many_reference_minima")
        while len(indices) < 3:
            gap = np.minimum(np.min(np.linalg.norm((uv[:,None]-uv[indices])*scale,axis=2),axis=1),
                             np.min(np.linalg.norm(uv[:,None]-uv[indices],axis=2),axis=1))
            idx = int(gap.argmax())
            if gap[idx] < 15: break
            indices.append(idx)
        self.w.para()
        A = self.depth_at(target,it,kt,[uv[i].tolist() for i in indices])
        scores = []
        self.raw_distance_scores = []
        for obj,iid,k in selected:
            self.w.para()
            other_uv, other = self.pool(iid,k)
            # The witness is selected against the complete reference pool.
            d = cKDTree(pool[indices]).query(other)[0]
            chosen = self.spaced_pixels(other_uv,d,3,k=k)
            B = self.depth_at(obj,iid,k,chosen)
            scores.append(self.calc("closest", A=A, B=B)[2])
            self.raw_distance_scores.append(min(float(np.linalg.norm(self.raw_P[a]-self.raw_P[b]))
                                                for a in A for b in B))
        return scores

    def check_click_spacing(self, k, pts):
        prior = [p['uv'] for p in self.P.values() if p['frame'] == k]
        scale = np.array([self.gt.W, self.gt.H])/1000
        for point in pts:
            if any(np.linalg.norm((np.asarray(point)-other)*scale) < 15
                   or np.linalg.norm(np.asarray(point)-other) < 15 for other in prior):
                raise Refusal("click_spacing")
            prior.append(point)

    def spaced_pixels(self, uv, distances, n, k=None):
        chosen = [int(np.argmin(distances))]
        # The minimum is mandatory; optional near-side clicks may be resampled.
        if k is not None: self.check_click_spacing(k, [uv[chosen[0]]])
        scale = np.array([self.gt.W,self.gt.H])/1000
        while len(chosen) < min(n,len(uv)):
            prior = [p['uv'] for p in self.P.values() if p['frame'] == k] if k is not None else []
            against = np.asarray([*uv[chosen], *prior])
            gap = np.minimum(np.min(np.linalg.norm((uv[:,None]-against)*scale,axis=2),axis=1),
                             np.min(np.linalg.norm(uv[:,None]-against,axis=2),axis=1))
            idx = int(gap.argmax())
            if gap[idx] < 15 or np.min(np.linalg.norm(uv[idx]-uv[chosen],axis=1)) < 15: break
            chosen.append(idx)
        return [uv[i].tolist() for i in chosen]

    def counted(self, cat):
        missing = sorted(set(range(1,33) if self.layout == "per_frame" else range(2,33,2))-set(self.anchors))
        if missing: defer("missing_count_anchor_depth_pose", str(missing))
        if is_generic_label(cat): raise Refusal("generic_label")
        ids = self.scene.ids(cat, many=True)
        if any(is_generic_label(self.scene.native[i]["label"]) for i in ids):
            raise Refusal("generic_label")
        minimum = (self.gt.H*self.gt.W + 199)//200
        sightings = {}
        for k in self.anchors:
            sightings[k] = []
            for iid in ids:
                if self.area(iid,k) < minimum: continue
                pool = self.pool(iid,k)
                if pool is None: raise Refusal("unclickable_visible_instance", cat)
                _, extent = self.count_extent_uv(iid,k)
                if extent < .10: continue
                uv, points = pool
                middle = uv[int(np.argmin(np.linalg.norm(points-np.median(points,axis=0),axis=1)))].tolist()
                sightings[k].append((iid,middle))
            sightings[k].sort(key=lambda item:(item[1][0],item[1][1],item[0]))
        floor = max(map(len,sightings.values()))
        count = len(ids)
        if count < floor: raise Refusal("count_below_floor")
        floor_frame = next(k for k in self.anchors if len(sightings[k]) == floor)
        for k, seen in sightings.items():
            if not seen: continue
            self.w.para()
            for start in range(0,len(seen),4):
                batch = seen[start:start+4]
                self.w.say(f"I click the {noun(cat)} in frame {k}.", click_object={"object":cat,"frame":k})
                pose = self.scene.pose(k)
                lines, published, values = [], [], {}
                cid = "c"+str(len(self.w.calls)+1)
                for index,(iid,uv) in enumerate(batch):
                    self.check_click_spacing(k, [uv])
                    value = self.scene.readout(iid,k,uv)
                    if value["spread"] > spread_limit(uv): raise Refusal("unstable_measurement_click")
                    self.n += 1
                    label = f"P{self.n}"
                    cam = [r2(x*s) for x,s in zip(value["camera"],(1,-1,1))]
                    f1 = [r2(x) for x in np.asarray(pose["camera_R_L1"]) @ np.asarray(value["camera"]) + np.asarray(pose["camera_t_L1"])]
                    spread = r2(value["spread"])
                    self.P[label] = {"object":cat,"frame":k,"uv":uv,"cam":cam,"f1":f1,"spread":spread}
                    self.private["clicks"].append({"label":label,"object":cat,"instance_id":int(iid),"frame":k,"uv":uv,"correction_initial":False})
                    lines.append(self.fixed.register(label,cam,f1,spread,k,k))
                    published.append(self.fixed.last_point)
                    prefix = "" if len(batch)==1 else str(index)+"."
                    for key,val,unit in (("camera",cam,"m"),("f1",f1,"m"),("spread",spread,"1")):
                        values[cid+"."+prefix+key] = {"value":val,"unit":unit}
                self.w.call("depth_at",{"frame":k,"pts":[uv for _,uv in batch]},"\n".join(lines),
                            {"object":cat,"data":{"points":published,"values":values}})
            self.w.say(f"Frame {k} shows {len(seen)} {plural(cat,len(seen))}.",
                       count_scan={"object":cat,"frame":k,"count":len(seen)})
        empty = [k for k in self.anchors if not sightings[k]]
        if empty:
            # Consecutive supported anchors form one range, including paired anchors.
            spans = []
            begin = end = empty[0]
            step = 1 if self.layout == "per_frame" else 2
            for k in empty[1:]:
                if k != end+step:
                    spans.append(str(begin) if begin==end else f"{begin}-{end}")
                    begin = k
                end = k
            spans.append(str(begin) if begin==end else f"{begin}-{end}")
            self.w.para()
            subject = "Frame" if len(empty)==1 else "Frames"
            self.w.say(f"{subject} {join(spans)} {'shows' if len(empty)==1 else 'show'} no {noun(cat)}.",
                       count_empty={"object":cat,"frames":empty})
        self.w.para()
        self.w.say(f"The most {plural(cat,2)} visible together is {floor}, in frame {floor_frame}, so there {'is' if floor == 1 else 'are'} at least {floor}.",
                   count_floor={"object":cat,"count":floor,"frame":floor_frame})
        return count, floor

    def direction_points(self, objs):
        if self.t != "route_planning":
            for obj in objs:
                ids_for_name = self.scene.ids(obj,many=True)
                if is_generic_label(obj) or any(is_generic_label(self.scene.native[i]["label"]) for i in ids_for_name):
                    raise Refusal("generic_label")
                categories = {self.scene.native[i]["label"].strip().lower() for i in ids_for_name}
                native_matches = [i for i,x in self.scene.native.items() if x["label"].strip().lower() in categories]
                if len(native_matches) != 1: raise Refusal("direction_multiple_native_instances")
        ids = [self.one_id(o) for o in objs]
        vis = [set(self.visible(i)) for i in ids]
        available = set.union(*vis)
        if not available or any(not v for v in vis): raise Refusal("no_supported_visible_frame")
        anchor = min(available, key=lambda k: (-sum(k in v for v in vis),
                     -min(self.area(i,k) for i,v in zip(ids,vis) if k in v), k))
        frames, rankings = [], []
        for o,i,v in zip(objs,ids,vis):
            if anchor in v: frames.append(anchor)
            else:
                ranked,shown = self.ranked_views([anchor],sorted(v), lambda a,b: self.usable(i,b) and all(self.usable(ii,a) for ii,vv in zip(ids,vis) if a in vv))
                frames.append(self.last_pair[1])
                rankings.append({"object": o, "candidates": [list(c) for c in ranked], "shown": [list(c[3:]) for c in shown]})
        if not all(self.usable(i,k) for i,k in zip(ids,frames)): raise Refusal("selected_frame_unclickable")
        kind = "common" if len(set(frames)) == 1 else "anchor"
        self.private["frame_choices"].append({"objects": objs, "instance_ids": [int(i) for i in ids],
                    "frames": frames, "kind": kind, "anchor": anchor, "rankings": rankings})
        if not rankings or any(len(r['shown']) > 1 for r in rankings):
            self.w.say("I use " + join(f"the {noun(o)} in frame {k}" for o,k in zip(objs,frames))+".",
                       selected_views={"objects": objs, "frames": frames})
        return [self.depth_at(o,i,k,[self.middle_uv(i,k)])[0] for o,i,k in zip(objs,ids,frames)]

    # ------------------------------------------------------------------ main
    def execute(self):
        t, p, q = self.t, self.plan, self.q
        roles = object_labels(p)
        for obj in roles:
            labels = [obj] + [self.scene.native[i]["label"] for i in self.scene.ids(obj, many=True)]
            if any(is_generic_label(label) for label in labels):
                raise Refusal("generic_label", "invalid_object_category")
            for label in labels:
                for part in ("ceiling", "floor", "wall"):
                    if re.search(r"\b"+part+r"s?$", label.strip(), re.I) and not re.search(r"\b"+part+r"s?\b", q["question"], re.I):
                        raise Refusal("structural_part_not_asked")
        unit = self.unit()
        self.w.para()
        if t == "room_size_estimation":
            corners = p.get("floor_corners")
            if not corners or len(corners) < 3 or not p.get("floor_polygon_reviewed") or p.get("floor_scope") != "whole_scene":
                defer("missing_reviewed_whole_scene_floor_corners")
            labels = []
            for c in corners:
                k = self.eff(c["frame"])
                iid = self.one_id(c["object"])
                if self.scene.native[iid]["label"].lower() != "floor": raise Refusal("floor_corner_not_floor")
                self.w.say(f"I click the reviewed floor corner in frame {k} at {c['uv']}.")
                labels += self.depth_at(c["object"], iid, k, [c["uv"]], c["frame"])
            self.substitution_sentence()
            value, result = self.calc("area", C=labels), None
            self.final = f"The whole-scene floor polygon has area {f2(value)} m^2."
        elif t == "camera_rotation":
            i, j = self.eff(p["i"], False), self.eff(p["j"], False)
            self.camera_admission(p["i"], p["j"])
            self.camera_admission(i, j)
            self.substitution_sentence()
            value, result = self.camera_turn(i,j), None
            self.final = f"The camera rotation is {value} degrees; positive yaw means left."
        elif t in ("object_abs_distance", "absolute_distance_object"):
            best, _ = self.closest_pair(p["a"], self.one_id(p["a"]), p["b"], self.one_id(p["b"]))
            value, result = best[2], None
            self.final = f"The closest pair is {best[0]}-{best[1]}, so the shortest distance between the {noun(p['a'])} and the {noun(p['b'])} is {f2(value)} m."
        elif t in ("object_rel_distance", "relative_distance_object"):
            target = p["target"]
            scores = self.relative_distances(target,p["cands"])
            order = sorted(range(len(scores)), key=lambda i: scores[i])
            from decimal import Decimal
            low, second = (Decimal(str(scores[i])) for i in order[:2])
            margin_m = second-low
            margin_rel = margin_m/second if second else Decimal(0)
            if margin_rel < Decimal("0.10") or margin_m < Decimal("0.10"): raise Refusal("near_tie")
            raw_low, raw_second = sorted(Decimal(str(v)) for v in self.raw_distance_scores)[:2]
            raw_gap = raw_second-raw_low
            if raw_second <= 0 or raw_gap < Decimal('.10') or raw_gap < Decimal('.10')*raw_second:
                raise Refusal('near_tie')
            self.unrounded_margins = dict(unrounded_margin_m=float(raw_gap),
                unrounded_margin_rel=float(raw_gap/raw_second))
            self.margin_m, self.margin_rel = float(margin_m), float(margin_rel)
            result = p["cands"][order[0]]
            listing = ", ".join(f"{noun(c)} {f2(s)} m" for c, s in zip(p["cands"], scores))
            self.compare = f"The closest-point distances to the {noun(target)} are {listing}; the smallest is the {noun(result)}."
        elif t in ("object_size_estimation", "absolute_size_object", "relative_size_object"):
            objs = [p["a"], p["b"]] if t == "relative_size_object" else [p["a"]]
            sizes = []
            for o in objs:
                iid = self.one_id(o)
                k = self.best_frame(iid)
                ends, vertical, _, height = self.extent_uv(iid, k)
                self.w.para()
                self.w.say(f"The {noun(o)} is most fully visible in frame {k}. I click the two ends of its longest visible side"
                           + (" and its top and bottom, in case its height is longer." if height > .2 else "."))
                labels = self.depth_at(o, iid, k, ends + (vertical if height > .2 else []))
                d1 = self.calc("dist", pts=labels[:2])
                cands = [d1]
                if height > .2: cands.append(self.calc("dist", pts=labels[2:4]))
                size = max(cands)
                if len(cands) > 1:
                    self.w.say(f"The longer of {f2(cands[0])} m and {f2(cands[1])} m is {f2(size)} m.")
                sizes.append(size)
            if t == "relative_size_object":
                if sizes[0] == sizes[1]: raise Refusal("size_tie")
                longer = p["a"] if sizes[0] > sizes[1] else p["b"]
                result = longer if p["comparison"] == "longer" else (p["b"] if longer == p["a"] else p["a"])
                self.compare = f"The {noun(p['a'])} measures {f2(sizes[0])} m and the {noun(p['b'])} {f2(sizes[1])} m, so the {p['comparison']} one is the {noun(result)}."
            else:
                value, result = sizes[0], None
                self.final = f"So the longest side of the {noun(p['a'])} is about {f2(value)} m."
        elif t in ("object_counting", "absolute_count", "relative_count"):
            cats = [p["a"], p["b"]] if t == "relative_count" else [p["cat"]]
            measured_counts, count_floors = {}, {}
            self.count_floors = count_floors
            for c in dict.fromkeys(cats):
                measured_counts[c], count_floors[c] = self.counted(c)
                video = f"Looking over the whole video, I count {measured_counts[c]} {plural(c,measured_counts[c])}, which is at least the floor of {count_floors[c]}, so there {'is' if measured_counts[c] == 1 else 'are'} {measured_counts[c]}."
                if t == "relative_count":
                    self.w.para()
                    self.w.say(video, count_video={"object":c,"count":measured_counts[c]})
                else:
                    self.final = video
            counts = [measured_counts[c] for c in cats]
            if t == "relative_count":
                result = "more" if counts[0] > counts[1] else "fewer" if counts[0] < counts[1] else "equal number"
                self.compare = f"I count {counts[0]} {plural(cats[0],counts[0])} and {counts[1]} {plural(cats[1],counts[1])}; the counts are equal." if result == "equal number" else f"I count {counts[0]} {plural(cats[0],counts[0])} and {counts[1]} {plural(cats[1],counts[1])}; {plural(cats[0],2)} are {'less' if result == 'fewer' else 'more'} numerous."
            else:
                value, result = counts[0], None
        elif t.startswith("object_rel_direction") or t in ("relative_direction_object", "absolute_direction_object"):
            objs = [p["stand"], p["face"], p["query"]]
            S, F, Q = self.direction_points(objs)
            rule = {"object_rel_direction_medium": "medium", "object_rel_direction_hard": "hard"}.get(t, "easy")
            self.w.para()
            self.w.say(SIGN_RULE + (" The question counts an object as behind when I would turn at least 135 degrees." if rule == "medium" else ""))
            u, v, dot, cross, theta, label = self.calc("angle", S=S, F=F, Q=Q, rule=rule)
            if min(np.linalg.norm(u), np.linalg.norm(v)) < .50: raise Refusal("direction_degenerate_floor")
            from .replay import native_reference, label_direction
            native = native_reference(self.scene,self.T,q,p)["value"]
            native_label = native
            click_label = theta % 360 if t == "absolute_direction_object" else label
            if click_label != native_label: raise Refusal("click_centroid_label_disagree")
            margin = boundary_margin(theta, "absolute" if t == "absolute_direction_object" else rule)
            self.private["direction_centroid_label"] = native_label
            self.boundary_margin_deg = margin
            if margin is not None and margin < 10: raise Refusal("near_boundary_refused")
            if t == "absolute_direction_object":
                value, result = theta % 360, None
                self.final = (f"Counterclockwise seen from above is the positive (left) direction, so ccw = {theta} mod 360 = {value} deg: "
                              f"I turn {value} degrees counterclockwise to face the {noun(p['query'])}.")
            else:
                result = label
                self.compare = ""
        elif t == "route_planning":
            steps = p["plan"]
            objs = list(dict.fromkeys([p["start"], p["face"]] + [o for k, o in steps if k == "go"]))
            pts = dict(zip(objs, self.direction_points(objs)))
            here, prev, turns, pending_turn = p["start"], None, [], False
            self.w.para()
            self.w.say(SIGN_RULE + " Turn Back applies when |theta| >= 135 degrees.")
            for i, (kind, obj) in enumerate(steps):
                if kind == "go":
                    if obj == here: raise Refusal("route_degenerate_go")
                    prev, here, pending_turn = here, obj, False
                    continue
                if pending_turn: raise Refusal("route_sequence")
                pending_turn = True
                nxt = next((o for k2, o in steps[i + 1:] if k2 == "go"), None)
                if nxt is None: raise Refusal("underspecified_route")
                self.w.para()
                if prev is None:
                    self.w.say(f"Blank {len(turns) + 1}: I stand at the {noun(here)} facing the {noun(p['face'])} and need to head to the {noun(nxt)}.")
                    out = self.calc("angle", S=pts[here], F=pts[p["face"]], Q=pts[nxt], rule="turn")
                else:
                    self.w.say(f"Blank {len(turns) + 1}: After the leg to the {noun(here)}, the incoming heading is from the {noun(prev)} to the {noun(here)}; I need to head to the {noun(nxt)}.")
                    out = self.calc("turn", **{"from": pts[prev], "at": pts[here], "to": pts[nxt]})
                turns.append(out[5])
            result = ", ".join(turns)
            self.compare = "So the turn at the blank is " + turns[0].removeprefix("Turn ").lower() if len(turns) == 1 else "So the turns at the blanks are " + join(x.removeprefix("Turn ").lower() for x in turns)
        elif t == "obj_appearance_order":
            firsts, seen = [], set()
            for cat in p["cats"]: self.scene.ids(cat, many=True)
            for k in range(1,33):
                observations = []
                for cat in p["cats"]:
                    if cat in seen: continue
                    masks = self.scene.appearance_masks(cat,k)
                    if not masks: continue
                    iid,mask = masks[0]
                    uv = innermost_uv(self.gt,mask)
                    xx,yy = self.gt.px([uv])
                    if self.gt.inst[k-1,yy[0],xx[0]] != iid: raise Refusal("rounded_click_outside_mask")
                    self.private["clicks"].append({"object":cat,"instance_id":int(iid),"frame":k,"uv":uv,"kind":"rgb_pointing"})
                    observations.append({"object":cat,"uv":uv})
                    firsts.append((k,cat)); seen.add(cat)
                self.w.para()
                text = (f"In frame {k}, I first spot " + join(f"the {noun(o['object'])} at {o['uv']}" for o in observations)+"." if observations
                        else f"In frame {k}, I find no new category from the question.")
                self.w.say(text, appearance_frame={"frame":k,"firsts":observations})
                if len(seen) == len(p["cats"]): break
            if len(seen) != len(p["cats"]): raise Refusal("never_visible")
            if len({k for k, _ in firsts}) != len(firsts): raise Refusal("appearance_tie")
            result = ", ".join(c for _, c in sorted(firsts))
            self.compare = "Sorting by first frame: " + ", ".join(f"{noun(c)} ({k})" for k, c in sorted(firsts)) + "."
        elif t in ("camera_displacement", "camera_movement_direction"):
            i, j = self.eff(p["i"], depth=False), self.eff(p["j"], depth=False)
            self.substitution_sentence()
            self.camera_admission(p["i"], p["j"])
            self.camera_admission(i, j)
            self.w.say(f"The move tool gives the camera displacement from frame {i} to frame {j} in frame {i}'s level frame (x right, y up, z forward).")
            m = self.move(i, j)
            if t == "camera_displacement":
                value, result = m["distance"], None
                self.final = f"The printed distance is {f2(value)} m, so the camera moved about {f2(value)} m."
            else:
                scores = {"forward": m["dz"], "backward": r2(-m["dz"]), "right": m["dx"], "left": r2(-m["dx"])}
                labels = [v.strip().lower() for v in self.T.option_texts(q["options"]).values()]
                if any(l not in scores for l in labels): raise Refusal("unsupported_movement_option")
                ranked = sorted(labels, key=lambda l: -scores[l])
                self.margin_m, self.margin_rel = direction_margins(scores[l] for l in labels)
                from .geometry import level_basis
                for ri, rj in dict.fromkeys(((p['i'], p['j']), (i, j))):
                    rotation, start = self.gt.cam(ri)
                    end = self.gt.cam(rj)[1]
                    raw = level_basis(rotation).T @ (np.asarray(end,dtype=float)-np.asarray(start,dtype=float))
                    raw_scores = dict(forward=raw[2], backward=-raw[2], right=raw[0], left=-raw[0])
                    raw_m, raw_rel = direction_margins(raw_scores[l] for l in labels)
                self.unrounded_margins = dict(unrounded_margin_m=raw_m, unrounded_margin_rel=raw_rel)
                expl = {"forward": "dz", "backward": "-dz", "right": "dx", "left": "-dx"}
                self.w.para()
                self.w.say("Scoring each option by the matching component: " + "; ".join(f"{l} = {expl[l]} = {f2(scores[l])} m" for l in labels) + ".")
                result = ranked[0]
                self.compare = f"The largest is {noun(result)}."
        else:
            k = self.eff(p["k"], depth=True)
            requested = p["k"]
            self.substitution_sentence()
            if t == "camera_obj_abs_dist":
                o = p["obj"]
                labels = []
                visible_ids = [i for i in self.scene.ids(o, many=True) if self.area(i,k) >= self.scene.programs.MIN_PX]
                if len(visible_ids) > 6: raise Refusal("camera_too_many_visible_instances")
                for iid in visible_ids:
                    if not self.usable(iid, k): raise Refusal("unclickable_visible_instance", o)
                    uv, _ = self.near_camera_uv(iid, k, n=3 if len(visible_ids)==1 else 1)
                    self.w.say(f"In frame {k} I click the part of the {noun(o)} nearest the camera.")
                    labels += self.depth_at(o, iid, k, uv, requested, announce=False)
                if not labels: raise Refusal("object_not_visible_in_frame", o)
                labels.sort(key=lambda l: digest([self.row["qid"], next(c['instance_id'] for c in self.private['clicks'] if c['label']==l), k, self.P[l]['uv']]))
                best = self.calc("cam_dist", pts=labels)
                value, result = best[1], None
                self.final = f"The nearest clicked point of the {noun(o)} is {best[0]} at {f2(value)} m from the camera."
            elif t.startswith("camera_obj_rel_dist"):
                scores = []
                for c in p["cands"]:
                    labels = []
                    for iid in self.scene.ids(c, many=True):
                        if self.area(iid, k) < self.scene.programs.MIN_PX: continue
                        if not self.usable(iid, k): raise Refusal("unclickable_visible_instance", c)
                        count = sum(self.area(ii,k) >= self.scene.programs.MIN_PX for ii in self.scene.ids(c,many=True))
                        if count > 3: raise Refusal("camera_too_many_visible_instances")
                        uv, _ = self.near_camera_uv(iid, k, n=max(1,3//count))
                        labels += self.depth_at(c, iid, k, uv, requested)
                    if not labels: raise Refusal("candidate_not_visible_in_frame", c)
                    labels.sort(key=lambda l: digest([self.row["qid"], next(x['instance_id'] for x in self.private['clicks'] if x['label']==l), k, self.P[l]['uv']]))
                    self.w.say(f"I compare these near-side candidates for the {noun(c)}.")
                    scores.append(self.calc("cam_dist", pts=labels)[1])
                    self.w.para()
                order = sorted(range(len(scores)), key=lambda i: scores[i])
                if r2(scores[order[1]]-scores[order[0]]) < .05: raise Refusal("camera_distance_margin_under_0.05")
                result = p["cands"][order[0]]
                self.compare = "Nearest-point distances from the camera: " + ", ".join(f"{noun(c)} {f2(s)} m" for c, s in zip(p["cands"], scores)) + f"; the smallest is the {noun(result)}."
            else:
                a, ref = p["a"], p["ref"]
                ia, ir = self.one_id(a), self.one_id(ref)
                if not self.usable(ia, k) or not self.usable(ir, k): raise Refusal("object_not_visible_in_frame")
                self.w.say(f"In frame {k} I click near the middle of the {noun(a)} and of the {noun(ref)}.")
                pa = self.depth_at(a, ia, k, [self.middle_uv(ia, k)], requested)[0]
                pr = self.depth_at(ref, ir, k, [self.middle_uv(ir, k)], requested)[0]
                self.w.para()
                if t.endswith("_lr"):
                    xa, xr = self.P[pa]["cam"][0], self.P[pr]["cam"][0]
                    if xa == xr: raise Refusal("position_tie")
                    result = "left" if xa < xr else "right"
                    self.compare = f"In frame {k}'s view, larger x is further right. The middle of the {noun(a)} is at x {f2(xa)} and the middle of the {noun(ref)} at x {f2(xr)}, so the {noun(a)} lies to the {noun(result)}."
                elif t.endswith("_nf"):
                    best = self.calc("cam_dist", pts=[pa, pr])
                    da, dr = best[2][pa], best[2][pr]
                    if da == dr: raise Refusal("position_tie")
                    result = "near" if da < dr else "far"
                    self.compare = f"The middle of the {noun(a)} is {f2(da)} m from the camera and the middle of the {noun(ref)} {f2(dr)} m, so the former is nearer." if result == "near" else f"The middle of the {noun(a)} is {f2(da)} m from the camera and the middle of the {noun(ref)} {f2(dr)} m, so the former is farther."
                else:
                    ya, yr = self.P[pa]["f1"][1], self.P[pr]["f1"][1]
                    if ya == yr: raise Refusal("position_tie")
                    result = "up" if ya > yr else "down"
                    self.compare = f"The pose head places the middle of the {noun(a)} at frame-1 height y {f2(ya)} and the middle of the {noun(ref)} at {f2(yr)}. With y up, the former is {'higher (up)' if result == 'up' else 'lower (down)'}."
        return self.finish(unit, locals().get("value"), result)

    def substitution_sentence(self):
        for k, e in sorted(self.substituted.items()):
            self.w.say(f"The heads read out one frame per temporal pair, the even one, so for frame {k} I use frame {e}.", substitution={"from": k, "to": e})
        if self.substituted: self.w.para()

    def unit(self):
        return unit_policy(self.q, self.config, self.reviewed)

    def finish(self, unit, value, result):
        self.w.para()
        if unit:
            if unit["factor"] != 1:
                from decimal import Decimal, localcontext, ROUND_HALF_EVEN
                with localcontext() as context:
                    context.prec = 80
                    converted = Decimal(str(value)) * Decimal(str(unit["factor"]))
                    answer = format(converted.quantize(Decimal(1).scaleb(-unit['decimals']),
                                                       rounding=ROUND_HALF_EVEN), f".{unit['decimals']}f")
            else:
                answer = f"{value * unit['factor']:.{unit['decimals']}f}"
            if unit["factor"] != 1:
                self.final += f" {unit['unit']} = {f2(value)} * {unit['factor']} = {answer}."
            self.w.say(self.final)
            text_answer = str(answer)
            decision = {"kind": "decision", "mode": "numeric", "result": answer, "unit": unit}
        else:
            letter = self.T.letter_of(self.q["options"], result)
            if letter is None: raise Refusal("option_content_mismatch", str(result))
            self.w.say((self.compare + (f", which matches option {letter}." if self.t == "route_planning" else f" That matches option {letter}." )).strip())
            text_answer = letter
            decision = {"kind": "decision", "mode": "option", "result": result}
        public_keys = {"cat", "a", "b", "target", "stand", "face", "query", "start", "goal", "plan",
                       "obj", "ref", "cands", "cats", "k", "i", "j", "M", "comparison"}
        decision.update(family=self.t, binding={k: v for k, v in self.plan.items() if k in public_keys},
                        call_ids=[c["call_id"] for c in self.w.calls])
        target, spans = self.w.render(text_answer)
        return {"schema": "derivgen-row-v2", "form": FORM, "readout_mode": "gt", "answer_policy": "trace_value",
                "infrastructure_only": bool(self.scene.entry.get("infrastructure_only")),
                **({"count_floor": self.count_floors if self.t == "relative_count" else self.count_floors[self.plan["cat"]],
                    "count_branch": "floor_then_video"} if self.t in ("object_counting", "absolute_count", "relative_count") else {}),
                "qid": self.row["qid"], "question_type": self.t, "question": self.q["question"], "options": self.q["options"],
                "answer": text_answer, "target": target, "tool_output_spans": spans,
                "events": self.w.events + [{"role": "assistant", "target_loss": 1, **decision}], "display": unit,
                "points": self.P, "substitutions": self.substituted, "head_layout": self.layout,
                "private": {**self.private, "bindings": self.plan, "source_question_sha256": digest(self.q),
                            "gt": self.scene.entry["gt"], "frame_indices": self.scene.entry["frame_indices"]}}


def generate(scene, T, config, row, reviewed=None, *, exact=False, _single_views=False):
    import copy
    from .canon_render import render
    from .calculator import SPEC_SHA256
    if config["spec"]["sha256"] != SPEC_SHA256: raise Refusal("canonical_spec_pin_mismatch")
    if config.get("trace_form", "canonical_v38") != "canonical_v38": raise Refusal("canonical_configuration_epoch")
    if question(row)["question_type"] in ("room_size_estimation", "object_size_estimation", "absolute_size_object", "relative_size_object") and not (
            scene.entry.get("infrastructure_only") and row.get("infrastructure_only") and config.get("infrastructure_only")):
        defer("p3_v1_direct_answer_required")
    if not scene.entry.get("infrastructure_only") and not config.get("phrase_bank"):
        defer("missing_pinned_phrase_bank")
    scene.__dict__.setdefault("_canon_areas", {})
    scene.__dict__.setdefault("_canon_pools", OrderedDict())
    bound = copy.copy(scene)
    bound.allow_exact_reference = exact
    c = Canon(bound, T, config, row, reviewed, exact=exact)
    c.surface_search = c.t in ('object_abs_distance','absolute_distance_object') and not _single_views
    c.single_view_limit = _single_views
    record = c.execute()
    roles = {k: c.plan[k] for k in ("a", "b", "cat", "target", "stand", "face", "query", "start", "goal",
                                   "obj", "ref", "cands", "cats", "i", "j", "k") if k in c.plan}
    if c.t == "route_planning":
        roles["goal"] = c.plan.get("goal", next(o for k, o in reversed(c.plan["plan"]) if k == "go"))
    common_frame = None
    if c.t in ("object_abs_distance", "absolute_distance_object"):
        closest, = [call for call in c.w.calls if call["name"] == "closest"]
        frames = {c.P[label]["frame"] for side in ("A", "B") for label in closest["arguments"][side]}
        if len(frames) == 1:
            common_frame = next(iter(frames))
    record["events"].insert(0, {"role": "assistant", "kind": "plan", "target_loss": 1,
                                "format": FORM, "text": enrich_opening(opening_text(c.t, roles, common_frame=common_frame), c.t, c.private["frame_choices"], config, row["qid"], bool(c.P))})
    record["frame_pair_rule"] = "frame_gap"
    record["frame_pair_turn"] = []
    record["trace_revision"] = "3.11"
    record["image_size"] = [c.gt.W, c.gt.H]
    if hasattr(c, "margin_m"):
        record.update(margin_m=c.margin_m, margin_rel=c.margin_rel)
    if hasattr(c, "unrounded_margins"):
        record.update(c.unrounded_margins)
    fixes = label_typo_fixes(row)
    if fixes:
        record["label_typo_fixed"] = fixes
        original = question(row, fix_typos=False)
        record["label_typo_original"] = {"question": original["question"],
                                         "options": list(original["options"])}
    if hasattr(c,"boundary_margin_deg"):
        record["boundary_margin_deg"] = c.boundary_margin_deg
        record["near_boundary"] = c.boundary_margin_deg is not None and c.boundary_margin_deg < 10
    if "stand" in c.plan:
        record["direction_roles"] = [scene.entry["canonical"], c.plan["stand"], c.plan["face"], c.plan["query"]]
    record.update(render(record["events"], record["answer"]))
    if c.surface_search:
        from .plan_contract import qwen_tokens
        from .plan_contract import view_selection_target
        if qwen_tokens(view_selection_target(record)) > 3000:
            return generate(scene,T,config,row,reviewed,exact=exact,_single_views=True)
    from .bindings import gt_label
    record["gt_answer"] = gt_label(row)
    if record["display"]:
        from decimal import Decimal
        gt, computed = Decimal(str(gt_label(row))), Decimal(record["answer"])
        gap = abs(computed-gt)
        relative = gap/abs(gt) if gt else (Decimal(0) if not gap else None)
        record["private"]["numeric_contract"] = {"gt": str(gt), "computed": str(computed),
            "absolute_gap": str(gap), "relative_gap": str(relative) if relative is not None else None,
            "unit": record["display"]["unit"], "decimals": record["display"]["decimals"],
            "policy": "relative_0.05_no_floor" if c.t in ("object_abs_distance", "absolute_distance_object", "camera_obj_abs_dist") else "exact_declared_precision"}
        record["numeric_contract"] = dict(record["private"]["numeric_contract"])
    record["plan_branch"] = {"family": c.t, "frame_choices": [
        {key: choice[key] for key in ("objects", "frames", "kind")} for choice in c.private["frame_choices"]],
        "substitutions": c.substituted}
    if c.t in F17:
        from .replay import native_reference
        record["private"]["native_reference"] = native_reference(c.scene, T, c.q, c.plan)
    if row.get("generated_gt"):
        record["private"]["generated_gt"] = row["generated_gt"]
    if c.substituted:
        reference = generate(scene, T, config, row, reviewed, exact=True, _single_views=_single_views)
        if reference["answer"] != record["answer"]:
            raise Refusal("odd_anchor_exact_reference_disagreement")
        record["private"]["exact_reference"] = reference
    return record
