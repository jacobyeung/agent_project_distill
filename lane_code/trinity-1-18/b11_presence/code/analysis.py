"""Presence probe analysis (CPU): first-seen read-outs fitted on K1 train, pricing on K1 held-out.

Read-outs over one (capture, object) vector of 32 presence logits x_1..x_32:
  head    learned temporal head (weights only, no external threshold): per-frame hazard
          p_k = sigmoid(conv1d_5(x)_k + w_pos * k/32 + b), P(first = k) = p_k prod_{j<k}(1 - p_j), P(never) = prod(1 - p_j);
          fitted by NLL of the GT first-seen frame on K1 train; prediction = argmax over {1..32, never}.
  thr0    first frame with logit > 0 (the model's own argmax token decides presence).
  thrfit  first frame with logit > tau, tau fitted on K1 train (reference only: a tuned threshold outside weights).
Pricing on K1 held-out items:
  appearance order: sort the 4 objects by predicted first-seen (ties: expected first-seen under the head, else minus the
                    logit sum, then name); answer = the option equal to that order; no equal option = wrong (no answer).
                    Secondary (reported, not decisive): head_optlik = option with the highest sum of log P(a before b)
                    under the head's first-seen distributions.
  counting: number of maximal runs of predicted-present frames (head: p_k >= 0.5 of a per-frame presence head of the
            same conv form fitted by BCE on GT visibility of K1 train,
            thr0: logit > 0); scored with the official MRA.
  gt program: the same rules on GT visibility (ceiling sanity); constant: best single answer on K1 train.
  direct: step-544 direct journal (direct.py), when present.
Paired differences: room-cluster bootstrap (10,000 draws, seed 0), 95% percentile interval.
Primary arm (pre-registered): chosen by room-grouped 5-fold CV on K1 train only (mean first-seen exact accuracy of head).
Two phases. `fit` (default) reads train captures' journals only and writes FROZEN.json (primary arm, all fitted weights,
tau, constants, input hashes). `price` (--read-heldout) reads FROZEN.json, never refits, reads held-out journals only,
and decides only when every held-out appearance-order item has primary-arm vectors for all 4 objects and a valid
B2048 direct score.
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


def jsonl_rows(path):
    """Rows of a jsonl file; a malformed final line is skipped (reported), a malformed interior line raises."""
    lines = Path(path).read_bytes().split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    rows, torn = [], False
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(lines) - 1:
                raise ValueError(f'malformed interior line {i + 1} in {path}')
            torn = True
    return rows, torn


def load_logits(journals, caps):
    """{arm: {(capture, obj): np.array[32]}} for complete vectors of the given captures only; timing; problems."""
    out = {a: {} for a in ARMS}
    timing, problems = {}, defaultdict(list)
    for sub in ('V', 'IY'):
        d = Path(journals) / sub
        if not d.is_dir():
            continue
        for cname in sorted(caps):
            p = d / (slug(cname) + '.jsonl')
            if not p.exists():
                problems['missing_file'].append(f'{sub}/{cname}')
                continue
            rows, torn = jsonl_rows(p)
            if torn or not rows or 'timing' not in rows[-1]:
                problems['incomplete_file'].append(f'{sub}/{cname}')
                continue
            acc = defaultdict(dict)
            for r in rows[:-1]:
                if r['capture'] != cname:
                    raise ValueError(f'row of {r["capture"]} in {p}')
                acc[(r['arm'], r['obj'])][r['frame']] = r['logit']
            timing.setdefault(cname, {}).update(rows[-1]['timing'])
            for (arm, obj), fr in acc.items():
                if sorted(fr) == list(range(1, 33)) and all(math.isfinite(v) for v in fr.values()):
                    out[arm][(cname, obj)] = np.array([fr[k] for k in range(1, 33)], dtype=np.float64)
                else:
                    problems['incomplete_vector'].append(f'{arm}/{cname}/{obj}')
    return out, timing, dict(problems)


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

    def frozen(self):
        return dict(head_params=[float(v) for v in self.params], presence_params=[float(v) for v in self.pparams])

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

    @classmethod
    def from_frozen(cls, d):
        torch = cls._torch()
        h = cls()
        h.params = torch.tensor(d['head_params'], dtype=torch.float64)
        h.pparams = torch.tensor(d['presence_params'], dtype=torch.float64)
        return h

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
def answer_order(item, first, tie):
    """Letter of the option equal to the sorted order, or None (counted wrong) when no option equals it."""
    order = sorted(item['objects'], key=lambda n: (first[n], tie[n], n))
    for L, o in zip('ABCD', item['option_orders']):
        if list(o) == order:
            return L, order
    return None, order


def answer_optlik(item, dists):
    """Option with the highest sum over ordered pairs of log P(first_a < first_b) (ties split) under the head."""
    def before(pa, pb):
        ca = np.cumsum(pb[::-1])[::-1]                      # P(first_b >= k)
        strictly = float(np.sum(pa[:-1] * ca[1:]))          # P(first_a = k, first_b > k)
        return strictly + 0.5 * float(np.sum(pa * pb))
    best = None
    for L, o in zip('ABCD', item['option_orders']):
        sc = sum(math.log(max(before(dists[o[i]], dists[o[j]]), 1e-12)) for i in range(len(o)) for j in range(i + 1, len(o)))
        if best is None or sc > best[0]:
            best = (sc, L)
    return best[1]


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


def load_direct(path, items, caps, model):
    """Complete direct rows that carry the binding direct.py computes for this item, checkpoint and frames, a B2048
    score in [0, 1] equal to the top-level score, and the direct cell name; rejected rows are counted by reason."""
    out, rejected = {}, defaultdict(int)
    if not (path and Path(path).is_file()):
        return out, dict(rejected)
    sys.path.insert(0, str(Path(__file__).parent))
    import direct as D
    ident = D.model_identity(model)
    want = {i['id']: D.binding_for(i, caps[i['capture']], ident) for i in items if i['capture'] in caps}
    rows, _ = jsonl_rows(path)
    for r in rows:
        if r.get('status') != 'complete':
            rejected['not_complete'] += 1; continue
        k = r.get('example_id')
        if k not in want:
            rejected['unknown_item'] += 1; continue
        if r.get('binding') != want[k] or r.get('cell') != D.CELL['name'] or r.get('prompt_shim') != D.SHIM:
            rejected['binding'] += 1; continue
        b = (r.get('B2048') or {}).get('score')
        if not (isinstance(b, (int, float)) and math.isfinite(b) and 0 <= b <= 1 and r.get('score') == b):
            rejected['score'] += 1; continue
        out[k] = r
    return out, dict(rejected)


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
            res['head_optlik'] = 100.0 * (answer_optlik(item, dict(zip(names, head.dist(X)))) == item['answer'])
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


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def price_items(items, caps, logits, heads, consts, direct):
    per_item = []
    for it in items:
        row = dict(id=it['id'], type=it['type'], room=it['room'], answer=it['answer'])
        if heads:
            for arm, (h, tau) in heads.items():
                for k, v in item_scores(it, caps, logits[arm], h, tau, consts, direct).items():
                    row[k if k in ('gt_program', 'constant', 'direct') else f'{arm}:{k}'] = v
        else:
            row.update(item_scores(it, caps, {}, None, 0.0, consts, direct))
        per_item.append(row)
    summary = {}
    for t in ('obj_appearance_order', 'object_counting'):
        rows = [r for r in per_item if r['type'] == t]
        methods = sorted({k for r in rows for k in r if k not in ('id', 'type', 'room', 'answer')})
        summary[t] = {m: dict(n=sum(m in r for r in rows), mean=float(np.mean([r[m] for r in rows if m in r])))
                      for m in methods}
    return per_item, summary


def fit_phase(a):
    caps_all = load_captures(a.prep)
    caps = {k: c for k, c in caps_all.items() if c['split'] == 'train'}
    items = [i for i in load_items(a.prep) if i['split'] == 'train']
    logits, timing, problems = load_logits(a.journals, caps)
    consts = constant_answers(items)
    cv = {arm: cv_arm(caps, logits[arm]) for arm in ARMS if logits[arm]}
    cv = {k: v for k, v in cv.items() if v is not None}
    primary = max(cv, key=lambda k: (cv[k], k == 'I')) if cv else None
    heads, arms = {}, {}
    for arm in ARMS:
        if not logits[arm]:
            continue
        _, Xtr, Ytr, Vtr = pair_table(caps, logits[arm], 'train')
        h = Head().fit(Xtr, Ytr).fit_presence(Xtr, Vtr); tau = fit_tau(Xtr, Ytr)
        heads[arm] = (h, tau)
        arms[arm] = dict(**h.frozen(), train_nll=h.train_nll, tau=tau, train_pairs=len(Ytr),
                         frame_auroc_train=auroc(Xtr, Vtr),
                         first_seen_train={'head': fs_metrics(h.first(Xtr)[0], Ytr),
                                           'thr0': fs_metrics(first_above(Xtr, 0.0), Ytr),
                                           'thrfit': fs_metrics(first_above(Xtr, tau), Ytr)})
    per_item, summary = price_items(items, caps, logits, heads, consts, {})
    frozen = dict(primary_arm=primary, cv_train_exact=cv, arms=arms, constant=dict(letter=consts[0], count=consts[1]),
                  code_sha256=sha_file(__file__), prep=dict(captures=sha_file(Path(a.prep) / 'CAPTURES.jsonl'),
                                                            items=sha_file(Path(a.prep) / 'ITEMS.jsonl')),
                  train_pairs={arm: len(v) for arm, v in logits.items()}, problems=problems,
                  frozen_utc=__import__('time').strftime('%Y-%m-%dT%H:%M:%SZ', __import__('time').gmtime()))
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / 'FROZEN.json').write_text(json.dumps(frozen, indent=1, sort_keys=True) + '\n')
    report = dict(phase='fit', frozen_sha256=sha_file(out / 'FROZEN.json'), summary_train=summary,
                  timing=summarize_timing(timing))
    (out / 'ANALYSIS_train.json').write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    with open(out / 'ANALYSIS_train.items.jsonl', 'w') as f:
        for r in per_item:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    return dict(primary=primary, cv=cv, summary=summary, problems={k: len(v) for k, v in problems.items()})


def price_phase(a):
    out = Path(a.out_dir)
    fz = json.loads((out / 'FROZEN.json').read_text())
    if fz['code_sha256'] != sha_file(__file__):
        raise SystemExit('analysis.py changed since FROZEN.json was written: refit first')
    if fz['prep'] != dict(captures=sha_file(Path(a.prep) / 'CAPTURES.jsonl'), items=sha_file(Path(a.prep) / 'ITEMS.jsonl')):
        raise SystemExit('prep files changed since FROZEN.json')
    caps = {k: c for k, c in load_captures(a.prep).items() if c['split'] == 'heldout'}
    items = [i for i in load_items(a.prep) if i['split'] == 'heldout']
    logits, timing, problems = load_logits(a.journals, caps)
    direct, rejected = load_direct(a.direct, items, caps, a.model)
    heads = {arm: (Head.from_frozen(d), d['tau']) for arm, d in fz['arms'].items()}
    lt, ln = fz['constant']['letter'], fz['constant']['count']
    arms = {}
    for arm, (h, tau) in heads.items():
        _, Xho, Yho, Vho = pair_table(caps, logits[arm], 'heldout')
        if not len(Yho):
            continue
        arms[arm] = dict(heldout_pairs=len(Yho), frame_auroc_heldout=auroc(Xho, Vho),
                         first_seen_heldout={'head': fs_metrics(h.first(Xho)[0], Yho),
                                             'thr0': fs_metrics(first_above(Xho, 0.0), Yho),
                                             'thrfit': fs_metrics(first_above(Xho, tau), Yho)})
    per_item, summary = price_items(items, caps, logits, heads, (lt, ln), direct)
    primary = fz['primary_arm']
    key = f'{primary}:head'
    decision = dict(rule='head-path minority iff primary head beats direct B2048 by >= 10 task points with paired 95% '
                         'room-cluster bootstrap interval above zero, on all held-out appearance-order items',
                    primary_arm=primary)
    for t in ('obj_appearance_order', 'object_counting'):
        rows = [r for r in per_item if r['type'] == t]
        both = [r for r in rows if 'direct' in r and key in r]
        if both:
            mean, lo, hi = cluster_boot([r['room'] for r in both], [r[key] - r['direct'] for r in both])
            summary[t]['primary_head_minus_direct'] = dict(n=len(both), of=len(rows), mean=mean, lo=lo, hi=hi,
                                                           rooms=len({r['room'] for r in both}))
    app = [r for r in per_item if r['type'] == 'obj_appearance_order']
    missing = [r['id'] for r in app if 'direct' not in r or key not in r]
    ao = summary['obj_appearance_order'].get('primary_head_minus_direct')
    if primary is None or missing or not ao or len(app) != 143:
        decision.update(status='incomplete', head_path=None, items=len(app), missing=len(missing), missing_ids=missing[:20])
    else:
        decision.update(status='decided', head_path=bool(ao['mean'] >= 10 and ao['lo'] > 0), **ao)
    report = dict(phase='price', frozen_sha256=sha_file(out / 'FROZEN.json'), frozen=dict(primary_arm=primary,
                  cv_train_exact=fz['cv_train_exact']), arms=arms, summary=summary, decision=decision,
                  heldout_pairs={arm: len(v) for arm, v in logits.items()}, direct_rows=len(direct),
                  direct_rejected=rejected,
                  problems={k: len(v) for k, v in problems.items()}, timing=summarize_timing(timing))
    (out / 'ANALYSIS_heldout.json').write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    with open(out / 'ANALYSIS_heldout.items.jsonl', 'w') as f:
        for r in per_item:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    return dict(summary=summary, decision=decision)


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
    ap.add_argument('--out-dir', default=str(LANE / 'out/analysis'))
    ap.add_argument('--model', default=str(LANE / 'work/model_m544'), help='checkpoint the direct rows must be bound to')
    ap.add_argument('--read-heldout', action='store_true', help='price held-out items from FROZEN.json (after review GO)')
    a = ap.parse_args()
    print(json.dumps(price_phase(a) if a.read_heldout else fit_phase(a)))
