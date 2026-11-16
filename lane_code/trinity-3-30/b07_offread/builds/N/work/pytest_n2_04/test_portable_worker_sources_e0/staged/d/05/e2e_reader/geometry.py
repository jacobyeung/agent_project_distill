"""Geometry of one read from tensors of the same generate(): frozen G3T outputs, the
checkpoint's own gravity head, and the scale head's output. Fixed math only: the tree's
gravity-reference conversion, pinhole intrinsics from the field of view, one scale applied
once. No gravity guard: the own gravity head's output is used as is.

The contract checks of the tree's GeometryContract.validate still run (shapes, proper
rotations, finite intrinsics). Only its terminal statement, the sealed gravity guard
`if -R[0,2,1] <= 0: raise reference_camera_up_opposes_gravity`, is not applied; its verdict
and the reviewed C8r guard's verdict are recorded for the report, never acted on.
"""
import ast
import hashlib
import inspect
import textwrap
import threading
from types import SimpleNamespace as NS

import numpy as np

SEALED_VALIDATE_SHA256 = '05cc553d9e84d235fcc616563b67b4cc1ce50f4b7c10efcaf8a314a59010521a'
GUARD = 'reference_camera_up_opposes_gravity'
UP_PLANE_MIN = .3  # reviewed C8r guard constant; used only to RECORD its verdict (report item 5)
_lock = threading.Lock()


def _check_sealed_validate(GP):
    source = inspect.getsource(GP.GeometryContract.validate)
    if hashlib.sha256(source.encode()).hexdigest() != SEALED_VALIDATE_SHA256:
        raise RuntimeError('sealed_validate_mismatch')
    body = ast.parse(textwrap.dedent(source)).body[0].body
    terminal = ast.parse("if -R[0, 2, 1] <= 0:\n    raise GeometryError('reference_camera_up_opposes_gravity')\nreturn self").body
    if len(body) < 2 or any(ast.dump(a) != ast.dump(b) for a, b in zip(body[-2:], terminal)):
        raise RuntimeError('sealed_validate_terminal_mismatch')


def reviewed_guard_refuses(R):
    """Verdict of C8r's reviewed guard (gravity_guard.validate_up_convention); report only."""
    R = np.asarray(R, float)
    plane = np.linalg.norm(R[:, 2, :2], axis=1)
    margin = -R[:, 2, 1]
    if plane[0] >= UP_PLANE_MIN:
        return bool(margin[0] <= 0)
    usable = plane >= UP_PLANE_MIN
    return bool(usable.any() and np.median(margin[usable] / plane[usable]) <= 0)


class no_guard:
    """Context in which the tree's GeometryContract.validate runs every check except the terminal
    gravity guard (used when tree code rebuilds a geometry inside a call, e.g. replay restore)."""
    def __enter__(self):
        from student_pilot import geometry_profiles as GP
        _check_sealed_validate(GP)
        _lock.acquire()
        self.GP, self.original = GP, GP.GeometryContract.validate
        original = self.original

        def validate(contract):
            try:
                return original(contract)
            except GP.GeometryError as error:
                if str(error) != GUARD:
                    raise
                return contract
        GP.GeometryContract.validate = validate
        return self

    def __exit__(self, *exc):
        self.GP.GeometryContract.validate = self.original
        _lock.release()
        return False


def unguarded(contract_factory):
    """Build a ProfileGeometry with every contract check except the terminal gravity guard."""
    from student_pilot import geometry_profiles as GP
    _check_sealed_validate(GP)
    verdict = dict(sealed_guard_refuses=False)
    with _lock:
        original = GP.GeometryContract.validate

        def validate(self):
            try:
                return original(self)
            except GP.GeometryError as error:
                if str(error) != GUARD:
                    raise
                verdict['sealed_guard_refuses'] = True
                return self  # the terminal guard is the last statement; every other check passed
        GP.GeometryContract.validate = validate
        try:
            geometry = contract_factory(GP)
        finally:
            GP.GeometryContract.validate = original
    R = np.asarray(geometry.C)[:, :3, :3]
    verdict['reviewed_guard_refuses'] = reviewed_guard_refuses(R)
    geometry.guard_verdicts = verdict
    return geometry


