"""Train ScaleHead on the 239 E3 train captures (target log SO); select config by room-grouped CV in train.

Usage: python -I train_scale.py OUT_DIR [--features CACHE.json]
Writes OUT_DIR/scale_head.safetensors, scale_head.json, scale_head.safetensors.sha256, cv_results.json.
Held-out captures are never loaded here.
"""
import argparse, glob, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
from safetensors.torch import save_file
from scale_head import ScaleHead, prepare_inputs, FEATURE_NAMES, N_FEATURES, file_sha256

SEED = 20261116
E3_TRAIN = '/scratch/jjyeung/orch_n30/b04_e2ehook/work/e3/work/harness/out_tr'
TOWERS = '/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2'
FOLDS, REPEATS = 5, 4
CANDIDATES = ([dict(hidden=0, ridge=l) for l in (0.3, 1.0, 3.0, 10.0, 30.0, 100.0)]
              + [dict(hidden=h, wd=w, steps=3000, lr=1e-2) for h in (8, 16) for w in (1e-3, 1e-2, 1e-1)])


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_train(cache=None):
    rows = []
    for p in sorted(glob.glob(E3_TRAIN + '/*__*.json')):
        d = json.load(open(p))['diagnostics']
        assert d['split'] == 'train', 'held-out capture in train input'
        rows.append(dict(capture=d['capture'], room=d['room'], dataset=d['dataset'], SO=d['SO'],
                         tower=f"{TOWERS}/{digest(d['capture'])[:16]}/tower.npz"))
    cached = {}
    if cache:
        cached = {r['capture']: r['features'] for r in json.load(open(cache))['rows'] if r['split'] == 'train'}
    for r in rows:
        if r['capture'] in cached:
            r['features'] = cached[r['capture']]
        else:
            f, _ = ScaleHead.features(**prepare_inputs(r['tower']))
            r['features'] = f[0].tolist()
        r['tower_sha256'] = file_sha256(r['tower'])
    return rows


def fit(X, y, cfg, seed=SEED):
    torch.manual_seed(seed)
    head = ScaleHead(hidden=cfg['hidden'])
    X, y = torch.tensor(X, dtype=torch.float64), torch.tensor(y, dtype=torch.float64)
    mean, std = X.mean(0), X.std(0)
    std = torch.where(std > 1e-12, std, torch.ones_like(std))
    head.feat_mean.copy_(mean)
    head.feat_std.copy_(std)
    Z = (X - mean) / std
    if cfg['hidden'] == 0:
        # Ridge on standardised features, unpenalised intercept (closed form = the linear layer's optimum).
        ym = y.mean()
        A = Z.T @ Z + cfg['ridge'] * torch.eye(N_FEATURES, dtype=torch.float64)
        w = torch.linalg.solve(A, Z.T @ (y - ym))
        with torch.no_grad():
            head.net.weight.copy_(w[None])
            head.net.bias.fill_(float(ym))
        return head
    with torch.no_grad():
        head.net[-1].bias.fill_(float(y.mean()))
    opt = torch.optim.Adam(head.net.parameters(), lr=cfg['lr'])
    for _ in range(cfg['steps']):
        opt.zero_grad()
        pred = head.net(Z)[:, 0]
        loss = ((pred - y) ** 2).mean() + cfg['wd'] * sum((m.weight ** 2).sum() for m in head.net if isinstance(m, torch.nn.Linear))
        loss.backward()
        opt.step()
    return head


def predict(head, X):
    with torch.no_grad():
        return head.from_features(torch.tensor(X, dtype=torch.float64)).numpy()


def baselines(Xtr, ytr, Xte):
    """E3's S2 and S4 refit on the training fold, from the same features (log h = floor q01, log span)."""
    ih, isp = FEATURE_NAMES.index('log_floor_dist_q01'), FEATURE_NAMES.index('log_span_q01_q99')
    s2 = np.log(np.median(np.exp(ytr + Xtr[:, ih]))) - Xte[:, ih]
    D = lambda X: np.column_stack([np.ones(len(X)), X[:, ih], X[:, isp]])
    coef = np.linalg.lstsq(D(Xtr), ytr, rcond=None)[0]
    return dict(S2=s2, S4=D(Xte) @ coef)


