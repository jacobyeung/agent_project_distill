"""Phase-2 head API: metric pose and point depth from the student's own heads, one video row at a time.

Frame convention (one convention, phase 2's): frames are 1-based, 1..32, over the row's 32 sampled
frames, and the pose origin is frame 1. Qwen3.5 fuses frames 2g+1 and 2g+2 (1-based) into temporal
group g; the heads describe the group's second frame, 2g+2. So:
- pose(frame) answers frame 1 (the origin: zero position, heading 0) and frames 2, 4, ..., 32;
- depth(frame, points) answers frames 2, 4, ..., 32;
- frames 3, 5, ..., 31 have no head output and raise (they share group (frame - 1) / 2 with frame + 1).
Internally (camera_targets, the label bank) the same frames are 0-based sampled-frame indices:
1-based frame f is sampled frame f - 1, the origin is sampled frame 0 and group g's anchor is 2g + 1.

- `pose(frame) -> (R, t, info)`: R [3, 3] camera-to-reference rotation and t [3] the camera centre in
  metres, in the frame-1 gravity reference: origin at frame 1's camera, +Z gravity up (from the predicted
  up vector), +Y frame 1's horizontal forward, +X = Y x Z horizontal right.
- `depth(frame, point_xy_0_1000) -> metres` along the optical axis (camera z), at [x, y] on the [0, 1000]
  grid with (0, 0) the top-left image corner.

A session runs one forward through the same hooks as training (auxiliary_losses.capture_camera_states):
carriers inserted after each group's video tokens (camera_targets.insert_carriers), the configured
carrier layer (final norm by default), the row's visual-token grid and ViT grids. Phase 2's decode
prefill therefore contains the 16 carriers. Missing inputs raise; nothing falls back.
"""
from contextlib import contextmanager
import contextvars
import math

import numpy as np
import torch

from .camera_targets import GROUPS, gravity_reference_rotation, rotation_from_xyzw, to_gravity_reference_frame

_ACTIVE_SESSION = contextvars.ContextVar('active_head_session', default=None)
REFERENCE_FRAME = 'frame1_gravity_reference_x_right_y_forward_z_up_metres'
FRAME_ORIGIN = 1
FRAME_ANCHORS = tuple(2 * g + 2 for g in range(GROUPS))
POSE_FRAMES = (FRAME_ORIGIN,) + FRAME_ANCHORS
DEPTH_FRAMES = FRAME_ANCHORS


def group_of_frame(frame):
    """1-based anchor frame 2g + 2 -> temporal group g; raises for every other frame."""
    if type(frame) is not int or frame not in FRAME_ANCHORS:
        if type(frame) is int and 3 <= frame <= 31 and frame % 2:
            raise ValueError(f'Frame {frame} has no head output; it shares temporal group {(frame - 1) // 2} '
                             f'with frame {frame + 1}, which the heads answer')
        raise ValueError(f'Frame {frame!r} is not an answerable 1-based frame (2, 4, ..., 32)')
    return frame // 2 - 1


