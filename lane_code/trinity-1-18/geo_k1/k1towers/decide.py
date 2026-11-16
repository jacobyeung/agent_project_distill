"""Apply the pre-registered C-rule (GEO_TOWERS_K1_PREREG_20261116.md) to k1_price output at full precision.

Usage: python decide.py CAPTURES_DIR OUT.json [--heldout-go FILE]
Statistics follow E3's harness: item-weighted mean MRA x100; 95% percentile bootstrap over physical rooms,
10,000 draws from np.random.default_rng(20261116) keyed by the room count (paired arms share draws). R2 is
E3's fit_r2/add_r2 procedure, fitted per arm on K1 train rows only. Train tables are always computed; held-out
tables only with --heldout-go naming an ORCH note holding a line 'GO heldout'.
"""
import argparse, collections, glob, json
from pathlib import Path

import numpy as np

PRIMARY = {'moge2': 'moge2_scale', 'mapanything': 'mapanything_native', 'da3': 'da3_native', 'pi3x': 'pi3x_native'}
TYPES = {'object_abs_distance': '', 'room_size_estimation': '+R0'}
REF = 'S4+G1'
DIST_BAR, ROOM_BAR, ROOM_BAR_SENS, GUARD = 5.0, 73.4, 79.0, -2.0
PREREG = 'dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88'


def mra(pred, gt):
    if pred is None:
        return 0.
    return float(np.mean([abs(pred - gt) / abs(gt) < 1 - t for t in np.arange(.5, .96, .05)]))


def fit_r2(rows):
    fits, grouped = {}, collections.defaultdict(list)
    for r in rows:
        if r['split'] == 'train' and r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            grouped[r['arm'][:-3]].append(r)
    for arm, rs in grouped.items():
        ok = [r for r in rs if r['pred'] is not None and r['pred'] > 0 and r['refusal_code'] is None]
        fits[arm] = dict(k=float(np.median([r['gt'] / r['pred'] for r in ok])) if ok else None, n_used=len(ok),
                         n_refused=len(rs) - len(ok))
    added = []
    for r in rows:
        if r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            k = (fits.get(r['arm'][:-3]) or {}).get('k')
            pred = None if r['pred'] is None or k is None else r['pred'] * k
            added.append(dict(r, arm=r['arm'][:-1] + '2', pred=pred, mra=mra(pred, r['gt']),
                              refusal_code=r['refusal_code'] or ('no_train_R2_fit' if k is None else None)))
    return fits, rows + added


class Draws(dict):
    def __missing__(self, n):
        self[n] = np.random.default_rng(20261116).integers(0, n, size=(10000, n))
        return self[n]


def interval(values, rooms, draws):
    names = sorted(set(rooms))
    idx = {n: i for i, n in enumerate(names)}
    cl = np.array([idx[r] for r in rooms])
    sums = np.bincount(cl, weights=np.asarray(values, float), minlength=len(names))
    counts = np.bincount(cl, minlength=len(names)).astype(float)
    d = draws[len(names)]
    est = sums[d].sum(1) / counts[d].sum(1)
    return [float(100 * np.percentile(est, 2.5)), float(100 * np.percentile(est, 97.5))]


def tables(rows, split, draws):
    out = {}
    for typ, suf in TYPES.items():
        by = collections.defaultdict(dict)
        for r in rows:
            if r['type'] == typ:
                by[r['arm']]  # every arm seen in any split; an arm absent from this split scores 0 on every item
        for r in rows:
            if r['split'] == split and r['type'] == typ:
                by[r['arm']][r['row_id']] = r
        if not any(by.values()):
            continue
        ids = sorted(by['GT' + ('+R0' if suf else '')])
        rooms = [by['GT' + ('+R0' if suf else '')][i]['room'] for i in ids]
        vals = {a: np.array([by[a][i]['mra'] if i in by[a] else 0. for i in ids]) for a in by}
        missing = {a: sum(i not in by[a] for i in ids) for a in by}
        res = {}
        for a in sorted(by):
            rec = dict(mean=float(100 * vals[a].mean()), ci95=interval(vals[a], rooms, draws), n_items=len(ids),
                       n_rooms=len(set(rooms)), refusals=sum(1 for i in ids if i in by[a] and by[a][i]['refusal_code']),
                       missing_items=missing[a])
            ref = REF + ('+' + a.split('+')[-1] if typ == 'room_size_estimation' and '+' in a else '')
            if ref in vals and ref != a:
                diff = vals[a] - vals[ref]
                rec.update(vs=ref, diff=float(100 * diff.mean()), diff_ci95=interval(diff, rooms, draws))
            res[a] = rec
        out[typ] = res
    return out