def metrics(err):
    err = np.asarray(err)
    return dict(mean_abs_log=float(np.mean(np.abs(err))), within20=float(np.mean((np.exp(err) >= .8) & (np.exp(err) <= 1.2))))


def grouped_folds(rooms, repeat):
    uniq = sorted(set(rooms))
    perm = np.random.default_rng(SEED + repeat).permutation(len(uniq))
    fold_of = {uniq[i]: k % FOLDS for k, i in enumerate(perm)}
    return np.array([fold_of[r] for r in rooms])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--features')
    args = ap.parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    os.makedirs(args.out, exist_ok=True)
    rows = load_train(args.features)
    assert len(rows) == 239, len(rows)
    X = np.array([r['features'] for r in rows])
    y = np.log([r['SO'] for r in rows])
    rooms = [r['room'] for r in rows]
    population = hashlib.sha256(json.dumps(sorted((r['capture'], r['SO'], r['tower_sha256']) for r in rows)).encode()).hexdigest()
    names = [json.dumps(c, sort_keys=True) for c in CANDIDATES] + ['baseline_S2', 'baseline_S4']
    errs = {n: [] for n in names}
    for rep in range(REPEATS):
        fold = grouped_folds(rooms, rep)
        oof = {n: np.zeros(len(y)) for n in names}
        for k in range(FOLDS):
            tr, te = fold != k, fold == k
            for c, n in zip(CANDIDATES, names):
                oof[n][te] = predict(fit(X[tr], y[tr], c), X[te])
            b = baselines(X[tr], y[tr], X[te])
            oof['baseline_S2'][te], oof['baseline_S4'][te] = b['S2'], b['S4']
        for n in names:
            errs[n].append(oof[n] - y)
    cv = {n: dict(metrics(np.concatenate(errs[n])),
                  per_repeat_mean_abs_log=[metrics(e)['mean_abs_log'] for e in errs[n]]) for n in names}
    best = min(names[:len(CANDIDATES)], key=lambda n: cv[n]['mean_abs_log'])
    cfg = json.loads(best)
    head = fit(X, y, cfg)
    sd = {k: v.contiguous() for k, v in head.state_dict().items()}
    wpath = os.path.join(args.out, 'scale_head.safetensors')
    save_file(sd, wpath)
    wsha = file_sha256(wpath)
    open(wpath + '.sha256', 'w').write(f'{wsha}  scale_head.safetensors\n')
    train_fit = metrics(predict(head, X) - y)
    meta = dict(config=dict(cfg, hidden=cfg['hidden']), feature_names=list(FEATURE_NAMES), seed=SEED,
                target='log SO (E3 oracle: median GT/g3t depth on conf>clip-median grid points)',
                train_population=dict(n_captures=len(rows), n_rooms=len(set(rooms)), sha256=population,
                                      source=E3_TRAIN, towers=TOWERS),
                selection=dict(rule='min room-grouped CV mean |log s/SO| over candidates', folds=FOLDS, repeats=REPEATS,
                               chosen=best, cv=cv[best]),
                n_parameters=int(sum(p.numel() for p in head.parameters())),
                train_fit=train_fit, weights_sha256=wsha,
                code_sha256={f: file_sha256(os.path.join(os.path.dirname(os.path.abspath(__file__)), f))
                             for f in ('scale_head.py', 'train_scale.py')})
    json.dump(meta, open(os.path.join(args.out, 'scale_head.json'), 'w'), indent=1)
    json.dump(dict(candidates=cv, chosen=best), open(os.path.join(args.out, 'cv_results.json'), 'w'), indent=1)
    for n in names:
        print(f"{n:70s} cv|log|={cv[n]['mean_abs_log']:.4f} w20={cv[n]['within20']:.3f}")
    print('CHOSEN', best, 'weights_sha256', wsha)


if __name__ == '__main__':
    main()
