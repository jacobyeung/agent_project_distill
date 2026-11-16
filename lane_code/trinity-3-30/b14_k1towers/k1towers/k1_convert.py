"""Convert one tower's K1 predictions into deployed-format geometry files, one per capture and arm.

Runs in an env that imports the deployed tree (planner_local_v1). Arms (pre-registration
GEO_TOWERS_K1_PREREG_20261116.md):
  <m>_native  joint towers: own depth, intrinsics, poses, scale 1; gravity = G1 rule on the tower's own anchor poses
  <m>_scale   G3T depth/pose/FoV with G1 gravity (E3's construction) and scale from the frozen rule
              tower_scale_rule.estimate(G3T depth, G3T confidence, candidate depth on the same grid)
  moge2_depth MoGe-2 depth and intrinsics on G3T rotations, G3T translations times moge2_scale's s
Each file is the deployed 'scaled_g3t_depth' profile and must load through load_geometry with
depth_scale_count 1. Output: OUT/<arm>/<dataset>__<capture>.npz plus OUT/<arm>/receipts/<digest16>.json.
No GT is read.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

TREE = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def norm(v):
    n = np.linalg.norm(v)
    if not np.isfinite(n) or n < 1e-6:
        raise ValueError('degenerate_gravity')
    return v / n


def g3t_g1(raw_anchor, ct):
    # Identical to E3 harness.gravities()['G1'].
    R = np.array([ct.rotation_from_xyzw(p[3:7]).T for p in raw_anchor])
    return norm(np.mean(-R[:, :, 1], axis=0))


def write(path, anchors, K, A, C, depth_grid, grid_uv, scale, load_geometry, FrameMap):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp.npz')
    np.savez(tmp, profile='scaled_g3t_depth', depth_unit='unscaled', pose_unit='unscaled',
             reference_source_frame=anchors[0], K=K, canvas_to_source=A, camera_to_world=C,
             scale=float(scale), depth_scale_count=0, pose_scale_count=0,
             anchor_frame_indices=np.asarray(anchors), depth_grid=np.asarray(depth_grid, np.float64),
             grid_uv=grid_uv)
    geo = load_geometry(tmp, FrameMap(tuple(anchors)), 'tower_scaled')
    if geo.depth_scale_count != 1 or geo.pose_scale_count != 1:
        raise ValueError('scale_count_not_one')
    tmp.rename(path)
    return sha(path)


def canvas_affine(hw):
    H, W = map(int, hw)
    return np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)


def g3t_cameras(raw_anchor, gravity, hw, ct):
    # Identical arithmetic to E3 harness.geometry_npz (centred FoV pinhole on the tower's source raster).
    R, t, fov = ct.to_gravity_reference_frame(raw_anchor, gravity)
    H, W = map(int, hw)
    C = np.repeat(np.eye(4)[None], 32, axis=0)
    C[:, :3, :3], C[:, :3, 3] = R, t
    K = np.zeros((32, 3, 3))
    K[:, 0, 0], K[:, 1, 1] = W / (2 * np.tan(fov[:, 1] / 2)), H / (2 * np.tan(fov[:, 0] / 2))
    K[:, 0, 2], K[:, 1, 2], K[:, 2, 2] = W / 2, H / 2, 1
    return C, K


def native_cameras(c2w_anchor, ct):
    """Tower c2w (OpenCV, own world) -> deployed gravity reference frame via the deployed encoder/decoder."""
    c2w = np.asarray(c2w_anchor, np.float64)
    R0 = c2w[0, :3, :3]
    up_world = norm(np.mean(np.einsum('nij,j->ni', c2w[:, :3, :3], [0., -1., 0.]), axis=0))
    up_ref = norm(R0.T @ up_world)
    enc = np.zeros((32, 9))
    for k in range(32):
        E = np.linalg.inv(c2w[k]) @ c2w[0]
        enc[k, :3] = E[:3, 3]
        enc[k, 3:7] = ct.quaternion_xyzw(E[:3, :3])
        enc[k, 7:9] = 1.0  # FoV slots are unused here; K comes from the tower's intrinsics
    R, t, _ = ct.to_gravity_reference_frame(enc, up_ref)
    C = np.repeat(np.eye(4)[None], 32, axis=0)
    C[:, :3, :3], C[:, :3, 3] = R, t
    return C, up_ref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', choices=('moge2', 'mapanything', 'da3', 'pi3x'), required=True)
    ap.add_argument('--pred', required=True, help='k1_infer output root for this model')
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--towers', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--captures', nargs='+')
    args = ap.parse_args()
    sys.path.insert(0, str(TREE))
    from student_pilot import camera_targets as ct, tower_scale_rule
    from student_pilot.ground_profiles import load_geometry
    from student_pilot.scene_state import FrameMap
    manifest = json.loads(Path(args.manifest).read_text())
    index = {}
    for p in sorted(Path(args.towers).glob('*/PHASE_COMPLETE.json')):
        r = json.loads(p.read_text())
        index[r['capture_sha256']] = (p.parent, r)
    caps = manifest['captures']
    if args.captures:
        caps = [c for c in caps if c['canonical'] in set(args.captures)]
    out = Path(args.out)
    arms = [args.model + '_scale'] + ([args.model + '_depth'] if args.model == 'moge2' else [args.model + '_native'])
    summary = dict(model=args.model, arms=arms, written={a: 0 for a in arms}, refused={a: {} for a in arms},
                   missing_pred=[])
    for c in caps:
        key = digest(c)
        folder, receipt = index[key]
        pdir = Path(args.pred) / key[:16]
        name = c['canonical'].replace('/', '__') + '.npz'
        if not (pdir / 'DONE.json').is_file():
            summary['missing_pred'].append(c['canonical'])
            continue
        done = json.loads((pdir / 'DONE.json').read_text())
        if done['pred_sha256'] != sha(pdir / 'pred.npz'):
            raise ValueError('pred.npz hash differs from its receipt: ' + c['canonical'])
        with np.load(pdir / 'pred.npz', allow_pickle=False) as z:
            pred = {k: z[k] for k in z.files}
        with np.load(folder / 'tower.npz', allow_pickle=False) as z:
            tower = {k: z[k] for k in ('raw_pose', 'depth_grid', 'depth_conf_grid', 'frame_indices', 'anchor_slots', 'grid_uv')}
        slots = tower['anchor_slots'].astype(int)
        anchors = list(c['anchor_indices'])
        assert np.array_equal(pred['frame_indices'], tower['frame_indices']) and np.array_equal(pred['anchor_slots'], slots)
        assert tower['frame_indices'][slots].tolist() == anchors
        assert np.array_equal(tower['grid_uv'], np.linspace(0, 1000, 51))
        cand = pred['depth_grid64'][slots].astype(np.float64)
        raw_anchor = tower['raw_pose'][slots]
        rec = dict(capture=c['canonical'], capture_sha256=key, pred_sha256=done['pred_sha256'],
                   tower_source_hw=receipt['source_hw'], pred_source_hw=pred['source_hw'].tolist(), arms={})
        s = None
        # Scale arm: G3T geometry, frozen rule fed the candidate's metric depth.
        arm = args.model + '_scale'
        try:
            s, mask, thr = tower_scale_rule.estimate(tower['depth_grid'], tower['depth_conf_grid'], cand)
            g1 = g3t_g1(raw_anchor, ct)
            C, K = g3t_cameras(raw_anchor, g1, receipt['source_hw'], ct)
            h = write(out / arm / name, anchors, K, canvas_affine(receipt['source_hw']), C, tower['depth_grid'],
                      tower['grid_uv'], s, load_geometry, FrameMap)
            rec['arms'][arm] = dict(sha256=h, scale=s, selected_points=int(mask.sum()), gravity_up_ref=g1.tolist())
            summary['written'][arm] += 1
        except (ValueError, AssertionError) as exc:
            rec['arms'][arm] = dict(refused=f'{type(exc).__name__}:{exc}')
            summary['refused'][arm][c['canonical']] = rec['arms'][arm]['refused']
        K_c = pred['intrinsics'][slots].copy()
        A_c = canvas_affine(pred['source_hw'])
        if args.model == 'moge2':
            arm = 'moge2_depth'
            try:
                if s is None:
                    raise ValueError('scale_arm_refused')
                g1 = g3t_g1(raw_anchor, ct)
                C, _ = g3t_cameras(raw_anchor, g1, receipt['source_hw'], ct)
                C[:, :3, 3] *= s
                h = write(out / arm / name, anchors, K_c, A_c, C, cand, tower['grid_uv'], 1.0, load_geometry, FrameMap)
                rec['arms'][arm] = dict(sha256=h, translation_scale=s)
                summary['written'][arm] += 1
            except (ValueError, AssertionError) as exc:
                rec['arms'][arm] = dict(refused=f'{type(exc).__name__}:{exc}')
                summary['refused'][arm][c['canonical']] = rec['arms'][arm]['refused']
        else:
            arm = args.model + '_native'
            try:
                C, up_ref = native_cameras(pred['c2w'][slots], ct)
                h = write(out / arm / name, anchors, K_c, A_c, C, cand, tower['grid_uv'], 1.0, load_geometry, FrameMap)
                rec['arms'][arm] = dict(sha256=h, gravity_up_ref=up_ref.tolist(),
                                        principal_offset_px=(K_c[:, :2, 2] - A_c[:, :2, :2].diagonal(axis1=1, axis2=2) * 500).tolist()[:1])
                summary['written'][arm] += 1
            except (ValueError, AssertionError) as exc:
                rec['arms'][arm] = dict(refused=f'{type(exc).__name__}:{exc}')
                summary['refused'][arm][c['canonical']] = rec['arms'][arm]['refused']
        (out / 'receipts').mkdir(parents=True, exist_ok=True)
        (out / 'receipts' / (key[:16] + '.json')).write_text(json.dumps(rec, indent=1, default=float))
    (out / f'CONVERT_SUMMARY_{args.model}.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ('written',)}), {a: len(v) for a, v in summary['refused'].items()},
          'missing_pred', len(summary['missing_pred']), flush=True)


if __name__ == '__main__':
    main()
