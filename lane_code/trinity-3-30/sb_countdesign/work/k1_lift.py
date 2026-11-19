"""Lane sb_countdesign, CPU pilot on K1: lift every SAM 3 teacher proposal (b05_owngrd teacher pass: floor 0.2, cap 10, GT-role names)
to a metric 3D centroid with the K1 convert geometry (G3T depth and pose x own-head scale; profile scaled_g3t_depth).
Read-only on inputs. Output: K1_LIFT.npz (per-proposal arrays) + K1_LIFT_META.json.
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_lift.py"""
import json, gzip, os, sys, time
import numpy as np
LAB = '/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1'
TEA = '/scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1'
GEO = '/scratch/jjyeung/n30_mirror/k1_ops3/run_convert_2'
D = json.load(open('/scratch/jjyeung/orch_n30/b05_owngrd/work/k1map/DIR_TO_CAPTURE.json'))
inv = {}
for k, v in D.items():
    for c in (v['canonical'] or []): inv[c] = k
NS = 300

def rle_decode(r):
    h, w = r['size']; counts = r['counts']
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')

def bilinear(d, uv):
    n = len(d)
    x, y = np.clip(uv * ((n - 1) / 1000.0), 0, n - 1).T
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, n - 1), np.minimum(y0 + 1, n - 1)
    fx, fy = x - x0, y - y0
    return d[y0, x0] * (1 - fx) * (1 - fy) + d[y0, x1] * fx * (1 - fy) + d[y1, x0] * (1 - fx) * fy + d[y1, x1] * fx * fy

rows = []; meta = dict(captures=[], skipped={}, names=[]); name_ix = {}; cap_ix = {}
t0 = time.time()
for fn in sorted(os.listdir(LAB)):
    if not fn.endswith('.labels.json.gz'): continue
    lab = json.load(gzip.open(os.path.join(LAB, fn)))
    can = lab['canonical']
    if can not in inv: meta['skipped'][can] = 'no_tower_dir'; continue
    gp = os.path.join(GEO, inv[can], 'geometry.npz')
    if not os.path.isfile(gp): meta['skipped'][can] = 'no_geometry'; continue
    g = np.load(gp, allow_pickle=True)
    tea = json.load(gzip.open(os.path.join(TEA, fn[:-len('.labels.json.gz')], 'teacher.json.gz')))
    if list(tea['frame_indices']) != [int(x) for x in g['anchor_frame_indices']]:
        meta['skipped'][can] = 'frame_indices_differ'; continue
    prof = str(g['profile']); scale = float(g['scale'])
    if prof != 'scaled_g3t_depth': meta['skipped'][can] = 'profile_' + prof; continue
    K = g['K'].astype(float); A = g['canvas_to_source'].astype(float); C = g['camera_to_world'].astype(float).copy()
    dg = g['depth_grid'].astype(float) * scale; C[:, :3, 3] *= scale
    ci = cap_ix.setdefault(can, len(cap_ix)); meta['captures'].append(dict(capture=can, split=lab['k1_split'], scale=scale, hw=tea['frames']['0']['size']))
    for name, role in lab['roles'].items():
        if role != 'gt': continue
        ni = name_ix.setdefault(name, len(name_ix))
        for k in range(32):
            lf = lab['frames'][str(k)].get(name); tf = tea['frames'][str(k)]['phrases'].get(name)
            if lf is None or tf is None: continue
            Kinv = np.linalg.inv(K[k]); Ainv = np.linalg.inv(A[k]); R = C[k, :3, :3]; t = C[k, :3, 3]
            for q in lf['proposals']:
                inst = tf['instances'][q['k']]
                m = rle_decode(inst['mask'])
                idx = np.flatnonzero(m)
                if idx.size == 0: continue
                sel = idx[np.linspace(0, idx.size - 1, min(NS, idx.size)).astype(int)]
                r_, c_ = np.unravel_index(sel, m.shape)
                src = np.column_stack((c_ + .5, r_ + .5, np.ones(len(sel))))
                uv = (src @ Ainv.T)[:, :2]
                d = bilinear(dg[k], uv)
                pc = (src @ Kinv.T) * d[:, None]
                pw = pc @ R.T + t
                cen = np.median(pw, axis=0)
                lo, hi = np.percentile(pw, (10, 90), axis=0)
                cls = dict(POS=1, HARDNEG=2, DISPUTED=3, DISTILL=0)[q['cls']]
                same = int(q.get('inst_name') == name) if q.get('inst') is not None else 0
                rows.append((ci, ni, k, q['k'], q['joint'], q['score'], cls, q.get('inst', -1) if q.get('inst') is not None else -1, same,
                             q.get('iou', 0.0) or 0.0, q.get('unlabelled', 1.0) if q.get('unlabelled') is not None else 1.0,
                             idx.size / float(m.size), cen[0], cen[1], cen[2], hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], float(np.median(d))))
    if len(meta['captures']) % 20 == 0:
        print(len(meta['captures']), 'captures', len(rows), 'rows', '%.0fs' % (time.time() - t0), flush=True)
arr = np.asarray(rows, dtype=np.float32)
meta['names'] = [n for n, _ in sorted(name_ix.items(), key=lambda x: x[1])]
meta['columns'] = ['cap', 'name', 'frame', 'k', 'joint', 'score', 'cls(0 DISTILL,1 POS,2 HARDNEG,3 DISPUTED)', 'inst', 'inst_has_name', 'iou', 'unlabelled', 'area_frac',
                   'x', 'y', 'z', 'ext_x', 'ext_y', 'ext_z', 'depth_med']
np.savez_compressed('K1_LIFT.npz', rows=arr)
json.dump(meta, open('K1_LIFT_META.json', 'w'))
print('DONE captures', len(meta['captures']), 'skipped', len(meta['skipped']), 'rows', arr.shape, '%.0fs' % (time.time() - t0))
