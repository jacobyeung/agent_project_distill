"""Observable clicks on GT rasters; raw world coordinates remain private."""
import math
import re
import copy
from collections import OrderedDict

import numpy as np
from scipy import ndimage

from .common import ProvenanceError, Refusal, defer, pinned, read_json, rounded


def frame_intrinsics(gt, k):
    """Return the requested frame's calibration, with legacy median-K fallback."""
    frames = getattr(gt, "K_frames", None)
    return gt.K if frames is None else frames[k - 1]


def calibrated_source(programs, path, frames):
    """Extend the pinned adapter locally without changing its depth statistics.

    A shallow per-call view supplies Kinv to the adapter's lift/dense methods;
    neither a shared adapter nor its median K is mutated during unprojection.
    """
    if frames is None:
        return programs.GTSource(path)

    class FrameGTSource(programs.GTSource):
        def lift(self, k, uv, mode="p30"):
            view = copy.copy(self)
            view.Kinv = self.Kinv_frames[k - 1]
            return programs.GTSource.lift(view, k, uv, mode)

        def dense(self, k, step=4):
            view = copy.copy(self)
            view.Kinv = self.Kinv_frames[k - 1]
            return programs.GTSource.dense(view, k, step)

    gt = FrameGTSource(path)
    gt.K_frames = frames
    gt.Kinv_frames = np.linalg.inv(frames)
    return gt


class MaskCache(OrderedDict):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        while len(self) > 64: self.popitem(last=False)


def rgb_hashes(frames):
    if not isinstance(frames, list) or any(not isinstance(f, dict) or not isinstance(f.get("sha256"), str) for f in frames):
        return None
    return [f["sha256"] for f in frames]


def level_basis(rotation):
    down = np.array([0., 0., -1.])
    forward = np.asarray(rotation[:, 2], float).copy()
    forward[2] = 0
    if np.linalg.norm(forward) < 1e-6:
        raise Refusal("vertical_camera_heading")
    forward /= np.linalg.norm(forward)
    right = np.cross(down, forward)
    return np.column_stack((right, down, forward))


def anchor(k, depth=False):
    if type(k) is not int or k < 1 or k > 32:
        raise Refusal("frame_out_of_range")
    if (k % 2 and k != 1) or (depth and k == 1):
        defer("unsupported_exact_odd_frame", str(k))


def native_annotations(pin):
    """Normalize source half/full extents explicitly; preserve source metadata."""
    source = read_json(pinned(pin, missing_row=True))
    if not source.get("provider_axesLengths") or not source.get("box_convention"):
        # These provider documents were read and bound to exact prepared bytes.
        # Dataset names, filenames and geometric magnitudes grant no convention.
        from pathlib import Path
        rule = None
        refusal = None
        for folder, manifest_sha256 in (
            ("scene_refusals_01", "7d46c9ee6a4d5ba309fece4d4aa30b1e7b2f7993a0fbcc2badffbb2d1bb8a425"),
            ("scene_refusals_02", "f66f3166949d1f9d84cf4994bcda7f2df42f4603dca8d7c13f8233fb5de3c2d6"),
            ("scene_refusals_03", "5deb7560789c1d8066a4b6347991c3562de4ce94fc73a2f3afd6cc0ee4036934"),
        ):
            evidence_dir = Path(__file__).resolve().parents[2] / "out" / folder
            evidence = {"path": str(evidence_dir / "PROVIDER_RULES.json"),
                        "sha256": manifest_sha256}
            rules = read_json(pinned(evidence))
            rule = rules.get("rules", {}).get(pin["sha256"])
            refusal = rules.get("refusals", {}).get(pin["sha256"], refusal)
            if rule is not None:
                break
        missing = [k for k in ("provider_axesLengths", "box_convention") if not source.get(k)]
        if rule is None:
            raise ProvenanceError("native annotation missing " + ", ".join(missing)
                                  + "; no verified provider rule for SHA256 " + pin["sha256"]
                                  + ("; " + refusal["reason"] if refusal else ""))
        documents = [{**document, "path": str(evidence_dir / Path(document["path"]).name)}
                     for document in rule["documents"]]
        for document in documents:
            pinned(document)
        for key, value in rule["declaration"].items():
            if key in source and source[key] != value:
                raise ProvenanceError("native annotation/provider convention conflict: " + key)
        source = {**source, **rule["declaration"], "box_convention_evidence": {
            "manifest": evidence, "annotation_sha256": pin["sha256"],
            "source_path": rule["source_path"], "documents": documents}}
    convention = source.get("provider_axesLengths")
    if convention not in ("half_extents", "full_extents") or not source.get("box_convention"):
        raise ProvenanceError("native annotation extent/box convention must be explicit")
    objects = {}
    for g in source["segGroups"]:
        iid = int(g["id"])
        if iid in objects: raise ProvenanceError("duplicate native instance id")
        box = g["obb"]
        c, length, axes = np.array(box["centroid"], float), np.array(box["axesLengths"], float), np.array(box["normalizedAxes"], float).reshape(3, 3)
        if (c.shape != (3,) or length.shape != (3,) or not np.isfinite(c).all()
                or not np.isfinite(length).all() or np.any(length < 0) or not np.isfinite(axes).all()
                or not np.allclose(axes @ axes.T, np.eye(3), atol=1e-5)):
            raise ProvenanceError("native annotation box schema")
        objects[iid] = {"label": g["label"], "centroid": c, "lengths": length*(2 if convention == "half_extents" else 1), "axes": axes}
    return source, objects


