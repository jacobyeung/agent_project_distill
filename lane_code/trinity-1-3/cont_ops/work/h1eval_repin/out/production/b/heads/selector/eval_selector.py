"""Held-out report: SelectorHead vs K1-refit logistic vs deployed MODELS.json on the same K1 held-out candidates.

Usage: python -I -B eval_selector.py HEAD_DIR   (needs work/logistic_heldout.json from logistic.py)
Bar (B6 4.6, K1_RULES max_auc_drop .02, max_top1_drop .02): head AUC >= refit - .02 and head top-1 >= refit - .02.
Paired room bootstrap: 10,000 draws over held-out physical rooms, seed 20261116, percentile 95% interval.
"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
from scipy.stats import rankdata
import common as C
import train_selector as T
from selector_head import load_head


def fast_auc(y, p):
    r = rankdata(p)
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    head, meta = load_head(sys.argv[1])
    torch.set_num_threads(1)
    rows = [r for r in C.load() if r['split'] == 'heldout']
    gs = T.groups(rows, T.names_table())
    probs = T.predict(head, gs)
    rows = [r for g in gs for r in g['rows']]
    ph = np.array([v for ps in probs for v in ps])
    lg = json.load(open(C.HERE / f'work/logistic_heldout{C.TAG}.json'))
    pr = np.array([lg['heldout'][C.key(r)]['refit'] for r in rows])
    pc = np.array([lg['heldout'][C.key(r)]['current'] for r in rows])
    y = np.array([r['y'] for r in rows])
    arms = dict(head=ph, refit=pr, current=pc)
    res = {k: dict(auc=C.auc(y, p), ap=C.ap(y, p), top1=C.top1(rows, p)) for k, p in arms.items()}
    res['head']['slot_acc_with_null'] = T.slot_accuracy(head, gs)
    res['head']['objects_without_positive'] = sum(int(g['y'].sum() == 0) for g in gs)
    # per-room index sets and per-object top-1 indicators
    room_idx = collections.defaultdict(list)
    for i, r in enumerate(rows):
        room_idx[r['room']].append(i)
    obj = collections.defaultdict(list)
    for i, r in enumerate(rows):
        obj[r['object_id']].append(i)
    obj_room = {o: rows[ix[0]]['room'] for o, ix in obj.items()}
    top = {k: {o: rows[max(ix, key=lambda i: (p[i], rows[i]['features'].get('peak', 0)))]['y'] for o, ix in obj.items()}
           for k, p in arms.items()}
    room_top = {k: collections.defaultdict(list) for k in arms}
    for k in arms:
        for o, v in top[k].items():
            room_top[k][obj_room[o]].append(v)
    rooms = sorted(room_idx)
    rng = np.random.default_rng(C.SEED)
    draws = rng.integers(0, len(rooms), size=(10000, len(rooms)))
    diffs = {f'head-{b}': dict(auc=[], top1=[]) for b in ('refit', 'current')}
    for d in draws:
        sel = [rooms[i] for i in d]
        ix = np.concatenate([room_idx[r] for r in sel])
        yy = y[ix]
        if yy.min() == yy.max():
            continue
        a = {k: fast_auc(yy, p[ix]) for k, p in arms.items()}
        t = {k: np.mean([v for r in sel for v in room_top[k][r]]) for k in arms}
        for b in ('refit', 'current'):
            diffs[f'head-{b}']['auc'].append(a['head'] - a[b]); diffs[f'head-{b}']['top1'].append(t['head'] - t[b])
    paired = {k: {m: dict(point=res['head'][m] - res[k.split('-')[1]][m],
                          ci=[float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))], draws=len(v))
                  for m, v in dv.items()} for k, dv in diffs.items()}
    bar = dict(auc_ok=res['head']['auc'] >= res['refit']['auc'] - .02, top1_ok=res['head']['top1'] >= res['refit']['top1'] - .02)
    bar['PASS'] = bar['auc_ok'] and bar['top1_ok']
    out = dict(head_dir=sys.argv[1], weights_sha256=meta['weights_sha256'], config=meta['config'], metrics=res, paired=paired,
               bar=bar, counts=dict(candidates=len(rows), positives=int(y.sum()), objects=len(obj), rooms=len(rooms),
                                    captures=len({r['capture'] for r in rows})),
               logistic=dict(upstream=lg['upstream'], current_models_sha256=lg['current_models_sha256'], versions=lg['versions']))
    json.dump(out, open(C.HERE / f'work/SELECTOR_HELDOUT{C.TAG}.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'logistic'}, indent=1))


if __name__ == '__main__':
    main()
