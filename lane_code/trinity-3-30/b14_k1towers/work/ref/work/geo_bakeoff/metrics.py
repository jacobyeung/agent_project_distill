from collections import defaultdict

import numpy as np
from scipy import ndimage


def edge_band(depth, radius=5):
    d = np.asarray(depth)
    good = np.isfinite(d) & (d > 0)
    edges = np.zeros(d.shape, bool)
    for axis in (0, 1):
        left = [slice(None), slice(None)]
        right = [slice(None), slice(None)]
        left[axis], right[axis] = slice(None, -1), slice(1, None)
        left, right = tuple(left), tuple(right)
        jump = good[left] & good[right] & (np.abs(d[left] - d[right]) > .05 + .03 * np.minimum(d[left], d[right]))
        edges[left] |= jump
        edges[right] |= jump
    if not edges.any():
        return edges
    return (ndimage.distance_transform_edt(~edges) <= radius) & good


def depth_statistics(pred, gt, valid_frames, instances=None, max_depth=20.):
    pred, gt = np.asarray(pred), np.asarray(gt)
    if pred.shape != gt.shape:
        raise ValueError("Depth rasters must be identical")
    good = np.isfinite(gt) & (gt > 0) & (gt <= max_depth) & np.asarray(valid_frames, bool)[:, None, None]
    pg = np.isfinite(pred) & (pred > 0)
    p = np.where(pg, pred, 0)
    error = np.abs(p - gt) / np.maximum(gt, 1e-12)
    delta = pg & (np.maximum(p / np.maximum(gt, 1e-12), gt / np.maximum(p, 1e-12)) < 1.25)
    regions = {"overall": good, "edge5": good & np.stack([edge_band(d) for d in gt]),
               "edge1": good & np.stack([edge_band(d, radius=1) for d in gt])}
    if instances is not None:
        regions["object_mask"] = good & (np.asarray(instances) >= 0)
    out = {}
    for name, mask in regions.items():
        n = int(mask.sum())
        out[name] = {
            "n": n, "absrel": float(error[mask].mean()) if n else None,
            "delta1": float(delta[mask].mean()) if n else None,
            "prediction_coverage": float(pg[mask].mean()) if n else None,
            "absrel_sum": float(error[mask].sum()), "delta1_sum": int(delta[mask].sum()),
            "predicted": int(pg[mask].sum()),
        }
    ratios = (p[good & pg] / gt[good & pg])
    frame_ratios = [float(np.median(p[i][good[i] & pg[i]] / gt[i][good[i] & pg[i]]))
                    if np.any(good[i] & pg[i]) else None for i in range(len(gt))]
    out["scale_ratio"] = float(np.median(ratios)) if len(ratios) else None
    out["frame_scale_ratios"] = frame_ratios
    log_scales = np.log([x for x in frame_ratios if x is not None and x > 0])
    out["frame_log_scale_std"] = float(log_scales.std()) if len(log_scales) >= 2 else None
    out["frame_scale_valid"] = len(log_scales)
    out["frame_scale_expected"] = int(good.any(axis=(1, 2)).sum())
    out["max_gt_depth_m"] = max_depth
    return out


def rotation_degrees(matrices):
    cosine = (np.trace(matrices, axis1=-2, axis2=-1) - 1) / 2
    return np.degrees(np.arccos(np.clip(cosine, -1, 1)))


