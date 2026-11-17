"""Rescore K1 distance reads (E3 harness incl. deployed GD arms) against half-extent-corrected labels.

Corrected label of a row: the row's two raster boxes doubled when the scene's convention is half (scene has >= 1 box
certified half by containment and none certified full), else unchanged. ScanNet++ v1 scenes with no decided box take
the asset convention (half). Variants: stored, corrected (scene convention), selective (only rows whose boxes are all
certified; others dropped), drop (affected rows removed).
"""
import collections, json, math, pathlib, sys
import numpy as np

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
W = LANE / 'work/k1audit'
PER_ITEM = LANE / 'work/k1/orch_n30/k1_ops3/work/e3gd/out/PER_ITEM.jsonl'


def mra(pred, truth):
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    rel = abs(pred - truth) / abs(truth)
    return sum(rel < (100 - t) / 100 for t in range(50, 100, 5)) / 10


def scene_conventions(rows):
    sc = collections.defaultdict(collections.Counter)
    for r in rows:
        for s in r['box_statuses']:
            sc[r['capture']][s] += 1
    conv = {}
    for cap, c in sc.items():
        if c['half'] and not c['full']:
            conv[cap] = 'half'
        elif c['full'] and not c['half']:
            conv[cap] = 'full'
        elif c['half'] and c['full']:
            conv[cap] = 'mixed'
        else:
            conv[cap] = 'half' if cap.startswith('scannetpp/') else 'undecided'
    return conv


def labels(rows):
    conv = scene_conventions(rows)
    out = {}
    for r in rows:
        c = conv.get(r['capture'], 'no_raster' if not r['box_keys'] else 'undecided')
        corrected = r['x2_m'] if c == 'half' else (r['x1_m'] if c == 'full' else None)
        affected = c in ('half', 'mixed', 'undecided', 'no_raster') or 'half' in r['box_statuses']
        out[r['id']] = dict(capture=r['capture'], split=r['split'], dataset=r['dataset'], convention=c, stored=r['stored_m'],
                            corrected=corrected, selective=r['selective_m'], affected=affected, box_statuses=r['box_statuses'])
    return out, conv


def boot(items, arms, ref, draws=10000, seed=20261116):
    rooms = sorted({i['room'] for i in items})
    ix = {r: k for k, r in enumerate(rooms)}
    s = np.zeros((len(arms), len(rooms))); n = np.zeros(len(rooms))
    for i in items:
        n[ix[i['room']]] += 1
        for a, arm in enumerate(arms):
            s[a, ix[i['room']]] += i['score'][arm]
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(rooms), size=(draws, len(rooms)))
    cnt = np.zeros((draws, len(rooms)))
    np.add.at(cnt, (np.repeat(np.arange(draws), len(rooms)), pick.ravel()), 1)
    tot = cnt @ n
    means = (cnt @ s.T) / tot[:, None] * 100
    res = {}
    for a, arm in enumerate(arms):
        pt = 100 * s[a].sum() / n.sum()
        lo, hi = np.percentile(means[:, a], [2.5, 97.5])
        d = means[:, a] - means[:, arms.index(ref)]
        dpt = pt - 100 * s[arms.index(ref)].sum() / n.sum()
        dlo, dhi = np.percentile(d, [2.5, 97.5])
        res[arm] = dict(mra=round(pt, 2), ci=[round(lo, 1), round(hi, 1)], vs_ref=round(dpt, 2), vs_ref_ci=[round(dlo, 1), round(dhi, 1)])
    return dict(items=len(items), rooms=len(rooms), ref=ref, arms=res)


def main():
    rows = [json.loads(l) for l in open(W / 'K1_ROW_AUDIT.jsonl')]
    L, conv = labels(rows)
    per = [json.loads(l) for l in open(PER_ITEM)]
    dist = [p for p in per if p['type'] == 'object_abs_distance']
    arms = sorted({p['arm'] for p in dist})
    byrow = collections.defaultdict(dict); meta = {}
    for p in dist:
        lab = L[p['row_id']]
        assert abs(lab['stored'] - p['gt']) < 1e-9, p['row_id']
        assert abs(mra(p['pred'], p['gt']) - p['mra']) < 1e-12 if p['pred'] is not None else p['mra'] == 0.0
        byrow[p['row_id']][p['arm']] = p['pred']
        meta[p['row_id']] = dict(room=p['room'], split=p['split'], dataset=p['dataset'], capture=p['capture'])
    report = {'scene_conventions': collections.Counter(conv.values()), 'tables': {}}
    for split in ['heldout', 'train']:
        ids = [i for i in byrow if meta[i]['split'] == split]
        for variant in ['stored', 'corrected', 'selective', 'drop']:
            items = []
            for i in ids:
                lab = L[i]
                if variant == 'stored':
                    g = lab['stored']
                elif variant == 'corrected':
                    g = lab['corrected']
                elif variant == 'selective':
                    g = lab['selective'] if 'half' in lab['box_statuses'] else (lab['stored'] if lab['convention'] == 'full' and 'unknown' not in lab['box_statuses'] else None)
                else:
                    g = None if lab['affected'] else lab['stored']
                if g is None:
                    continue
                items.append(dict(room=meta[i]['room'], dataset=meta[i]['dataset'], score={a: mra(byrow[i].get(a), g) for a in arms}))
            t = boot(items, arms, 'GD_reviewed')
            t['by_dataset'] = {ds: {a: round(100 * np.mean([x['score'][a] for x in items if x['dataset'] == ds]), 2) for a in ['GT', 'GD_reviewed', 'S4+G1', 'SO+G1', 'SO+GO', 'S1+G1']}
                               for ds in sorted({x['dataset'] for x in items})}
            t['n_by_dataset'] = dict(collections.Counter(x['dataset'] for x in items))
            report['tables'][split + ':' + variant] = t
            print(split, variant, t['items'], t['rooms'], {a: t['arms'][a]['mra'] for a in ['GT', 'GD_reviewed', 'GD_sealed', 'S4+G1', 'SO+G1', 'SO+GO', 'S1+G1']}, flush=True)
    rat = collections.defaultdict(list)
    for i, lab in L.items():
        if lab['convention'] == 'half' and lab['corrected'] and lab['stored'] > 0:
            rat[(lab['split'], lab['dataset'])].append(lab['corrected'] / lab['stored'])
    report['corrected_over_stored'] = {'%s:%s' % k: dict(n=len(v), median=float(np.median(v)), p05=float(np.quantile(v, .05)), p95=float(np.quantile(v, .95)),
                                       min=float(min(v)), max=float(max(v))) for k, v in rat.items()}
    json.dump(report, open(W / 'K1_RESCORE.json', 'w'), indent=1, sort_keys=True, default=dict)
    with open(W / 'K1_LABELS_CORRECTED.jsonl', 'w') as f:
        for i in sorted(L):
            f.write(json.dumps(dict(id=i, **L[i]), sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
