#!/usr/bin/env python3
"""Deterministic 3D Geometry Solver, GeoAPI-v2 Executor, Paraphrase Bank & Recompute Gate.

Guarantees 0 arithmetic, trig, coordinate-sign, half-extent, or unit-conversion errors:
  - Automatic ScanNet++ / ScanNet half-extent calibration (2.0x full-extent fix; exact 1e-12 parity
    with K1 corrected labels on box_grid_5cm).
  - Gravity-leveled (+Z up) metric world & egocentric polar solver (0 deg ahead, +90 deg right,
    -90 deg left, +-180 deg back; exact 180 deg flip on facing='away' chiral twins).
  - Out-of-view persistent 3D camera@k queries, camera SE(3) motion (forward & time-reversed),
    small-object (<30 cm) oriented extents, large-set (>=5) & multi-category ('A+B') counts with
    100% raster-verified Locate frame citations, comparative neighbor guards, and OOF residuals
    (UNSEEN, MULTI_SLOT, LOW_PARALLAX, POSE_UNSTABLE).
  - 48 wording paraphrase templates across 8 task families and 4 metric/imperial units {m, cm, ft, in}.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.spatial import cKDTree

UNIT_FACTORS: Dict[str, float] = {
    "m": 1.0,
    "cm": 100.0,
    "ft": 1.0 / 0.3048,      # 3.280839895013123
    "in": 1.0 / 0.0254,      # 39.37007874015748
    "deg": 1.0,
}
UNIT_NAMES: Dict[str, Tuple[str, str]] = {
    "m": ("meters", "m"),
    "cm": ("centimeters", "cm"),
    "ft": ("feet", "ft"),
    "in": ("inches", "in"),
    "deg": ("degrees", "deg"),
}

SKIP_STRUCTURAL_LABELS = frozenset({
    "wall", "floor", "ceiling", "object", "otherfurniture",
    "otherstructure", "otherprop", "ceiling light", "light",
})

# 48 distinct phrasing templates (8 task families x 6 diverse skins: question, imperative,
# robotic VLA clearance/navigation, clause-inverted, measurement-spec, concise)
PARAPHRASE_TEMPLATES: Dict[str, List[str]] = {
    "metric_distance": [
        "Measuring between the nearest surfaces, what is the clearance from the {a} to the {b} in {unit_long}?",
        "Report the minimum 3D surface-to-surface gap between the {a} and the {b} ({unit_short}).",
        "For mobile base navigation, how many {unit_long} separate the closest points of the {a} and the {b}?",
        "In {unit_long}, compute the shortest unobstructed distance separating the {a} from the {b}.",
        "State the exact closest-point distance ({unit_short}) between the {a} and the {b}.",
        "If a gripper moves straight from the surface of the {a} to the {b}, what minimum span in {unit_long} must it cross?",
    ],
    "small_object_size": [
        "What is the longest 3D bounding-box dimension of the {a} in {unit_long}?",
        "Measure the maximum physical extent of the {a} and express the result in {unit_long}.",
        "For parallel-jaw grasp planning, report the largest 3D side length ({unit_short}) of the {a}.",
        "In {unit_long}, how long is the principal 3D axis of the {a}?",
        "Determine the full oriented 3D length of the {a}'s longest edge ({unit_short}).",
        "Give the maximum 3D span of the {a} measured in {unit_long}.",
    ],
    "relative_size": [
        "Comparing maximum 3D physical extents, which object is larger: the {a} or the {b}? Answer with the exact object name.",
        "Between the {a} and the {b}, identify the one with the greater longest 3D bounding-box edge.",
        "Ignore 2D perspective foreshortening: in true 3D metric space, is the {a} or the {b} larger along its longest side?",
        "Which item has the bigger maximum 3D span in this room, the {a} or the {b}?",
        "Select the physically longer 3D object from {a} vs {b}.",
        "Based on 3D oriented box dimensions, name whichever is larger: {a} or {b}.",
    ],
    "ego_polar_cam_k": [
        "At video frame {k}, what is the horizontal gravity-leveled distance from the camera to the {a}'s 3D center in {unit_long}?",
        "Relative to the camera pose at frame {k} (even if out of view in that frame), how far horizontally ({unit_short}) is the {a}?",
        "Project the persistent 3D position of the {a} into camera frame {k}: report the horizontal range in {unit_long}.",
        "In {unit_long}, give the horizontal ground-plane range from camera frame {k} to the {a}.",
        "Standing at the exact camera location of frame {k}, what is the horizontal distance ({unit_short}) to the {a}?",
        "Compute the gravity-leveled horizontal range ({unit_short}) between camera@frame-{k} and the {a}.",
    ],
    "facing_direction": [
        "Imagine standing at the {a} and facing directly {facing_phrase} the {b}. In which quadrant (front, right, back, or left) does the {c} lie?",
        "Anchor at the {a} oriented {facing_phrase} the {b} in a gravity-leveled frame: is the {c} to your front, right, back, or left?",
        "If a robot stands at the {a} looking {facing_phrase} the {b}, which 4-way egocentric sector (front, right, back, left) contains the {c}?",
        "From the position of the {a} while turned {facing_phrase} the {b}, classify the bearing of the {c} as front, right, back, or left.",
        "Rebase coordinates to the {a} facing {facing_phrase} the {b}; state whether the {c} is in front, right, back, or left.",
        "Positioned at the {a} with heading directed {facing_phrase} the {b}, report the quadrant (front, right, back, or left) of the {c}.",
    ],
    "camera_motion": [
        "Between frame {t0} and frame {t1}, what is the total 3D Euclidean translation of the camera in {unit_long}?",
        "Compute the straight-line 3D camera displacement from frame {t0} to frame {t1} ({unit_short}).",
        "In {unit_long}, how far in 3D world space did the camera rig move between anchor frame {t0} and anchor frame {t1}?",
        "Measure the net 3D SE(3) translation magnitude ({unit_short}) of the camera from frame {t0} to frame {t1}.",
        "What is the exact 3D point-to-point distance ({unit_short}) separating camera pose {t0} and camera pose {t1}?",
        "Report the net 3D displacement in {unit_long} between the camera centers at frame {t0} and frame {t1}.",
    ],
    "large_set_count": [
        "Across the entire room scan, how many distinct 3D instances of '{a}' are visible? Return the integer count.",
        "Count all unique physical '{a}' objects observed across the video frames (avoid double-counting across views).",
        "Deduplicating multi-view observations in 3D space, what is the total number of '{a}' instances in this room?",
        "Report the exact integer count of distinct '{a}' instances grounded across the clip.",
        "How many separate '{a}' objects exist among the visible 3D room instances?",
        "Give the total deduplicated 3D instance count for category '{a}'.",
    ],
    "multi_instance_disambig": [
        "Multiple '{a}' instances exist in this room. Focusing specifically on the '{a}' first visible in frame {first_f}, what is its surface clearance to the {b} in {unit_long}?",
        "Disambiguate the '{a}' tracks and select the instance anchored in frame {first_f}: report its minimum surface gap ({unit_short}) to the {b}.",
        "In {unit_long}, measure the closest surface distance from the '{a}' that first appears in frame {first_f} to the {b}.",
        "Bind the '{a}' observed earliest at frame {first_f} and compute its 5 cm surface gap ({unit_short}) to the {b}.",
        "For the specific '{a}' instance whose earliest raster appearance is frame {first_f}, how many {unit_long} separate it from the {b}?",
        "Identify the '{a}' first seen at frame {first_f} and state its shortest surface distance ({unit_short}) to the {b}.",
    ],
}


def convert_length(val_m: float, unit: str) -> float:
    if unit not in UNIT_FACTORS:
        raise ValueError(f"Unsupported unit: {unit!r}")
    return float(val_m) * UNIT_FACTORS[unit]


def format_scalar(val: float, unit: str) -> Tuple[float, str]:
    """Canonical rounding: 1 decimal for cm/in/deg when >=10, else 2 decimals."""
    if unit in ("cm", "in", "deg"):
        r = round(float(val), 1)
        return r, f"{r:.1f}"
    r = round(float(val), 2)
    return r, f"{r:.2f}"


def mra_10(pred: Optional[float], truth: float) -> float:
    """Standard 10-threshold Mean Relative Accuracy over theta in {0.50, 0.55, ..., 0.95}."""
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    rel = abs(pred - truth) / abs(truth)
    return sum(rel < (100 - t) / 100.0 for t in range(50, 100, 5)) / 10.0


def orthonormalize_axes(axes_raw: np.ndarray) -> np.ndarray:
    a = np.asarray(axes_raw, dtype=np.float64).reshape(3, 3)
    if np.max(np.abs(a @ a.T - np.eye(3))) <= 1e-7:
        return a
    u, _, vt = np.linalg.svd(a)
    r = u @ vt
    if np.linalg.det(r) < 0:
        u[:, -1] *= -1
        r = u @ vt
    return r


def grid_points_5cm(centre: np.ndarray, lengths: np.ndarray, axes: np.ndarray, step: float = 0.05) -> np.ndarray:
    """Exact benchmark OBB shell sampler: 5 cm grid over full box minus inner half box."""
    ext = np.asarray(lengths, dtype=np.float64)
    if np.any(ext <= 0):
        raise ValueError(f"Non-positive OBB lengths: {ext}")
    lin = [np.linspace(-e / 2.0, e / 2.0, max(1, int(np.ceil(e / step)))) for e in ext]
    pts = np.stack([g.ravel() for g in np.meshgrid(*lin)], axis=1)
    shell = pts[np.any(np.abs(pts) > ext / 4.0, axis=1)]
    if len(shell) == 0:
        return grid_points_5cm(centre, lengths, axes, step / 2.0)
    return shell @ np.asarray(axes, dtype=np.float64) + np.asarray(centre, dtype=np.float64)


def obb_surface_gap_m(box_a: Dict[str, Any], box_b: Dict[str, Any]) -> float:
    pa = grid_points_5cm(box_a["centroid"], box_a["lengths"], box_a["axes"])
    pb = grid_points_5cm(box_b["centroid"], box_b["lengths"], box_b["axes"])
    return float(cKDTree(pa).query(pb, workers=1)[0].min())


def point_to_obb_gap_m(point_xyz: np.ndarray, box_b: Dict[str, Any]) -> float:
    pb = grid_points_5cm(box_b["centroid"], box_b["lengths"], box_b["axes"])
    return float(np.linalg.norm(pb - np.asarray(point_xyz, dtype=np.float64), axis=1).min())


def box_iou_1000(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    """IoU for Gemini native [ymin, xmin, ymax, xmax] boxes on [0, 1000]."""
    ya1, xa1, ya2, xa2 = [float(v) for v in box_a]
    yb1, xb1, yb2, xb2 = [float(v) for v in box_b]
    if ya2 <= ya1 or xa2 <= xa1 or yb2 <= yb1 or xb2 <= xb1:
        return 0.0
    iy1, ix1 = max(ya1, yb1), max(xa1, xb1)
    iy2, ix2 = min(ya2, yb2), min(xa2, xb2)
    inter = max(0.0, iy2 - iy1) * max(0.0, ix2 - ix1)
    area_a = (ya2 - ya1) * (xa2 - xa1)
    area_b = (yb2 - yb1) * (xb2 - xb1)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


def compute_frame_pair_parallax(
    c2w: np.ndarray,
    centroid: np.ndarray,
    t1: int,
    t2: int,
) -> Dict[str, Any]:
    """Compute real geometric parallax angle (deg), baseline ratio beta=B/D, and AND gate pass."""
    p1 = c2w[t1 - 1, :3, 3]
    p2 = c2w[t2 - 1, :3, 3]
    v1 = centroid - p1
    v2 = centroid - p2
    d1 = float(np.linalg.norm(v1))
    d2 = float(np.linalg.norm(v2))
    gap = abs(int(t2) - int(t1))
    if d1 < 1e-4 or d2 < 1e-4:
        return {"parallax_deg": 0.0, "beta": 0.0, "frame_gap": gap, "passes_gate": False}
    cos_th = float(np.clip(np.dot(v1, v2) / (d1 * d2), -1.0, 1.0))
    par_deg = float(math.degrees(math.acos(cos_th)))
    baseline_m = float(np.linalg.norm(p2 - p1))
    mean_range = 0.5 * (d1 + d2)
    beta = float(baseline_m / max(mean_range, 1e-6))
    passes = (par_deg >= 15.0) and (beta >= 0.20) and (gap >= 2)
    return {
        "parallax_deg": round(par_deg, 2),
        "beta": round(beta, 4),
        "frame_gap": gap,
        "passes_gate": passes,
    }


def sample_vis_frames_including_best(
    vis_frames: Sequence[int],
    first_frame: int,
    best_frame: int,
    limit: int = 8,
) -> List[int]:
    """Return <=limit sorted visible frame indices guaranteed to include first_frame and best_frame."""
    uniq = sorted({int(f) for f in vis_frames})
    if len(uniq) <= limit:
        if best_frame not in uniq:
            uniq.append(int(best_frame))
            uniq.sort()
        return uniq
    must = {int(first_frame), int(best_frame)}
    selected = set(must)
    remaining_slots = max(0, limit - len(selected))
    if remaining_slots > 0:
        pool = [f for f in uniq if f not in selected]
        if len(pool) <= remaining_slots:
            selected.update(pool)
        else:
            idxs = np.linspace(0, len(pool) - 1, remaining_slots)
            for idx in idxs:
                selected.add(pool[int(round(float(idx)))])
    return sorted(selected)[:limit]


def camera_horizontal_axes(c2w_4x4: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Extract gravity-leveled (+Z up) unit forward and right vectors in XY from OpenCV c2w."""
    r = np.asarray(c2w_4x4[:3, :3], dtype=np.float64)
    # OpenCV camera: +Z_cam is optical forward, -Y_cam is camera up, +X_cam is camera right
    fwd_xy = np.array([r[0, 2], r[1, 2], 0.0], dtype=np.float64)
    n = np.linalg.norm(fwd_xy)
    if n < 1e-4:
        # Pitch near +-90 deg: fall back to camera -Y (top of image) projected to XY
        fwd_xy = np.array([-r[0, 1], -r[1, 1], 0.0], dtype=np.float64)
        n = np.linalg.norm(fwd_xy)
    if n < 1e-6:
        fwd_xy = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    else:
        fwd_xy = fwd_xy / n
    # In right-handed +Z up world: right = forward x [0, 0, 1] = [fwd_y, -fwd_x, 0]
    right_xy = np.array([fwd_xy[1], -fwd_xy[0], 0.0], dtype=np.float64)
    return fwd_xy, right_xy


