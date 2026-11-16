"""Presence probe analysis (CPU): first-seen read-outs fitted on K1 train, pricing on K1 held-out.

Read-outs over one (capture, object) vector of 32 presence logits x_1..x_32:
  head    learned temporal head (weights only, no external threshold): per-frame hazard
          p_k = sigmoid(conv1d_5(x)_k + w_pos * k/32 + b), P(first = k) = p_k prod_{j<k}(1 - p_j), P(never) = prod(1 - p_j);
          fitted by NLL of the GT first-seen frame on K1 train; prediction = argmax over {1..32, never}.
  thr0    first frame with logit > 0 (the model's own argmax token decides presence).
  thrfit  first frame with logit > tau, tau fitted on K1 train (reference only: a tuned threshold outside weights).
Pricing on K1 held-out items:
  appearance order: sort the 4 objects by predicted first-seen (ties: expected first-seen under the head, else logit sum),
                    answer = option with the highest Kendall agreement with that order (exact order first).
  counting: number of maximal runs of predicted-present frames (head: p_k >= 0.5 of a per-frame presence head of the
            same conv form fitted by BCE on GT visibility of K1 train,
            thr0: logit > 0); scored with the official MRA.
  gt program: the same rules on GT visibility (ceiling sanity); constant: best single answer on K1 train.
  direct: step-544 direct journal (direct.py), when present.
Paired differences: room-cluster bootstrap (10,000 draws, seed 0), 95% percentile interval.
Primary arm (pre-registered): chosen by room-grouped 5-fold CV on K1 train only (mean first-seen exact accuracy of head).
"""
import argparse, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

LANE = Path('/scratch/jjyeung/orch_n30/b11_presence')
ARMS = ('V', 'I', 'Y')
NEVER = 33


# ---------------- data ----------------
def load_captures(prep):
    return {c['canonical']: c for c in map(json.loads, open(Path(prep) / 'CAPTURES.jsonl'))}


def load_items(prep):
    return [json.loads(l) for l in open(Path(prep) / 'ITEMS.jsonl')]


def slug(c):
    return c.replace('/', '__')


def load_logits(journals, caps):
    """{arm: {(capture, obj): np.array[32]}} for complete vectors only; plus timing per capture."""
    out = {a: {} for a in ARMS}
    timing = {}
    for sub in ('V', 'IY'):
        d = Path(journals) / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob('*.jsonl')):
            acc = defaultdict(dict)
            for line in open(p):
                r = json.loads(line)
                if 'timing' in r:
                    timing.setdefault(r.get('capture') or p.stem, {}).update(r['timing'])
                    continue
                acc[(r['arm'], r['capture'], r['obj'])][r['frame']] = r['logit']
            for (arm, cap, obj), fr in acc.items():
                if sorted(fr) == list(range(1, 33)):
                    out[arm][(cap, obj)] = np.array([fr[k] for k in range(1, 33)], dtype=np.float64)
    return out, timing


def pair_table(caps, logits, split):
    keys, X, Y, V = [], [], [], []
    for cname, c in sorted(caps.items()):
        if split != 'all' and c['split'] != split:
            continue
        for obj in c['scored']:
            k = (cname, obj)
            if k not in logits:
                continue
            cat = c['categories'][obj]
            keys.append(k); X.append(logits[k]); Y.append(cat['first_seen']); V.append(cat['visible'])
    return keys, np.array(X).reshape(-1, 32), Y, np.array(V).reshape(-1, 32)


