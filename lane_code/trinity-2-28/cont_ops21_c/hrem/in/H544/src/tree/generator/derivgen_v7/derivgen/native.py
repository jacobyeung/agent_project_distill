"""Bounded, local-only FIRST_HITS + face-instance conversion (no rendering)."""
from pathlib import Path
import re

import numpy as np

from .common import ProvenanceError, pinned, read_json, sha256, write_json
from .geometry import native_annotations


AMBIGUOUS_FACE_INSTANCE = -2


def native_mesh(path, *, raster_compatible=False):
    """Read single-label faces or official-instance-face-csr-v2 memberships.

    The multilabel producer saves each instance's face set independently
    (source_gt_adapters__scannetpp_multilabel__prepare_gt_scene.py.txt:68-83,
    279,295). It specifies no precedence between overlapping instances.
    """
    with np.load(path, allow_pickle=False) as z:
        keys = set(z.files)
        base = {"faces", "vertices_world"}
        membership = {"membership_instance_ids", "membership_face_offsets",
                      "membership_face_indices", "segment_ids", "segment_offsets",
                      "segment_instance_ids"}
        if base <= keys and "face_instance_ids" in keys:
            return z["face_instance_ids"], z["faces"], z["vertices_world"]
        if not (base | membership) <= keys:
            raise ProvenanceError(
                "unsupported native mesh schema: expected vertices_world/faces and "
                "face_instance_ids or official-instance-face-csr-v2; missing CSR keys: "
                + ", ".join(sorted((base | membership) - keys))
                + "; present keys: " + ", ".join(sorted(keys)))
        triangles, vertices = z["faces"], z["vertices_world"]
        ids = z["membership_instance_ids"]
        offsets = z["membership_face_offsets"]
        indices = z["membership_face_indices"]
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise ProvenanceError("native multilabel mesh faces must have shape (F, 3)")
    for name, values in (("membership_instance_ids", ids),
                         ("membership_face_offsets", offsets),
                         ("membership_face_indices", indices)):
        if values.ndim != 1 or not np.issubdtype(values.dtype, np.integer):
            raise ProvenanceError("native multilabel mesh " + name + " must be an integer vector")
    if (np.any(ids < 0) or np.any(ids > np.iinfo(np.int32).max)
            or len(np.unique(ids)) != len(ids)):
        raise ProvenanceError("native multilabel mesh instance IDs must be unique nonnegative int32 values")
    if (offsets.shape != (len(ids) + 1,) or offsets[0] != 0
            or offsets[-1] != len(indices) or np.any(offsets[1:] < offsets[:-1])):
        raise ProvenanceError("native multilabel mesh CSR offsets must start at 0, be nondecreasing, "
                              "and end at membership_face_indices length, with one span per instance")
    if np.any(indices < 0) or np.any(indices >= len(triangles)):
        raise ProvenanceError("native multilabel mesh membership face index out of range")
    face_ids = np.full(len(triangles), -1, dtype=np.int32)
    for row, iid in enumerate(ids):
        selected = indices[offsets[row]:offsets[row + 1]]
        previous = face_ids[selected]
        # Repeated entries for the same owner do not create an overlap.
        face_ids[selected] = np.where((previous == -1) | (previous == iid),
                                      iid, AMBIGUOUS_FACE_INSTANCE)
    if raster_compatible:
        # GTScene's raster schema admits only -1 outside reviewed instance IDs.
        # Exclude overlaps from every instance mask without changing that schema.
        face_ids[face_ids == AMBIGUOUS_FACE_INSTANCE] = -1
    return face_ids, triangles, vertices