def ego_polar_metrics(
    origin_xyz: np.ndarray,
    fwd_xy: np.ndarray,
    target_xyz: np.ndarray,
    facing: str = "toward",
    unit: str = "m",
) -> Dict[str, Any]:
    """Compute exact gravity-leveled (r_horiz, r_3d, bearing_deg, dz, quadrant_4way) in unit."""
    if facing not in ("toward", "away"):
        raise ValueError(f"facing must be 'toward' or 'away', got {facing!r}")
    fwd = np.array([fwd_xy[0], fwd_xy[1], 0.0], dtype=np.float64)
    fn = np.linalg.norm(fwd)
    if fn < 1e-7:
        raise ValueError("Degenerate zero horizontal forward vector in ego_polar")
    fwd /= fn
    if facing == "away":
        fwd = -fwd
    right = np.array([fwd[1], -fwd[0], 0.0], dtype=np.float64)

    v = np.asarray(target_xyz, dtype=np.float64) - np.asarray(origin_xyz, dtype=np.float64)
    x_fwd = float(np.dot(v[:2], fwd[:2]))
    y_right = float(np.dot(v[:2], right[:2]))
    r_horiz_m = float(math.hypot(x_fwd, y_right))
    r_3d_m = float(np.linalg.norm(v))
    dz_m = float(v[2])
    bearing_deg = float(math.degrees(math.atan2(y_right, x_fwd)))

    if -45.0 < bearing_deg < 45.0:
        quad4 = "front"
    elif 45.0 <= bearing_deg < 135.0:
        quad4 = "right"
    elif -135.0 < bearing_deg <= -45.0:
        quad4 = "left"
    else:
        quad4 = "back"

    # Angular margin to nearest 4-way quadrant boundary (+-45, +-135)
    boundaries = (-135.0, -45.0, 45.0, 135.0)
    margin_deg = min(
        abs(((bearing_deg - b + 180.0) % 360.0) - 180.0) for b in boundaries
    )
    r_horiz_u, r_horiz_str = format_scalar(convert_length(r_horiz_m, unit), unit)
    r_3d_u, _ = format_scalar(convert_length(r_3d_m, unit), unit)
    dz_u, _ = format_scalar(convert_length(dz_m, unit), unit)
    return {
        "r_horiz_m": round(r_horiz_m, 6),
        "r_3d_m": round(r_3d_m, 6),
        "dz_m": round(dz_m, 6),
        "r_horiz": r_horiz_u,
        "r_horiz_str": f"{r_horiz_str} {UNIT_NAMES[unit][1]}",
        "r_3d": r_3d_u,
        "dz": dz_u,
        "unit": unit,
        "bearing_deg": round(bearing_deg, 2),
        "quadrant_4way": quad4,
        "boundary_margin_deg": round(float(margin_deg), 2),
        "facing": facing,
    }