# ---------------- read-outs ----------------
class Head:
    """Temporal hazard head; 8 parameters (5 conv taps, logit scale folded into taps, position weight, bias, never)."""

    def __init__(self, seed=0):
        self.seed = seed
        self.params = None

    @staticmethod
    def _torch():
        import torch
        torch.use_deterministic_algorithms(True)
        return torch

    def _hazard(self, X, params):
        torch = self._torch()
        taps, wpos, b = params[:5], params[5], params[6]
        x = torch.as_tensor(X, dtype=torch.float64).unsqueeze(1)                          # [n,1,32]
        x = torch.nn.functional.pad(x, (2, 2), mode='replicate')
        z = torch.nn.functional.conv1d(x, taps.view(1, 1, 5)).squeeze(1)                    # [n,32]
        pos = torch.arange(1, 33, dtype=torch.float64) / 32
        return torch.sigmoid(z + wpos * pos + b)

    def _dist(self, X, params):
        torch = self._torch()
        p = self._hazard(X, params).clamp(1e-6, 1 - 1e-6)
        surv = torch.cumprod(torch.cat([torch.ones(p.shape[0], 1, dtype=p.dtype), 1 - p], 1), 1)  # [n,33]
        first = p * surv[:, :32]
        return torch.cat([first, surv[:, 32:33]], 1)                                         # [n,33] P(first=k), P(never)

    def fit(self, X, Y, iters=200):
        torch = self._torch()
        torch.manual_seed(self.seed)
        keep = [i for i, y in enumerate(Y) if y is not None]
        Xt, yt = X[keep], torch.tensor([Y[i] - 1 for i in keep])
        params = torch.zeros(7, dtype=torch.float64)
        params.data[2] = 1.0
        params.requires_grad_(True)
        opt = torch.optim.LBFGS([params], lr=0.5, max_iter=iters, line_search_fn='strong_wolfe',
                                tolerance_grad=1e-10, tolerance_change=1e-12)

        def closure():
            opt.zero_grad()
            d = self._dist(Xt, params)
            loss = -torch.log(d[torch.arange(len(yt)), yt]).mean() + 1e-4 * (params ** 2).sum()
            loss.backward()
            return loss
        opt.step(closure)
        self.params = params.detach().clone()
        with torch.no_grad():
            self.train_nll = float(-torch.log(self._dist(Xt, self.params)[torch.arange(len(yt)), yt]).mean())
        return self

    def fit_presence(self, X, V, iters=200):
        """Per-frame presence posterior for track counting: same conv form, fitted by BCE on GT visibility (train)."""
        torch = self._torch()
        torch.manual_seed(self.seed)
        Vt = torch.as_tensor(np.asarray(V), dtype=torch.float64)
        params = torch.zeros(7, dtype=torch.float64)
        params.data[2] = 1.0
        params.requires_grad_(True)
        opt = torch.optim.LBFGS([params], lr=0.5, max_iter=iters, line_search_fn='strong_wolfe',
                                tolerance_grad=1e-10, tolerance_change=1e-12)

        def closure():
            opt.zero_grad()
            p = self._hazard(X, params).clamp(1e-6, 1 - 1e-6)
            loss = -(Vt * torch.log(p) + (1 - Vt) * torch.log(1 - p)).mean() + 1e-4 * (params ** 2).sum()
            loss.backward()
            return loss
        opt.step(closure)
        self.pparams = params.detach().clone()
        return self

    def dist(self, X):
        torch = self._torch()
        with torch.no_grad():
            return self._dist(X, self.params).numpy()

    def presence(self, X):
        torch = self._torch()
        with torch.no_grad():
            return self._hazard(X, self.pparams).numpy()

    def first(self, X):
        d = self.dist(X)
        return (d.argmax(1) + 1).tolist(), (d * np.arange(1, 34)).sum(1).tolist()


def first_above(X, tau):
    out = []
    for x in X:
        idx = np.nonzero(x > tau)[0]
        out.append(int(idx[0]) + 1 if len(idx) else NEVER)
    return out


def fit_tau(X, Y):
    keep = [i for i, y in enumerate(Y) if y is not None]
    grid = np.round(np.arange(-8, 8.001, 0.25), 2)
    acc = [np.mean([p == Y[i] for p, i in zip(first_above(X[keep], t), keep)]) for t in grid]
    return float(grid[int(np.argmax(acc))])


def fs_metrics(pred, Y):
    pairs = [(p, y) for p, y in zip(pred, Y) if y is not None]
    if not pairs:
        return {}
    err = np.array([abs(p - y) for p, y in pairs])
    seen = [(p, y) for p, y in pairs if y != NEVER]
    return dict(n=len(pairs), exact=float(np.mean(err == 0)), within1=float(np.mean(err <= 1)),
                within2=float(np.mean(err <= 2)), mae=float(err.mean()),
                early=float(np.mean([p < y for p, y in seen])) if seen else None,
                late=float(np.mean([p > y for p, y in seen])) if seen else None,
                never_acc=float(np.mean([p == NEVER for p, y in pairs if y == NEVER])) if any(y == NEVER for _, y in pairs) else None)


def auroc(scores, labels):
    s, l = np.asarray(scores, float).ravel(), np.asarray(labels, int).ravel()
    pos, neg = s[l == 1], s[l == 0]
    if not len(pos) or not len(neg):
        return None
    order = np.argsort(np.concatenate([pos, neg]), kind='mergesort')
    ranks = np.empty(len(order)); ranks[order] = np.arange(1, len(order) + 1)
    allv = np.concatenate([pos, neg])
    for v in np.unique(allv):                      # average ties
        m = allv == v
        ranks[m] = ranks[m].mean()
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


# ---------------- pricing ----------------
def kendall_agree(a, b):
    pos = {n: i for i, n in enumerate(b)}
    return sum((pos[a[i]] < pos[a[j]]) for i in range(len(a)) for j in range(i + 1, len(a)))


def answer_order(item, first, tie):
    order = sorted(item['objects'], key=lambda n: (first[n], tie[n], n))
    scores = [kendall_agree(order, o) for o in item['option_orders']]
    return 'ABCD'[int(np.argmax(scores))], order


