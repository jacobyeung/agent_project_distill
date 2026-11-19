"""Independent reviewer recomputation of RECORD.md numbers from raw K1 train arrays.

Reads only train captures listed in sb_scale1 BARS_FROZEN.json (asserts k1_split == 'train'),
their tower.npz, own.npz (step 544) and GT npz, plus sb_scale2 DISTANCE_ROWS.json.
Own implementation of the scale rule, camera-centre decoding, MRA, fits and bootstrap.
"""
import os
for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[k] = '8'
import sys
sys.dont_write_bytecode = True
import hashlib, json, time
from collections import defaultdict
from pathlib import Path
import numpy as np

S1 = Path('/scratch/jjyeung/orch_n30/sb_scale1/out')
S2 = Path('/scratch/jjyeung/orch_n30/sb_scale2/out')
OUT = Path(__file__).resolve().parent / 'RECOMPUTE.json'
THETA = np.arange(50, 100, 5) / 100.0
PINS = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def pin(p, expected=None):
    d = sha(p)
    if expected is not None:
        assert d == expected, ('hash mismatch', p)
    PINS[str(p)] = d
    return p


def quat_R(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def centres(enc):
    # enc rows: [t_rel(3), q_rel xyzw(4), fov(2)] with E_k = inv(C_k) C_0 -> centre_k = -R^T t in frame 0
    return np.array([-quat_R(e[3:7]).T @ e[:3] for e in enc])


def rule(g3t, conf, v):
    thr = np.median(conf[np.isfinite(conf)])
    m = np.isfinite(conf) & (conf > thr) & np.isfinite(g3t) & (g3t > 0) & np.isfinite(v) & (v > 0.1) & (v < 10)
    return float(np.median(v[m] / g3t[m])), m


def pair_mra(p, g):
    p = np.asarray(p, float)
    rel = np.abs(p - g) / g
    ok = np.isfinite(rel)
    out = np.zeros(len(g))
    out[ok] = 100 * np.mean(rel[ok, None] < (1 - THETA)[None, :], axis=1)
    return out


def boot(vals, seed=17, draws=10000):
    a = np.asarray(vals, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(draws, len(a)))
    m = a[idx].mean(1)
    return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def logfit(caps, rooms, ds=None):
    by = defaultdict(list)
    for c in caps:
        if c['room'] in rooms and (ds is None or c['ds'] == ds):
            by[c['room']].extend(np.log(c['gt'] / c['A']).tolist())
    return float(np.exp(np.mean([np.mean(v) for v in by.values()])))


def room_scores(caps, key):
    by = defaultdict(list)
    for c in caps:
        by[c['room']].extend(pair_mra(c[key], c['gt']).tolist())
    return {r: float(np.mean(v)) for r, v in by.items()}


def main():
    t0 = time.time()
    bars = json.load(open(pin(S1 / 'BARS_FROZEN.json')))
    folds = bars['folds']
    caps = []
    depth_px = defaultdict(list)
    for r in bars['captures']:
        assert r['k1_split'] == 'train'
        if not r['gt_present']:
            continue
        ds = r['canonical'].split('/')[0]
        with np.load(pin(r['gt']['path'], r['gt']['sha256'])) as z:
            gdepth, c2w, valid = z['depth'], z['c2w'], z['valid'].astype(bool)
            gfi = z['frame_indices']
        with np.load(pin(r['tower']['path'], r['tower']['sha256'])) as z:
            raw_pose, dg, conf, slots, uv, tfi = (z[k] for k in ('raw_pose', 'depth_grid', 'depth_conf_grid', 'anchor_slots', 'grid_uv', 'frame_indices'))
        with np.load(pin(r['own544']['path'], r['own544']['sha256'])) as z:
            own = z['depth'].astype(float)
        assert np.array_equal(tfi[slots], r['anchor_indices']) and np.array_equal(gfi, r['anchor_indices'])
        dg = dg.astype(float); conf = conf.astype(float)
        scale, m_own = rule(dg, conf, own)
        cen = centres(raw_pose[slots].astype(float))
        i, j = np.triu_indices(32, 1)
        truth = np.linalg.norm(c2w[i, :3, 3] - c2w[j, :3, 3], axis=1)
        ok = valid[i] & valid[j] & np.isfinite(truth) & (truth >= 0.1)
        raw = np.linalg.norm(cen[i] - cen[j], axis=1)[ok]
        truth = truth[ok]
        pose_scale = float(raw @ truth / (raw @ raw))
        H, W = gdepth.shape[1:]
        x = np.clip(np.floor(uv / 1000 * W).astype(int), 0, W - 1)
        y = np.clip(np.floor(uv / 1000 * H).astype(int), 0, H - 1)
        td = gdepth[:, y[:, None], x[None, :]].astype(float)
        td[~valid] = np.nan
        depth_scale, m_gt = rule(dg, conf, td)
        common = m_own & m_gt
        depth_px[ds].append(own[common] / td[common])
        caps.append(dict(capture=r['canonical'], room=r['room'], ds=ds, gt=truth, raw=raw, A=raw * scale,
                         E=raw * pose_scale, scale=scale, pose_scale=pose_scale,
                         dsp=depth_scale / pose_scale, cap_ratio=float(np.median(raw * scale / truth))))
    res = dict(captures=len(caps), rooms=len({c['room'] for c in caps}), pairs=int(sum(len(c['gt']) for c in caps)))
    # bias summaries
    bias = {}
    for ds in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
        sel = [c for c in caps if ds == 'all' or c['ds'] == ds]
        px = np.concatenate([v for d, vs in depth_px.items() if ds == 'all' or d == ds for v in vs])
        bias[ds] = dict(captures=len(sel),
                        served_over_gt_pooled=float(np.median(np.concatenate([c['A'] / c['gt'] for c in sel]))),
                        capture_median_p10_p50_p90=[float(q) for q in np.quantile([c['cap_ratio'] for c in sel], [.1, .5, .9])],
                        frac_captures_ratio_ge_1_03=float(np.mean([c['cap_ratio'] >= 1.03 for c in sel])),
                        frac_captures_ratio_ge_1_09=float(np.mean([c['cap_ratio'] >= 1.09 for c in sel])),
                        own_over_gt_depth_pooled=float(np.median(px)),
                        depthscale_over_posescale_capture_p50=float(np.median([c['dsp'] for c in sel])))
    res['bias'] = bias
    # folds: A, G (global), D (dataset), E (GT per capture), F (raw x global)
    out = {}
    combined = defaultdict(dict)
    for f in folds:
        fit, test = set(f['fit_rooms']), set(f['test_rooms'])
        assert not fit & test
        cg = logfit(caps, fit)
        cd = {d: logfit(caps, fit, d) for d in ('arkitscenes', 'scannet', 'scannetpp')}
        byr = defaultdict(list)
        for c in caps:
            if c['room'] in fit:
                byr[c['room']].extend(np.log(c['gt'] / c['raw']).tolist())
        cf = float(np.exp(np.mean([np.mean(v) for v in byr.values()])))
        tc = []
        for c in caps:
            if c['room'] in test:
                tc.append(dict(c, G=c['A'] * cg, D=c['A'] * cd[c['ds']], F=c['raw'] * cf))
        rs = {k: room_scores(tc, k) for k in ('A', 'G', 'D', 'E', 'F')}
        for k, v in rs.items():
            combined[k].update(v)
        rooms = sorted(rs['A'])
        fo = dict(c_global=cg, c_dataset=cd, c_raw=cf, test_rooms=len(rooms))
        for k in rs:
            fo[k] = float(np.mean([rs[k][r] for r in rooms]))
        for a, b in (('G', 'A'), ('D', 'A'), ('D', 'G')):
            d = [rs[a][r] - rs[b][r] for r in rooms]
            fo[a + '-' + b] = dict(points=float(np.mean(d)), ci95=boot(d))
        out[f['name']] = fo
    rooms = sorted(combined['A'])
    co = dict(rooms=len(rooms))
    for k in combined:
        v = [combined[k][r] for r in rooms]
        co[k] = dict(mra=float(np.mean(v)), ci95=boot(v))
    for a, b in (('G', 'A'), ('D', 'A'), ('D', 'G')):
        d = [combined[a][r] - combined[b][r] for r in rooms]
        co[a + '-' + b] = dict(points=float(np.mean(d)), ci95=boot(d))
    out['combined'] = co
    res['displacement'] = out
    # sensitivity: uniform scale multiplier on arm A (proxy only; not a step-400 measurement)
    sens = {}
    base = room_scores(caps, 'A')
    for k in (0.98, 0.99, 1.0138, 1.02, 1.03):
        sc = room_scores([dict(c, X=c['A'] * k) for c in caps], 'X')
        d = [sc[r] - base[r] for r in sorted(base)]
        sens[str(k)] = dict(points=float(np.mean(d)), ci95=boot(d))
    res['uniform_multiplier_on_A_all_rooms'] = sens
    # distance: own aggregation of sb_scale2 DISTANCE_ROWS.json
    rows = json.load(open(pin(S2 / 'DISTANCE_ROWS.json')))['rows']
    test_of = {}
    for f in folds:
        for r in f['test_rooms']:
            test_of[r] = f['name']
    dist = {}
    for ds in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
        e = {}
        for arm in ('A', 'G', 'D'):
            sel = [v for v in rows if v['arm'] == arm and (ds == 'all' or v['dataset'] == ds)]
            by = defaultdict(list)
            for v in sel:
                by[v['room']].append(pair_mra([np.nan if v['pred'] is None else v['pred']], np.array([v['gt']]))[0])
            fin = [v['pred'] / v['gt'] for v in sel if v['pred'] is not None]
            e[arm] = dict(rows=len(sel), rooms=len(by), refusals=sum(v['pred'] is None for v in sel),
                          mra=float(np.mean([np.mean(x) for x in by.values()])),
                          pooled_ratio=float(np.median(fin)), roommap={r: float(np.mean(x)) for r, x in by.items()})
        for a in ('G', 'D'):
            for scope in ('fold1', 'fold2', 'combined'):
                rr = sorted(r for r in e['A']['roommap'] if scope == 'combined' or test_of[r] == scope)
                d = [e[a]['roommap'][r] - e['A']['roommap'][r] for r in rr]
                e[a + '-A_' + scope] = dict(points=float(np.mean(d)), ci95=boot(d), rooms=len(rr))
        for arm in ('A', 'G', 'D'):
            e[arm].pop('roommap')
        dist[ds] = e
    res['distance'] = dist
    res['input_sha256'] = PINS
    res['code_sha256'] = sha(__file__)
    res['command'] = 'cd /scratch/jjyeung/orch_n30/sb_scalerev && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/recompute.py'
    res['elapsed_seconds'] = time.time() - t0
    OUT.write_text(json.dumps(res, indent=1) + '\n')
    slim = {k: v for k, v in res.items() if k != 'input_sha256'}
    print(json.dumps(slim, indent=1))


if __name__ == '__main__':
    main()