def pose_statistics(pred, gt, valid):
    valid = np.asarray(valid, bool) & np.isfinite(gt).all(axis=(1, 2))
    slots = np.flatnonzero(valid)
    if len(slots) < 2:
        return {"valid_frames": len(slots), "rotation_deg": None, "translation_m": None, "centre_relative": None}
    p, g = np.asarray(pred)[slots], np.asarray(gt)[slots]
    if not np.isfinite(p).all():
        raise ValueError("Predicted poses contain nonfinite values")
    p, g = np.linalg.inv(p[0]) @ p, np.linalg.inv(g[0]) @ g
    rot = rotation_degrees(p[1:, :3, :3] @ g[1:, :3, :3].transpose(0, 2, 1))
    distance = np.linalg.norm(g[1:, :3, 3], axis=-1)
    error = np.linalg.norm(p[1:, :3, 3] - g[1:, :3, 3], axis=-1)
    moving = distance >= .25
    rp, rg = np.linalg.inv(p[:-1]) @ p[1:], np.linalg.inv(g[:-1]) @ g[1:]
    return {
        "valid_frames": len(slots), "rotation_deg": float(np.median(rot)),
        "translation_m": float(np.median(error)),
        "translation_rmse_m": float(np.sqrt(np.mean(error ** 2))),
        "centre_relative": float(np.median(error[moving] / distance[moving])) if moving.any() else None,
        "rpe_rotation_deg": float(np.median(rotation_degrees(rp[:, :3, :3] @ rg[:, :3, :3].transpose(0, 2, 1)))),
        "rpe_translation_m": float(np.median(np.linalg.norm(rp[:, :3, 3] - rg[:, :3, 3], axis=-1))),
        "alignment": "first_valid_camera_SE3_no_scale_fit",
    }


def centre_scatter(depth, c2w, intrinsics, instances, valid, min_pixels=154):
    by = defaultdict(list)
    h, w = depth.shape[-2:]
    yy, xx = np.mgrid[0:h:2, 0:w:2]
    pixels = np.stack([xx + .5, yy + .5, np.ones_like(xx)], axis=-1)
    for frame in np.flatnonzero(valid):
        rays = pixels @ np.linalg.inv(intrinsics[frame]).T
        labels = instances[frame][::2, ::2]
        z = depth[frame][::2, ::2]
        ids, counts = np.unique(instances[frame], return_counts=True)
        for obj, count in zip(ids, counts):
            if obj < 0 or count < min_pixels:
                continue
            mask = (labels == obj) & np.isfinite(z) & (z > 0)
            if mask.sum() < 3:
                continue
            points = (rays[mask] * z[mask, None]) @ c2w[frame, :3, :3].T + c2w[frame, :3, 3]
            by[int(obj)].append((int(frame), np.median(points, axis=0)))
    rows = []
    for obj, frames in by.items():
        if len(frames) < 2:
            continue
        centres = np.stack([v for _, v in frames])
        median = np.median(centres, axis=0)
        distances = np.linalg.norm(centres - median, axis=-1)
        rows.append({
            "instance": obj, "frames": [f for f, _ in frames],
            "centres": centres.tolist(), "median_scatter_m": float(np.median(distances)),
            "rms_scatter_m": float(np.sqrt(np.mean(distances ** 2))),
        })
    return rows


def paired_bootstrap(rows, baseline, draws=2000, seed=20261111):
    def keyed(values):
        result = {}
        for row in values:
            key = str(row.get("set", "vsi")) + "/" + str(row["id"])
            if key in result:
                raise ValueError("Duplicate item in a paired arm")
            result[key] = row
        return result
    aa, bb = keyed(rows), keyed(baseline)
    if set(aa) != set(bb) or not aa:
        raise ValueError("A paired comparison requires identical nonempty item sets")
    grouped = defaultdict(list)
    for key in sorted(aa):
        a, b = aa[key], bb[key]
        if a["scene"] != b["scene"]:
            raise ValueError("Paired item scene differs")
        if not np.isfinite([a["score"], b["score"]]).all():
            raise ValueError("Invalid score")
        grouped[a["scene"]].append(a["score"] - b["score"])
    scenes = sorted(grouped)
    sums = np.array([sum(grouped[s]) for s in scenes])
    counts = np.array([len(grouped[s]) for s in scenes])
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        choice = rng.integers(0, len(scenes), len(scenes))
        samples.append(100 * sums[choice].sum() / counts[choice].sum())
    return {
        "items": len(aa), "scenes": len(scenes),
        "score_points": 100 * float(np.mean([r["score"] for r in aa.values()])),
        "baseline_points": 100 * float(np.mean([r["score"] for r in bb.values()])),
        "delta_points": 100 * float(sums.sum() / counts.sum()),
        "ci95": np.percentile(samples, [2.5, 97.5]).tolist(), "draws": draws, "seed": seed,
    }
