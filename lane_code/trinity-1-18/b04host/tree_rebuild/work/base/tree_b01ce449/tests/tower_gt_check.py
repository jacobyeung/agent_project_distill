"""Independent end-to-end check of the tower pose chain against ScanNet GT.

Tower side: the builder's TowerState.from_npz + scaled_pose9 (own V-C depth) -> OwnGeometry (printed text).
GT side: raw ScanNet c2w (OpenCV camera, world z-up), with relative poses computed here from first principles,
not through camera_targets / rkit / e.py. A convention error (axis flip, transpose, wrong reference frame, wrong
anchor slots, scale applied wrong) shows up as large rotation / centre / printed-value errors.
usage: python tests/tower_gt_check.py --tree TREE --root INPUT_ROOT [--limit N]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np


def quat_to_R(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def R_to_quat(m):
    # Shepperd; returns xyzw with w >= 0
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t+1)*2; q = [(m[2,1]-m[1,2])/s, (m[0,2]-m[2,0])/s, (m[1,0]-m[0,1])/s, .25*s]
    else:
        i = int(np.argmax(np.diag(m)))
        if i == 0:
            s = math.sqrt(1+m[0,0]-m[1,1]-m[2,2])*2; q = [.25*s, (m[0,1]+m[1,0])/s, (m[0,2]+m[2,0])/s, (m[2,1]-m[1,2])/s]
        elif i == 1:
            s = math.sqrt(1+m[1,1]-m[0,0]-m[2,2])*2; q = [(m[0,1]+m[1,0])/s, .25*s, (m[1,2]+m[2,1])/s, (m[0,2]-m[2,0])/s]
        else:
            s = math.sqrt(1+m[2,2]-m[0,0]-m[1,1])*2; q = [(m[0,2]+m[2,0])/s, (m[1,2]+m[2,1])/s, .25*s, (m[1,0]-m[0,1])/s]
    q = np.array(q); q /= np.linalg.norm(q)
    return -q if q[3] < 0 else q


def angle(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return math.degrees(math.acos(max(-1., min(1., c))))


def gt_pose9(c2w, K, hw):
    p = np.zeros((32, 9))
    h, w = hw
    for k in range(32):
        E = np.linalg.inv(c2w[k]) @ c2w[0]
        p[k, :3] = E[:3, 3]
        p[k, 3:7] = R_to_quat(E[:3, :3])
        p[k, 7] = 2*math.atan(h/(2*K[1, 1])); p[k, 8] = 2*math.atan(w/(2*K[0, 0]))
    return p


def parse_move(text):
    vals = [float(v) for v in __import__('re').findall(r'= ([+-]?\d+(?:\.\d+)?) m', text)]
    return np.array(vals[:3]), vals[3]


def check(root, limit=10):
    from student_pilot.tower_read import TowerState, g3t_to_c1_pose9
    from student_pilot import carrier_c1_routing as routing
    ROOT = Path(root)
    G64 = ROOT / 'ttower/work/g3t/n64'
    OWN = ROOT / 'evalx/work/exports/heads_t0m800d'
    GT = ROOT / 'toolprog/work/gt/scannet'
    if not (ROOT / 'ttower/work/geo/heads_g3s64_vcd/CONVERT.json').is_file():
        return dict(status='PENDING-INPUT', expected=str(ROOT / 'ttower/work/geo/heads_g3s64_vcd/CONVERT.json'))
    keys = json.loads((ROOT / 'ttower/work/geo/heads_g3s64_vcd/CONVERT.json').read_text())['converted']
    keys = [k for k in keys if k.startswith('scannet__')]
    rows, skipped = [], {}
    for key in keys:
        if len(rows) >= limit:
            break
        scene = key.split('__', 1)[1]
        paths = (G64 / (key+'.npz'), OWN / (key+'.npz'), GT / (scene+'.npz'))
        if not all(p.is_file() for p in paths):
            skipped[key] = 'missing input'; continue
        with np.load(paths[0], allow_pickle=False) as z:
            converted = g3t_to_c1_pose9(z['local_pose_enc'], z['global_pose_enc'], z['coords_1024'])
            state = TowerState(converted['raw_pose'], z['depth_grid'], z['depth_conf_grid'],
                               z['frame_indices'], z['anchor_slots'])
        with np.load(paths[1], allow_pickle=False) as v, np.load(paths[2], allow_pickle=False) as g:
            own_depth, own_up = v['depth_grid'].astype(float), v['gravity_up'].astype(float)
            c2w, K, valid, gidx = g['c2w'], g['K'], g['valid'], g['frame_indices']
            gt_hw = g['depth'].shape[1:]
        anchors = state.frame_indices[state.anchor_slots]
        if not np.array_equal(anchors, gidx) or not valid.all():
            skipped[key] = 'anchor/GT index mismatch or invalid GT frame'; continue
        pose9, s = state.scaled_pose9(own_depth)
        # K is for the GT depth raster (240x320); FoV is resolution independent.
        gt9 = gt_pose9(c2w, K, gt_hw)
        up_gt = c2w[0][:3, :3].T @ np.array([0., 0., 1.])
        # GT metric scale for this clip: ratio of GT to raw-tower camera path length.
        raw = state.raw_pose9[state.anchor_slots]
        rot_err, cen_err, cen_norm, fov_err = [], [], [], []
        for k in range(1, 32):
            Rt = quat_to_R(pose9[k, 3:7]); Rg = quat_to_R(gt9[k, 3:7])
            rot_err.append(angle(Rt, Rg))
            ct = -Rt.T @ pose9[k, :3]; cg = -Rg.T @ gt9[k, :3]
            cen_err.append(np.linalg.norm(ct-cg)); cen_norm.append(np.linalg.norm(cg))
            fov_err.append(math.degrees(abs(pose9[k, 7]-gt9[k, 7])))
        path_t = sum(np.linalg.norm((-quat_to_R(pose9[k,3:7]).T@pose9[k,:3])-(-quat_to_R(pose9[k-1,3:7]).T@pose9[k-1,:3])) for k in range(1,32))
        path_g = sum(np.linalg.norm((-quat_to_R(gt9[k,3:7]).T@gt9[k,:3])-(-quat_to_R(gt9[k-1,3:7]).T@gt9[k-1,:3])) for k in range(1,32))
        # Printed text: tower formatter (own gravity) vs GT formatter (GT gravity), as the trainer printed GT.
        tg = routing.OwnGeometry(pose9, own_up, None)
        gg = routing.OwnGeometry(gt9, up_gt, None)
        turn_err, dist_ratio, sign_agree, dom_agree = [], [], [], []
        for i, j in [(1, 8), (2, 9), (5, 20), (10, 30), (1, 32), (16, 24)]:
            ta = int(tg.turn_text(i, j).split()[2]); ga = int(gg.turn_text(i, j).split()[2])
            turn_err.append(abs((ta-ga+180) % 360-180))
            vt, dt = parse_move(tg.move_text(i, j)); vg, dg = parse_move(gg.move_text(i, j))
            if dg > .2:
                dist_ratio.append(dt/dg)
                dom_agree.append(int(np.argmax(np.abs(vt)) == np.argmax(np.abs(vg)) and
                                     np.sign(vt[np.argmax(np.abs(vg))]) == np.sign(vg[np.argmax(np.abs(vg))])))
        up_err = math.degrees(math.acos(np.clip(own_up @ up_gt / np.linalg.norm(own_up), -1, 1)))
        rows.append(dict(scene=key, s=s, path_ratio=path_t/path_g, rot_med=float(np.median(rot_err)),
                         centre_rel_med=float(np.median(np.array(cen_err)/np.maximum(cen_norm, 1e-3))),
                         fov_v_err_deg=float(np.median(fov_err)), gravity_err_deg=up_err,
                         turn_err_med=float(np.median(turn_err)),
                         dist_ratio_med=float(np.median(dist_ratio)) if dist_ratio else None,
                         dominant_axis_sign_agree=float(np.mean(dom_agree)) if dom_agree else None,
                         raw_unscaled_path_ratio=sum(np.linalg.norm((-quat_to_R(raw[k,3:7]).T@raw[k,:3])-(-quat_to_R(raw[k-1,3:7]).T@raw[k-1,:3])) for k in range(1,32))/path_g))
    if not rows:
        return dict(status='PENDING-INPUT', expected=[str(G64), str(OWN), str(GT)])
    agg = {k: float(np.median([r[k] for r in rows if r[k] is not None])) for k in rows[0] if k != 'scene'}
    # These aggregate bounds test conventions, not per-scene reconstruction accuracy.
    ok = (len(rows) >= 5 and agg['rot_med'] < 6 and agg['centre_rel_med'] < .25
          and agg['turn_err_med'] < 8 and .8 < agg['path_ratio'] < 1.25
          and agg['dominant_axis_sign_agree'] > .9)
    return dict(status='PASS' if ok else 'FAIL', scenes=len(rows), median_over_scenes=agg,
                skipped=len(skipped), rows=rows)


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree', required=True, type=Path)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    sys.path.insert(0, str(args.tree.resolve()))
    report = check(args.root, args.limit)
    print(json.dumps(report, indent=2))
    return {'PASS': 0, 'FAIL': 1, 'PENDING-INPUT': 2}[report['status']]


if __name__ == '__main__':
    raise SystemExit(main())
