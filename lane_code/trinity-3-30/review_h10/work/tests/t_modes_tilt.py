"""Same refutation on a scene whose reference camera is pitched 20 deg and rolled 10 deg against gravity
(encodings stay relative to camera 0, gravity stays in camera-0 coordinates, the convention of to_gravity_reference_frame)."""
import numpy as np, runpy, sys
import tests.fixtures as F
from student_pilot.camera_targets import rotation_from_xyzw, quaternion_xyzw
from h1eval.perception import axis_rotation
orig = F.camera_fixtures
def tilted():
    rows, clip, x = orig(); p = np.array(clip['gt_pose9'], float)
    W = [rotation_from_xyzw(c[3:7]).T for c in p]; C = [-w @ c[:3] for w, c in zip(W, p)]
    P = axis_rotation([1, 0, 0], 20.) @ axis_rotation([0, 0, 1], 10.)
    W[0] = W[0] @ P
    q = p.copy()
    for k in range(len(p)):
        r_c2ref = W[0].T @ W[k]; t_c2ref = W[0].T @ (C[k] - C[0]); r_rel = r_c2ref.T
        q[k, 3:7] = quaternion_xyzw(r_rel); q[k, :3] = -r_rel @ t_c2ref
    up = W[0].T @ np.array(clip['gt_up'], float)
    return rows, {**clip, 'gt_pose9': q.tolist(), 'gt_up': up.tolist()}, x
F.camera_fixtures = tilted
runpy.run_path(sys.argv[1], run_name='__main__')
