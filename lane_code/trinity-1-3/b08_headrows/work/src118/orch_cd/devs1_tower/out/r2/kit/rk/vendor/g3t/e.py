import math
import numpy as np
ORIGIN_FRAME = 0
FRAMES = 32
ANCHOR_FRAMES = tuple(range(1, 32, 2))

def quaternion_xyzw(rotation):
    m = np.asarray(rotation, dtype=np.float64)
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.asarray(q) / np.linalg.norm(q)
    return -q if q[3] < 0 else q

def rotation_from_xyzw(q):
    x, y, z, w = np.asarray(q, dtype=np.float64) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

def rigid(pose):
    pose = np.asarray(pose, dtype=np.float64)
    rotation = pose[:3, :3]
    return pose.shape == (4, 4) and np.isfinite(pose).all() and np.allclose(pose[3], [0, 0, 0, 1], atol=1e-05) and np.allclose(rotation.T @ rotation, np.eye(3), atol=0.0001) and (abs(np.linalg.det(rotation) - 1) < 0.0001)

def trajectory_scale(camera, mask):
    camera, mask = (np.asarray(camera, dtype=np.float64), np.asarray(mask, dtype=bool))
    steps = [np.linalg.norm(camera[g, :3] - camera[g - 1, :3]) for g in range(1, len(camera)) if mask[g] and mask[g - 1]]
    return float(np.mean(steps)) if steps else 0.0

def encode_cameras(c2w, intrinsics, raster_hw, valid=None, all_frames=False):
    c2w, intrinsics = (np.asarray(c2w, dtype=np.float64), np.asarray(intrinsics, dtype=np.float64))
    frames = len(c2w)
    if c2w.shape != (frames, 4, 4) or intrinsics.shape != (frames, 3, 3) or (not all_frames and frames != FRAMES) or (all_frames and (not 2 <= frames <= 256 or frames % 2)):
        raise ValueError('Expected matching even camera-to-world poses and intrinsics matrices')
    raster = np.asarray(raster_hw, dtype=np.float64)
    raster = np.broadcast_to(raster, (frames, 2)) if raster.shape == (2,) else raster
    if raster.shape != (frames, 2) or not np.all(raster > 0):
        raise ValueError('Expected positive raster height and width')
    valid = np.ones(frames, bool) if valid is None else np.asarray(valid, dtype=bool)
    if valid.shape != (frames,):
        raise ValueError('Pose validity must match the frame count')
    anchors = tuple(range(frames)) if all_frames else ANCHOR_FRAMES
    groups = len(anchors)
    camera, mask = (np.zeros((groups, 9)), np.zeros(groups, bool))
    if not (valid[ORIGIN_FRAME] and rigid(c2w[ORIGIN_FRAME])):
        return (camera, mask, 0.0)
    for g, f in enumerate(anchors):
        fx, fy = (intrinsics[f, 0, 0], intrinsics[f, 1, 1])
        mask[g] = bool(valid[f] and rigid(c2w[f]) and np.isfinite(intrinsics[f]).all() and (fx > 0) and (fy > 0))
    if mask.sum() < 2:
        return (camera, np.zeros(groups, bool), 0.0)
    reference = c2w[ORIGIN_FRAME]
    for g in np.flatnonzero(mask):
        f = anchors[g]
        relative = np.linalg.inv(c2w[f]) @ reference
        height, width = raster[f]
        camera[g, :3] = relative[:3, 3]
        camera[g, 3:7] = quaternion_xyzw(relative[:3, :3])
        camera[g, 7] = 2 * math.atan(height / (2 * intrinsics[f, 1, 1]))
        camera[g, 8] = 2 * math.atan(width / (2 * intrinsics[f, 0, 0]))
    return (camera, mask, trajectory_scale(camera, mask))

def encode_gravity(c2w, world_up=(0.0, 0.0, 1.0)):
    c2w = np.asarray(c2w, dtype=np.float64)
    pose = c2w[ORIGIN_FRAME] if c2w.ndim == 3 else c2w
    if not rigid(pose):
        return (np.zeros(3, dtype=np.float64), False)
    up_world = np.asarray(world_up, dtype=np.float64)
    if up_world.shape != (3,) or not np.isfinite(up_world).all() or np.linalg.norm(up_world) < 1e-06:
        raise ValueError('World up must be a finite nonzero 3-vector')
    up_world = up_world / np.linalg.norm(up_world)
    up_ref = pose[:3, :3].T @ up_world
    return (up_ref / np.linalg.norm(up_ref), True)

def gravity_reference_rotation(up_in_ref):
    ez = np.asarray(up_in_ref, dtype=np.float64)
    norm_z = float(np.linalg.norm(ez))
    if ez.shape != (3,) or not math.isfinite(norm_z) or norm_z < 1e-06:
        raise ValueError('The gravity up vector must be a finite nonzero 3-vector')
    ez = ez / norm_z
    forward = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    y_perp = forward - float(np.dot(forward, ez)) * ez
    if np.linalg.norm(y_perp) < 1e-06:
        raise ValueError('The origin camera looks along gravity: its horizontal forward is undefined')
    ey = y_perp / np.linalg.norm(y_perp)
    ex = np.cross(ey, ez)
    ex = ex / np.linalg.norm(ex)
    return np.stack((ex, ey, ez), axis=0)

def to_gravity_reference_frame(camera_targets, up_in_ref):
    cam = np.asarray(camera_targets, dtype=np.float64)
    single = cam.ndim == 1
    if single:
        cam = cam[None, :]
    if cam.ndim != 2 or cam.shape[1] != 9 or (not np.isfinite(cam).all()):
        raise ValueError('Expected finite [S, 9] camera encodings')
    r_align = gravity_reference_rotation(up_in_ref)
    slots = cam.shape[0]
    r_grav = np.zeros((slots, 3, 3), dtype=np.float64)
    t_grav = np.zeros((slots, 3), dtype=np.float64)
    for k in range(slots):
        q_rel = cam[k, 3:7]
        if np.linalg.norm(q_rel) < 1e-06:
            raise ValueError('A camera encoding has a zero quaternion')
        r_rel = rotation_from_xyzw(q_rel)
        r_c2ref = r_rel.T
        t_c2ref = -r_c2ref @ cam[k, :3]
        r_grav[k] = r_align @ r_c2ref
        t_grav[k] = r_align @ t_c2ref
    fov_hw = cam[:, 7:9].copy()
    if single:
        return (r_grav[0], t_grav[0], fov_hw[0])
    return (r_grav, t_grav, fov_hw)
