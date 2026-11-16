"""Metric camera targets; fixed-viewpoint clips use the reviewed 32-camera path."""
import math

import numpy as np

from .camera_targets import encode_cameras, encode_gravity, quaternion_xyzw, rigid, trajectory_scale


def encode_cameras_n(c2w, intrinsics, raster_hw, valid=None):
    """Generalize the reviewed all-frame encoder without changing its 32-frame path."""
    c2w, intrinsics = np.asarray(c2w, dtype=np.float64), np.asarray(intrinsics, dtype=np.float64)
    n = len(c2w)
    if n < 2 or n % 2 or c2w.shape != (n, 4, 4) or intrinsics.shape != (n, 3, 3):
        raise ValueError('Expected an even number of camera poses and intrinsics')
    raster = np.asarray(raster_hw, dtype=np.float64)
    raster = np.broadcast_to(raster, (n, 2)) if raster.shape == (2,) else raster
    if raster.shape != (n, 2) or not np.isfinite(raster).all() or not np.all(raster > 0):
        raise ValueError('Expected finite positive raster height and width')
    valid = np.ones(n, bool) if valid is None else np.asarray(valid, dtype=bool)
    if valid.shape != (n,):
        raise ValueError('Expected one validity flag per frame')
    if n == 32:
        return encode_cameras(c2w, intrinsics, raster, valid=valid, all_frames=True)
    camera, mask = np.zeros((n, 9)), np.zeros(n, bool)
    if not (valid[0] and rigid(c2w[0])):
        return camera, mask, 0.0
    for f in range(n):
        fx, fy = intrinsics[f, 0, 0], intrinsics[f, 1, 1]
        mask[f] = bool(valid[f] and rigid(c2w[f]) and np.isfinite(intrinsics[f]).all() and fx > 0 and fy > 0)
    if mask.sum() < 2:
        return camera, np.zeros(n, bool), 0.0
    for f in np.flatnonzero(mask):
        relative = np.linalg.inv(c2w[f]) @ c2w[0]
        height, width = raster[f]
        camera[f, :3] = relative[:3, 3]
        camera[f, 3:7] = quaternion_xyzw(relative[:3, :3])
        camera[f, 7] = 2 * math.atan(height / (2 * intrinsics[f, 1, 1]))
        camera[f, 8] = 2 * math.atan(width / (2 * intrinsics[f, 0, 0]))
    return camera, mask, trajectory_scale(camera, mask)


def encode_target(poses, ordinals, source):
    """Select posed raw ordinals, reject invalid GT, and return the package target."""
    numbers = source.get('frame_numbers')
    if numbers is None:
        if (source['pose_count'] != source['total_num_frames']
                or any(type(v) is not int or not 0 <= v < source['total_num_frames'] for v in ordinals)):
            raise ValueError('Clip includes an unposed ordinal')
        order = list(ordinals)
    else:
        lookup = {value: i for i, value in enumerate(numbers)}
        try:
            order = [lookup[value] for value in ordinals]
        except KeyError as error:
            raise ValueError('Clip includes an unposed ordinal') from error
    c2w = poses['c2w'][order]
    if not all(rigid(pose) for pose in c2w):
        raise ValueError('Clip GT poses must be finite and rigid')
    raster = np.asarray(poses['raster_hw'])
    if raster.ndim == 2:
        raster = raster[order]
    camera, mask, scale = encode_cameras_n(c2w, poses['intrinsics'][order], raster)
    gravity, ok = encode_gravity(c2w, poses['world_up'])
    if not mask.all() or not ok:
        raise ValueError('Clip has invalid calibration or gravity')
    return {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': scale,
            'gravity': gravity.tolist(), 'gravity_mask': bool(ok), 'metric': True, 'point_depth': []}
