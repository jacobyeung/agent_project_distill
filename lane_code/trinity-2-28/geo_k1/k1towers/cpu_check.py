"""Diagnostic for a CPU first pass: anchor depth and relative pose of one tower prediction against K1 GT.
Usage: python cpu_check.py MANIFEST PRED_ROOT CAPTURE   (reads GT; diagnostic only, never a decision input)"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
man, root, cap = sys.argv[1:4]
c = next(c for c in json.loads(Path(man).read_text())['captures'] if c['canonical'] == cap)
key = hashlib.sha256(json.dumps(c, sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
for d in sorted(Path(root).glob("*/" + key)):
    if not (d / "pred.npz").is_file(): print(d.parent.name, "no pred"); continue
    z = np.load(d / 'pred.npz'); g = np.load(c['gt']['path'])
    if 'smoke_anchor_pos' in z.files:
        pos = z['smoke_anchor_pos'].astype(int); g = {k: g[k][pos] for k in ('depth', 'valid', 'K_frames', 'c2w')}
    slots = z['anchor_slots'].astype(int); depth = z['depth_grid64'][slots].astype(float)
    H, W = g['depth'].shape[1:]; ax = np.linspace(0, 1000, 51)
    x = np.clip(np.floor(ax / 1000 * W).astype(int), 0, W - 1); y = np.clip(np.floor(ax / 1000 * H).astype(int), 0, H - 1)
    t = g['depth'][:, y[:, None], x[None, :]].astype(float); valid = g['valid'].astype(bool); t[~valid] = np.nan
    ok = np.isfinite(t) & (t > 0) & np.isfinite(depth) & (depth > 0)
    r = np.median(t[ok] / depth[ok])
    out = dict(model=d.parent.name, n=int(ok.sum()), absrel=float(np.mean(np.abs(depth[ok] - t[ok]) / t[ok])),
               gt_over_pred_median=float(r), absrel_aligned=float(np.mean(np.abs(r * depth[ok] - t[ok]) / t[ok])),
               source_hw=z['source_hw'].tolist(), raster_hw=z['raster_hw'].tolist(), gt_hw=[int(H), int(W)],
               fx_pred_over_gt=float(np.median(z['intrinsics'][slots][valid, 0, 0] * W / z['source_hw'][1] / g['K_frames'][valid, 0, 0])),
               seconds=json.loads((d / 'DONE.json').read_text())['seconds'])
    if 'c2w' in z.files:
        P, G = z['c2w'][slots][valid], g['c2w'][valid]
        rel = lambda A: np.einsum('ij,njk->nik', np.linalg.inv(A[0]), A)
        Rp, Rg = rel(P)[:, :3, :3], rel(G)[:, :3, :3]
        ang = np.degrees(np.arccos(np.clip((np.einsum('nij,nij->n', Rp, Rg) - 1) / 2, -1, 1)))
        tp, tg = rel(P)[:, :3, 3], rel(G)[:, :3, 3]
        s = np.sum(tp * tg) / max(np.sum(tp * tp), 1e-12)
        out.update(rot_err_deg_median=float(np.median(ang)), trans_scale_gt_over_pred=float(s),
                   trans_err_m_median_after_scale=float(np.median(np.linalg.norm(s * tp - tg, axis=1))),
                   trans_err_m_median_native=float(np.median(np.linalg.norm(tp - tg, axis=1))))
    print(json.dumps(out))