def native_intrinsics_policy(scaled, raster_hw, *, per_frame=False):
    """Summarize frame intrinsics after raster scaling; return median K and policy.

    FoV uses 2*atan(raster_size/(2*focal_length)) in degrees. Principal-point
    deviations use fractions of the corresponding raster dimension.
    """
    scaled = np.asarray(scaled, dtype=float)
    hw = np.asarray(raster_hw, dtype=float)
    if (scaled.ndim != 3 or scaled.shape[1:] != (3, 3) or not len(scaled)
            or not np.isfinite(scaled).all() or hw.shape != (2,)
            or not np.isfinite(hw).all() or np.any(hw <= 0)
            or np.any(scaled[:, (0, 1), (0, 1)] <= 0)
            or np.any(np.linalg.det(scaled) <= 0)
            or not np.allclose(scaled[:, 2], [0, 0, 1])):
        raise ProvenanceError("native intrinsics require finite matrices and positive focal lengths/raster")
    median = np.median(scaled, axis=0)
    wh = hw[::-1]
    fov = np.degrees(2 * np.arctan(wh / (2 * scaled[:, (0, 1), (0, 1)])))
    fov_median = np.median(fov, axis=0)
    fov_max = np.max(np.abs(fov - fov_median), axis=0)
    pp_max = np.max(np.abs(scaled[:, :2, 2] - median[:2, 2]), axis=0)
    pp_fraction = pp_max / wh
    reasons = []
    for axis, value in zip(("horizontal", "vertical"), fov_max):
        if value > 0.5:
            reasons.append(f"{axis} FoV deviation {value:.9g} deg exceeds 0.5 deg from scene median")
    for axis, value in zip(("horizontal", "vertical"), pp_fraction):
        if value > 0.005:
            reasons.append(f"{axis} principal-point deviation {value:.9g} of raster exceeds 0.005 from scene median")
    policy = {
        "name": "per_frame_k" if per_frame else "elementwise_median_k",
        "frames": len(scaled),
        "fov_tolerance_deg": 0.5,
        "principal_point_tolerance_raster_fraction": 0.005,
        "median_K": median.tolist(),
        "median_fov_deg_xy": fov_median.tolist(),
        "max_fov_deviation_deg_xy": fov_max.tolist(),
        "max_principal_point_deviation_px_xy": pp_max.tolist(),
        "max_principal_point_deviation_raster_fraction_xy": pp_fraction.tolist(),
        "constant_k_accepted": not reasons,
        "constant_k_refusal_reasons": reasons,
        "K_frames_stored": per_frame,
        "accepted": per_frame or not reasons,
        "refusal_reasons": [] if per_frame else reasons,
    }
    return median, policy