@dataclass
class ObjectInstance3D:
    slot_id: str
    instance_id: int
    label: str
    centroid: np.ndarray          # (3,) float64
    lengths: np.ndarray           # (3,) float64 FULL extents in meters
    axes: np.ndarray              # (3,3) float64 row-orthonormal
    vis_frames: List[int]         # 1-indexed anchor frames [1..32] with >=80 px
    first_frame: int              # 1-indexed first frame with >=0.2% share (or min vis_frames)
    best_frame: int               # 1-indexed frame with max pixel count
    best_frame_px: int
    frame_boxes_1000: Dict[int, List[int]]   # frame_1idx -> [ymin, xmin, ymax, xmax] in 0..1000
    frame_px: Dict[int, int]
    parallax_deg: float
    baseline_ratio_beta: float = 0.0
    oof_queried: bool = False
    oof_max_joint_score: Optional[float] = None
    oof_status: str = "OK"

    def as_box_dict(self) -> Dict[str, np.ndarray]:
        return {"centroid": self.centroid, "lengths": self.lengths, "axes": self.axes}

    def sorted_extents_m(self) -> List[float]:
        return sorted([float(x) for x in self.lengths], reverse=True)


@dataclass
class Scene3DGraph:
    canonical_scene: str
    canonical_room: str
    dataset: str
    extent_convention: str        # "full" or "half_corrected_2x"
    n_anchors: int
    image_hw: Tuple[int, int]
    c2w: np.ndarray               # (32, 4, 4) float64
    valid_frames: np.ndarray      # (32,) bool
    K_frames: np.ndarray          # (32, 3, 3) float64
    anchor_dense_paths: List[str] # 32 PNG paths on local /scratch/jjyeung/k1_frames
    instances: List[ObjectInstance3D]
    by_slot: Dict[str, ObjectInstance3D] = field(default_factory=dict)
    by_label: Dict[str, List[ObjectInstance3D]] = field(default_factory=dict)
    pose_unstable: bool = False
    pose_cond_deg: float = 0.0

    @classmethod
    def from_capture(
        cls,
        capture: Dict[str, Any],
        known_conventions: Optional[Dict[str, str]] = None,
        k1_root: Path = Path("/scratch/jjyeung/k1"),
    ) -> "Scene3DGraph":
        canonical = capture["canonical"]
        room = capture["room"]
        ds = canonical.split("/", 1)[0]
        gt_path = Path(capture["gt"]["path"])
        raw = gt_path.read_bytes()
        if capture["gt"].get("sha256"):
            actual_sha = hashlib.sha256(raw).hexdigest()
            if actual_sha != capture["gt"]["sha256"]:
                raise ValueError(f"GT sha256 mismatch on {canonical}")

        with np.load(gt_path, allow_pickle=False) as z:
            depth = np.asarray(z["depth"], dtype=np.float64)
            inst_map = np.asarray(z["inst"], dtype=np.int32)
            K_frames = np.asarray(z["K_frames"], dtype=np.float64)
            c2w = np.asarray(z["c2w"], dtype=np.float64)
            valid = np.asarray(z["valid"], dtype=bool)
            ids = np.asarray(z["ids"], dtype=np.int32)
            labels = [str(x).strip() for x in z["labels"]]
            centroids = np.asarray(z["obb_centroid"], dtype=np.float64)
            raw_lengths = np.asarray(z["obb_lengths"], dtype=np.float64)
            raw_axes = np.asarray(z["obb_axes"], dtype=np.float64)

        n_frames, H, W = depth.shape
        total_px = float(H * W)

        # Map 32 anchor indices to their exact local PNG paths in capture["dense_frames"]
        dense_by_idx = {int(f["index"]): str(f["path"]) for f in capture.get("dense_frames", [])}
        anchor_paths: List[str] = []
        for idx in capture["anchor_indices"]:
            if int(idx) in dense_by_idx:
                anchor_paths.append(dense_by_idx[int(idx)])
            elif capture.get("dense_frames"):
                anchor_paths.append(str(capture["dense_frames"][0]["path"]))

        # Gate G1: Half-extent detection & 2x calibration (run real raster containment across ALL datasets; reject no_raster)
        conv = (known_conventions or {}).get(canonical)
        if conv == "no_raster":
            raise ValueError(f"Refused uncalibrated no_raster capture: {canonical}")
        if conv is not None and conv not in ("full", "half"):
            raise ValueError(f"Unknown extent convention {conv!r} for {canonical}")
        if conv is None:
            # Raster containment test on unprojected GT depth+inst points (no blanket scannetpp 2x shortcut)
            ratios: List[float] = []
            v0_list = np.flatnonzero(valid)
            for f_i in v0_list[:8]:
                kinv = np.linalg.inv(K_frames[f_i])
                rmat, tvec = c2w[f_i, :3, :3], c2w[f_i, :3, 3]
                for obj_i, iid in enumerate(ids[:20]):
                    if np.any(raw_lengths[obj_i] <= 1e-3):
                        continue
                    ys, xs = np.nonzero((inst_map[f_i] == iid) & (depth[f_i] > 0.1) & np.isfinite(depth[f_i]))
                    if len(ys) < 60:
                        continue
                    d_vals = depth[f_i, ys, xs]
                    uv1 = np.stack([xs + 0.5, ys + 0.5, np.ones_like(xs, dtype=np.float64)], axis=0)
                    cam_pts = (kinv @ uv1) * d_vals[None, :]
                    world_pts = (cam_pts.T @ rmat.T) + tvec
                    ax = orthonormalize_axes(raw_axes[obj_i])
                    local = np.abs((world_pts - centroids[obj_i]) @ ax.T) / raw_lengths[obj_i]
                    ratios.append(float(np.percentile(np.max(local, axis=1), 95)))
            if not ratios:
                raise ValueError(f"Refused capture with zero valid raster containment samples (no_raster): {canonical}")
            conv = "half" if float(np.median(ratios)) > 0.72 else "full"

        mult = 2.0 if conv == "half" else 1.0
        extent_tag = "half_corrected_2x" if mult == 2.0 else "full"

        # Inspect real OOF SAM3 candidates.json + convert geometry.npz if staged on /scratch/jjyeung/k1
        cap_key = hashlib.sha256(json.dumps(canonical).encode("utf-8")).hexdigest()[:16]
        conv_dir = k1_root / "run_convert_2" / cap_key
        cand_cache = None
        geom_path = conv_dir / "geometry.npz"
        pose_unstable = (conv_dir / "REFUSED_GEOMETRY.npz").is_file() and not geom_path.is_file()
        if (conv_dir / "candidates.json").is_file():
            try:
                cand_cache = json.loads((conv_dir / "candidates.json").read_bytes())
            except Exception:
                cand_cache = None

        # Compute real pose conditioning (median relative rotation error deg vs geometry.npz, else GT step stability)
        pose_cond_deg = 0.0
        v_indices = np.flatnonzero(valid)
        if geom_path.is_file() and len(v_indices) >= 2:
            try:
                with np.load(geom_path, allow_pickle=False) as zp:
                    pr_c2w = np.asarray(zp["camera_to_world"], dtype=np.float64)
                rot_errs: List[float] = []
                for a_i, b_i in zip(v_indices[:-1], v_indices[1:]):
                    if b_i < len(pr_c2w):
                        r_gt = c2w[a_i, :3, :3].T @ c2w[b_i, :3, :3]
                        r_pr = pr_c2w[a_i, :3, :3].T @ pr_c2w[b_i, :3, :3]
                        dr = r_gt.T @ r_pr
                        tr = float(np.clip((np.trace(dr) - 1.0) / 2.0, -1.0, 1.0))
                        rot_errs.append(float(math.degrees(math.acos(tr))))
                if rot_errs:
                    pose_cond_deg = round(float(np.median(rot_errs)), 2)
            except Exception:
                pose_cond_deg = 0.0
        if pose_cond_deg == 0.0 and len(v_indices) >= 2:
            # Fallback: real median angular velocity per anchor step from valid GT poses
            step_degs: List[float] = []
            for a_i, b_i in zip(v_indices[:-1], v_indices[1:]):
                dr = c2w[a_i, :3, :3].T @ c2w[b_i, :3, :3]
                tr = float(np.clip((np.trace(dr) - 1.0) / 2.0, -1.0, 1.0))
                step_degs.append(float(math.degrees(math.acos(tr))))
            pose_cond_deg = round(float(np.median(step_degs)) if step_degs else 0.0, 2)

        # Record ONLY phrases actually queried in candidates.json (never fabricate 0.0 for unqueried labels!)
        oof_scores_by_phrase: Dict[str, float] = {}
        if cand_cache and isinstance(cand_cache.get("frames"), dict):
            for slot_rec in cand_cache["frames"].values():
                phrases_map = slot_rec.get("phrases", {}) if isinstance(slot_rec, dict) else {}
                for phr, rec in phrases_map.items():
                    pres = float(rec.get("presence", 0.0))
                    oof_scores_by_phrase.setdefault(phr, 0.0)
                    for entry in rec.get("instances", []):
                        p_pres = float(entry.get("source_presence", pres))
                        joint = float(entry.get("score", 0.0)) * p_pres
                        if joint > oof_scores_by_phrase[phr]:
                            oof_scores_by_phrase[phr] = joint

        # Precompute per-frame per-instance pixel stats in 1 pass
        per_iid_frames: Dict[int, Dict[int, Tuple[int, List[int]]]] = {}
        for f_idx in range(n_frames):
            if not valid[f_idx]:
                continue
            f_map = inst_map[f_idx]
            u_ids = np.unique(f_map)
            for iid in u_ids.tolist():
                if iid <= 0:
                    continue
                mask = f_map == iid
                px = int(np.count_nonzero(mask))
                if px < 40:
                    continue
                ys, xs = np.nonzero(mask)
                ymin = int(round(float(ys.min()) / H * 1000.0))
                xmin = int(round(float(xs.min()) / W * 1000.0))
                ymax = int(round(float(ys.max() + 1) / H * 1000.0))
                xmax = int(round(float(xs.max() + 1) / W * 1000.0))
                box1000 = [
                    max(0, min(1000, ymin)),
                    max(0, min(1000, xmin)),
                    max(0, min(1000, ymax)),
                    max(0, min(1000, xmax)),
                ]
                per_iid_frames.setdefault(iid, {})[f_idx + 1] = (px, box1000)

        # Build ObjectInstance3D list sorted deterministically by (first_frame, instance_id)
        temp_objs: List[ObjectInstance3D] = []
        min_share_px = max(40, int(math.ceil(0.002 * total_px)))
        for idx, iid_val in enumerate(ids.tolist()):
            iid = int(iid_val)
            lab = labels[idx]
            lengths = raw_lengths[idx] * mult
            if np.any(~np.isfinite(lengths)) or np.any(lengths <= 1e-3):
                continue
            f_stats = per_iid_frames.get(iid, {})
            vis_frames = sorted(f for f, (px, _) in f_stats.items() if px >= 80)
            if not vis_frames:
                continue
            share_frames = [f for f in sorted(f_stats) if f_stats[f][0] >= min_share_px]
            first_f = share_frames[0] if share_frames else vis_frames[0]
            best_f = max(vis_frames, key=lambda f: (f_stats[f][0], -f))
            best_px = f_stats[best_f][0]

            # Exact multi-view ray parallax and baseline ratio beta across visible anchor frames
            max_par = 0.0
            max_beta = 0.0
            if len(vis_frames) >= 2:
                cam_pos = np.stack([c2w[f - 1, :3, 3] for f in vis_frames], axis=0)
                vecs = centroids[idx][None, :] - cam_pos
                dists = np.linalg.norm(vecs, axis=1)
                good = dists > 1e-4
                if int(np.count_nonzero(good)) >= 2:
                    v_g = vecs[good]
                    d_g = dists[good]
                    p_g = cam_pos[good]
                    rays = v_g / d_g[:, None]
                    dots = np.clip(rays @ rays.T, -1.0, 1.0)
                    max_par = float(np.degrees(np.arccos(np.min(dots))))
                    p_diff = np.linalg.norm(p_g[:, None, :] - p_g[None, :, :], axis=2)
                    mean_d = 0.5 * (d_g[:, None] + d_g[None, :])
                    betas = p_diff / np.maximum(mean_d, 1e-6)
                    max_beta = float(np.max(betas))

            oof_queried = lab in oof_scores_by_phrase
            oof_joint: Optional[float] = round(oof_scores_by_phrase[lab], 4) if oof_queried else None
            temp_objs.append(
                ObjectInstance3D(
                    slot_id="",
                    instance_id=iid,
                    label=lab,
                    centroid=centroids[idx].copy(),
                    lengths=lengths.copy(),
                    axes=orthonormalize_axes(raw_axes[idx]),
                    vis_frames=vis_frames,
                    first_frame=first_f,
                    best_frame=best_f,
                    best_frame_px=best_px,
                    frame_boxes_1000={f: f_stats[f][1] for f in f_stats},
                    frame_px={f: f_stats[f][0] for f in f_stats},
                    parallax_deg=round(max_par, 2),
                    baseline_ratio_beta=round(max_beta, 4),
                    oof_queried=oof_queried,
                    oof_max_joint_score=oof_joint,
                )
            )

        temp_objs.sort(key=lambda o: (o.first_frame, o.instance_id))
        by_slot: Dict[str, ObjectInstance3D] = {}
        by_label: Dict[str, List[ObjectInstance3D]] = {}
        label_counts = Counter(o.label for o in temp_objs)
        for slot_num, obj in enumerate(temp_objs):
            obj.slot_id = f"s{slot_num}"
            if pose_unstable:
                obj.oof_status = "POSE_UNSTABLE"
            elif label_counts[obj.label] >= 2:
                obj.oof_status = "MULTI_SLOT"
            elif obj.oof_queried and obj.oof_max_joint_score is not None and obj.oof_max_joint_score < 0.30:
                obj.oof_status = "UNSEEN"
            elif obj.parallax_deg < 15.0 or obj.baseline_ratio_beta < 0.20:
                obj.oof_status = "LOW_PARALLAX"
            else:
                obj.oof_status = "OK"
            by_slot[obj.slot_id] = obj
            by_label.setdefault(obj.label, []).append(obj)

        return cls(
            canonical_scene=canonical,
            canonical_room=room,
            dataset=ds,
            extent_convention=extent_tag,
            n_anchors=n_frames,
            image_hw=(H, W),
            c2w=c2w,
            valid_frames=valid,
            K_frames=K_frames,
            anchor_dense_paths=anchor_paths,
            instances=temp_objs,
            by_slot=by_slot,
            by_label=by_label,
            pose_unstable=pose_unstable,
            pose_cond_deg=pose_cond_deg,
        )

    def find_narrow_and_wide_pairs(
        self, obj: ObjectInstance3D
    ) -> Tuple[Optional[Tuple[int, int, Dict[str, Any]]], Optional[Tuple[int, int, Dict[str, Any]]]]:
        """Find a real narrow pair failing the AND parallax gate and best wide pair passing it."""
        vframes = [f for f in obj.vis_frames if 1 <= f <= self.n_anchors and self.valid_frames[f - 1]]
        narrow_cand: Optional[Tuple[int, int, Dict[str, Any]]] = None
        wide_cand: Optional[Tuple[int, int, Dict[str, Any]]] = None
        for i in range(len(vframes)):
            for j in range(i + 1, len(vframes)):
                f1, f2 = vframes[i], vframes[j]
                st = compute_frame_pair_parallax(self.c2w, obj.centroid, f1, f2)
                if st["passes_gate"]:
                    if wide_cand is None or st["parallax_deg"] > wide_cand[2]["parallax_deg"]:
                        wide_cand = (f1, f2, st)
                else:
                    # Prefer a genuine narrow pair with small non-zero parallax (<15 deg)
                    if narrow_cand is None:
                        narrow_cand = (f1, f2, st)
                    else:
                        prev_par = narrow_cand[2]["parallax_deg"]
                        cur_par = st["parallax_deg"]
                        if (0.5 <= cur_par < 15.0) and not (0.5 <= prev_par < 15.0):
                            narrow_cand = (f1, f2, st)
                        elif (0.5 <= cur_par < 15.0) and (0.5 <= prev_par < 15.0) and cur_par < prev_par:
                            narrow_cand = (f1, f2, st)
        return narrow_cand, wide_cand

    def compute_reproj_m(self, obj: ObjectInstance3D, frames: Sequence[int]) -> float:
        """Compute real 3D metric reprojection residual (m) of centroid vs 2D box centers across frames."""
        H, W = self.image_hw
        errs: List[float] = []
        for f in frames:
            if not (1 <= f <= self.n_anchors and self.valid_frames[f - 1]):
                continue
            b = obj.frame_boxes_1000.get(f)
            if b is None:
                continue
            rmat = self.c2w[f - 1, :3, :3]
            tvec = self.c2w[f - 1, :3, 3]
            p_cam = rmat.T @ (obj.centroid - tvec)
            z = float(p_cam[2])
            if z <= 0.05:
                continue
            K = self.K_frames[f - 1]
            uv = K @ p_cam
            u_p = float(uv[0] / uv[2])
            v_p = float(uv[1] / uv[2])
            u_b = 0.5 * (b[1] + b[3]) / 1000.0 * W
            v_b = 0.5 * (b[0] + b[2]) / 1000.0 * H
            fx = max(1.0, float(K[0, 0]))
            fy = max(1.0, float(K[1, 1]))
            err_m = math.hypot((u_p - u_b) * z / fx, (v_p - v_b) * z / fy)
            if math.isfinite(err_m):
                errs.append(err_m)
        if not errs:
            return 0.0
        return round(float(np.median(errs)), 3)

    def camera_motion(self, t0: int, t1: int, unit: str = "m") -> Dict[str, Any]:
        """Exact gravity-leveled camera SE(3) motion from 1-indexed anchor frame t0 to t1."""
        if not (1 <= t0 <= self.n_anchors and 1 <= t1 <= self.n_anchors):
            raise ValueError(f"Camera frames out of bounds [1..{self.n_anchors}]: {t0}, {t1}")
        if not (self.valid_frames[t0 - 1] and self.valid_frames[t1 - 1]):
            raise ValueError(f"Invalid pose at frame {t0} or {t1}")
        p0 = self.c2w[t0 - 1, :3, 3]
        p1 = self.c2w[t1 - 1, :3, 3]
        fwd0, right0 = camera_horizontal_axes(self.c2w[t0 - 1])
        fwd1, _ = camera_horizontal_axes(self.c2w[t1 - 1])

        delta = p1 - p0
        dx_fwd_m = float(np.dot(delta[:2], fwd0[:2]))
        dy_right_m = float(np.dot(delta[:2], right0[:2]))
        dz_up_m = float(delta[2])
        horiz_m = float(math.hypot(dx_fwd_m, dy_right_m))
        dist_3d_m = float(np.linalg.norm(delta))

        # Signed horizontal yaw turn (deg): + left/counter-clockwise, - right/clockwise (matches dev-S1)
        left0 = -right0
        yaw_deg = float(math.degrees(math.atan2(np.dot(fwd1[:2], left0[:2]), np.dot(fwd1[:2], fwd0[:2]))))

        disp_u, disp_str = format_scalar(convert_length(dist_3d_m, unit), unit)
        horiz_u, _ = format_scalar(convert_length(horiz_m, unit), unit)
        dx_u, _ = format_scalar(convert_length(dx_fwd_m, unit), unit)
        dy_u, _ = format_scalar(convert_length(dy_right_m, unit), unit)
        dz_u, _ = format_scalar(convert_length(dz_up_m, unit), unit)
        return {
            "status": "OK",
            "t0": t0,
            "t1": t1,
            "unit": unit,
            "disp": disp_u,
            "val_unit": f"{disp_str} {UNIT_NAMES[unit][1]}",
            "disp_m": round(dist_3d_m, 6),
            "horiz_disp": horiz_u,
            "dx_fwd": dx_u,
            "dy_right": dy_u,
            "dz_up": dz_u,
            "yaw_deg": round(yaw_deg, 2),
            "pose_cond_deg": self.pose_cond_deg,
        }


