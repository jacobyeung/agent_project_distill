import numpy as np

from .contract import validate_export


def clip_ratio(source, target):
    good = np.isfinite(source) & np.isfinite(target) & (source > 0) & (target > 0)
    if good.sum() < 100:
        raise ValueError("Too few valid paired depth samples to infer scale")
    return float(np.median(target[good].astype(np.float64) / source[good]))


def fit_affine(source, target, diagnostics=False):
    scales, shifts = [], []
    report = {"scale_only_frames": [], "abstained_frames": [], "minimum_paired_pixels": 100}
    for index, (x, y) in enumerate(zip(source, target)):
        good = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
        if good.sum() < 100:
            scales.append(0.)
            shifts.append(0.)
            report["abstained_frames"].append(index)
            continue
        x, y = x[good].astype(np.float64), y[good].astype(np.float64)
        if np.std(x) < 1e-4:
            a, b = float(np.median(y / x)), 0.
            report["scale_only_frames"].append(index)
        else:
            a, b = np.polyfit(x, y, 1)
            for _ in range(3):
                residual = y - (a * x + b)
                centre = np.median(residual)
                cutoff = max(1e-4, 2.5 * 1.4826 * np.median(np.abs(residual - centre)))
                keep = np.abs(residual - centre) <= cutoff
                if keep.sum() < 100:
                    break
                a, b = np.polyfit(x[keep], y[keep], 1)
            if a <= 0 or not np.isfinite([a, b]).all():
                a, b = float(np.median(y / x)), 0.
                report["scale_only_frames"].append(index)
        scales.append(float(a))
        shifts.append(float(b))
    result = np.array(scales), np.array(shifts)
    return (*result, report) if diagnostics else result


def blend_depth(first, second):
    valid = np.isfinite(first) & np.isfinite(second) & (first > 0) & (second > 0)
    return np.where(valid, .5 * (first + second), 0).astype(np.float32)


def hybrid(kind, tower, candidate, second=None):
    validate_export(tower)
    validate_export(candidate, tower["anchor_frame_indices"])
    out = {key: value.copy() for key, value in tower.items()}
    meta = {"kind": kind, "gt_used": False, "pose_scale_applied": False}
    source, target = tower["depth_grid"], candidate["depth_grid"]
    if kind in ("depth", "pose_g3t"):
        out["depth_grid"] = target.copy()
        if kind == "pose_g3t":
            out["fov_hw"] = candidate["fov_hw"].copy()
            out["raw_pose"][:, 7:9] = candidate["fov_hw"]
            meta["intrinsics_source"] = "candidate"
    elif kind in ("clip_scale", "clip_scale_depth_only"):
        s = clip_ratio(source, target)
        out["depth_grid"] *= s
        meta["clip_scale"] = s
        if kind == "clip_scale":
            out["t_grav"] *= s
            out["raw_pose"][:, :3] *= s
            out["scale"] *= s
            meta["pose_scale_applied"] = True
    elif kind == "frame_affine":
        a, b, fit = fit_affine(source, target, diagnostics=True)
        out["depth_grid"] = np.where((source > 0) & (a[:, None, None] > 0),
                                    np.maximum(a[:, None, None] * source + b[:, None, None], 1e-3), 0).astype(np.float32)
        meta.update(scales=a.tolist(), shifts_m=b.tolist(), fit=fit)
    elif kind == "average":
        if second is None:
            raise ValueError("A depth ensemble requires a second candidate")
        validate_export(second, tower["anchor_frame_indices"])
        out["depth_grid"] = blend_depth(target, second["depth_grid"])
        meta["weights"] = [.5, .5]
    else:
        raise ValueError(f"Unknown hybrid: {kind}")
    validate_export(out, tower["anchor_frame_indices"])
    return out, meta
