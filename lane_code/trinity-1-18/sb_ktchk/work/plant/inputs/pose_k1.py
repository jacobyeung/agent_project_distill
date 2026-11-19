"""Camera-pose accuracy of the cached K1 tower outputs (lane tower_redecide).

Poses: Pi3X native and DA3 native geometry (b14 geo_k1/geom, 32 anchors), G3T from the deployed K1 convert geometry
(run_convert_2, G3T pose in the own-gravity frame, own-depth scale); extracted read-only on trinity-1-18 into
remote/poses_118.npz. GT: the K1 GT rasters' c2w on the same 32 frames (anchor_indices == raster frame_indices on
296 of 296 captures). Every metric is relative to frame 1 (anchor 0) over the 31 later frames:
  rotation error  = angle(R_rel_pred^T R_rel_gt), R_rel = R_0^T R_k
  direction error = angle between camera-k centres in camera-0 coordinates (scale-free)
  rotation-angle MRA (a <turn>-like read) = MRA(angle(R_rel_pred), angle(R_rel_gt)) on pairs with GT angle >= 10 deg
  displacement MRA (a <move>-like read) = MRA(|t_rel_pred| * s, |t_rel_gt|) on pairs with GT displacement >= 0.25 m
  direction accuracy (a movement-direction-like read) = same dominant horizontal axis and sign (camera-0 x vs z)
Metric scale: Pi3X and DA3 native are metric (scale field applied if present); G3T uses the K1 convert scale (own depth).
"""
import collections, json, math, os, sys
import numpy as np

GA = '/scratch/jjyeung/orch_n30/gt_audit'
MAN = GA + '/work/k1/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
RROOT = GA + '/work/k1r'
P = '/scratch/jjyeung/orch_n30/tower_redecide/work/remote/poses_118.npz'
OUT = '/scratch/jjyeung/orch_n30/tower_redecide/work/pose_k1'
ARMS = ['GD', 'pi3x_native', 'da3_native']
NAME = {'GD': 'G3T (deployed K1 geometry)', 'pi3x_native': 'Pi3X native', 'da3_native': 'DA3 native'}


def ang(R):
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))


def vang(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return float('nan')
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b) / (na * nb)))))


def mra(p, t):
    if t <= 0 or not math.isfinite(p):
        return 0.0
    r = abs(p - t) / abs(t)
    return sum(r < (100 - th) / 100 for th in range(50, 100, 5)) / 10


def dom(v):
    # dominant horizontal move in camera-0 coordinates (OpenCV: x right, z forward)
    return ('x', np.sign(v[0])) if abs(v[0]) >= abs(v[2]) else ('z', np.sign(v[2]))


def rel(c2w):
    R0, c0 = c2w[0, :3, :3], c2w[0, :3, 3]
    return [(R0.T @ c2w[k, :3, :3], R0.T @ (c2w[k, :3, 3] - c0)) for k in range(len(c2w))]


