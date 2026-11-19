"""Raw-prompt-only K1 selector tables with every name featurised alone (data/caps_iso).

The live call sees only the name it grounds, so cross-name exclusivity (routed_candidates.scene_candidates) must
see no other name in the training tables either. Each caps_raw record keeps its rows, labels and split; its
selector inputs `x` and its rows' `features` are recomputed by the reader's own StageOne (one name per pool) on
the record's K1 capture (raw-prompt instances of the cached SAM 3 run, cap 30) and geometry (tower poses, own
anchor gravity, the record's S4 scale). CPU.
"""
import gzip, hashlib, json, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TREE = '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449'
sys.path[:0] = [str(ROOT), TREE, str(ROOT / 'heads/selector'), str(ROOT / 'tests')]
MIRROR = Path('/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2')
SRC, DST = ROOT / 'heads/selector/data/caps_raw', ROOT / 'heads/selector/data/caps_iso'


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def geometry(rec, folder):
    from e2e_reader.geometry import from_tower
    from student_pilot import camera_targets
    with np.load(folder / 'tower.npz') as z:
        tower = {k: z[k] for k in z.files}
    receipt = json.loads((folder / 'PHASE_COMPLETE.json').read_text())
    raw = tower['raw_pose'][tower['anchor_slots']]
    R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    g = np.mean(-R[:, :, 1], axis=0); g /= np.linalg.norm(g)
    return from_tower(tower['raw_pose'], tower['anchor_slots'], tower['frame_indices'], tower['depth_grid'],
                      tower['grid_uv'], g, rec['scale'], receipt['source_hw'])


def one(path):
    from e2e_reader.stage1 import StageOne
    from test_stage1_k1 import cache_detect
    t0 = time.monotonic()
    rec = json.load(gzip.open(path, 'rt'))
    folder = MIRROR / digest(rec['capture'])[:16]
    cand = json.loads((folder / 'candidates.json').read_text())
    geo = geometry(rec, folder)
    detect = cache_detect(cand, raw_only=True)
    got = {}
    for name in sorted({i['name'] for i in rec['inputs']}):
        accepted, x = StageOne(detect, None, geo).features(name)
        got.update({(name, a['candidate_id']): (v, a['features']) for a, v in zip(accepted, x)})
    missing, changed = 0, 0
    rows, inputs = [], []
    for r, i in zip(rec['rows'], rec['inputs'], strict=True):
        k = (i['name'], i['candidate_id'])
        if k not in got:
            missing += 1
            continue
        x, feats = got[k]
        changed += int(np.max(np.abs(np.asarray(x) - np.asarray(i['x']))) > 1e-9)
        inputs.append(dict(i, x=[float(v) for v in x]))
        rows.append(dict(r, features={**r['features'], **{f: float(feats[f]) for f in r['features'] if f in feats}}))
    out = dict(rec, rows=rows, inputs=inputs, isolated=dict(missing=missing, changed=changed, kept=len(rows)),
               seconds_iso=time.monotonic() - t0)
    with gzip.open(DST / path.name, 'wt') as f:
        json.dump(out, f)
    return dict(capture=rec['capture'], **out['isolated'])


if __name__ == '__main__':
    DST.mkdir(parents=True, exist_ok=True)
    paths = sorted(SRC.glob('*.json.gz'))
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 12) as pool:
        res = pool.map(one, paths, chunksize=1)
    summary = dict(captures=len(res), missing=sum(r['missing'] for r in res), changed=sum(r['changed'] for r in res),
                   kept=sum(r['kept'] for r in res), per_capture=res)
    (DST.parent / 'caps_iso_SUMMARY.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != 'per_capture'}))
