"""Points programs for every SPEC family. All decisions depend on trace nodes."""
import copy
import math

import numpy as np

from .bindings import F17, NUMERIC, bind, question, unit_policy
from .common import CONVENTION, Refusal, defer, digest, rounded
from .trace import Trace, render


class Program:
    def __init__(self, scene, T, config, exact_reference=False):
        self.scene, self.T, self.config = scene, T, config
        self.tr = Trace()
        self.poses, self.clicks = {}, []
        self.group, self.groups = None, []
        self.centres = {}
        self.frame_bindings = {}
        self.exact_reference = exact_reference
        self.requested_frames = {}
        self.count_run = 0

    def frame(self, k, depth=False):
        if type(k) is not int or not 1 <= k <= 32:
            raise Refusal("frame_out_of_range")
        if self.exact_reference:
            return k
        if k % 2 and (k != 1 or depth):
            if self.config.get("odd_frame_policy") != "next_anchor_exact_gt_equality":
                defer("unsupported_exact_odd_frame", str(k))
            self.requested_frames[k+1] = k
            self.tr.add("assistant", "substitution", requested_frame=k, effective_frame=k+1,
                        text=f"Requested frame {k}; use anchor frame {k+1}. The label must also match exact frame {k} GT.")
            return k + 1
        return k

    def pose(self, k):
        if k not in self.poses:
            p = self.scene.pose(k)
            self.poses[k] = self.tr.tool("pose", {"frame": k, "coordinates": "L_1"}, {
                "R": (p["camera_R_L1"], "1"), "t": (p["camera_t_L1"], "m"),
                "level_R": (p["level_R_L1"], "1"), "yaw": (p["yaw_degree"], "degree")})
        return self.poses[k]

    def move(self, i, j):
        self.pose(i), self.pose(j)
        # The fixed layer works at full precision, then prints its authoritative
        # distance. Assistant arithmetic must never rederive it from rounded dx/dy/dz.
        pi, pj = self.scene.pose(i), self.scene.pose(j)
        delta = np.array(pj["camera_t_L1"])-np.array(pi["camera_t_L1"])
        local = np.array(pi["level_R_L1"]).T @ delta
        nodes = self.tr.tool("move", {"from": i, "to": j}, {
            "delta": (local, "m"), "distance": (np.linalg.norm(local), "m")})
        module = getattr(self.scene, "l1", None)
        if module:
            self.tr.events[-1]["p1_v2_text"] = module.format_move(local)
        return nodes

    def click(self, obj, iid, k, uv, correction=False):
        return self.click_batch(obj, iid, k, [uv], correction)[0]

    def click_batch(self, obj, iid, k, points, correction=False):
        self.tr.add("assistant", "click", object=obj, frame=k, points=points, group=self.group)
        self.pose(k)
        raw_pose = self.scene.pose(k)
        fields = {}
        for i, uv in enumerate(points):
            v = self.scene.readout(iid, k, uv)
            # This is the fixed depth/FoV/pose layer, not assistant arithmetic.
            point = np.array(raw_pose["camera_R_L1"]) @ np.array(v["camera"]) + raw_pose["camera_t_L1"]
            prefix = "" if len(points) == 1 else f"{i}."
            fields.update({prefix+"camera": (v["camera"], "m"), prefix+"f1": (point, "m"),
                           prefix+"spread": (v["spread"], "1")})
        args = {"frame": self.requested_frames.get(k, k), "pts": points}
        if args["frame"] != k: args["image_frame"] = k
        nodes = self.tr.tool("depth_at", args, fields)
        out = []
        for i, uv in enumerate(points):
            prefix = "" if len(points) == 1 else f"{i}."
            self.clicks.append({"instance_id": iid, "object": obj, "frame": k, "uv": uv,
                                "camera_node": nodes[prefix+"camera"], "spread_node": nodes[prefix+"spread"],
                                "correction_initial": correction, "group": self.group})
            out.append((nodes[prefix+"f1"], nodes[prefix+"spread"]))
        return out

    def points_id(self, obj, iid, k, kind="middle", other=None):
        self.group = "g" + str(len(self.groups))
        self.groups.append({"id": self.group, "object": obj, "instance_id": iid,
                            "frame": k, "purpose": kind, "toward_id": other[0] if isinstance(other, tuple) else other})
        uv = self.scene.select(iid, k, kind, other)
        nodes = []
        want_correction = self.config.get("edge_correction", False) and not self.exact_reference
        if want_correction:
            edge = self.scene.edge_example(iid, k, uv)
            if edge:
                initial, (nxt, _) = edge
                _, spread = self.click(obj, iid, k, initial, correction=True)
                self.tr.add("assistant", "correction", frame=k, initial=initial, next=nxt,
                            toward=rounded(np.mean(uv, axis=0), 2), spread_node=spread)
                node, s = self.click(obj, iid, k, nxt)
                if self.tr.values[s] > .25:
                    raise Refusal("unresolved_edge_correction")
                nodes.append(node)
                uv = uv[:2]
        for node, s in self.click_batch(obj, iid, k, uv):
            if self.tr.values[s] > .25:
                raise Refusal("unresolved_edge_correction")
            nodes.append(node)
        if not 2 <= len(nodes) <= 4:
            raise Refusal("grounded_click_count")
        return nodes

    def points(self, obj, kind="middle", other=None, k=None, many=False):
        ids = self.scene.ids(obj, many=many)
        other_ids = self.scene.ids(other, many=many) if other else [None]
        out = []
        for iid in ids:
            successes = []
            for oi in other_ids:
                if oi is not None and k is None:
                    chosen, other_frame = self.choose_frames(iid, oi, obj, other)
                    successes.extend(self.points_id(obj, iid, chosen, kind, (oi, other_frame)))
                    continue
                frames = [k] if k is not None else self.scene.anchors
                chosen = None
                for frame in frames:
                    # Pick a view by mask visibility, never by whether its answer matches.
                    if not np.any(self.scene.gt.inst[frame-1] == iid):
                        continue
                    if oi is not None and not np.any(self.scene.gt.inst[frame-1] == oi):
                        continue
                    chosen = frame
                    break
                if chosen is None:
                    raise Refusal("no_supported_joint_view", obj)
                successes.extend(self.points_id(obj, iid, chosen, kind, oi))
            out.extend(successes)
        return out

    def centre(self, obj, k=None):
        if k is None and obj in self.centres:
            return self.centres[obj]
        return self.tr.calc("mean", *self.points(obj, k=k), unit="m", meaning="mean of observable object clicks")

    def visible(self, iid):
        return [k for k in self.scene.anchors if int(np.sum(self.scene.gt.inst[k-1] == iid)) >= self.scene.programs.MIN_PX]

    def choose_frames(self, aid, bid, a, b):
        selection_id = "s" + str(len(self.frame_bindings))
        self.frame_bindings[selection_id] = [aid, bid]
        A, B = self.visible(aid), self.visible(bid)
        common = sorted(set(A) & set(B))
        if common:
            k = common[0]
            self.tr.add("assistant", "frame_choice", selection_id=selection_id, objects=[a, b], selected=[k, k], candidates=[],
                        reason=f"Frame {k} shows both objects; use this common frame.")
            return k, k
        if not A or not B: raise Refusal("no_supported_visible_frame_pair")
        choices = []
        for i in A:
            for j in B:
                pi, pj = self.pose(i), self.pose(j)
                movement = self.move(i, j)
                distance = movement["distance"]
                f = self.tr.calc("matvec", pj["level_R"], [0, 0, 1], unit="m")
                f = self.tr.calc("local", pi["level_R"], f, unit="m")
                z = self.tr.calc("z", f, unit="m")
                x = self.tr.calc("x", f, unit="m")
                nx = self.tr.calc("scale", x, -1, unit="m")
                yaw = self.tr.calc("atan2", nx, z, unit="degree", meaning="positive yaw means left")
                absolute = self.tr.calc("abs", yaw, unit="degree")
                penalty = self.tr.calc("scale", absolute, .02, unit="m", meaning="SPEC v3 yaw degrees / 50 ranking penalty")
                score = self.tr.calc("add", distance, penalty, unit="m", meaning="SPEC v3 r = norm(move) + abs(yaw)/50")
                choices.append({"frames": [i, j], "distance": distance, "yaw": yaw, "score": score})
        best = min(choices, key=lambda c: (self.tr.values[c["score"]], abs(c["frames"][0]-c["frames"][1]), *c["frames"]))
        i, j = best["frames"]
        self.tr.add("assistant", "frame_choice", selection_id=selection_id, objects=[a, b], selected=[i, j], candidates=choices,
                    reason=f"No frame shows both; frames {i} and {j} minimize printed r = norm(move) + abs(yaw)/50; ties use smaller frame gap.")
        return i, j

    def prepare_centres(self, objects):
        objects = list(dict.fromkeys(objects))
        if len(objects) > 12: raise Refusal("too_many_route_referents")
        ids = {obj: self.scene.ids(obj)[0] for obj in objects}
        visible = [set(self.visible(i)) for i in ids.values()]
        common = sorted(set.intersection(*visible))
        if common:
            k = common[0]
            selection_id = "s" + str(len(self.frame_bindings))
            self.frame_bindings[selection_id] = [ids[obj] for obj in objects]
            self.tr.add("assistant", "frame_choice", selection_id=selection_id, objects=objects, selected=[k]*len(objects), candidates=[],
                        reason=f"Frame {k} shows all referents; use one common frame.")
            for obj in objects:
                self.centres[obj] = self.tr.calc("mean", *self.points_id(obj, ids[obj], k), unit="m", meaning="observable centre")
        else:
            from itertools import combinations
            nodes = {obj: [] for obj in objects}
            for a, b in combinations(objects, 2):
                i, j = self.choose_frames(ids[a], ids[b], a, b)
                nodes[a].extend(self.points_id(a, ids[a], i))
                nodes[b].extend(self.points_id(b, ids[b], j))
            for obj in objects:
                self.centres[obj] = self.tr.calc("mean", *nodes[obj], unit="m", meaning="mean of observable centres across minimum-pose pairs")

    def closest(self, A, B):
        ds = [self.tr.distance(a, b) for a in A for b in B]
        value = self.tr.calc("min", *ds, unit="m", meaning="closest: minimum of all printed point-pair distances")
        # Cross-check the reused canonical helper on displayed points.
        canonical = self.scene.programs.closest_sets(np.array([self.tr.values[a] for a in A]),
                                                     np.array([self.tr.values[b] for b in B]))
        if abs(canonical - self.tr.values[value]) > .0050001:
            raise Refusal("canonical_closest_disagreement")
        return value

    def bearing(self, S, F, Q):
        u = self.tr.calc("sub", F, S, unit="m", meaning="u = facing - stand")
        v = self.tr.calc("sub", Q, S, unit="m", meaning="v = query - stand")
        return self.tr.angle(u, v)

    def decision(self, mode, nodes, labels=None, **extra):
        vals = [self.tr.values[n] for n in nodes]
        if mode in ("direction", "route") and any(abs(v) in (0, 90, 135, 180) for v in vals):
            # Whole-angle classifiers must not contradict the printed cross/dot
            # signs at a rounded boundary. Numeric and cross-only programs
            # retain their separately defined semantics.
            raise Refusal("rounding_boundary")
        if mode == "numeric": result = vals[0]
        elif mode == "compare_count": result = "more" if vals[0] > vals[1] else "fewer" if vals[0] < vals[1] else "equal number"
        elif mode == "cross_direction":
            if vals[0] == 0: raise Refusal("direction_tie")
            result = "left" if vals[0] > 0 else "right"
        elif mode == "direction": result = self.T.direction_label(extra["family"], vals[0])
        elif mode == "argmin":
            order = sorted(range(len(vals)), key=lambda i: vals[i])
            if len(order) < 2 or abs(vals[order[0]] - vals[order[1]]) < 1e-6:
                raise Refusal("distance_tie")
            result = labels[order[0]]
        elif mode == "argmax":
            order = sorted(range(len(vals)), key=lambda i: -vals[i])
            if len(order) < 2 or abs(vals[order[0]] - vals[order[1]]) < 1e-6:
                raise Refusal("movement_tie")
            result = labels[order[0]]
        elif mode == "less":
            if abs(vals[0] - vals[1]) < 1e-6: raise Refusal("position_tie")
            result = labels[0 if vals[0] < vals[1] else 1]
        elif mode == "order":
            if len(set(vals)) != len(vals): raise Refusal("appearance_tie")
            result = ", ".join(labels[i] for i in sorted(range(len(vals)), key=lambda i: vals[i]))
        elif mode == "route":
            result = ", ".join("Turn Back" if abs(v) >= 135 else "Turn Left" if v > 0 else "Turn Right" for v in vals)
        else: raise Refusal("unknown_decision")
        self.tr.add("assistant", "decision", mode=mode, nodes=nodes, labels=labels,
                    result=result, **extra)
        return result

    def counting(self, cat):
        run = self.count_run
        self.count_run += 1
        ids = self.scene.ids(cat, many=True)
        clusters, seen_ids = [], set()
        for k in self.scene.anchors:
            for iid in ids:
                if not any(i == iid for i, _ in self.scene.ground.masks(cat, k)):
                    continue
                P = self.points_id(cat, iid, k)
                seen_ids.add(iid)
                c = self.tr.calc("mean", *P, unit="m", meaning="instances: visible detection centre")
                ext = self.tr.calc("max", *[self.tr.distance(a, b) for a in P for b in P],
                                   unit="m", meaning="extent of this detection's clicked points")
                checks, candidates = [], []
                for j, cluster in enumerate(clusters):
                    d = self.tr.distance(c, cluster["centre"])
                    small = self.tr.calc("min", ext, cluster["extent"], unit="m")
                    half = self.tr.calc("scale", small, .5, unit="m")
                    threshold = self.tr.calc("max", half, .35, unit="m", meaning="merge threshold max(0.35 m, half smaller extent)")
                    checks.append({"distance": d, "threshold": threshold, "cluster": j+1})
                    if self.tr.values[d] < self.tr.values[threshold] and k not in cluster["frames"]:
                        candidates.append(j)
                if len(candidates) > 1: raise Refusal("ambiguous_instance_merge")
                if candidates:
                    j = candidates[0]
                    clusters[j]["members"].append(c)
                    clusters[j]["centre"] = self.tr.calc("mean", *clusters[j]["members"], unit="m", meaning="merged instance centre")
                    clusters[j]["frames"].add(k)
                    clusters[j]["ids"].add(iid)
                else:
                    j = len(clusters)
                    clusters.append({"centre": c, "extent": ext, "members": [c], "frames": {k}, "ids": {iid}})
                self.tr.add("assistant", "merge", detection=c, cluster=j+1, checks=checks, frame=k, extent=ext, category=cat, count_run=run)
        if seen_ids != set(ids): raise Refusal("unobservable_count_instance")
        if any(len(c["ids"]) != 1 for c in clusters) or len(clusters) != len(ids):
            raise Refusal("observable_merge_disagrees_with_identity")
        return self.tr.calc("count", *[c["centre"] for c in clusters], unit="count", meaning="count merged instances")

    def appearance(self, cats):
        firsts = []
        for obj in cats:
            self.scene.ids(obj, many=True)
            visible = []
            for k in range(1, 33):
                points = [np.rint(self.scene.ground.interior(m)).astype(int).tolist()
                          for _, m in self.scene.appearance_masks(obj, k)]
                for uv in points:
                    x, y = self.scene.gt.px([uv])
                    if self.scene.gt.inst[k-1, y[0], x[0]] not in self.scene.ids(obj, many=True):
                        raise Refusal("rounded_click_outside_mask")
                self.tr.add("assistant", "click", object=obj, frame=k, points=points)
                if points: visible.append(k)
            if not visible: raise Refusal("never_visible", obj)
            node = self.tr.calc("min", *visible, unit="frame", meaning=f"first_seen({obj}): earliest frame with an assistant RGB click")
            firsts.append(node)
        return self.decision("order", firsts, cats)

    def room(self, plan):
        corners = plan.get("floor_corners")
        if not corners or len(corners) < 3 or not plan.get("floor_polygon_reviewed"):
            defer("missing_reviewed_floor_corners")
        points = []
        for corner in corners:
            k = self.frame(corner["frame"], depth=True)
            iid, = self.scene.ids(corner["object"])
            if self.scene.gt.labels[list(self.scene.gt.ids).index(iid)].lower() != "floor":
                raise Refusal("floor_corner_not_floor")
            point, spread = self.click(corner["object"], iid, k, corner["uv"])
            if self.tr.values[spread] > .25: raise Refusal("unresolved_floor_corner")
            points.append(point)
        coords = np.array([self.tr.values[p] for p in points])
        if np.ptp(coords[:, 1]) > .1: raise Refusal("nonplanar_floor")
        # Refuse self-intersections rather than emitting a spurious shoelace area.
        xz = coords[:, [0, 2]]
        for i in range(len(xz)):
            a, b = xz[i], xz[(i+1) % len(xz)]
            for j in range(i+2, len(xz)):
                if i == 0 and j == len(xz)-1: continue
                c, d = xz[j], xz[(j+1) % len(xz)]
                cross = lambda x, y: x[0]*y[1]-x[1]*y[0]
                if cross(b-a, c-a)*cross(b-a, d-a) < 0 and cross(d-c, a-c)*cross(d-c, b-c) < 0:
                    raise Refusal("self_intersecting_floor_polygon")
        return self.tr.calc("shoelace", *points, unit="m2", meaning="floor_area: absolute shoelace sum / 2")

    def execute(self, row, reviewed=None):
        q = question(row)
        plan = bind(q, self.T, reviewed)
        t = q["question_type"]
        # Bind qualified RGB referents only in this row's scene copy.
        self.scene = copy.copy(self.scene)
        self.scene.referent_ids = plan.get("referent_ids", {})
        display = unit_policy(q, self.config, reviewed)
        self.tr.events.insert(0, {"role": "assistant", "kind": "plan", "target_loss": 1, "text": "PLAN pending"})
        if t in ("object_counting", "absolute_count"): value = self.counting(plan["cat"])
        elif t == "relative_count":
            result = self.decision("compare_count", [self.counting(plan["a"]), self.counting(plan["b"])])
        elif t == "relative_size_object":
            scores = []
            for obj in (plan["a"], plan["b"]):
                A = self.points(obj, "extent")
                scores.append(self.tr.calc("max", *[self.tr.distance(a, b) for a in A for b in A], unit="m"))
            result = self.decision("argmin" if plan["comparison"] == "shorter" else "argmax", scores, [plan["a"], plan["b"]])
        elif t == "obj_appearance_order": result = self.appearance(plan["cats"])
        elif t == "room_size_estimation": value = self.room(plan)
        elif t in ("object_abs_distance", "absolute_distance_object"):
            A = self.points(plan["a"], "facing", plan["b"])
            B = self.points(plan["b"], "facing", plan["a"])
            value = self.closest(A, B)
        elif t in ("object_size_estimation", "absolute_size_object"):
            A = self.points(plan["a"], "extent")
            value = self.tr.calc("max", *[self.tr.distance(a, b) for a in A for b in A], unit="m", meaning="extent: maximum printed point-pair norm")
        elif t in ("object_rel_distance", "relative_distance_object"):
            scores = [self.closest(self.points(plan["target"], "facing", obj, many=True),
                                   self.points(obj, "facing", plan["target"], many=True)) for obj in plan["cands"]]
            result = self.decision("argmin", scores, plan["cands"])
        elif t.startswith("object_rel_direction") or t in ("relative_direction_object", "absolute_direction_object"):
            self.prepare_centres([plan[key] for key in ("stand", "face", "query")])
            angle = self.bearing(*[self.centre(plan[key]) for key in ("stand", "face", "query")])
            if t == "absolute_direction_object":
                value = self.tr.calc("mod", angle, 360, unit="degree", meaning="counterclockwise whole degrees")
            elif t == "relative_direction_object":
                result = self.decision("cross_direction", [self.tr.last_cross], family=t)
            else: result = self.decision("direction", [angle], family=t)
        elif t == "route_planning":
            self.prepare_centres([plan["start"], plan["face"]] + [obj for kind, obj in plan["plan"] if kind == "go"])
            here, face = self.centre(plan["start"]), self.centre(plan["face"])
            heading = self.tr.calc("sub", face, here, unit="m", meaning="initial route heading")
            turns = []
            for i, (kind, obj) in enumerate(plan["plan"]):
                if kind == "go":
                    nxt = self.centre(obj)
                    heading = self.tr.calc("sub", nxt, here, unit="m", meaning="route segment heading")
                    here = nxt
                else:
                    obj = next((o for kind, o in plan["plan"][i+1:] if kind == "go"), None)
                    if not obj: raise Refusal("underspecified_route")
                    nxt = self.centre(obj)
                    direction = self.tr.calc("sub", nxt, here, unit="m", meaning="route next - here")
                    turns.append(self.tr.angle(heading, direction))
                    heading = direction
            result = self.decision("route", turns)
        elif t in ("camera_displacement", "camera_movement_direction", "camera_rotation"):
            i, j = self.frame(plan["i"]), self.frame(plan["j"])
            pi, pj = self.pose(i), self.pose(j)
            movement = self.move(i, j)
            local = movement["delta"]
            if t == "camera_displacement": value = movement["distance"]
            elif t == "camera_rotation":
                forward = self.tr.calc("matvec", pj["level_R"], [0, 0, 1], unit="m")
                local_f = self.tr.calc("local", pi["level_R"], forward, unit="m")
                # u is forward in L_i; cross= -v_x, so positive yaw is left.
                value = self.tr.angle(self.tr.calc("stack", 0, 0, 1, unit="m"), local_f)
            else:
                x = self.tr.calc("x", local, unit="m")
                z = self.tr.calc("z", local, unit="m")
                nx = self.tr.calc("scale", x, -1, unit="m")
                nz = self.tr.calc("scale", z, -1, unit="m")
                scores = {"forward": z, "backward": nz, "right": x, "left": nx}
                labels = [v.strip().lower() for v in self.T.option_texts(q["options"]).values()]
                if any(v not in scores for v in labels): raise Refusal("unsupported_movement_option")
                result = self.decision("argmax", [scores[v] for v in labels], labels)
        else:
            k = self.frame(plan["k"], depth=True)
            cam = self.pose(k)["t"]
            if t == "camera_obj_abs_dist":
                value = self.tr.calc("min", *[self.tr.distance(p, cam) for p in self.points(plan["obj"], "facing", k=k, many=True)],
                                     unit="m", meaning="nearest observable point to camera")
            elif t.startswith("camera_obj_rel_dist"):
                scores = [self.tr.calc("min", *[self.tr.distance(p, cam) for p in self.points(obj, "facing", k=k, many=True)],
                                       unit="m") for obj in plan["cands"]]
                result = self.decision("argmin", scores, plan["cands"])
            else:
                a, b = self.centre(plan["a"], k), self.centre(plan["ref"], k)
                if t.endswith("_nf"):
                    nodes = [self.tr.distance(a, cam), self.tr.distance(b, cam)]; labels = ["near", "far"]
                elif t.endswith("_ud"):
                    nodes = [self.tr.calc("local", self.pose(k)["level_R"], self.tr.calc("sub", p, cam, unit="m"), unit="m") for p in (a, b)]
                    nodes = [self.tr.calc("y", n, unit="m") for n in nodes]; labels = ["up", "down"]
                else:
                    nodes = [self.tr.calc("local", self.pose(k)["R"], self.tr.calc("sub", p, cam, unit="m"), unit="m") for p in (a, b)]
                    nodes = [self.tr.calc("x", n, unit="m") for n in nodes]; labels = ["left", "right"]
                result = self.decision("less", nodes, labels)
        if t in NUMERIC:
            converted = self.tr.calc("scale", value, display["factor"], unit=display["unit"], meaning="explicit conversion to question unit")
            raw = self.decision("numeric", [converted], display=display)
            quantum = 10 ** -display["decimals"]
            # Refuse half-quantum boundaries, where display precision may flip a label.
            if abs((raw / quantum) % 1 - .5) < 1e-5:
                raise Refusal("rounding_boundary", "numeric display boundary")
            answer = round(raw, display["decimals"])
            if display["decimals"] == 0: answer = int(answer)
        else:
            answer = self.T.letter_of(q["options"], result)
            if answer is None: raise Refusal("option_content_mismatch", result)
        choices = [e["reason"] for e in self.tr.events if e["kind"] == "frame_choice"]
        frames = sorted({e["frame"] for e in self.tr.events if e["kind"] == "click"})
        if t == "obj_appearance_order":
            text = "PLAN: I will inspect all 32 RGB frames for each named category, record its first visible click, and compare the resulting order with the options."
        elif t in ("camera_displacement", "camera_movement_direction", "camera_rotation"):
            text = "PLAN: I will query the requested camera frames with the pose and scale heads, use gravity to align them, and derive the displacement, movement scores or signed yaw from the printed poses."
        else:
            method = ("I will compare candidate points on the facing surfaces and take the smallest printed pairwise distance. "
                      if "distance" in t or "_dist" in t else "I will derive the answer from the printed point measurements and compare it with the question's choices or units. ")
            if t in ("absolute_count", "relative_count", "object_counting"):
                method = "I will merge detections using printed centre distances and thresholds, count each named category, and compare the counts in the supplied option order. "
            elif t in ("absolute_size_object", "object_size_estimation", "relative_size_object"):
                method = "I will measure the longest printed pairwise extent for each object. "
                if t == "relative_size_object": method += f"I will select the {plan['comparison']} extent and match that object's option. "
            elif t in ("relative_direction_object", "absolute_direction_object") or t.startswith("object_rel_direction"):
                method = "I will subtract the standing point from the facing and query points, then print floor dot, cross and the whole-degree angle. "
                method += "I will reduce the angle modulo 360 for counterclockwise degrees. " if t == "absolute_direction_object" else "I will compare the resulting direction with the options. "
            referents = list(dict.fromkeys(v for key in ("cat", "a", "b", "target", "stand", "face", "query", "obj", "ref") if isinstance((v := plan.get(key)), str)))
            referents += [x for x in plan.get("cands", []) if x not in referents]
            text = ("PLAN: I will locate " + ", ".join(referents) + " in " + ", ".join("frame "+str(k) for k in frames) + ". "
                    + (" ".join(dict.fromkeys(choices)) if choices else "These supported anchors show the required objects.")
                    + " I will query depth with the depth and FoV heads; the fixed unprojection and pose layer uses gravity, scale and pose to print camera points and frame-1 points with y up. " + method)
        substitutions = [e["text"] for e in self.tr.events if e["kind"] == "substitution"]
        text += " " + " ".join(dict.fromkeys(substitutions)) if substitutions else ""
        self.tr.events[0]["text"] = text
        frame_choices = [e for e in self.tr.events if e["kind"] == "frame_choice"]
        branch = {"family": t, "referents": {k: plan[k] for k in ("cat", "a", "b", "target", "cands", "stand", "face", "query", "cats", "obj", "ref", "start", "goal") if k in plan},
                  "frames": frames, "frame_choices": frame_choices,
                  "requested_frames": {key: plan[key] for key in ("i", "j", "k") if key in plan},
                  "pose_frames": sorted({e["arguments"]["frame"] for e in self.tr.events if e["kind"] == "tool_call" and e["name"] == "pose"}),
                  "frame_strategy": "cross_frame" if any(len(set(e["selected"])) > 1 for e in frame_choices) else "common_or_single_frame",
                  "measurement_strategy": "candidate_facing_pairs_minimum" if any(g["purpose"] == "facing" for g in self.groups) else "extreme_point_extent" if any(g["purpose"] == "extent" for g in self.groups) else "middle_points_or_rgb",
                  "route_blanks": [i for i, (kind, _) in enumerate(plan.get("plan", [])) if kind == "turn"],
                  "substitutions": [{k: e[k] for k in ("requested_frame", "effective_frame")} for e in self.tr.events if e["kind"] == "substitution"],
                  "measurement_groups": [{k: g[k] for k in ("object", "frame", "purpose")} for g in self.groups],
                  "counting": [{"category": e["category"], "cluster": e["cluster"], "frame": e["frame"]} for e in self.tr.events if e["kind"] == "merge"],
                  "comparison": plan.get("comparison"),
                  "corrections": sum(e["kind"] == "correction" for e in self.tr.events),
                  "decisions": [e for e in self.tr.events if e["kind"] == "decision"],
                  "argon_bank_integrated": False}
        projection = render(self.tr.events, answer, include_spans=True)
        return {"schema": "derivgen-row-v1", "readout_mode": "gt", "answer_policy": "gt_and_faithful_equal",
                "infrastructure_only": bool(self.scene.entry.get("infrastructure_only")),
                "qid": row["qid"], "question_type": t, "question": q["question"], "options": q["options"],
                "answer": answer, "events": self.tr.events, "plan_branch": branch, **projection,
                "display": display, "convention": CONVENTION,
                "private": {"clicks": self.clicks, "bindings": plan,
                            "groups": self.groups,
                            "frame_bindings": self.frame_bindings,
                            "source_question_sha256": digest(q), "gt": self.scene.entry["gt"],
                            "frame_indices": self.scene.entry["frame_indices"]}}


def generate(scene, T, config, row, reviewed=None):
    record = Program(scene, T, config).execute(row, reviewed)
    q = question(row)
    plan = record["private"]["bindings"]
    if q["question_type"] in F17:
        from .replay import native_reference
        bound_scene = copy.copy(scene)
        bound_scene.referent_ids = plan.get("referent_ids", {})
        record["private"]["native_reference"] = native_reference(bound_scene, T, q, plan)
    if any(e["kind"] == "substitution" for e in record["events"]):
        exact_scene = copy.copy(scene)
        exact_scene.allow_exact_reference = True
        reference = Program(exact_scene, T, {**config, "edge_correction": False}, exact_reference=True).execute(row, reviewed)
        if q["question_type"] in F17:
            reference["private"]["native_reference"] = record["private"]["native_reference"]
        if reference["answer"] != record["answer"]:
            raise Refusal("odd_anchor_exact_reference_disagreement")
        record["private"]["exact_reference"] = reference
    return record