class HeadSession:
    """Pose, gravity, trajectory step and point depth for one video row."""

    def __init__(self, supervision, carrier_states, visual_grid=None, vit_grids=None,
                 g3t_cam_tokens=None, g3t_pose_9d=None, g3t_gravity_up=None, g3t_step_scale=None):
        self.supervision = supervision
        device = next(supervision.parameters()).device
        states = torch.as_tensor(carrier_states, dtype=torch.float32, device=device)
        if tuple(states.shape) != (GROUPS, supervision.projector.in_features):
            raise ValueError(f'carrier_states must be [16, {supervision.projector.in_features}], got {tuple(states.shape)}')
        cam_tok = None if g3t_cam_tokens is None else torch.as_tensor(g3t_cam_tokens, dtype=torch.float32, device=device)
        if cam_tok is not None and cam_tok.ndim == 2:
            cam_tok = cam_tok[None]
        pose_prior = None if g3t_pose_9d is None else torch.as_tensor(g3t_pose_9d, dtype=torch.float32, device=device)
        if pose_prior is not None and pose_prior.ndim == 2:
            pose_prior = pose_prior[None]
        grav_prior = None if g3t_gravity_up is None else torch.as_tensor(g3t_gravity_up, dtype=torch.float32, device=device)
        if grav_prior is not None and grav_prior.ndim == 1:
            grav_prior = grav_prior[None]
        step_s = None if g3t_step_scale is None else torch.as_tensor(g3t_step_scale, dtype=torch.float32, device=device)
        if step_s is not None and step_s.ndim <= 1:
            step_s = step_s.view(1, 1)
        with torch.no_grad():
            if (any(x is not None for x in (cam_tok, pose_prior, grav_prior, step_s))
                    or getattr(supervision, "has_g3t_prior", False)
                    or getattr(getattr(supervision, "head", None), "has_g3t_prior", False)):
                stages, grav_stages, scale_stages, fov_raw = supervision.predict_all(
                    states[None],
                    g3t_cam_tokens=cam_tok,
                    g3t_pose_9d=pose_prior,
                    g3t_gravity_up=grav_prior,
                    g3t_step_scale=step_s,
                    return_fov_raw=True,
                )
            else:
                pred = supervision.predict_all(states[None])
                stages, grav_stages, scale_stages = pred[:3]
                fov_raw = pred[3] if len(pred) > 3 else stages[-1][..., 7:9]
            self.raw_pose = stages[-1][0].double().cpu().numpy()
            self.gravity_up = grav_stages[-1][0].double().cpu().numpy() if grav_stages else None
            self.trajectory_step_m = float(torch.exp(scale_stages[-1][0]).item()) if scale_stages else None
            self.feature_map = None
            if supervision.point_depth is not None:
                if visual_grid is None or vit_grids is None:
                    raise ValueError('The depth head needs the row visual grid and ViT grids')
                fov = fov_raw[0].clamp(0.1, math.pi - 0.1)
                vis = torch.as_tensor(visual_grid, dtype=torch.float32, device=device)
                vit = [torch.as_tensor(grid, dtype=torch.float32, device=device) for grid in vit_grids]
                self.feature_map = supervision.point_depth.encode(vis, vit, fov)
        if self.gravity_up is not None:
            self.r_grav, self.t_grav, self.fov_hw = to_gravity_reference_frame(self.raw_pose, self.gravity_up)
            self.r_origin = gravity_reference_rotation(self.gravity_up)

    @classmethod
    def from_forward(cls, model, batch, forward_context=None):
        """Run one no-grad forward of a single carrier-bearing row and build its session."""
        from .auxiliary_losses import capture_camera_states, unwrap

        states = capture_camera_states(model, batch, forward_context=forward_context)
        heads = unwrap(model).auxiliary_heads
        return cls(
            heads.camera,
            states['carrier_states'],
            states['visual_grid'],
            states['vit_grids'],
            g3t_cam_tokens=states.get('aux_g3t_cam_tokens'),
            g3t_pose_9d=states.get('aux_g3t_pose_9d'),
            g3t_gravity_up=states.get('aux_g3t_gravity_up'),
            g3t_step_scale=states.get('aux_g3t_step_scale'),
        )

    def relative_pose(self, frame):
        """E = inv(C_frame) @ C_1 (1-based frames) as (R [3, 3], t [3] metres) in OpenCV camera axes, without gravity."""
        if frame == FRAME_ORIGIN:
            return np.eye(3), np.zeros(3)
        encoding = self.raw_pose[group_of_frame(frame)]
        return rotation_from_xyzw(encoding[3:7]), encoding[:3].copy()

    def pose(self, frame):
        if self.gravity_up is None:
            raise ValueError('This model has no gravity branch: the gravity reference is undefined (use relative_pose)')
        info = {'frame': frame, 'reference': REFERENCE_FRAME, 'is_metric': True,
                'gravity_up_in_origin_camera': self.gravity_up.tolist(), 'trajectory_step_m': self.trajectory_step_m}
        if frame == FRAME_ORIGIN:
            return self.r_origin.copy(), np.zeros(3), {**info, 'group': 0, 'fov_hw_rad': None}
        group = group_of_frame(frame)
        return self.r_grav[group].copy(), self.t_grav[group].copy(), {
            **info, 'group': group, 'fov_hw_rad': [float(v) for v in self.fov_hw[group]]}

    def depth(self, frame, point_xy_0_1000):
        if self.feature_map is None:
            raise ValueError('This model has no point-depth head')
        group = group_of_frame(frame)
        points = np.asarray(point_xy_0_1000, dtype=np.float32)
        single = points.ndim == 1
        points = points[None] if single else points
        if (points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all()
                or np.any(points < 0) or np.any(points > 1000)):
            raise ValueError('Points must be [x, y] or [K, 2] on the [0, 1000] grid')
        fmap = self.feature_map[group:group + 1]
        with torch.no_grad():
            query = torch.as_tensor(points, device=fmap.device)[None]
            out = self.supervision.point_depth.query(fmap, query)[0].double().cpu().numpy()
        return float(out[0]) if single else out


@contextmanager
def bind_session(session):
    """Bind a HeadSession for the module-level pose(...) and depth(...) calls."""
    token = _ACTIVE_SESSION.set(session)
    try:
        yield session
    finally:
        _ACTIVE_SESSION.reset(token)


def _session(session):
    session = session if session is not None else _ACTIVE_SESSION.get()
    if not isinstance(session, HeadSession):
        raise ValueError('Pass a HeadSession or call inside `with bind_session(session):`')
    return session


def pose(frame, session=None):
    """(R, t, info) of a 1-based frame (1, 2, 4, ..., 32) in the frame-1 gravity reference, metres."""
    return _session(session).pose(frame)


def depth(frame, point_xy_0_1000, session=None):
    """Optical-axis metres at [x, y] (or [K, 2]) on the [0, 1000] grid of a 1-based frame 2, 4, ..., 32."""
    return _session(session).depth(frame, point_xy_0_1000)


def pose_all(session=None):
    """{frame: (R, t, info)} for every answerable 1-based frame (1, 2, 4, ..., 32)."""
    session = _session(session)
    return {frame: session.pose(frame) for frame in POSE_FRAMES}