def decide(tr, ho):
    dec = {}
    for m, arm in PRIMARY.items():
        d = {}
        for typ, suf in TYPES.items():
            t = tr.get(typ, {}).get(arm + suf)
            if t is None or 'diff' not in t:
                d[typ] = dict(status='absent')
                continue
            row = dict(train_mean=t['mean'], train_diff=t['diff'], train_diff_lo=t['diff_ci95'][0])
            if ho is not None:
                h, ref = ho[typ][arm + suf], ho[typ][REF + suf]
                row.update(heldout_mean=h['mean'], heldout_diff=h['diff'], heldout_diff_ci95=h['diff_ci95'],
                           vsi_points_heldout=h['diff'] / 8)
                row['qualifies'] = row['train_diff_lo'] > 0 and h['diff'] > 0
                row['bar'] = ref['mean'] + DIST_BAR if typ == 'object_abs_distance' else ROOM_BAR
                row['clears_bar'] = h['mean'] >= row['bar']
                if typ == 'room_size_estimation':
                    row['clears_sensitivity_bar'] = h['mean'] >= ROOM_BAR_SENS
            d[typ] = row
        if ho is not None:
            q = [t for t in TYPES if d[t].get('qualifies')]
            guard = all(d[o].get('train_diff_lo') is not None and d[o]['train_diff_lo'] >= GUARD
                        for t in q for o in TYPES if o != t)
            d['replaces_g3t'] = bool(q) and guard
        dec[m] = d
    if ho is None:
        return dec, None
    winners = {}
    for typ in TYPES:
        qual = sorted(((dec[m][typ]['train_mean'], m) for m in dec if dec[m][typ].get('qualifies')), reverse=True)
        if not qual or (len(qual) > 1 and qual[0][0] == qual[1][0]):
            winners[typ] = 'G3T'
        else:
            winners[typ] = qual[0][1] if dec[qual[0][1]]['replaces_g3t'] else 'G3T'
    gt_free = [REF + '+R0'] + [arm + '+R0' for arm in PRIMARY.values()]  # secondary arms are diagnostic, never decide
    room_path = sorted(a for a in gt_free if a in ho.get('room_size_estimation', {})
                       and ho['room_size_estimation'][a]['mean'] >= ROOM_BAR)
    return dec, dict(per_type_winner=winners, room_head_path_arms_at_bar=room_path,
                     note='Per-type winners; a candidate replaces G3T only if replaces_g3t holds (qualifies on one type, other-type train lower bound >= -2).')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('captures'); ap.add_argument('out')
    ap.add_argument('--heldout-go')
    a = ap.parse_args()
    rows = [r for p in sorted(glob.glob(a.captures + '/*.json')) for r in json.load(open(p))['items']]
    r2, rows = fit_r2(rows)
    draws = Draws()
    res = dict(prereg_sha256=PREREG, reference=REF, r2_fits=r2, tables={'train': tables(rows, 'train', draws)})
    ho = None
    if a.heldout_go:
        if not any(l.strip() == 'GO heldout' for l in Path(a.heldout_go).read_text().splitlines()):
            raise PermissionError('held-out tables need an ORCH note with a "GO heldout" line')
        ho = res['tables']['heldout'] = tables(rows, 'heldout', draws)
    res['decision'], res['verdict'] = decide(res['tables']['train'], ho)
    Path(a.out).write_text(json.dumps(res, indent=1))
    for typ, t in res['tables']['train'].items():
        print('##', typ, 'train')
        for arm, s in t.items():
            print(f"{arm:24s} {s['mean']:7.2f} [{s['ci95'][0]:6.2f},{s['ci95'][1]:6.2f}] ref={s['refusals']}"
                  + (f" | vs {s['vs']}: {s['diff']:+7.2f} [{s['diff_ci95'][0]:+7.2f},{s['diff_ci95'][1]:+7.2f}]" if 'diff' in s else ''))
    print(json.dumps(res['verdict']))


if __name__ == '__main__':
    main()
