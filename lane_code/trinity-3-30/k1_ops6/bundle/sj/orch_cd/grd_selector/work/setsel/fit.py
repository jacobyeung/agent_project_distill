"""Fit the per-candidate accept classifier (logistic and boosted tree) and write out-of-room probabilities.

Splits: P1 (fit on the 31 tuning scans, apply to the 33 room-disjoint clean scans); CV84 (grouped 6-fold by room over
all 84 dev scans; rooms never cross folds); DEPLOY (fit on all 84 dev scans, apply frozen to the VSI table).
The name prior is refit inside every training fold; the *_np feature sets drop it. Labels (y) come from the scoring-only GT match in build.py.
usage: fit.py --dev data/dev_tab.jsonl --vsi data/vsi_tab.jsonl --out data/probs"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import setlib as L

SPLITS = '/scratch/jjyeung/orch_cd/verify_kit/out/SPLITS.json'


def matrix(cands, feats, prior):
    X = np.array([[prior(r['name'])[0] if f == 'name_prior' else r['features'][f] for f in feats] for r in cands], float)
    return X, np.array([r['y'] for r in cands])


def model(kind):
    if kind == 'logistic':
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=.05, max_iter=200, l2_regularization=1., random_state=0)


def fit_predict(train, test, feats, kind):
    pr = L.name_prior(train)
    pri = lambda n: (pr[0](n), None)  # noqa: E731
    Xtr, ytr = matrix(train, feats, pri)
    Xte, _ = matrix(test, feats, pri)
    m = model(kind).fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1], m, pr


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--dev', required=True)
    ap.add_argument('--vsi')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    _, dc = L.load(a.dev)
    cands = [r for v in dc.values() for r in v]
    sp = json.load(open(SPLITS))
    tun, clean = set(sp['tuning_scenes']), set(sp['room_disjoint_scenes'])
    probs, summary = {}, {}
    variants = [(fs, k) for fs in ('portable', 'full', 'portable_np', 'full_np') for k in ('logistic', 'tree')]
    variants += [(f'full-{g}', 'logistic') for g in L.GROUPS]
    for fs, kind in variants:
        feats = L.FEATS[fs] if fs in L.FEATS else [f for f in L.FEATS['full'] if f not in L.GROUPS[fs.split('-', 1)[1]]]
        tag = f'{fs}|{kind}'
        tr = [r for r in cands if r['scene'] in tun]
        te = [r for r in cands if r['scene'] in clean]
        p1, _, _ = fit_predict(tr, te, feats, kind)
        oof = np.zeros(len(cands))
        groups = [L.room(r['scene']) for r in cands]
        for trn, tst in GroupKFold(6).split(cands, groups=groups):
            oof[tst], _, _ = fit_predict([cands[i] for i in trn], [cands[i] for i in tst], feats, kind)
        probs[f'P1|{tag}'] = {f"{r['object_id']}|{r['candidate_id']}": float(p) for r, p in zip(te, p1)}
        probs[f'CV84|{tag}'] = {f"{r['object_id']}|{r['candidate_id']}": float(p) for r, p in zip(cands, oof)}
        y1, y = np.array([r['y'] for r in te]), np.array([r['y'] for r in cands])
        summary[tag] = dict(P1_auc=roc_auc_score(y1, p1), P1_ap=average_precision_score(y1, p1),
                            CV84_auc=roc_auc_score(y, oof), CV84_ap=average_precision_score(y, oof), n_feats=len(feats))
        print(tag, json.dumps({k: round(v, 4) for k, v in summary[tag].items()}), flush=True)
    if a.vsi:
        _, vc = L.load(a.vsi)
        vcands = [r for v in vc.values() for r in v]
        for fs, kind in ((fs, k) for fs in ('portable', 'portable_np', 'full_np') for k in ('logistic', 'tree')):
            p, m, pr = fit_predict(cands, vcands, L.FEATS[fs], kind)
            probs[f'DEPLOY|{fs}|{kind}'] = {f"{r['object_id']}|{r['candidate_id']}": float(x) for r, x in zip(vcands, p)}
            pickle.dump(dict(model=m, feats=L.FEATS[fs], prior_names=None), open(out/f'deploy_{fs}_{kind}.pkl', 'wb'))
            yv = np.array([r['y'] for r in vcands])
            summary[f'DEPLOY|{fs}|{kind}'] = dict(vsi_auc=roc_auc_score(yv, p), vsi_ap=average_precision_score(yv, p))
            print('DEPLOY', fs, kind, summary[f'DEPLOY|{fs}|{kind}'], flush=True)
    json.dump(probs, open(out/'probs.json', 'w'))
    json.dump(summary, open(out/'fit_summary.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
