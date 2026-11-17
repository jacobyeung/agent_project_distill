"""Price candidate-tower geometry on K1 with E3's harness functions, unchanged.

Lives in a copy of E3's harness directory (only harness.py's ROOT constant differs from E3's file). For each
selected capture it rebuilds E3's reference arms GT, S4+G1 and SO+G1 with E3's frozen FITS.json, loads every
candidate arm's deployed-format geometry file, and runs the same distance and room programs. Output per capture:
OUT/captures/<dataset>__<capture>.json = {diagnostics, items}, the layout agg.py reads.

Usage: python -B k1_price.py --out OUTDIR --fits E3_FITS.json [--arm NAME=DIR ...] [--split train|heldout] [--shard i/n]
A candidate capture without a geometry file scores 0 with refusal 'no_candidate_geometry' (pre-registered).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

import harness as H

REF_ARMS = ('S4+G1', 'SO+G1')


def depth_diag(geo, gt, tower_grid_uv):
    """Grid AbsRel of an arm's metric depth against GT at the anchors, raw and after per-capture median alignment."""
    axis = tower_grid_uv
    Hh, Ww = gt['depth'].shape[1:]
    x = np.clip(np.floor(axis / 1000 * Ww).astype(int), 0, Ww - 1)
    y = np.clip(np.floor(axis / 1000 * Hh).astype(int), 0, Hh - 1)
    truth = gt['depth'][:, y[:, None], x[None, :]].astype(float)
    truth[~gt['valid'].astype(bool)] = np.nan
    d = np.asarray(geo.depth_grid, float)
    ok = np.isfinite(truth) & (truth > 0) & np.isfinite(d) & (d > 0)
    if not ok.any():
        return dict(absrel=None, absrel_median_aligned=None, gt_over_pred_median=None, n=0)
    ratio = float(np.median(truth[ok] / d[ok]))
    return dict(absrel=float(np.mean(np.abs(d[ok] - truth[ok]) / truth[ok])),
                absrel_median_aligned=float(np.mean(np.abs(ratio * d[ok] - truth[ok]) / truth[ok])),
                gt_over_pred_median=ratio, n=int(ok.sum()))


def gravity_err(geo, gt):
    """Angle between the arm's world z-up and GT up, both seen from the valid anchor cameras."""
    valid = gt['valid'].astype(bool)
    Rw = np.asarray(geo.C)[:, :3, :3]
    up_cam_pred = np.einsum('nji,j->ni', Rw, [0., 0., 1.])            # R^T z: arm's up in each camera
    up_cam_gt = np.einsum('nji,j->ni', gt['c2w'][:, :3, :3], [0., 0., 1.])
    cos = np.clip(np.sum(up_cam_pred[valid] * up_cam_gt[valid], axis=1), -1, 1)
    return float(np.degrees(np.median(np.arccos(cos))))


def run_arm(c, arm, geo, gt, mode, rows):
    if isinstance(geo, str):
        for row in c['rows']:
            if row['type'] == 'object_abs_distance':
                rows.append(H.item(c, row, arm, (None, geo)))
            else:
                for r in ('R0', 'R1'):
                    rows.append(H.item(c, row, arm + '+' + r, (None, geo)))
        return
    lifted = {}
    ar = H.areas(geo, mode) if any(r['type'] == 'room_size_estimation' for r in c['rows']) else {}
    for row in c['rows']:
        if row['type'] == 'object_abs_distance':
            rows.append(H.item(c, row, arm, H.attempt(lambda: H.distance(row, geo, gt, mode, lifted))))
        elif row['type'] == 'room_size_estimation':
            for r in ('R0', 'R1'):
                rows.append(H.item(c, row, arm + '+' + r, ar[r]))
        else:
            raise ValueError('unsupported row type')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--fits', required=True, help="E3's frozen out/FITS.json")
    ap.add_argument('--arm', action='append', default=[], help='NAME=DIR holding <dataset>__<capture>.npz')
    ap.add_argument('--split', choices=('train', 'heldout'))
    ap.add_argument('--shard')
    ap.add_argument('--captures', nargs='+')
    ap.add_argument('--no-reference', action='store_true', help='skip GT/S4/SO arms (candidate-only rerun)')
    args = ap.parse_args()
    out = Path(args.out).resolve()
    assert out.is_relative_to(H.ROOT), 'outputs stay inside the harness workspace'
    (out / 'captures').mkdir(parents=True, exist_ok=True)
    H.OUT = out  # tests.log and generated reference geometry go under this run's folder
    fits = json.loads(Path(args.fits).read_text())
    arms = dict(a.split('=', 1) for a in args.arm)
    cs, cache, inv = H.inventory()
    if args.split:
        cs = [c for c in cs if c['k1_split'] == args.split]
    if args.captures:
        cs = [c for c in cs if c['canonical'] in set(args.captures)]
    if args.shard:
        i, n = map(int, args.shard.split('/'))
        cs = cs[i::n]
    start = time.monotonic()
    for n, c in enumerate(cs):
        dest = out / 'captures' / (c['canonical'].replace('/', '__') + '.json')
        if dest.exists():
            continue
        gt, tower, hw = H.load_capture(c, cache[H.digest(c)], True)
        f = H.features(c, tower, gt, hw, 'specified')
        rows, diag = [], dict(capture=c['canonical'], room=c['room'], split=c['k1_split'], SO=f['SO'], arms={})
        if not args.no_reference:
            scale_values = H.scales(f, fits)
            diag['reference_scales'] = {k: scale_values[k] for k in ('S4', 'SO')}
            run_arm(c, 'GT', H.GTGeometry(gt), gt, 'sensor', rows)
            for arm in REF_ARMS:
                s = scale_values[arm.split('+')[0]]
                try:
                    if not np.isfinite(s):
                        raise ValueError('feature_geometry_refused')
                    geo = H.geometry_npz(c, tower, hw, f['gravity']['G1'], s, arm)
                except ValueError as exc:
                    geo = type(exc).__name__ + ':' + str(exc)
                run_arm(c, arm, geo, gt, 'predicted', rows)
        for arm, d in sorted(arms.items()):
            path = Path(d) / (c['canonical'].replace('/', '__') + '.npz')
            info = {}
            if not path.is_file():
                geo = 'no_candidate_geometry'
            else:
                try:
                    geo = H.load_geometry(path, H.FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
                    assert geo.depth_scale_count == 1
                    info = dict(path=str(path), sha256=H.sha(path), scale=float(geo.contract.scale),
                                **depth_diag(geo, gt, tower['grid_uv']), gravity_err_deg=gravity_err(geo, gt))
                    info['scale_to_SO'] = (info['scale'] / f['SO']) if arm.endswith('_scale') else None
                except ValueError as exc:
                    geo = type(exc).__name__ + ':' + str(exc)
            if isinstance(geo, str):
                info['refused'] = geo
            diag['arms'][arm] = info
            run_arm(c, arm, geo, gt, 'predicted', rows)
        H.dump(dest, dict(diagnostics=diag, items=rows))
        print(json.dumps(dict(done=n + 1, total=len(cs), capture=c['canonical'], seconds=round(time.monotonic() - start))), flush=True)
    print('COMPLETE', len(cs), flush=True)


if __name__ == '__main__':
    main()