def runs(mask):
    m = np.asarray(mask, bool)
    return int(m[0]) + int(np.sum(m[1:] & ~m[:-1]))


READER = Path('/scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader/evaluator')


def mra(pred, target):
    if str(READER) not in sys.path:
        sys.path.insert(0, str(READER))
    from evalpath.official import official_mra
    return official_mra(float(pred), float(target))


def constant_answers(train_items):
    app = [i for i in train_items if i['type'] == 'obj_appearance_order']
    cnt = [i for i in train_items if i['type'] == 'object_counting']
    letter = max('ABCD', key=lambda L: (sum(i['answer'] == L for i in app), L)) if app else 'A'
    num = max(range(0, 21), key=lambda v: (sum(mra(v, i['answer']) for i in cnt), -v)) if cnt else 1
    return letter, num


def cluster_boot(rooms, diffs, draws=10000, seed=0):
    by = defaultdict(list)
    for r, d in zip(rooms, diffs):
        by[r].append(d)
    keys = sorted(by)
    sums = np.array([sum(by[k]) for k in keys]); ns = np.array([len(by[k]) for k in keys])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(keys), size=(draws, len(keys)))
    est = sums[idx].sum(1) / ns[idx].sum(1)
    return float(np.mean(diffs)), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def load_direct(path):
    out = {}
    if path and Path(path).is_file():
        for line in open(path):
            r = json.loads(line)
            if r.get('status') == 'complete':
                out[r['example_id']] = r
    return out


def item_scores(item, caps, arm_logits, head, tau, consts, direct):
    """Task points (0-100) per method for one item; None when a method cannot answer it."""
    c = caps[item['capture']]
    cats = c['categories']
    res = {}
    # GT program
    if item['type'] == 'obj_appearance_order':
        gt_first = {n: cats[n]['first_seen'] for n in item['objects']}
        res['gt_program'] = 100.0 * (answer_order(item, gt_first, {n: 0 for n in item['objects']})[0] == item['answer'])
        res['constant'] = 100.0 * (consts[0] == item['answer'])
    else:
        n = item['objects'][0]
        res['gt_program'] = 100.0 * mra(runs(cats[n]['visible']), item['answer'])
        res['constant'] = 100.0 * mra(consts[1], item['answer'])
    vecs = {n: arm_logits.get((item['capture'], n)) for n in item['objects']}
    if all(v is not None for v in vecs.values()):
        X = np.stack([vecs[n] for n in item['objects']])
        hf, hexp = head.first(X)
        if item['type'] == 'obj_appearance_order':
            names = item['objects']
            res['head'] = 100.0 * (answer_order(item, dict(zip(names, hf)), dict(zip(names, hexp)))[0] == item['answer'])
            for key, t in (('thr0', 0.0), ('thrfit', tau)):
                f = dict(zip(names, first_above(X, t)))
                res[key] = 100.0 * (answer_order(item, f, {n: -float(vecs[n].sum()) for n in names})[0] == item['answer'])
        else:
            res['head'] = 100.0 * mra(runs(head.presence(X)[0] >= 0.5), item['answer'])
            res['thr0'] = 100.0 * mra(runs(X[0] > 0), item['answer'])
            res['thrfit'] = 100.0 * mra(runs(X[0] > tau), item['answer'])
    d = direct.get(item['id'])
    if d is not None:
        res['direct'] = 100.0 * float(d['score'])
    return res


def cv_arm(caps, logits, folds=5):
    keys, X, Y, _ = pair_table(caps, logits, 'train')
    if not keys:
        return None
    rooms = sorted({caps[k[0]]['room'] for k in keys})
    fold_of = {r: int(hashlib.sha256(r.encode()).hexdigest(), 16) % folds for r in rooms}
    accs = []
    for f in range(folds):
        tr = [i for i, k in enumerate(keys) if fold_of[caps[k[0]]['room']] != f]
        te = [i for i, k in enumerate(keys) if fold_of[caps[k[0]]['room']] == f]
        if not tr or not te:
            continue
        h = Head().fit(X[tr], [Y[i] for i in tr])
        m = fs_metrics(h.first(X[te])[0], [Y[i] for i in te])
        if m:
            accs.append(m['exact'])
    return float(np.mean(accs)) if accs else None


