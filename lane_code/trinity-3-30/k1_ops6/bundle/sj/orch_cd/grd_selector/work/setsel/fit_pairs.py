"""Fit the learned identity merge P(same object) on labelled dev pairs (logistic and boosted tree) and write
out-of-room probabilities for every dev pair (grouped 6-fold by room; a pair's prediction comes from the fold that
holds its room out) plus frozen-deployment probabilities for every VSI pair (fit on all labelled dev pairs).
Baselines: the heuristic merge rule (centre distance below 0.3 m + 0.5 x the larger extent and no disjoint shared
frame) and -distance ratio alone. Metrics on labelled pairs, also restricted to pairs of two true candidates (y = 1).
usage: fit_pairs.py --dev data/dev_pairs.jsonl --vsi data/vsi_pairs.jsonl --out data/pairs_fit"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

import fit as FT
import setlib as L


def load(path):
    rs = [json.loads(l) for l in open(path)]
    X = np.array([[r['f'][k] for k in L.PFEATS] for r in rs], float)
    return rs, X, np.array([r['y'] for r in rs])


def heur(X):
    i = {k: n for n, k in enumerate(L.PFEATS)}
    return ((X[:, i['d_rel']] < 1) & (X[:, i['n_disjoint']] == 0)).astype(float)


def metrics(y, s, both):
    out = {}
    for tag, m in (('all', y >= 0), ('true_pairs', (y >= 0) & both)):
        if m.sum() and 0 < y[m].mean() < 1:
            out[tag] = dict(n=int(m.sum()), pos=int(y[m].sum()), auc=float(roc_auc_score(y[m], s[m])),
                            ap=float(average_precision_score(y[m], s[m])))
    return out


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--dev', required=True)
    ap.add_argument('--vsi', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dr, DX, dy = load(a.dev)
    vr, VX, vy = load(a.vsi)
    dboth = np.array([r['ya'] == 1 and r['yb'] == 1 for r in dr])
    vboth = np.array([r['ya'] == 1 and r['yb'] == 1 for r in vr])
    groups = np.array([L.room(r['scene']) for r in dr])
    lab = dy >= 0
    summary = dict(dev=dict(heuristic=metrics(dy, heur(DX), dboth), neg_d_rel=metrics(dy, -DX[:, L.PFEATS.index('d_rel')], dboth)),
                   vsi=dict(heuristic=metrics(vy, heur(VX), vboth), neg_d_rel=metrics(vy, -VX[:, L.PFEATS.index('d_rel')], vboth)))
    probs = {}
    key = lambda r: f"{r['object_id']}|{r['a']}|{r['b']}"  # noqa: E731
    for kind in ('logistic', 'tree'):
        oof = np.zeros(len(dr))
        for trn, tst in GroupKFold(6).split(DX, groups=groups):
            m = FT.model(kind).fit(DX[trn][lab[trn]], dy[trn][lab[trn]])
            oof[tst] = m.predict_proba(DX[tst])[:, 1]
        m = FT.model(kind).fit(DX[lab], dy[lab])
        pv = m.predict_proba(VX)[:, 1]
        pickle.dump(dict(model=m, feats=L.PFEATS), open(out/f'deploy_pairs_{kind}.pkl', 'wb'))
        probs[f'CV84|{kind}'] = {key(r): float(p) for r, p in zip(dr, oof)}
        probs[f'DEPLOY|{kind}'] = {key(r): float(p) for r, p in zip(vr, pv)}
        summary['dev'][kind] = metrics(dy, oof, dboth)
        summary['vsi'][kind] = metrics(vy, pv, vboth)
        print(kind, json.dumps(summary['dev'][kind]), json.dumps(summary['vsi'][kind]), flush=True)
    print('heuristic', json.dumps(summary['dev']['heuristic']), json.dumps(summary['vsi']['heuristic']))
    json.dump(probs, open(out/'pair_probs.json', 'w'))
    json.dump(summary, open(out/'pair_fit_summary.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
