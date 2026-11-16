"""dev-S1 room items (36, ScanNet) on dev-S1 raw G3T caches: K1-train-fitted scale rules, G1 and tower gravity, R0/R1/R2."""
import sys, json, glob, re
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/e3_geom/work/harness')
import importlib.util as iu
sp = iu.spec_from_file_location('e3h', '/scratch/jjyeung/orch_n30/e3_geom/work/harness/harness.py'); H = iu.module_from_spec(sp); sp.loader.exec_module(H)
fits = json.load(open(H.OUT.parent / 'out_tr' / 'FITS_R2_from_shards.json'))
V = '/scratch/jjyeung/orch_cd/legs1_reads/work/vendor/r3'
tasks = [json.loads(l) for l in open(V + '/TASKS.jsonl') if '"room_size_estimation"' in l]
frames = {c['native']: c for c in json.load(open(V + '/FRAMES.json'))['captures']}
out = []


def tower_for(native):
    key = 'scannet__' + native.split('/')[1]
    hits = sorted(glob.glob(f'/scratch/jjyeung/devs1_r2/g3s*/g3t/{key}.npz'))
    for h in hits:
        z = np.load(h, allow_pickle=False)
        t = {k: z[k] for k in z.files}
        if t['frame_indices'][t['anchor_slots']].tolist() == frames[native]['anchor_indices']:
            return h, t
    return (hits[0] if hits else None), None


def feats(c, tower, hw, g):
    geo = H.geometry_npz(c, tower, hw, g, 1., 'devs1_features')
    u, v = np.meshgrid(tower['grid_uv'], tower['grid_uv'])
    uv = np.column_stack((u.ravel(), v.ravel()))
    parts = []
    for k in range(1, 33):
        d = tower['depth_grid'][k - 1].ravel()
        R, t = geo.cam(k)
        p = (geo.rays(k, uv) * d[:, None]) @ R.T + t
        parts.append(p[np.isfinite(p).all(1) & np.isfinite(d) & (d > 0)])
    P = np.concatenate(parts)
    z1, z99 = np.percentile(P[:, 2], [1, 99])
    return float(np.median(geo.C[:, 2, 3] - z1)), float(z99 - z1)


for t in tasks:
    native = t['native']
    unit = 'ft2' if re.search(r'square f(?:ee|oo)t|sq\.? ?ft\b', t['question'], re.I) else 'm2'
    conv = 10.7639 if unit == 'ft2' else 1.
    path, tower = tower_for(native)
    rec = dict(id=t['id'], native=native, room=t['room'], unit=unit, gt=float(t['ground_truth']), tower=path)
    if tower is None:
        rec['error'] = 'no_anchor_matched_tower'; out.append(rec); continue
    c = dict(canonical='devs1/' + native.replace('/', '_'), anchor_indices=frames[native]['anchor_indices'])
    raw = tower['raw_pose'][tower['anchor_slots']]
    Rr = np.array([H.camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    gravs = dict(G1=H.norm(np.mean(-Rr[:, :, 1], axis=0)), Gtow=H.norm(np.asarray(tower['gravity_up'], float)))
    hw = tower['source_hw'].tolist()
    preds = {}
    for gname, g in gravs.items():
        try:
            h, span = feats(c, tower, hw, g)
        except ValueError as exc:
            preds[gname] = 'refused:' + str(exc); continue
        sc = dict(S1=fits['S1'], S2=fits['h_prior'] / h, S3=fits['H_prior'] / span,
                  S4=float(np.exp(np.dot([1., np.log(h), np.log(span)], fits['S4_coefficients']))))
        for sname, s in sc.items():
            arm = sname + '+' + gname
            try:
                geo = H.geometry_npz(c, tower, hw, g, s, 'devs1_' + arm)
                a = H.areas(geo, 'predicted')
            except ValueError as exc:
                a = {r: (None, str(exc)) for r in ('R0', 'R1')}
            for r in ('R0', 'R1'):
                preds[arm + '+' + r] = None if a[r][0] is None else a[r][0] * conv
            k = (fits.get('R2', {}).get(sname + '+G1') or {}).get('k')
            preds[arm + '+R2'] = None if (k is None or a['R0'][0] is None) else a['R0'][0] * k * conv
    rec['preds'] = preds
    rec['mra'] = {arm: H.mra(p, rec['gt']) if not isinstance(p, str) else 0. for arm, p in preds.items()}
    out.append(rec)
    print(t['id'], unit, flush=True)
with open(H.OUT.parent / 'out_devs1' / 'DEVS1_ROOM.jsonl', 'w') as f:
    for r in out:
        f.write(json.dumps(r, default=float) + '\n')
print('DEVS1_DONE', flush=True)
