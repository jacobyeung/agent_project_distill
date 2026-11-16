from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial.transform import Rotation

from .io import check_space, local_output


FIELDS = {
    "layout", "r_grav", "t_grav", "fov_hw", "raw_pose", "gravity_up", "gravity_source",
    "depth_grid", "grid_uv", "scale", "source_hw", "anchor_frame_indices",
}


def validate_frames(dense_indices, anchor_slots, expected, production=True):
    dense_indices = np.asarray(dense_indices)
    slots = np.asarray(anchor_slots)
    expected = np.asarray(expected)
    if dense_indices.ndim != 1 or not np.issubdtype(dense_indices.dtype, np.integer):
        raise ValueError("Frame ordinals must be a one-dimensional integer array")
    if production and (len(dense_indices) < 64 or len(slots) != 32):
        raise ValueError("Production requires at least 64 reconstructed frames and exactly 32 anchors")
    if len(dense_indices) < 1 or np.any(np.diff(dense_indices) <= 0):
        raise ValueError("Dense frames must be distinct and increasing")
    if slots.ndim != 1 or not np.issubdtype(slots.dtype, np.integer):
        raise ValueError("Anchor slots must be integer indices")
    if not len(slots) or slots[0] != 0 or slots[-1] >= len(dense_indices) or np.any(np.diff(slots) <= 0):
        raise ValueError("Invalid anchor slots")
    if not np.array_equal(dense_indices[slots], expected):
        raise ValueError("The exact tower anchor ordinals must be retained")


def gravity_rotation(up):
    z = np.asarray(up, np.float64)
    if z.shape != (3,) or not np.isfinite(z).all() or np.linalg.norm(z) < 1e-6:
        raise ValueError("Invalid gravity vector")
    z = z / np.linalg.norm(z)
    y = np.array([0., 0., 1.]) - z[2] * z
    if np.linalg.norm(y) < 1e-6:
        raise ValueError("The reference camera points along gravity")
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    x /= np.linalg.norm(x)
    return np.stack([x, y, z])


def sample_grid(depth, size=51):
    depth = np.asarray(depth, np.float32)
    if depth.ndim != 3:
        raise ValueError("Optical-axis depth must have shape [frames,height,width]")
    h, w = depth.shape[-2:]
    yy, xx = np.meshgrid(np.linspace(0, h, size) - .5, np.linspace(0, w, size) - .5, indexing="ij")
    return np.stack([map_coordinates(d, [yy, xx], order=1, mode="nearest", prefilter=False) for d in depth])


def raster_depth(grid, hw=(240, 320)):
    grid = np.asarray(grid, np.float32)
    h, w = hw
    g = grid.shape[-1]
    if grid.ndim != 3 or grid.shape[-2] != g:
        raise ValueError("Depth grid must be square")
    yy, xx = np.mgrid[:h, :w]
    x = np.clip((xx + .5) / w * 1000 * ((g - 1) / 1000.), 0, g - 1)
    y = np.clip((yy + .5) / h * 1000 * ((g - 1) / 1000.), 0, g - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, g - 1), np.minimum(y0 + 1, g - 1)
    fx, fy = x - x0, y - y0
    return (grid[:, y0, x0] * (1 - fx) * (1 - fy)
            + grid[:, y0, x1] * fx * (1 - fy)
            + grid[:, y1, x0] * (1 - fx) * fy
            + grid[:, y1, x1] * fx * fy).astype(np.float32)


def centre_projection(intrinsics, source_hw):
    projected = np.array(intrinsics, np.float64, copy=True)
    h, w = source_hw
    offsets = projected[:, :2, 2] - [w / 2, h / 2]
    projected[:, :2, 2] = [w / 2, h / 2]
    return projected, {"approximation": bool(np.any(np.abs(offsets) > .51)),
                       "max_principal_offset_px": float(np.max(np.abs(offsets))),
                       "principal_offsets_px": offsets.tolist(),
                       "scope": "centre-only legacy proxy; native calibration is retained separately"}


def make_export(c2w, intrinsics, depth, frame_indices, anchor_slots, source_hw, gravity_up,
                scale=1., production=True, principal_tolerance=.51):
    c2w, intrinsics = np.asarray(c2w, np.float64), np.asarray(intrinsics, np.float64)
    frame_indices, slots = np.asarray(frame_indices, np.int64), np.asarray(anchor_slots, np.int64)
    validate_frames(frame_indices, slots, frame_indices[slots], production)
    n = len(frame_indices)
    if c2w.shape != (n, 4, 4) or intrinsics.shape != (n, 3, 3) or len(depth) != n:
        raise ValueError("Native geometry does not cover every reconstructed frame")
    if not np.isfinite(c2w).all() or not np.isfinite(intrinsics).all():
        raise ValueError("Nonfinite camera outputs")
    if not np.allclose(c2w[:, 3], [0., 0., 0., 1.], atol=1e-5):
        raise ValueError("Invalid homogeneous camera matrices")
    if not np.allclose(c2w[:, :3, :3] @ c2w[:, :3, :3].transpose(0, 2, 1), np.eye(3), atol=1e-3):
        raise ValueError("Camera rotations are not orthonormal")
    h, w = source_hw
    if np.any(np.abs(intrinsics[:, :2, 2] - [w / 2, h / 2]) > principal_tolerance):
        raise ValueError("The export cannot represent an off-centre principal point")
    if np.any(intrinsics[:, (0, 1), (0, 1)] <= 0):
        raise ValueError("Nonpositive focal length")
    relative = np.linalg.inv(c2w[0]) @ c2w
    relative[:, :3, 3] *= scale
    extrinsic = np.linalg.inv(relative)
    fov = 2 * np.arctan(np.stack([h / (2 * intrinsics[:, 1, 1]), w / (2 * intrinsics[:, 0, 0])], axis=-1))
    raw = np.concatenate([extrinsic[:, :3, 3], Rotation.from_matrix(extrinsic[:, :3, :3]).as_quat(), fov], axis=-1)
    g = gravity_rotation(gravity_up)
    out = {
        "layout": np.array("per_frame"),
        "r_grav": (g @ relative[:, :3, :3])[slots],
        "t_grav": (relative[:, :3, 3] @ g.T)[slots],
        "fov_hw": fov[slots],
        "raw_pose": raw[slots],
        "gravity_up": np.asarray(gravity_up, np.float64),
        "gravity_source": np.array("own"),
        "depth_grid": sample_grid(np.asarray(depth)[slots] * scale),
        "grid_uv": np.linspace(0, 1000, 51, dtype=np.float32),
        "scale": np.array(scale, np.float64),
        "source_hw": np.asarray(source_hw, np.int64),
        "anchor_frame_indices": frame_indices[slots],
    }
    validate_export(out, frame_indices[slots], expected_count=32 if production else len(slots))
    return out