def reconcile_native_labels(annotations, visibility):
    """Keep native spelling; require exact alias class membership for differences."""
    labels = {}
    for group in annotations["segGroups"]:
        iid = str(group["id"])
        if iid in labels:
            raise ProvenanceError("duplicate native instance id: " + iid)
        labels[iid] = group["label"]
    visible = visibility["labels"]
    if labels.keys() != visible.keys():
        raise ProvenanceError("annotation/visibility instance inventory differs: native_only="
                              + str(sorted(labels.keys() - visible.keys())) + " visibility_only="
                              + str(sorted(visible.keys() - labels.keys())))
    reconciled = []
    for iid, label in labels.items():
        other = visible[iid]
        if label == other:
            continue
        # An alias may also contain instances already spelled exactly like it.
        native_ids = {int(i) for i, value in labels.items() if value in (label, other)}
        visible_ids = {int(i) for i, value in visible.items() if value == other}
        alias = visibility.get("aliases", {}).get(other, {})
        ids = alias.get("instance_ids", [])
        if (alias.get("source_label") != other or not ids
                or any(type(i) is not int for i in ids) or len(set(ids)) != len(ids)
                or set(ids) != native_ids or visible_ids != native_ids):
            raise ProvenanceError(f"annotation/visibility labels disagree at instance {iid}: "
                                  f"native={label!r}, visibility={other!r}; "
                                  "no exact visibility alias with identical class instance IDs")
        reconciled.append({"instance_id": int(iid), "native_label": label,
                           "visibility_label": other, "alias": alias})
    return labels, reconciled