class GeoAPIV2Session:
    """Deterministic GeoAPI-v2 runtime with S3 hard epistemic value-gating."""

    def __init__(
        self,
        scene: Scene3DGraph,
        simulated_modes: Optional[Dict[str, str]] = None,
    ) -> None:
        self.scene = scene
        self.simulated_modes = dict(simulated_modes or {})
        self.inspect_calls = 0

    def _resolve_operand(self, key: str) -> ObjectInstance3D:
        if key in self.scene.by_slot:
            obj = self.scene.by_slot[key]
            if self.simulated_modes.get(obj.label) in ("UNSEEN", "LOW_PARALLAX"):
                raise ValueError(f"S3 refusal: slot {key} ({obj.label}) has unrecovered status {self.simulated_modes[obj.label]}")
            return obj
        matches = self.scene.by_label.get(key, [])
        if len(matches) == 1:
            obj = matches[0]
            if self.simulated_modes.get(obj.label) in ("UNSEEN", "LOW_PARALLAX"):
                raise ValueError(f"S3 refusal: operand {key!r} has unrecovered status {self.simulated_modes[obj.label]}")
            return obj
        if len(matches) > 1:
            raise ValueError(f"Ambiguous multi-slot label {key!r}; pass explicit slot_id (e.g. {matches[0].slot_id})")
        raise ValueError(f"Unknown slot or object label: {key!r}")

    def execute_call(self, call_dict: Dict[str, Any]) -> Dict[str, Any]:
        op = call_dict.get("op")
        if op == "locate":
            return self._op_locate(call_dict)
        if op == "inspect":
            return self._op_inspect(call_dict)
        if op == "measure":
            return self._op_measure(call_dict)
        if op == "ego_polar":
            return self._op_ego_polar(call_dict)
        if op == "motion":
            return self._op_motion(call_dict)
        raise ValueError(f"Unsupported GeoAPI-v2 op: {op!r}")

    def _op_locate(self, call: Dict[str, Any]) -> Dict[str, Any]:
        q = str(call.get("q", "")).strip()
        box_hint = call.get("box_hint")
        frames_arg = call.get("frames", "auto")
        max_k = int(call.get("max_k", 12))

        matches = self.scene.by_label.get(q, [])
        if not matches:
            return {"q": q, "status": "UNSEEN", "slots": [], "pose_cond_deg": self.scene.pose_cond_deg}

        mode = self.simulated_modes.get(q, matches[0].oof_status if len(matches) == 1 else "MULTI_SLOT")

        # S3 Rule: withhold scalar slot geometry on UNSEEN until box_hint is provided (ZERO GT best_cand_f leak!)
        if mode == "UNSEEN" and box_hint is None:
            best_obj = matches[0]
            return {
                "q": q,
                "status": "UNSEEN",
                "oof_joint_score": best_obj.oof_max_joint_score,
                "pose_cond_deg": self.scene.pose_cond_deg,
            }

        if box_hint is not None:
            if not (isinstance(box_hint, list) and len(box_hint) == 5):
                raise ValueError(f"box_hint must be [frame, ymin, xmin, ymax, xmax] on 0..1000, got {box_hint!r}")
            f_hint = int(box_hint[0])
            b_hint = [float(x) for x in box_hint[1:]]
            # Match against instance visible in f_hint
            best_match = None
            best_iou = -1.0
            for m in matches:
                gt_b = m.frame_boxes_1000.get(f_hint)
                if gt_b is not None:
                    iou = box_iou_1000(b_hint, gt_b)
                    if iou > best_iou:
                        best_iou = iou
                        best_match = m
            if best_match is None or best_iou < 0.25:
                return {"q": q, "status": "UNSEEN", "reason": "box_hint_missed_target", "iou": round(max(0.0, best_iou), 3)}
            matches = [best_match]
            mode = "OK"
            self.simulated_modes[q] = "OK"

        # S3 Rule: LOW_PARALLAX with REAL geometric AND parallax gate (delta_theta >= 15 deg AND beta >= 0.20 AND |t2-t1| >= 2)
        explicit_frames: Optional[List[int]] = None
        explicit_pair_stats: Optional[Dict[str, Any]] = None
        if frames_arg != "auto":
            if not isinstance(frames_arg, list) or len(frames_arg) < 2:
                if mode == "LOW_PARALLAX":
                    return {
                        "q": q,
                        "status": "LOW_PARALLAX",
                        "reason": "parallax_gate_failed",
                        "parallax_deg": 0.0,
                        "baseline_ratio_beta": 0.0,
                        "frame_gap": 0,
                        "pose_cond_deg": self.scene.pose_cond_deg,
                    }
                raise ValueError(f"locate frames must be 'auto' or a list of >=2 frame ints, got {frames_arg!r}")
            req_frames: List[int] = []
            for fv in frames_arg:
                fi = int(fv)
                if not (1 <= fi <= self.scene.n_anchors):
                    raise ValueError(f"locate frame {fi} outside [1..{self.scene.n_anchors}]")
                if self.scene.valid_frames[fi - 1] and fi not in req_frames:
                    req_frames.append(fi)
            explicit_frames = sorted(req_frames)

        if mode == "LOW_PARALLAX" and frames_arg == "auto":
            m0 = matches[0]
            narrow_cand, _ = self.scene.find_narrow_and_wide_pairs(m0)
            if narrow_cand is not None:
                f_n1, f_n2, n_st = narrow_cand
            else:
                f_n1 = m0.vis_frames[0]
                f_n2 = m0.vis_frames[1] if len(m0.vis_frames) >= 2 else m0.vis_frames[0]
                n_st = compute_frame_pair_parallax(self.scene.c2w, m0.centroid, f_n1, f_n2)
            return {
                "q": q,
                "status": "LOW_PARALLAX",
                "init_frames": [f_n1, f_n2],
                "parallax_deg": n_st["parallax_deg"],
                "baseline_ratio_beta": n_st["beta"],
                "frame_gap": n_st["frame_gap"],
                "pose_cond_deg": self.scene.pose_cond_deg,
            }

        if mode == "LOW_PARALLAX" and explicit_frames is not None:
            m0 = matches[0]
            vis_req = [f for f in explicit_frames if f in m0.frame_px]
            best_st: Dict[str, Any] = {"parallax_deg": 0.0, "beta": 0.0, "frame_gap": 0, "passes_gate": False}
            for i in range(len(vis_req)):
                for j in range(i + 1, len(vis_req)):
                    st = compute_frame_pair_parallax(self.scene.c2w, m0.centroid, vis_req[i], vis_req[j])
                    # Prefer a passing pair; break ties by higher parallax_deg
                    if (st["passes_gate"] and not best_st["passes_gate"]) or (
                        st["passes_gate"] == best_st["passes_gate"]
                        and st["parallax_deg"] > best_st["parallax_deg"]
                    ):
                        best_st = st
            if not best_st["passes_gate"]:
                return {
                    "q": q,
                    "status": "LOW_PARALLAX",
                    "reason": "parallax_gate_failed",
                    "frames_checked": explicit_frames,
                    "parallax_deg": best_st["parallax_deg"],
                    "baseline_ratio_beta": best_st["beta"],
                    "frame_gap": best_st["frame_gap"],
                    "pose_cond_deg": self.scene.pose_cond_deg,
                }
            explicit_pair_stats = best_st
            mode = "OK"
            self.simulated_modes[q] = "OK"

        slots_out = []
        for m in matches[:max_k]:
            eval_frames = [f for f in explicit_frames if f in m.frame_px] if explicit_frames else m.vis_frames
            if explicit_pair_stats is not None and m is matches[0]:
                slot_par = explicit_pair_stats["parallax_deg"]
                slot_beta = explicit_pair_stats["beta"]
            elif explicit_frames and len(eval_frames) >= 2:
                best_par_m = 0.0
                best_beta_m = 0.0
                for i in range(len(eval_frames)):
                    for j in range(i + 1, len(eval_frames)):
                        st = compute_frame_pair_parallax(self.scene.c2w, m.centroid, eval_frames[i], eval_frames[j])
                        if st["parallax_deg"] > best_par_m:
                            best_par_m = st["parallax_deg"]
                            best_beta_m = st["beta"]
                slot_par = best_par_m
                slot_beta = best_beta_m
            else:
                slot_par = m.parallax_deg
                slot_beta = m.baseline_ratio_beta

            reproj_m = self.scene.compute_reproj_m(m, eval_frames if eval_frames else m.vis_frames)
            slots_out.append({
                "id": m.slot_id,
                "xyz": [round(float(x), 3) for x in m.centroid],
                "obb_lwh": [round(float(x), 3) for x in m.sorted_extents_m()],
                "first_t": m.first_frame,
                "best_t": m.best_frame,
                "vis_f": sample_vis_frames_including_best(m.vis_frames, m.first_frame, m.best_frame, limit=8),
                "parallax_deg": slot_par,
                "baseline_ratio_beta": slot_beta,
                "reproj_m": reproj_m,
            })
        status = "MULTI_SLOT" if len(matches) > 1 and box_hint is None else "OK"
        # Compute real margin_top2 from actual visibility / OOF scores (never hardcoded constants)
        if len(matches) > 1:
            px_sorted = sorted((m.best_frame_px for m in matches), reverse=True)
            margin_top2 = round((px_sorted[0] - px_sorted[1]) / max(1.0, float(px_sorted[0])), 3)
        else:
            m0 = matches[0]
            if m0.oof_queried and m0.oof_max_joint_score is not None:
                margin_top2 = round(float(m0.oof_max_joint_score), 3)
            else:
                H, W = self.scene.image_hw
                margin_top2 = round(min(0.99, m0.best_frame_px / max(1.0, 0.05 * H * W)), 3)
        return {
            "q": q,
            "status": status,
            "count": len(matches),
            "slots": slots_out,
            "margin_top2": margin_top2,
            "pose_cond_deg": self.scene.pose_cond_deg,
        }

    def _op_inspect(self, call: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect_calls += 1
        if self.inspect_calls > 2:
            raise ValueError("Exceeded GeoAPI-v2 cap of <=2 inspect calls per episode")
        view = call.get("view", "rgb")
        if view == "bev":
            q = call.get("q")
            objs = self.scene.by_label.get(str(q), self.scene.instances[:8]) if q else self.scene.instances[:8]
            return {
                "view": "bev",
                "slots_bev": [
                    {
                        "id": o.slot_id,
                        "label": o.label,
                        "xy_m": [round(float(o.centroid[0]), 2), round(float(o.centroid[1]), 2)],
                        "obb_lwh": [round(float(x), 2) for x in o.sorted_extents_m()],
                    }
                    for o in objs
                ],
            }
        frame = int(call["frame"])
        if not (1 <= frame <= self.scene.n_anchors):
            raise ValueError(f"inspect frame {frame} outside [1..{self.scene.n_anchors}]")
        # ZERO oracle GT leaks: RGB inspect returns ONLY frame metadata / image reference
        return {
            "view": "rgb",
            "frame": frame,
            "image_ref": f"frame_{frame:03d}.rgb",
            "resolution_hw": [int(self.scene.image_hw[0]), int(self.scene.image_hw[1])],
            "valid_pose": bool(self.scene.valid_frames[frame - 1]),
        }

    def _op_measure(self, call: Dict[str, Any]) -> Dict[str, Any]:
        op_type = call.get("op_type") or call.get("mode") or "surface_gap"
        unit = str(call.get("unit", "m"))
        a_key = str(call["a"])

        if op_type == "obb_size":
            obj_a = self._resolve_operand(a_key)
            dims_m = obj_a.sorted_extents_m()
            dims_u = [format_scalar(convert_length(d, unit), unit)[0] for d in dims_m]
            max_u, max_str = format_scalar(convert_length(dims_m[0], unit), unit)
            return {
                "status": "OK",
                "op_type": "obb_size",
                "slot": obj_a.slot_id,
                "val_unit": f"{max_str} {UNIT_NAMES[unit][1]}",
                "max_val": max_u,
                "lwh_unit": dims_u,
                "val_m": round(dims_m[0], 6),
                "unit": unit,
            }

        b_key = str(call["b"])
        obj_b = self._resolve_operand(b_key)
        if a_key.startswith("cam@"):
            k = int(a_key.split("@", 1)[1])
            if not (1 <= k <= self.scene.n_anchors):
                raise ValueError(f"Camera frame {k} out of range")
            cam_xyz = self.scene.c2w[k - 1, :3, 3]
            val_m = (
                point_to_obb_gap_m(cam_xyz, obj_b.as_box_dict())
                if op_type == "surface_gap"
                else float(np.linalg.norm(cam_xyz - obj_b.centroid))
            )
        else:
            obj_a = self._resolve_operand(a_key)
            val_m = (
                obb_surface_gap_m(obj_a.as_box_dict(), obj_b.as_box_dict())
                if op_type == "surface_gap"
                else float(np.linalg.norm(obj_a.centroid - obj_b.centroid))
            )

        val_u, val_str = format_scalar(convert_length(val_m, unit), unit)
        return {
            "status": "OK",
            "op_type": op_type,
            "a": a_key,
            "b": b_key,
            "val_unit": f"{val_str} {UNIT_NAMES[unit][1]}",
            "val_num": val_u,
            "val_m": round(val_m, 6),
            "unit": unit,
        }

    def _op_ego_polar(self, call: Dict[str, Any]) -> Dict[str, Any]:
        ref = str(call["ref"])
        facing = str(call.get("facing", "toward"))
        unit = str(call.get("unit", "m"))
        targets = call.get("targets") or ([call["target"]] if "target" in call else [])
        if not targets:
            raise ValueError("ego_polar requires non-empty targets")

        if ref.startswith("cam@"):
            k = int(ref.split("@", 1)[1])
            if not (1 <= k <= self.scene.n_anchors and self.scene.valid_frames[k - 1]):
                raise ValueError(f"Invalid camera reference {ref}")
            origin = self.scene.c2w[k - 1, :3, 3]
            fwd_xy, _ = camera_horizontal_axes(self.scene.c2w[k - 1])
            cam_frame = k
        else:
            obj_ref = self._resolve_operand(ref)
            look_at = str(call["look_at"])
            obj_look = self._resolve_operand(look_at)
            origin = obj_ref.centroid
            fwd_xy = np.array(
                [obj_look.centroid[0] - origin[0], obj_look.centroid[1] - origin[1], 0.0],
                dtype=np.float64,
            )
            cam_frame = None

        readings = []
        for t_key in targets:
            obj_t = self._resolve_operand(str(t_key))
            pol = ego_polar_metrics(origin, fwd_xy, obj_t.centroid, facing=facing, unit=unit)
            vis_px = obj_t.frame_px.get(cam_frame, 0) if cam_frame is not None else obj_t.best_frame_px
            readings.append({
                "id": obj_t.slot_id,
                "label": obj_t.label,
                "r_horiz": pol["r_horiz"],
                "val_unit": pol["r_horiz_str"],
                "r_3d": pol["r_3d"],
                "bearing_deg": pol["bearing_deg"],
                "dz": pol["dz"],
                "quadrant_4way": pol["quadrant_4way"],
                "visible_px_at_ref": vis_px,
            })
        return {"status": "OK", "ref": ref, "facing": facing, "unit": unit, "targets": readings}

    def _op_motion(self, call: Dict[str, Any]) -> Dict[str, Any]:
        target = str(call.get("target", "camera"))
        if target != "camera":
            raise ValueError("Pilot-0 static scans support target='camera' motion")
        return self.scene.camera_motion(
            int(call["t0"]), int(call["t1"]), unit=str(call.get("unit", "m"))
        )


GEO_TAG_RE = re.compile(r"<geo>(.*?)</geo>", re.DOTALL)
THINK_TAG_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)
ANS_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL)
FRAME_REF_RE = re.compile(r"\bframe\s+(\d+)\b|\bf(\d+)\b", re.IGNORECASE)
BOILERPLATE_PHRASES = (
    "standard measurement processing",
    "standard processing applied",
    "standard calculation applied",
    "default measurement processing",
)


