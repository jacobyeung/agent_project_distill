import numpy as np

def transform_geometry(data, transform):
    """Move points and camera poses together; camera depth and pixel masks stay fixed."""
    transform = np.asarray(transform, dtype=np.float64)
    if (transform.shape != (4, 4) or not np.isfinite(transform).all()
            or not np.allclose(transform[3], [0, 0, 0, 1])
            or not np.allclose(transform[:3, :3].T @ transform[:3, :3], np.eye(3), atol=1e-6)
            or not np.isclose(np.linalg.det(transform[:3, :3]), 1, atol=1e-6)):
        raise ValueError('world transform must be proper rigid; scale fitting is forbidden')
    result = dict(data)
    points = np.asarray(data['pts3d_world'], dtype=np.float64)
    result['pts3d_world'] = (points @ transform[:3, :3].T + transform[:3, 3]).astype(np.float32)
    result['camera_poses'] = (transform @ data['camera_poses']).astype(np.float32)
    result['coordinate_convention'] = 'r2_metric_source_world_camera_to_world_opencv'
    return result


def canonical_geometry(data, gravity_up):
    """Return meters with +Z up, +Y initial horizontal view, origin at camera 0.

    Under re-expression X'=QX+t, poses'=T@poses, pass up'=Q@up.
    Both the main heading and vertical-view fallback then give identical output.
    This fixes coordinates; it does not repair relative poses or metric scale.
    """
    poses = np.asarray(data['camera_poses'], dtype=np.float64)
    if (poses.shape != (32, 4, 4) or not np.isfinite(poses).all()
            or not np.allclose(poses[:, 3], [0, 0, 0, 1], atol=1e-6)
            or not np.allclose(poses[:, :3, :3].transpose(0, 2, 1) @ poses[:, :3, :3], np.eye(3), atol=1e-4)
            or not np.allclose(np.linalg.det(poses[:, :3, :3]), 1, atol=1e-4)):
        raise ValueError('coordinate gauge requires 32 proper finite poses')
    up = np.asarray(gravity_up, dtype=np.float64)
    if up.shape != (3,) or not np.isfinite(up).all() or np.linalg.norm(up) < 1e-8:
        raise ValueError('coordinate gauge requires a finite nonzero gravity-up direction')
    up = up / np.linalg.norm(up)
    forward = poses[0, :3, 2]
    heading = forward - up * np.dot(up, forward)
    if np.linalg.norm(heading) <= 1e-6:
        right = poses[0, :3, 0]
        right = right - up * np.dot(up, right)
        if np.linalg.norm(right) <= 1e-6:
            raise ValueError('camera bases do not identify a horizontal heading')
        right /= np.linalg.norm(right)
        heading = np.cross(up, right)
    heading /= np.linalg.norm(heading)
    right = np.cross(heading, up)
    basis = np.column_stack((right, heading, up))
    transform = np.eye(4)
    transform[:3, :3] = basis.T
    transform[:3, 3] = -basis.T @ poses[0, :3, 3]
    result = transform_geometry(data, transform)
    result['coordinate_convention'] = 'first_camera_origin_heading_gravity_up_camera_to_world_opencv'
    return result