def validate_export(data, expected_frames=None, expected_count=32):
    if set(data) != FIELDS:
        raise ValueError(f"Export fields differ: missing={FIELDS-set(data)}, extra={set(data)-FIELDS}")
    n = len(data["anchor_frame_indices"])
    shapes = {
        "r_grav": (n, 3, 3), "t_grav": (n, 3), "fov_hw": (n, 2), "raw_pose": (n, 9),
        "gravity_up": (3,), "depth_grid": (n, 51, 51), "grid_uv": (51,), "source_hw": (2,),
    }
    if n != expected_count or str(data["layout"]) != "per_frame":
        raise ValueError("Wrong anchor count or layout")
    for key, shape in shapes.items():
        value = np.asarray(data[key])
        if value.shape != shape or not np.isfinite(value).all():
            raise ValueError(f"Invalid {key}: shape={value.shape}")
    if np.any(data["depth_grid"] < 0):
        raise ValueError("Depth must be nonnegative optical metres; zero marks missing output")
    if not np.isfinite(data["scale"]) or data["scale"] <= 0:
        raise ValueError("Invalid scale")
    if np.any(data["fov_hw"] <= 0) or np.any(data["fov_hw"] >= np.pi):
        raise ValueError("FoV must be in radians in (0, pi)")
    if not np.array_equal(data["grid_uv"], np.linspace(0, 1000, 51, dtype=np.float32)):
        raise ValueError("Incorrect grid coordinates")
    r = data["r_grav"]
    if not np.allclose(r @ r.transpose(0, 2, 1), np.eye(3), atol=1e-3) or not np.allclose(np.linalg.det(r), 1, atol=1e-3):
        raise ValueError("Invalid camera rotation")
    raw = data["raw_pose"]
    if not np.allclose(np.linalg.norm(raw[:, 3:7], axis=-1), 1, atol=1e-3):
        raise ValueError("Invalid raw quaternion")
    if not np.allclose(raw[0, :6], 0, atol=2e-5) or not np.isclose(abs(raw[0, 6]), 1, atol=2e-5):
        raise ValueError("Raw camera 0 must be identity")
    g = gravity_rotation(data["gravity_up"])
    rr = Rotation.from_quat(raw[:, 3:7]).as_matrix().transpose(0, 2, 1)
    tt = -np.einsum("nij,nj->ni", rr, raw[:, :3])
    if not np.allclose(g @ rr, r, atol=2e-5) or not np.allclose(tt @ g.T, data["t_grav"], atol=2e-5):
        raise ValueError("Raw pose and gravity-frame pose disagree")
    if not np.allclose(raw[:, 7:9], data["fov_hw"], atol=1e-8):
        raise ValueError("Raw pose and FoV disagree")
    frames = data["anchor_frame_indices"]
    if np.any(np.diff(frames) <= 0):
        raise ValueError("Anchor ordinals must be increasing")
    if expected_frames is not None and not np.array_equal(frames, expected_frames):
        raise ValueError("Frame identity differs from the tower")
    return data


def load_export(path, expected_frames=None, expected_count=32):
    with np.load(path, allow_pickle=False) as z:
        data = {key: z[key] for key in z.files}
    return validate_export(data, expected_frames, expected_count)


def write_export(path, data, check_disk=True, expected_count=32):
    validate_export(data, expected_count=expected_count)
    path = local_output(path) if check_disk else Path(path)
    if check_disk:
        check_space(sum(x.nbytes for x in data.values()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        np.savez_compressed(f, **data)


def camera_arrays(data, hw=(240, 320)):
    n = len(data["t_grav"])
    c2w = np.repeat(np.eye(4)[None], n, axis=0)
    c2w[:, :3, :3], c2w[:, :3, 3] = data["r_grav"], data["t_grav"]
    h, w = hw
    k = np.repeat(np.eye(3)[None], n, axis=0)
    k[:, 0, 0] = w / (2 * np.tan(data["fov_hw"][:, 1] / 2))
    k[:, 1, 1] = h / (2 * np.tan(data["fov_hw"][:, 0] / 2))
    k[:, 0, 2], k[:, 1, 2] = w / 2, h / 2
    return c2w, k
