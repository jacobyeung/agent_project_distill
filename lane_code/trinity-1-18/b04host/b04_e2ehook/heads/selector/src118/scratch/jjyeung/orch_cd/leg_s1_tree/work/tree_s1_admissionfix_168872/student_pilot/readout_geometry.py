"""Stage-1 depth queries and P3 validation diagnostics, without tool admission."""
import math

import torch

from .p3_grammar import ToolError


def depth_readout(capture, pose, uv, depth_anchors):
    """Match PrefixCapture.geometry's depth_fn, including dtype and slot mapping."""
    anchors = tuple(capture.model.config.p3['anchors'])
    if len(uv) != len(depth_anchors):
        raise ValueError('Depth query slots differ from the head contract')
    camera = capture.heads.camera
    with torch.no_grad():
        fmap = camera.point_depth.encode(capture.grids[0], capture.vits[0], pose[-1][0, :, 7:9])
        depth = []
        for k, points in zip(depth_anchors, uv):
            index = anchors.index(k)
            points = torch.as_tensor(points, dtype=torch.float32, device=fmap.device)[None]
            depth.append(camera.point_depth.query(fmap[index:index+1], points)[0].double().cpu().numpy())
    return [value.tolist() for value in depth]


def geometry_diagnostics(capture, raw_pose):
    """Retain tool errors without changing, clipping or masking predictions."""
    error = None
    try:
        capture.geometry()
    except ToolError as exc:
        error = exc.code
    invalid = [
        dict(frame=frame, fov_hw_rad=pose[7:9])
        for frame, pose in zip(capture.model.config.p3['anchors'], raw_pose)
        if any(not 0 < value < math.pi for value in pose[7:9])
    ]
    metadata = {}
    if capture.heads.camera.settings.get('pose_input'):
        metadata['pose_input'] = capture.heads.camera.settings['pose_input']
    return dict(geometry_error=error, invalid_fov_frames=invalid, **metadata)


def validation_summary(rows):
    """Count sampled frame slots once per row, even when both FoVs are invalid."""
    rows = list(rows)
    errors = {}
    for row in rows:
        error = row.get('geometry_error')
        if error is not None:
            errors[error] = errors.get(error, 0) + 1
    return dict(geometry_error_rows=sum(errors.values()), geometry_errors=errors,
                invalid_fov_rows=sum(bool(row.get('invalid_fov_frames')) for row in rows),
                invalid_fov_frames=sum(len(row.get('invalid_fov_frames', [])) for row in rows))