def main():
    os.makedirs(OUT, exist_ok=True)
    M = json.load(open(MAN)); Z = np.load(P)
    have = set(Z.files)
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    caprows = []
    for c in M['captures']:
        p = RROOT + '/' + c['gt']['path'][len('/scratch/jjyeung/'):]
        if not os.path.exists(p):
            continue
        g = np.load(p)
        gc2w = g['c2w'].astype(np.float64); valid = g['valid'] if 'valid' in g.files else np.ones(32, bool)
        key = c['canonical'].replace('/', '__')
        if not all(f'{a}|{key}|c2w' in have for a in ARMS):
            caprows.append(dict(capture=c['canonical'], missing=[a for a in ARMS if f'{a}|{key}|c2w' not in have]))
            continue
        if not valid[0]:
            continue
        G = rel(gc2w)
        rec = dict(capture=c['canonical'], split=c['k1_split'], dataset=c['canonical'].split('/')[0])
        for a in ARMS:
            A = Z[f'{a}|{key}|c2w'].astype(np.float64)
            s = float(Z[f'{a}|{key}|scale']) if f'{a}|{key}|scale' in have else 1.0
            Pr = rel(A)
            rot, dirn, tm, dm, da, scl = [], [], [], [], [], []
            for k in range(1, 32):
                if not valid[k]:
                    continue
                (Rp, tp), (Rg, tg) = Pr[k], G[k]
                rot.append(ang(Rp.T @ Rg)); dirn.append(vang(tp, tg))
                ag = ang(Rg)
                if ag >= 10:
                    tm.append(mra(ang(Rp), ag))
                dg = float(np.linalg.norm(tg))
                if dg >= 0.25:
                    dm.append(mra(float(np.linalg.norm(tp)) * s, dg)); da.append(dom(tp) == dom(tg))
                    scl.append(float(np.linalg.norm(tp)) * s / dg)
            rec[a] = dict(scale=s, rot_med=float(np.median(rot)), dir_med=float(np.nanmedian(dirn)),
                          turn_mra=float(np.mean(tm)) if tm else None, n_turn=len(tm),
                          move_mra=float(np.mean(dm)) if dm else None, n_move=len(dm),
                          dir_acc=float(np.mean(da)) if da else None, disp_ratio_med=float(np.median(scl)) if scl else None,
                          rot_all=rot, dir_all=dirn)
        caprows.append(rec)
    ok = [r for r in caprows if 'split' in r]
    print('captures with GT + all three arms:', len(ok), 'missing:', [r for r in caprows if 'missing' in r])
    res = {}
    for split in ('train', 'heldout', 'all'):
        for ds in ('all', 'arkitscenes', 'scannetpp', 'scannet'):
            rs = [r for r in ok if (split == 'all' or r['split'] == split) and (ds == 'all' or r['dataset'] == ds)]
            if not rs:
                continue
            line = {}
            for a in ARMS:
                rot = np.concatenate([r[a]['rot_all'] for r in rs]); dr = np.concatenate([r[a]['dir_all'] for r in rs])
                tm = [r[a]['turn_mra'] for r in rs if r[a]['turn_mra'] is not None]
                mv = [r[a]['move_mra'] for r in rs if r[a]['move_mra'] is not None]
                dacc = [r[a]['dir_acc'] for r in rs if r[a]['dir_acc'] is not None]
                line[a] = dict(n_captures=len(rs), rot_median_pairs=float(np.median(rot)), rot_p90=float(np.percentile(rot, 90)),
                               dir_median_pairs=float(np.nanmedian(dr)), dir_p90=float(np.nanpercentile(dr, 90)),
                               rot_capture_median=float(np.median([r[a]['rot_med'] for r in rs])),
                               dir_capture_median=float(np.median([r[a]['dir_med'] for r in rs])),
                               turn_mra=100 * float(np.mean(tm)) if tm else None, move_mra=100 * float(np.mean(mv)) if mv else None,
                               dir_acc=100 * float(np.mean(dacc)) if dacc else None,
                               disp_ratio_median=float(np.median([r[a]['disp_ratio_med'] for r in rs if r[a]['disp_ratio_med']])))
            # paired capture-level differences vs G3T with a capture bootstrap (rooms ~ captures here)
            rng = np.random.default_rng(20261117)
            for a in ('pi3x_native', 'da3_native'):
                for m in ('rot_med', 'dir_med', 'turn_mra', 'move_mra'):
                    d = np.array([(r[a][m] - r['GD'][m]) for r in rs if r[a][m] is not None and r['GD'][m] is not None], float)
                    if len(d) < 3:
                        continue
                    b = d[rng.integers(0, len(d), (5000, len(d)))].mean(1)
                    f = 100 if 'mra' in m else 1
                    line[a]['vs_G3T_' + m] = [f * float(d.mean()), f * float(np.percentile(b, 2.5)), f * float(np.percentile(b, 97.5)), len(d)]
            res[f'{split}/{ds}'] = line
            print(f'## {split}/{ds} ({len(rs)} captures)')
            for a in ARMS:
                v = line[a]
                print(f"  {NAME[a]:28s} rot med {v['rot_median_pairs']:5.2f} (p90 {v['rot_p90']:5.1f}) dir med {v['dir_median_pairs']:5.2f} (p90 {v['dir_p90']:5.1f})"
                      f" | turn MRA {v['turn_mra'] if v['turn_mra'] is None else round(v['turn_mra'], 1)} move MRA {v['move_mra'] if v['move_mra'] is None else round(v['move_mra'], 1)}"
                      f" dir acc {v['dir_acc'] if v['dir_acc'] is None else round(v['dir_acc'], 1)} disp ratio {v['disp_ratio_median']:.3f}"
                      + ''.join(f" | {k[7:]} {x[0]:+.2f} [{x[1]:+.2f},{x[2]:+.2f}]" for k, x in v.items() if k.startswith('vs_G3T_')))
    json.dump(dict(summary=res, captures=[{k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if not kk.endswith('_all')}) for k, v in r.items()} for r in caprows]),
              open(OUT + '/POSE_K1.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