def prepare_native(config_path, output, *, validate_only=False):
    """Prepare one explicitly staged scene. The parent owns staging and admission.

    Labels and RGB selection need reviewed evidence; this command cannot infer
    identity or admission from a dataset name, native path or raster dimensions.
    """
    config = read_json(config_path)
    out = Path(output).resolve()
    allowed = Path("/scratch/jjyeung/orch_cd/derivgen/out")
    if not out.is_relative_to(allowed) or out == allowed:
        raise ProvenanceError("native output must be a fresh directory below derivgen/out")
    e = config["entry"]
    if config.get("calibration_convention") != "opencv_c2w_raw_z_up_m":
        raise ProvenanceError("reviewed native calibration convention required")
    paths = {key: pinned(config[key]) for key in ("first_hits", "mesh", "calibration")}
    # Reuse the registry's label/RGB/selection contract. All actual assets must be local.
    labels = read_json(pinned(e["label_provenance"]))
    annotation_source, annotations = native_annotations(e["native_annotations"])
    if (labels.get("verified") is not True or labels.get("canonical") != e["canonical"]
            or labels.get("basis") != "native_instance_annotations"):
        raise ProvenanceError("native labels require reviewed annotation provenance")
    selection = read_json(pinned(e["selection"]))
    if selection.get("frame_indices") != e["frame_indices"] or selection.get("canonical") != e["canonical"] or not selection.get("verified"):
        raise ProvenanceError("native selection evidence mismatch")
    rgb = read_json(pinned(e["rgb_manifest"]))
    binding = config.get("rgb_binding", "byte_verified")
    if binding not in ("byte_verified", "identity_only"):
        raise ProvenanceError("unknown native RGB binding")
    identity = binding == "identity_only"
    if (rgb.get("frame_indices") != e["frame_indices"] or len(rgb.get("frames", [])) != 32
            or rgb.get("canonical") != e["canonical"]
            or (not identity and rgb.get("verified") is not True)
            or (identity and (rgb.get("verified") is not False or rgb.get("binding") != binding))):
        raise ProvenanceError("native RGB evidence mismatch")
    visibility = None
    if identity:
        visibility = read_json(pinned(config["native_source_evidence"]["visibility"]))
        if len(visibility.get("frames", [])) != 32:
            raise ProvenanceError("native visibility frame count mismatch")
    for k, (index, frame) in enumerate(zip(e["frame_indices"], rgb["frames"])):
        if type(frame.get("source_index")) is not int or frame["source_index"] != index:
            raise ProvenanceError("native RGB frame mismatch")
        if identity:
            source = visibility["frames"][k]
            native = source.get("native_rgb", {})
            if (type(source.get("source_ordinal")) is not int or source["source_ordinal"] != index
                    or not isinstance(frame.get("path"), str) or not frame["path"]
                    or not isinstance(frame.get("sha256"), str)
                    or not re.fullmatch(r"[0-9a-fA-F]{64}", frame.get("sha256", ""))
                    or any(frame.get(key) != native.get(key) for key in ("path", "sha256"))):
                raise ProvenanceError("native RGB identity/visibility mismatch")
        else:
            pinned(frame)
    with np.load(paths["first_hits"], allow_pickle=False) as z:
        depth, faces = z["depth"], z["face_index"]
    face_ids, triangles, vertices = native_mesh(paths["mesh"], raster_compatible=True)
    with np.load(paths["calibration"], allow_pickle=False) as z:
        poses, intrinsics, indices, raster = z["camera_poses"], z["intrinsics"], z["indices"], z["raster_hw"]
    if (depth.ndim != 3 or depth.shape[0] != 32 or faces.shape != depth.shape
            or not np.issubdtype(faces.dtype, np.integer)
            or np.any(depth < 0)
            or poses.shape != (32, 4, 4) or not np.isfinite(poses).all()
            or intrinsics.shape != (32, 3, 3) or not np.isfinite(intrinsics).all()
            or indices.tolist() != e["frame_indices"] or len(raster) != 2
            or np.any(np.asarray(raster) <= 0)
            or triangles.ndim != 2 or triangles.shape[1] != 3
            or not np.issubdtype(triangles.dtype, np.integer) or not np.issubdtype(face_ids.dtype, np.integer)
            or face_ids.shape != (len(triangles),) or vertices.ndim != 2 or vertices.shape[1] != 3
            or not np.isfinite(vertices).all() or triangles.min() < 0 or triangles.max() >= len(vertices)):
        raise ProvenanceError("native schema/selection mismatch")
    hit = faces >= 0
    if (not np.isfinite(depth[hit]).all() or np.any(depth[hit] <= 0)
            or np.isnan(depth[~hit]).any() or np.isneginf(depth[~hit]).any()):
        raise ProvenanceError("native depth sentinel invalid at hit/unhit pixels")
    positive_inf_unhit = int(np.isposinf(depth[~hit]).sum())
    depth = depth.copy()
    depth[~hit] = 0
    if np.any(faces[hit] >= len(face_ids)): raise ProvenanceError("FIRST_HITS face index out of range")
    inst = np.full(faces.shape, -1, dtype=np.int32)
    inst[hit] = face_ids[faces[hit]]
    # Negative first-hit faces stay invalid; never use numpy's negative indexing.
    inst[depth <= 0] = -1
    ids = np.array(sorted(int(i) for i in labels["labels"]), dtype=np.int32)
    if not set(np.unique(inst)) <= set(ids.tolist()) | {-1}:
        raise ProvenanceError("native face instances missing reviewed labels")
    H, W = depth.shape[1:]
    scale = np.diag([W/float(raster[1]), H/float(raster[0]), 1.])
    scaled = np.asarray([scale @ K for K in intrinsics])
    K, intrinsics_policy = native_intrinsics_policy(scaled, (H, W), per_frame=True)
    if not intrinsics_policy["accepted"]:
        raise ProvenanceError("native intrinsics refused: " + "; ".join(intrinsics_policy["refusal_reasons"]))
    # Preserve the actual native source convention; never substitute mesh AABBs.
    # Full extents are normalized only for the canonical adapter's NPZ schema.
    centres, lengths = [], []
    axes = []
    if set(ids.tolist()) != set(annotations): raise ProvenanceError("native annotation/label identity mismatch")
    for iid in ids:
        item = annotations[int(iid)]
        if item["label"] != labels["labels"][str(iid)]: raise ProvenanceError("native annotation label mismatch")
        centres.append(item["centroid"]); lengths.append(item["lengths"]); axes.append(item["axes"].reshape(9))
    if validate_only:
        # Run every preparation check without retaining a second raster/mesh copy.
        return {"canonical": e["canonical"], "validated": True,
                "raster_hw": [H, W], "instances": len(ids),
                "intrinsics_policy": intrinsics_policy,
                "native_box_convention": {key: annotation_source.get(key) for key in
                    ("box_convention", "provider_axesLengths", "released_boxes", "obb_estimator_used")},
                "box_convention_evidence": annotation_source.get("box_convention_evidence")}
    out.mkdir(parents=True, exist_ok=False)
    path = out / "GT.npz"
    # A new directory and exclusive handle preserve every previous output.
    with path.open("xb") as f:
        np.savez_compressed(f, depth=depth.astype(np.float32), inst=inst, K=K, K_frames=scaled, c2w=poses,
                            valid=np.ones(32, dtype=bool), ids=ids,
                            labels=np.array([labels["labels"][str(i)] for i in ids]),
                            obb_centroid=np.array(centres), obb_lengths=np.array(lengths),
                            obb_axes=np.array(axes), frame_indices=indices)
    entry = {**e, "gt": {"path": str(path), "sha256": sha256(path)},
             "rgb_binding": binding,
             "coordinates": "raw_z_up_opencv_c2w_m", "geometry": {"kind": "native_gt"},
             "native_provenance": {**{k: config[k] for k in ("first_hits", "mesh", "calibration")},
                                   "intrinsics_policy": intrinsics_policy},
             "native_source_evidence": config.get("native_source_evidence", {}),
             "native_box_convention": {key: annotation_source.get(key) for key in ("box_convention", "provider_axesLengths", "released_boxes", "obb_estimator_used")},
             "box_convention_evidence": annotation_source.get("box_convention_evidence"),
             "private_boxes": "native annotation boxes; NPZ lengths normalized to full extents; never tool outputs"}
    write_json(out / "SCENE_REGISTRY.json", {"schema": "derivgen-scenes-v1", "scenes": {config["alias"]: entry}})
    write_json(out / "PREPARATION.json", {"config": {"path": str(Path(config_path).resolve()), "sha256": sha256(config_path)},
                                         "gt": entry["gt"], "raster_hw": [H, W], "source_raster_hw": raster.tolist(),
                                         "intrinsics_scale_xy": [W/float(raster[1]), H/float(raster[0])],
                                         "intrinsics_policy": intrinsics_policy,
                                         "native_annotations": e["native_annotations"], "native_box_convention": entry["native_box_convention"],
                                         "unhit_cells_normalized_to_zero": int((~hit).sum()), "positive_inf_unhit": positive_inf_unhit,
                                         "admission": "not granted by preparation; production physical admission still required"})
    return entry