class GTScene:
    allow_exact_reference = False

    def check_rgb_input(self, student_input, required=False):
        frames = student_input.get("frames")
        if frames is None or frames == []:
            if required: defer("missing_rgb_input_join")
            return
        if rgb_hashes(frames) != rgb_hashes(self.rgb_manifest["frames"]):
            raise Refusal("rgb_input_hash_mismatch")
        if student_input.get("rgb_manifest", self.entry["rgb_manifest"]) != self.entry["rgb_manifest"]:
            raise Refusal("rgb_input_manifest_mismatch")

    def check(self, k, depth=False):
        if self.allow_exact_reference or getattr(self, "head_layout", "paired_anchor") == "per_frame":
            if type(k) is not int or not 1 <= k <= 32:
                raise Refusal("frame_out_of_range")
        else:
            anchor(k, depth)

    def __init__(self, entry, programs):
        self.entry, self.programs = entry, programs
        path = pinned(entry["gt"], missing_row=True)
        # All evidence is pinned before the adapter is allowed to open an NPZ.
        selection = read_json(pinned(entry["selection"], missing_row=True))
        if (selection.get("canonical") != entry["canonical"]
                or selection.get("frame_indices") != entry["frame_indices"]
                or selection.get("verified") is not True):
            raise ProvenanceError("selection evidence mismatch")
        rgb = read_json(pinned(entry["rgb_manifest"], missing_row=True))
        binding = entry.get("rgb_binding", "byte_verified")
        if binding not in ("byte_verified", "identity_only"):
            raise ProvenanceError("unknown RGB binding")
        identity = binding == "identity_only"
        if (rgb.get("canonical") != entry["canonical"]
                or (not identity and rgb.get("verified") is not True)
                or (identity and (rgb.get("verified") is not False or rgb.get("binding") != binding))
                or rgb.get("frame_indices") != entry["frame_indices"]
                or len(rgb.get("frames", [])) != 32):
            raise ProvenanceError("RGB evidence mismatch")
        for index, frame in zip(entry["frame_indices"], rgb["frames"]):
            if type(frame.get("source_index")) is not int or frame["source_index"] != index:
                raise ProvenanceError("RGB selection mismatch")
            if identity:
                if (not isinstance(frame.get("path"), str) or not frame["path"]
                        or not isinstance(frame.get("sha256"), str)
                        or not re.fullmatch(r"[0-9a-fA-F]{64}", frame.get("sha256", ""))):
                    raise ProvenanceError("invalid identity-only RGB frame")
            else:
                pinned(frame, missing_row=True)
        self.rgb_manifest = rgb
        labels = read_json(pinned(entry["label_provenance"], missing_row=True))
        if (labels.get("canonical") != entry["canonical"] or labels.get("verified") is not True
                or labels.get("basis") != "native_instance_annotations"):
            raise ProvenanceError("label provenance is not native/verified")
        if not entry.get("native_annotations"):
            defer("missing_native_annotation_provenance")
        self.native_source, self.native = native_annotations(entry["native_annotations"])
        with np.load(path, allow_pickle=False) as z:
            required = {"depth", "inst", "K", "c2w", "valid", "ids", "labels",
                        "obb_centroid", "obb_lengths", "obb_axes", "frame_indices"}
            if not required <= set(z.files):
                raise ProvenanceError("NPZ missing required arrays")
            d, inst, K, poses, valid = (z[k] for k in ("depth", "inst", "K", "c2w", "valid"))
            K_frames = z["K_frames"] if "K_frames" in z.files else None
            if K_frames is not None and (
                    K_frames.shape != (32, 3, 3) or not np.isfinite(K_frames).all()
                    or np.any(np.linalg.det(K_frames) <= 0)
                    or np.any(K_frames[:, (0, 1), (0, 1)] <= 0)
                    or not np.allclose(K_frames[:, 2], [0, 0, 1])
                    or not np.allclose(K, np.median(K_frames, axis=0), rtol=0, atol=1e-8)):
                raise ProvenanceError("invalid per-frame intrinsics or median K")
            n = len(z["ids"])
            if (d.ndim != 3 or d.shape[0] != 32 or min(d.shape[1:]) < 5
                    or inst.shape != d.shape or K.shape != (3, 3) or poses.shape != (32, 4, 4)
                    or valid.shape != (32,) or z["labels"].shape != (n,)
                    or z["obb_centroid"].shape != (n, 3) or z["obb_lengths"].shape != (n, 3)
                    or z["obb_axes"].shape not in ((n, 9), (n, 3, 3))):
                raise ProvenanceError("NPZ shape mismatch")
            if z["frame_indices"].tolist() != entry["frame_indices"]:
                raise ProvenanceError("NPZ exact frame alignment mismatch")
            if (not np.isfinite(d).all() or np.any(d < 0) or not np.isfinite(K).all()
                    or np.linalg.det(K) <= 0 or K[0, 0] <= 0 or K[1, 1] <= 0
                    or not np.allclose(K[2], [0, 0, 1])
                    or not np.isfinite(poses).all()):
                raise ProvenanceError("nonfinite/invalid matrices")
            for pose in poses:
                R = pose[:3, :3]
                if (not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6)
                        or not np.allclose(R.T @ R, np.eye(3), atol=1e-5)
                        or abs(np.linalg.det(R) - 1) > 1e-5):
                    raise ProvenanceError("c2w is not an OpenCV rigid transform")
            ids = z["ids"].tolist()
            if (len(set(ids)) != n or not np.issubdtype(z["ids"].dtype, np.integer)
                    or not np.issubdtype(inst.dtype, np.integer)
                    or not set(np.unique(inst)) <= set(ids) | {-1}
                    or {str(i): str(l) for i, l in zip(ids, z["labels"])} != labels.get("labels")):
                raise ProvenanceError("NPZ instance/label provenance mismatch")
            if set(ids) != set(self.native): raise ProvenanceError("native annotation/NPZ ids mismatch")
            for ix, iid in enumerate(ids):
                native = self.native[iid]
                if (native["label"] != str(z["labels"][ix])
                        or not np.allclose(z["obb_centroid"][ix], native["centroid"], atol=1e-6, rtol=0)
                        or not np.allclose(z["obb_lengths"][ix], native["lengths"], atol=1e-6, rtol=0)
                        or not np.allclose(z["obb_axes"][ix].reshape(3, 3), native["axes"], atol=1e-6, rtol=0)):
                    raise ProvenanceError("NPZ boxes changed native annotation convention")
        self.gt = calibrated_source(programs, path, K_frames)
        self.ground = programs.GTGround(self.gt)
        self.ground.cache = MaskCache()
        if not self.gt.has(1):
            defer("missing_reference_pose")
        self.basis = level_basis(self.gt.cam(1)[0])
        self.origin = self.gt.cam(1)[1]
        self.anchors = [k for k in range(2, 33, 2) if self.gt.has(k)]

    def pose(self, k):
        self.check(k)
        if not self.gt.has(k):
            defer("missing_pose", str(k))
        R, t = self.gt.cam(k)
        flip = np.diag([1., -1., 1.])
        level = rounded(flip @ self.basis.T @ level_basis(R))
        return {"camera_R_L1": rounded(flip @ self.basis.T @ R),
                "camera_t_L1": rounded(flip @ self.basis.T @ (t - self.origin)),
                "level_R_L1": level,
                "yaw_degree": round(math.degrees(math.atan2(-level[0][2], level[2][2]))),
                "frame": k, "unit": "m"}

    def ids(self, obj, many=False):
        from .bindings import fix_label_typos
        obj = fix_label_typos(obj)
        # The canonical matcher discards qualifiers. Refuse those without an explicit
        # reviewed RGB binding rather than treating a red chair as any chair.
        T = self.programs.T
        bindings = getattr(self, "referent_ids", {})
        if obj in bindings:
            ids = bindings[obj]
            if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids) or any(type(i) is not int or i not in self.native for i in ids):
                raise Refusal("invalid_reviewed_referent_ids", obj)
            if not many and len(ids) != 1: defer("ambiguous_referent", obj)
            return ids
        # The object called "frame" in native annotations is worded "picture frame".
        # Preserve the annotation and resolve this one explicit wording alias here.
        exact = [i for i, x in self.native.items()
                 if fix_label_typos(x["label"]).lower().strip() == obj.lower().strip()
                 or (obj.lower().strip() == "picture frame" and x["label"].lower().strip() == "frame")]
        if exact:
            if not many and len(exact) != 1: defer("ambiguous_referent", obj)
            return exact
        if T.head_noun(obj) != obj.lower().strip():
            defer("unresolved_qualified_referent", obj)
        ids = self.ground.instances(obj)
        # The canonical matcher also permits substrings. A substring may discard
        # an unlisted material or description, so admit only exact labels or the
        # canonical owner's explicit synonym table unless RGB IDs were reviewed.
        aliases = set(T.SYN.get(obj.lower().strip(), [obj.lower().strip()]))
        if any(self.native[i]["label"].lower().strip() not in aliases for i in ids):
            defer("unresolved_qualified_referent", obj)
        if not ids:
            defer("ungroundable_label", obj)
        if not many and len(ids) != 1:
            defer("ambiguous_referent", obj)
        return ids

    def appearance_masks(self, obj, k):
        """Native RGB masks meeting the first-seen area threshold."""
        raster = self.gt.inst[k - 1]
        minimum = (raster.size + 499) // 500
        masks = [(iid, raster == iid) for iid in self.ids(obj, many=True)]
        return sorted(((iid, m) for iid, m in masks if np.count_nonzero(m) >= minimum),
                      key=lambda im: -np.count_nonzero(im[1]))

    def candidates(self, iid, k, edge=False, complete=False, *, canonical=False):
        self.check(k, depth=True)
        if not self.gt.has(k):
            defer("missing_depth_pose", str(k))
        mask = self.gt.inst[k - 1] == iid
        distance = ndimage.distance_transform_edt(mask)
        ys, xs = np.nonzero(mask & ((distance <= 2) if edge else (distance >= 3)))
        if len(xs) < 2:
            raise Refusal("insufficient_interior_mask")
        # Facing minima use the complete pool; other probes remain bounded.
        ix = np.arange(len(xs)) if complete else np.linspace(0, len(xs) - 1, min(len(xs), 512)).astype(int)
        uv = np.rint(np.column_stack(((xs[ix] + .5) / self.gt.W * 1000,
                                     (ys[ix] + .5) / self.gt.H * 1000))).astype(int)
        uv = np.unique(uv, axis=0)
        x, y = self.gt.px(uv)
        keep = mask[y, x] & ((distance[y, x] >= 3) if not edge else (distance[y, x] <= 2))
        uv = uv[keep]
        if canonical:
            uv = uv[np.all((uv >= 20) & (uv <= 980), axis=1)]
            if not len(uv): raise Refusal("insufficient_stable_points")
        world, _, spread = self.gt.lift(k, uv)
        keep = np.isfinite(world).all(1) & np.isfinite(spread)
        if not edge:
            limits = np.where(np.minimum(uv, 1000-uv).min(axis=1) <= 40, .10, .25) if canonical else .25
            keep &= np.asarray(rounded(spread, 2)) <= limits
        uv, world = uv[keep], world[keep]
        if len(uv) < 2:
            raise Refusal("insufficient_stable_points")
        return uv, world

    def select(self, iid, k, kind="middle", other=None):
        uv, P = self.candidates(iid, k, complete=(kind == "facing"))
        if kind == "facing":
            if other is None:
                target = self.gt.cam(k)[1][None]
            else:
                oi, ok = other if isinstance(other, tuple) else (other, k)
                _, target = self.candidates(oi, ok, complete=True)
            from scipy.spatial import cKDTree
            scores = cKDTree(target).query(P)[0]
            order = np.argsort(scores, kind="stable")
            return uv[order[:3]].tolist()
        if kind == "extent":
            from scipy.spatial.distance import cdist
            i, j = np.unravel_index(int(np.argmax(cdist(P, P))), (len(P), len(P)))
            if i == j:
                raise Refusal("zero_extent")
            return uv[[i, j]].tolist()
        centre = np.median(uv, axis=0)
        return uv[np.argsort(np.linalg.norm(uv - centre, axis=1), kind="stable")[:3]].tolist()

    def readout(self, iid, k, uv):
        self.check(k, depth=True)
        x, y = self.gt.px([uv])
        if self.gt.inst[k - 1, y[0], x[0]] != iid:
            raise Refusal("rounded_click_outside_mask")
        _, pc, spread = self.gt.lift(k, [uv])
        return {"camera": rounded(pc[0]), "spread": rounded(spread[0], 2), "unit": "m"}

    def correction(self, iid, k, initial, other_clicks, *, canonical=False):
        def limit(uv):
            if canonical and not all(20 <= x <= 980 for x in uv):
                raise Refusal("depth_click_border")
            return .10 if canonical and min(*uv, *(1000-x for x in uv)) <= 40 else .25
        readout = self.readout(iid, k, initial)
        if readout["spread"] <= limit(initial):
            return None
        x, y = self.gt.px([initial])
        dt = ndimage.distance_transform_edt(self.gt.inst[k - 1] == iid)
        if not canonical and dt[y[0], x[0]] > 2:
            raise Refusal("correction_requires_real_edge")
        target = np.asarray(rounded(np.mean(other_clicks, axis=0), 2))
        if canonical:
            xx, yy = self.gt.px([target])
            if dt[yy[0], xx[0]] < 3: raise Refusal("correction_ungrounded_interior")
        delta = target - np.asarray(initial)
        norm = np.linalg.norm(delta)
        if norm < 30:
            raise Refusal("correction_interior_too_close")
        nxt = np.rint(np.asarray(initial) + 30 * delta / norm).astype(int).tolist()
        corrected = self.readout(iid, k, nxt)
        xx, yy = self.gt.px([nxt])
        if (not canonical and dt[yy[0], xx[0]] <= dt[y[0], x[0]] or corrected["spread"] > limit(nxt)
                or canonical and dt[yy[0], xx[0]] < 3):
            raise Refusal("unresolved_edge_correction")
        return nxt, corrected

    def edge_example(self, iid, k, other_clicks, *, canonical=False):
        try:
            uv, _ = self.candidates(iid, k, edge=True, canonical=canonical)
        except Refusal:
            return None
        uv = uv.tolist()
        if canonical:
            # Filter starts by mask geometry before reading depth. The selected
            # example still refuses the row if its one replacement is unreliable.
            mask = self.gt.inst[k - 1] == iid
            dt = ndimage.distance_transform_edt(mask)
            target = np.asarray(rounded(np.mean(other_clicks, axis=0), 2))

            def lands(p):
                delta = target - np.asarray(p)
                norm = np.linalg.norm(delta)
                if norm < 30: return False
                nxt = np.rint(np.asarray(p) + 30 * delta / norm).astype(int).tolist()
                if not all(20 <= c <= 980 for c in nxt): return False
                x, y = self.gt.px([nxt])
                return bool(mask[y[0], x[0]] and dt[y[0], x[0]] >= 3)
            uv = [p for p in uv if lands(p)]
        for p in uv:
            limit = .10 if canonical and min(*p, *(1000-x for x in p)) <= 40 else .25
            if self.readout(iid, k, p)["spread"] > limit:
                # Once a real signal is selected, failure drops the row. Never search
                # for a new stable readout to obtain a desired answer.
                correction = self.correction(iid, k, p, other_clicks, canonical=canonical)
                return p, correction
        return None