def run(a):
    caps = load_captures(a.prep)
    items = load_items(a.prep)
    logits, timing = load_logits(a.journals, caps)
    direct = load_direct(a.direct)
    report = dict(inputs=dict(prep=a.prep, journals=a.journals, direct=a.direct,
                              code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                              pairs={arm: len(v) for arm, v in logits.items()}, direct_rows=len(direct)),
                  arms={}, items={})
    consts = constant_answers([i for i in items if i['split'] == 'train'])
    report['constant'] = dict(letter=consts[0], count=consts[1])
    cv = {arm: cv_arm(caps, logits[arm]) for arm in ARMS if logits[arm]}
    report['cv_train_exact'] = cv
    primary = max(cv, key=lambda k: (cv[k] if cv[k] is not None else -1, k == 'I')) if cv else None
    report['primary_arm'] = primary
    heads = {}
    for arm in ARMS:
        if not logits[arm]:
            continue
        _, Xtr, Ytr, Vtr = pair_table(caps, logits[arm], 'train')
        _, Xho, Yho, Vho = pair_table(caps, logits[arm], 'heldout')
        h = Head().fit(Xtr, Ytr).fit_presence(Xtr, Vtr); tau = fit_tau(Xtr, Ytr)
        heads[arm] = (h, tau)
        report['arms'][arm] = dict(head_params=[round(float(v), 6) for v in h.params],
                                   presence_params=[round(float(v), 6) for v in h.pparams], train_nll=h.train_nll, tau=tau,
                                   train_pairs=len(Ytr), heldout_pairs=len(Yho),
                                   frame_auroc_train=auroc(Xtr, Vtr), frame_auroc_heldout=auroc(Xho, Vho) if len(Yho) else None)
        if a.read_heldout and len(Yho):
            report['arms'][arm]['first_seen_heldout'] = {
                'head': fs_metrics(h.first(Xho)[0], Yho), 'thr0': fs_metrics(first_above(Xho, 0.0), Yho),
                'thrfit': fs_metrics(first_above(Xho, tau), Yho)}
        report['arms'][arm]['first_seen_train'] = {'head': fs_metrics(h.first(Xtr)[0], Ytr),
                                                   'thr0': fs_metrics(first_above(Xtr, 0.0), Ytr)}
    split = 'heldout' if a.read_heldout else 'train'
    per_item = []
    for it in items:
        if it['split'] != split:
            continue
        row = dict(id=it['id'], type=it['type'], room=it['room'], answer=it['answer'])
        for arm, (h, tau) in heads.items():
            for k, v in item_scores(it, caps, logits[arm], h, tau, consts, direct).items():
                row[k if k in ('gt_program', 'constant', 'direct') else f'{arm}:{k}'] = v
        if not heads:
            row.update(item_scores(it, caps, {}, None, 0.0, consts, direct))
        per_item.append(row)
    report['split_priced'] = split
    summary = {}
    for t in ('obj_appearance_order', 'object_counting'):
        rows = [r for r in per_item if r['type'] == t]
        methods = sorted({k for r in rows for k in r if k not in ('id', 'type', 'room', 'answer')})
        summary[t] = {m: dict(n=sum(m in r for r in rows), mean=float(np.mean([r[m] for r in rows if m in r])))
                      for m in methods if any(m in r for r in rows)}
        if primary and 'direct' in methods and f'{primary}:head' in methods:
            both = [r for r in rows if 'direct' in r and f'{primary}:head' in r]
            if both:
                mean, lo, hi = cluster_boot([r['room'] for r in both], [r[f'{primary}:head'] - r['direct'] for r in both])
                summary[t]['primary_head_minus_direct'] = dict(n=len(both), mean=mean, lo=lo, hi=hi,
                                                               rooms=len({r['room'] for r in both}))
    report['summary'] = summary
    ao = summary.get('obj_appearance_order', {}).get('primary_head_minus_direct')
    report['decision'] = None if not ao else dict(
        rule='head-path minority iff primary head beats direct by >= 10 task points with paired 95% interval above zero',
        head_path=bool(ao['mean'] >= 10 and ao['lo'] > 0), **ao)
    report['timing'] = summarize_timing(timing)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    with open(Path(a.out).with_suffix('.items.jsonl'), 'w') as f:
        for r in per_item:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    return report


def summarize_timing(timing):
    out = {}
    for key in ('V', 'IY'):
        rows = [t[key] for t in timing.values() if key in t]
        if rows:
            out[key] = dict(captures=len(rows), seconds=float(sum(r['seconds'] for r in rows)),
                            queries=int(sum(r['queries'] for r in rows)),
                            seconds_per_query=float(sum(r['seconds'] for r in rows) / max(1, sum(r['queries'] for r in rows))))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--prep', default=str(LANE / 'out/prep'))
    ap.add_argument('--journals', default=str(LANE / 'out/journals'))
    ap.add_argument('--direct', default=str(LANE / 'out/direct/journal.jsonl'))
    ap.add_argument('--out', default=str(LANE / 'out/analysis/ANALYSIS_train.json'))
    ap.add_argument('--read-heldout', action='store_true', help='price held-out items (only after the second reader signs off)')
    r = run(ap.parse_args())
    print(json.dumps(dict(primary=r['primary_arm'], cv=r['cv_train_exact'], summary=r['summary'], decision=r['decision'])))
