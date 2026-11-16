import numpy as np
from scipy.ndimage import map_coordinates


def temporal_scales(depth, c2w, intrinsics, iterations=3, offsets=(1, 2, 4, 8), pixel_offset=.5):
    depth = np.asarray(depth, np.float64)
    c2w, intrinsics = np.asarray(c2w, np.float64), np.asarray(intrinsics, np.float64)
    if depth.ndim != 3 or c2w.shape != (len(depth), 4, 4) or intrinsics.shape != (len(depth), 3, 3):
        raise ValueError("Temporal correction requires aligned depth, pose and intrinsics")
    if not np.isfinite(c2w).all() or not np.isfinite(intrinsics).all():
        raise ValueError("Temporal correction cannot use nonfinite cameras")
    n, height, width = depth.shape
    if n == 0:
        raise ValueError("No frames")
    depth = np.where(np.isfinite(depth) & (depth > 0), depth, 0)
    step = max(1, int(np.ceil(max(height, width) / 40)))
    yy, xx = np.mgrid[0:height:step, 0:width:step]
    pixels = np.stack([xx.ravel() + pixel_offset, yy.ravel() + pixel_offset, np.ones(xx.size)], -1)
    rays = pixels[None] @ np.linalg.inv(intrinsics).transpose(0, 2, 1)
    w2c = np.linalg.inv(c2w)
    pairs = [(i, j) for i in range(n) for offset in offsets for j in (i-offset, i+offset) if 0 <= j < n]
    log_scale = np.zeros(n)
    residuals, accepted, used_iterations = [], [], 0
    for iteration in range(iterations):
        current = depth * np.exp(log_scale)[:, None, None]
        accepted, residuals = [], []
        for i, j in pairs:
            z = current[i, yy, xx].ravel()
            points = (rays[i] * z[:, None]) @ c2w[i, :3, :3].T + c2w[i, :3, 3]
            target = points @ w2c[j, :3, :3].T + w2c[j, :3, 3]
            uv = (target / np.maximum(target[:, 2:3], 1e-12)) @ intrinsics[j].T
            uv = uv[:, :2] - pixel_offset
            inside = (z > 0) & (target[:, 2] > 0) & (uv[:, 0] >= 0) & (uv[:, 0] <= width-1)
            inside &= (uv[:, 1] >= 0) & (uv[:, 1] <= height-1)
            observed = map_coordinates(current[j], [uv[:, 1], uv[:, 0]], order=1, mode="constant", cval=0)
            keep = inside & (observed > 0)
            ratios = np.log(observed[keep] / target[keep, 2])
            ratios = ratios[np.isfinite(ratios) & (np.abs(ratios) <= np.log(2.))]
            if len(ratios) < 32:
                continue
            median = float(np.median(ratios))
            mad = float(np.median(np.abs(ratios - median)))
            weight = np.sqrt(min(len(ratios), 256)) / (1 + mad / .05)
            accepted.append((i, j, weight, median))
            residuals.append(abs(median))
        if not accepted:
            break
        matrix = np.zeros((len(accepted) + n + 1, n))
        target = np.zeros(len(matrix))
        for row, (i, j, weight, value) in enumerate(accepted):
            matrix[row, i], matrix[row, j], target[row] = weight, -weight, weight * value
        matrix[len(accepted):-1] = .01 * np.eye(n)
        matrix[-1] = 1.
        log_scale += np.linalg.lstsq(matrix, target, rcond=None)[0]
        log_scale -= log_scale.mean()
        magnitude = float(np.max(np.abs(log_scale)))
        if magnitude > np.log(2.):
            log_scale *= np.log(2.) / magnitude
        used_iterations = iteration + 1
    return np.exp(log_scale), {
        "method": "symmetric_reprojection_log_scale_v1", "gt_used": False,
        "iterations": used_iterations, "offsets": list(offsets), "pairs": len(accepted),
        "raster_hw": [height, width], "pixel_offset": pixel_offset,
        "median_pair_log_residual_before_last_update": float(np.median(residuals)) if residuals else None,
        "scale_bounds": [.5, 2.], "gauge": "zero_mean_log_scale", "frame_log_scales": log_scale.tolist(),
    }