def from_arrays(*, K, canvas_to_source, camera_to_world, scale, depth_grid, grid_uv, anchor_frame_indices):
    """ProfileGeometry from in-memory arrays (G3T unscaled pose/depth, one scale)."""
    from student_pilot.scene_state import FrameMap
    anchors = [int(a) for a in np.asarray(anchor_frame_indices).tolist()]

    def make(GP):
        c = GP.GeometryContract('scaled_g3t_depth', FrameMap(tuple(anchors)), anchors[0],
                                np.asarray(K, float), np.asarray(canvas_to_source, float),
                                np.asarray(camera_to_world, float), float(scale),
                                'g3t', 'unscaled', 'unscaled', 0, 0)
        return GP.ProfileGeometry(c, np.asarray(depth_grid), np.asarray(grid_uv))
    return unguarded(make)


def from_tower(raw_pose9, anchor_slots, frame_indices, depth_grid, grid_uv, gravity, scale, source_hw):
    """The C8r conversion (native/out2/geometry.py convert) without the scale rule and guard:
    G3T raw pose at the anchor slots, rotated into the own gravity head's reference frame."""
    from student_pilot.camera_targets import to_gravity_reference_frame
    H, W = map(int, source_hw)
    raw = np.asarray(raw_pose9, np.float64)[np.asarray(anchor_slots)]
    R, t, fov = to_gravity_reference_frame(raw, np.asarray(gravity, np.float64))
    C = np.repeat(np.eye(4)[None], 32, axis=0)
    C[:, :3, :3] = R
    C[:, :3, 3] = t
    K = np.zeros((32, 3, 3))
    K[:, 0, 0] = W / (2 * np.tan(fov[:, 1] / 2))
    K[:, 1, 1] = H / (2 * np.tan(fov[:, 0] / 2))
    K[:, 0, 2], K[:, 1, 2], K[:, 2, 2] = W / 2, H / 2, 1
    A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)
    anchors = np.asarray(frame_indices)[np.asarray(anchor_slots)]
    return from_arrays(K=K, canvas_to_source=A, camera_to_world=C, scale=scale, depth_grid=depth_grid,
                       grid_uv=grid_uv, anchor_frame_indices=anchors)


def from_npz(path):
    """Test/replay helper: an exported scaled_g3t_depth geometry file (the old runtime's input)."""
    with np.load(path, allow_pickle=False) as z:
        if str(z['profile']) != 'scaled_g3t_depth' or int(z['depth_scale_count']) or int(z['pose_scale_count']):
            raise ValueError('expected an unscaled scaled_g3t_depth export')
        if int(z['reference_source_frame']) != int(z['anchor_frame_indices'][0]):
            raise ValueError('reference frame differs')
        return from_arrays(K=z['K'], canvas_to_source=z['canvas_to_source'], camera_to_world=z['camera_to_world'],
                           scale=float(z['scale']), depth_grid=z['depth_grid'], grid_uv=z['grid_uv'],
                           anchor_frame_indices=z['anchor_frame_indices'])


def camera_geometry(geometry):
    """Per-frame pose relative to frame 1 + gravity, as the old reader's camera_geometry (C8r
    native/out2/perception.py:170) computes it; the depth query reads the same geometry."""
    from student_pilot.camera_targets import quaternion_xyzw
    from student_pilot.carrier_c1_routing import OwnGeometry
    first_R, first_t = geometry.cam(1)
    pose = np.empty((32, 9), dtype=np.float64)
    for k in range(1, 33):
        rotation, centre = geometry.cam(k)
        pose[k - 1, :3] = rotation.T @ (first_t - centre)
        pose[k - 1, 3:7] = quaternion_xyzw(rotation.T @ first_R)
        pose[k - 1, 7:] = geometry.fov_of(k)
    up = first_R.T @ np.array([0., 0., 1.])
    queries = []

    def depth(frame, points):
        result = geometry.depth(frame, points)
        queries.append(dict(frame=frame, depth=result.tolist()))
        return result
    return OwnGeometry(pose, up, depth), pose, up, queries