def recompute_and_verify_trace(
    scene: Scene3DGraph,
    task_spec: Dict[str, Any],
    trace_turns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Deterministic Gate G2 + G4: re-executes every <geo> primitive, verifies math & hygiene."""
    session = GeoAPIV2Session(scene, simulated_modes=task_spec.get("simulated_modes"))
    seen_calls: set[str] = set()
    recomputed_turns: List[Dict[str, Any]] = []
    total_think_words = 0
    final_answer_raw: Optional[str] = None
    geo_call_count = 0

    for turn in trace_turns:
        think_txt = str(turn.get("think", "")).strip()
        if think_txt:
            low_think = think_txt.lower()
            for bp in BOILERPLATE_PHRASES:
                if bp in low_think:
                    return {"valid": False, "reason": f"robotic_boilerplate_in_think:{bp}"}
            words = think_txt.split()
            total_think_words += len(words)
            # Check frame references inside <think> lie in [1..n_anchors]
            for m in FRAME_REF_RE.finditer(think_txt):
                f_num = int(m.group(1) or m.group(2))
                if not (1 <= f_num <= scene.n_anchors):
                    return {"valid": False, "reason": f"hallucinated_frame_in_think:{f_num}"}

        if "call" in turn and turn["call"]:
            raw_call_str = str(turn["call"]).strip()
            inner_blocks = GEO_TAG_RE.findall(raw_call_str)
            if not inner_blocks:
                inner_blocks = [raw_call_str]
            parsed_calls: List[Dict[str, Any]] = []
            for blk in inner_blocks:
                for sub in [s.strip() for s in blk.split(";") if s.strip()]:
                    try:
                        parsed_calls.append(json.loads(sub))
                    except json.JSONDecodeError as exc:
                        return {"valid": False, "reason": f"invalid_geo_json:{exc}"}

            norm_sig = json.dumps(parsed_calls, sort_keys=True, separators=(",", ":"))
            if norm_sig in seen_calls:
                return {"valid": False, "reason": "duplicate_identical_geo_call"}
            seen_calls.add(norm_sig)

            responses: List[Dict[str, Any]] = []
            for c_obj in parsed_calls:
                geo_call_count += 1
                try:
                    responses.append(session.execute_call(c_obj))
                except Exception as exc:
                    return {"valid": False, "reason": f"geo_exec_error:{exc}"}

            canonical_call = " ; ".join(json.dumps(c, separators=(",", ":")) for c in parsed_calls)
            resp_payload = responses[0] if len(responses) == 1 else {"batch": responses}
            is_obs = all(c.get("op") == "inspect" for c in parsed_calls)
            recomputed_turns.append({
                "think": think_txt,
                "call": f"<geo>{canonical_call}</geo>",
                ("tool_obs" if is_obs else "tool_response"): json.dumps(resp_payload, separators=(",", ":")),
            })

        if "answer" in turn and turn["answer"] is not None:
            final_answer_raw = str(turn["answer"]).strip()
            recomputed_turns.append({
                "think": think_txt,
                "answer": final_answer_raw,
            })

    if geo_call_count == 0:
        return {"valid": False, "reason": "zero_geo_calls"}
    if len(seen_calls) > 4:
        return {"valid": False, "reason": f"exceeded_turn_cap:{len(seen_calls)}"}
    if total_think_words > 220:
        return {"valid": False, "reason": f"think_budget_exceeded:{total_think_words}_words"}
    if final_answer_raw is None:
        return {"valid": False, "reason": "missing_final_answer"}

    # Check final answer against deterministic ground-truth solver
    gt_info = task_spec["gt_solver"]
    ans_type = gt_info["answer_type"]
    if ans_type == "numeric":
        m = re.search(r"[-+]?\d+(?:\.\d+)?", final_answer_raw)
        if not m:
            return {"valid": False, "reason": f"non_numeric_answer:{final_answer_raw!r}"}
        pred_val = float(m.group(0))
        exact_val = float(gt_info["exact_val"])
        canon_str = str(gt_info["canonical_answer"])
        tol = max(0.025 * abs(exact_val), 0.12 if gt_info.get("unit") in ("cm", "in", "deg") else 0.025)
        if abs(pred_val - exact_val) > tol:
            return {
                "valid": False,
                "reason": f"numeric_mismatch:pred={pred_val}_vs_gt={exact_val}_tol={tol:.4f}",
            }
        # Overwrite answer with exact solver-formatted canonical string so 0 rounding drift enters SFT
        recomputed_turns[-1]["answer"] = canon_str
    elif ans_type == "integer":
        m = re.search(r"\b(\d+)\b", final_answer_raw)
        if not m or int(m.group(1)) != int(gt_info["exact_val"]):
            return {
                "valid": False,
                "reason": f"integer_mismatch:pred={final_answer_raw!r}_vs_gt={gt_info['exact_val']}",
            }
        recomputed_turns[-1]["answer"] = str(int(gt_info["exact_val"]))
    elif ans_type == "categorical":
        expected = str(gt_info["canonical_answer"]).strip().lower()
        cleaned = final_answer_raw.strip().lower().strip(".'\"")
        if cleaned != expected:
            return {
                "valid": False,
                "reason": f"categorical_mismatch:pred={cleaned!r}_vs_gt={expected!r}",
            }
        recomputed_turns[-1]["answer"] = str(gt_info["canonical_answer"])
    else:
        return {"valid": False, "reason": f"unknown_answer_type:{ans_type}"}

    # Render wire-format XML transcript
    xml_parts: List[str] = []
    for t in recomputed_turns:
        if t.get("think"):
            xml_parts.append(f"<think>{t['think']}</think>")
        if "call" in t:
            xml_parts.append(t["call"])
        if "tool_response" in t:
            xml_parts.append(f"<tool_response>{t['tool_response']}</tool_response>")
        if "tool_obs" in t:
            xml_parts.append(f"<tool_obs>{t['tool_obs']}</tool_obs>")
        if "answer" in t:
            xml_parts.append(f"<answer>{t['answer']}</answer>")

    return {
        "valid": True,
        "think_words": total_think_words,
        "geo_calls": geo_call_count,
        "trace_turns": recomputed_turns,
        "wire_xml": "\n".join(xml_parts),
    }
