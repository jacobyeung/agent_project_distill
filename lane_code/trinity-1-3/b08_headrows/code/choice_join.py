"""b08_headrows Part A: per-item choice join (head path vs direct) on dev-S1 and the cue study.

Inputs (all node-local on trinity-1-3):
  --items     kit ITEMS.jsonl (dev-S1, 6161 rows)
  --program   PER_ITEM.jsonl from price_cues.py (arms predicted, predicted_vcd)
  --cues      directory holding <scene>.cues.json from price_cues.py
  --direct    NAME=report.json (evalx report with rows[key,scores.released_answer]); repeatable
  --raw       NAME=budget meta jsonl with raw_answer per source_key (for program/direct agreement); optional
  --out       output prefix
Scores: the kit's task score (MRA for numeric, exact for options/counts). Program no-answer scores 0.
Bootstrap: physical room, 10,000 draws, seed 20261116, percentile.
Cue model: L2 logistic (numpy), room-grouped 5-fold cross-fit; target = head path strictly better than direct.
"""
import argparse, json, collections, hashlib, math
from pathlib import Path
import numpy as np

TYPES = ['object_counting', 'object_size_estimation', 'object_rel_distance', 'object_rel_direction_easy',
         'object_rel_direction_medium', 'object_rel_direction_hard', 'object_abs_distance', 'room_size_estimation']
VSI_TASK = {'object_counting': 'count', 'object_size_estimation': 'size', 'object_rel_distance': 'reldist',
            'object_rel_direction_easy': 'dir', 'object_rel_direction_medium': 'dir', 'object_rel_direction_hard': 'dir',
            'object_abs_distance': 'absdist', 'room_size_estimation': 'room'}
SEED = 20261116


def rows(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def boot(groups, stat, draws=10000, seed=SEED):
    """groups: dict room -> list of item dicts; stat: fn(list of items) -> float."""
    keys = sorted(groups)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(draws):
        ix = rng.integers(0, len(keys), len(keys))
        its = [it for i in ix for it in groups[keys[i]]]
        vals.append(stat(its))
    lo, hi = np.quantile(vals, [.025, .975])
    return float(lo), float(hi)


def m(xs):
    return float(np.mean(xs)) if len(xs) else float('nan')


def fixed_forms(its):
    return dict(direct=m([i['direct'] for i in its]), program=m([i['program'] for i in its]),
                fallback=m([i['fallback'] for i in its]), best=m([i['best'] for i in its]))


def gap(its):
    f = fixed_forms(its)
    return f['best'] - max(f['direct'], f['program'], f['fallback'])


def auroc(score, y):
    score = np.asarray(score, float); y = np.asarray(y, int)
    ok = np.isfinite(score)
    score, y = score[ok], y[ok]
    P, N = (y == 1).sum(), (y == 0).sum()
    if P == 0 or N == 0:
        return float('nan')
    order = np.argsort(score, kind='mergesort')
    s = score[order]; r = np.empty(len(s)); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        r[i:j + 1] = (i + j) / 2 + 1; i = j + 1
    ranks = np.empty(len(s)); ranks[order] = r
    return float((ranks[y == 1].sum() - P * (P + 1) / 2) / (P * N))


def auroc_ci(score, y, rooms, draws=2000, seed=SEED):
    score = np.asarray(score, float); y = np.asarray(y, int); rooms = np.asarray(rooms)
    keys = sorted(set(rooms)); idx = {k: np.where(rooms == k)[0] for k in keys}
    rng = np.random.default_rng(seed); vals = []
    for _ in range(draws):
        ii = np.concatenate([idx[keys[k]] for k in rng.integers(0, len(keys), len(keys))])
        a = auroc(score[ii], y[ii])
        if np.isfinite(a):
            vals.append(a)
    if not vals:
        return float('nan'), float('nan')
    lo, hi = np.quantile(vals, [.025, .975]); return float(lo), float(hi)


def fit_logistic(X, y, l2=1.0, iters=500):
    mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1
    Z = np.c_[(X - mu) / sd, np.ones(len(X))]
    w = np.zeros(Z.shape[1])
    for _ in range(iters):  # Newton steps
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (p - y) + l2 * np.r_[w[:-1], 0]
        H = (Z * (p * (1 - p))[:, None]).T @ Z + l2 * np.diag(np.r_[np.ones(len(w) - 1), 0]) + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-8:
            break
    return dict(mu=mu, sd=sd, w=w)


def predict(model, X):
    Z = np.c_[(X - model['mu']) / model['sd'], np.ones(len(X))]
    return 1 / (1 + np.exp(-np.clip(Z @ model['w'], -30, 30)))


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def item_cues(it, prog, vcd, cues, raw544):
    """Features a response could print (status, views, mask area, selector confidence, ambiguity, spread),
    plus two agreement cues. Missing operand features -> neutral fill with an indicator."""
    f = {}
    f['status_no_answer'] = float(prog['no_answer'])
    ops = it.get('operands') or []
    counting = it['question_type'] == 'object_counting'
    feats = cues.get('features', {})
    views, areas, ps, nsel, spread, margin, ncand = [], [], [], [], [], [], []
    for n in ops:
        fe = feats.get(n.lower())
        if not fe:
            continue
        fe = fe['count' if counting else 'unique']
        ncand.append(fe['n_candidates']); nsel.append(fe['n_selected'])
        for inst in fe['instances']:
            views.append(inst['frames'])
            if inst['area_px']:
                areas.append(float(np.mean(inst['area_px'])))
        for s in fe['selected']:
            if s['p'] is not None: ps.append(s['p'])
            if s['member_spread_m'] is not None: spread.append(s['member_spread_m'])
        if fe['selected'] and fe['p_top_unselected'] is not None:
            margin.append(min(s['p'] for s in fe['selected'] if s['p'] is not None) - fe['p_top_unselected'])
    f['has_features'] = float(bool(views))
    f['min_views'] = float(min(views)) if views else 0.
    f['log_min_area'] = float(np.log1p(min(areas))) if areas else 0.
    f['min_selector_p'] = float(min(ps)) if ps else 0.
    f['max_spread_m'] = float(max(spread)) if spread else 0.
    f['min_margin'] = float(min(margin)) if margin else 0.
    f['n_selected_total'] = float(sum(nsel)) if nsel else 0.
    f['n_candidates_total'] = float(sum(ncand)) if ncand else 0.
    # two geometry calls (G3T vs VCD lifting of the same masks): agreement
    a, b = prog.get('pred'), vcd.get('pred') if vcd else None
    if a is None or b is None:
        f['two_call_disagree'] = 1.0 if (a is None) != (b is None) else 0.0
    elif num(a) is not None and num(b) is not None and not isinstance(a, str):
        f['two_call_disagree'] = float(abs(num(a) - num(b)) / max(abs(num(a)), abs(num(b)), 1e-6))
    else:
        f['two_call_disagree'] = float(str(a) != str(b))
    # program vs the model's own direct answer (step 544 raw answer)
    d = raw544.get(it['qid']) if raw544 else None
    if a is None or d is None:
        f['prog_direct_disagree'] = 1.0
    elif num(a) is not None and num(d) is not None and not isinstance(a, str):
        f['prog_direct_disagree'] = float(min(abs(num(a) - num(d)) / max(abs(num(d)), 1e-6), 5.0))
    else:
        f['prog_direct_disagree'] = float(str(a).strip().upper()[:1] != str(d).strip().upper()[:1])
    return f


# direction in which each single cue is expected to signal "head path better" (fixed in advance)
CUE_SIGN = {'status_no_answer': -1, 'min_views': +1, 'log_min_area': +1, 'min_selector_p': +1, 'max_spread_m': -1,
            'min_margin': +1, 'n_selected_total': -1, 'n_candidates_total': -1, 'two_call_disagree': -1,
            'prog_direct_disagree': +1, 'has_features': +1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--items', required=True); ap.add_argument('--program', required=True)
    ap.add_argument('--cues', required=True); ap.add_argument('--direct', action='append', required=True)
    ap.add_argument('--raw'); ap.add_argument('--out', required=True); ap.add_argument('--cue-arm', default='step544')
    a = ap.parse_args()
    items = {r['qid']: r for r in rows(a.items)}
    prog = {}; vcd = {}
    for r in rows(a.program):
        if r['arm'] == 'predicted': prog[r['qid']] = r
        elif r['arm'] == 'predicted_vcd': vcd[r['qid']] = r
    cues = {}
    for p in Path(a.cues).glob('*/*.cues.json'):
        c = json.loads(p.read_text()); cues[c['scene']] = c
    raw544 = {}
    if a.raw:
        for r in rows(a.raw):
            raw544[r['source_key'].removeprefix('devrows:')] = r.get('raw_answer')
    out = {}
    tables = {}
    per_item = {}
    for spec in a.direct:
        name, path = spec.split('=', 1)
        rep = json.loads(Path(path).read_text())
        d = {r['key'].removeprefix('devrows:'): r for r in rep['rows']}
        its_by_type = collections.defaultdict(list)
        for qid, dr in d.items():
            it = items.get(qid)
            if not it or it['stratum'] != 'primary' or it['question_type'] not in TYPES:
                continue
            pr = prog[qid]
            if pr['score'] is None:
                raise ValueError('unscored program row ' + qid)
            x = float(dr['scores']['released_answer']); y = float(pr['score'])
            rec = dict(qid=qid, room=it['room'], type=it['question_type'], dataset=it['dataset'], direct=x, program=y,
                       no_answer=bool(pr['no_answer']), fallback=x if pr['no_answer'] else y, best=max(x, y),
                       direct_unanswered=bool(dr.get('unanswered')))
            its_by_type[it['question_type']].append(rec)
        tab = []
        for t in TYPES:
            its = its_by_type[t]
            groups = collections.defaultdict(list)
            for i in its: groups[i['room']].append(i)
            f = fixed_forms(its)
            row = dict(type=t, items=len(its), rooms=len(groups), no_answer=sum(i['no_answer'] for i in its))
            for k in ['direct', 'program', 'fallback', 'best']:
                lo, hi = boot(groups, lambda xs, k=k: m([i[k] for i in xs]))
                row[k] = 100 * f[k]; row[k + '_ci'] = [100 * lo, 100 * hi]
            better = max(('direct', 'program', 'fallback'), key=lambda k: f[k])
            row['better_fixed'] = better
            row['best_minus_better_fixed'] = 100 * gap(its)
            lo, hi = boot(groups, gap); row['best_minus_better_fixed_ci'] = [100 * lo, 100 * hi]
            row['best_minus_direct'] = 100 * (f['best'] - f['direct'])
            row['fallback_minus_direct'] = 100 * (f['fallback'] - f['direct'])
            lo, hi = boot(groups, lambda xs: m([i['fallback'] - i['direct'] for i in xs]))
            row['fallback_minus_direct_ci'] = [100 * lo, 100 * hi]
            row['head_wins'] = sum(i['program'] > i['direct'] for i in its)
            row['direct_wins'] = sum(i['program'] < i['direct'] for i in its)
            row['mix_worth_by_gap'] = row['best_minus_better_fixed'] >= 5.0
            tab.append(row)
        tables[name] = tab
        per_item[name] = [i for t in TYPES for i in its_by_type[t]]
    out['tables'] = tables

    # VSI points: a task point is 1/8 VSI point; direction task = mean of easy/medium/hard
    vsi = {}
    for name, tab in tables.items():
        by = {r['type']: r for r in tab}
        def task(k, key):
            ts = [t for t in TYPES if VSI_TASK[t] == k]
            return float(np.mean([by[t][key] for t in ts]))
        res = {}
        for k in ['count', 'size', 'reldist', 'dir']:
            res[k] = dict(best_minus_direct=task(k, 'best_minus_direct'), best_minus_better_fixed=task(k, 'best_minus_better_fixed'))
        res['vsi_points_best_minus_direct_4tasks'] = sum(v['best_minus_direct'] for v in res.values()) / 8
        res['vsi_points_best_minus_better_fixed_4tasks'] = sum(v['best_minus_better_fixed'] for k2, v in res.items() if isinstance(v, dict)) / 8
        vsi[name] = res
    out['vsi_points'] = vsi

    # ---------------- cue study on the chosen direct arm ----------------
    arm = a.cue_arm
    its = [i for i in per_item[arm] if i['type'] not in ('object_abs_distance', 'room_size_estimation')]
    F = []
    for i in its:
        it = items[i['qid']]
        F.append(item_cues(it, prog[i['qid']], vcd.get(i['qid']), cues.get(it['scene'], {}), raw544))
    names = sorted(F[0])
    X = np.array([[f[k] for k in names] for f in F], float)
    y = np.array([int(i['program'] > i['direct']) for i in its])
    rooms = np.array([i['room'] for i in its]); types = np.array([i['type'] for i in its])
    single = {}
    for t in sorted(set(types)) + ['ALL']:
        sel = np.ones(len(its), bool) if t == 'ALL' else types == t
        single[t] = {}
        for j, k in enumerate(names):
            s = CUE_SIGN.get(k, 1) * X[sel, j]
            au = auroc(s, y[sel]); lo, hi = auroc_ci(s, y[sel], rooms[sel])
            ans = sel & (X[:, names.index('status_no_answer')] == 0)
            au2 = auroc(CUE_SIGN.get(k, 1) * X[ans, j], y[ans])
            dis = sel & (X[:, names.index('prog_direct_disagree')] > 0)
            au3 = auroc(CUE_SIGN.get(k, 1) * X[dis, j], y[dis])
            single[t][k] = dict(auroc=au, ci=[lo, hi], answered_auroc=au2, disagree_auroc=au3, n=int(sel.sum()), positives=int(y[sel].sum()), n_disagree=int(dis.sum()))
    out['single_cue_auroc'] = single

    # room-grouped 5-fold cross-fit, pooled model with type one-hots
    tnames = sorted(set(types))
    T1 = np.array([[float(t == u) for u in tnames] for t in types])
    variants = {'status_only': ['status_no_answer'],
                'printed': [k for k in names if k not in ('prog_direct_disagree', 'two_call_disagree')],
                'printed+two_call': [k for k in names if k != 'prog_direct_disagree'],
                'all': names}
    ukeys = sorted(set(rooms))
    fold_of = {r: int(hashlib.sha256((r + str(SEED)).encode()).hexdigest(), 16) % 5 for r in ukeys}
    folds = np.array([fold_of[r] for r in rooms])
    cv = {}
    for vname, cols in variants.items():
        Xv = np.c_[X[:, [names.index(c) for c in cols]], T1]
        p = np.zeros(len(its)); choose = np.zeros(len(its), bool)
        sc_h = np.array([i['fallback'] for i in its]); sc_d = np.array([i['direct'] for i in its])
        for k in range(5):
            tr, te = folds != k, folds == k
            mdl = fit_logistic(Xv[tr], y[tr]); p[te] = predict(mdl, Xv[te]); ptr = predict(mdl, Xv[tr])
            # per-type threshold chosen on the training folds only: maximise training policy score
            for t in tnames:
                a_tr = tr & (types == t); a_te = te & (types == t)
                cands = np.r_[np.inf, np.unique(ptr[types[tr] == t]), -np.inf]
                best_th, best_v = np.inf, -1
                for th in cands:
                    ch = ptr[types[tr] == t] >= th
                    v = np.where(ch, sc_h[a_tr], sc_d[a_tr]).mean() if a_tr.any() else 0
                    if v > best_v + 1e-12: best_v, best_th = v, th
                choose[a_te] = p[a_te] >= best_th
        res = {}
        for t in tnames + ['ALL']:
            sel = np.ones(len(its), bool) if t == 'ALL' else types == t
            lo, hi = auroc_ci(p[sel], y[sel], rooms[sel])
            choose_head = choose[sel]
            sub = [its[i] for i in np.where(sel)[0]]
            dis = sel & (X[:, names.index('prog_direct_disagree')] > 0)
            au_dis = auroc(p[dis], y[dis])
            pol = m([s['program'] if ch else s['direct'] for s, ch in zip(sub, choose_head)])
            pol_fb = m([(s['fallback'] if ch else s['direct']) for s, ch in zip(sub, choose_head)])
            f = fixed_forms(sub); bf = max(f['direct'], f['program'], f['fallback'])
            res[t] = dict(auroc=auroc(p[sel], y[sel]), ci=[lo, hi], auroc_disagree_only=au_dis, n_disagree=int(dis.sum()), pos_disagree=int(y[dis].sum()), policy=100 * pol, policy_fallback=100 * pol_fb,
                          better_fixed=100 * bf, best=100 * f['best'],
                          share_of_gap=(max(pol, pol_fb) - bf) / (f['best'] - bf) if f['best'] > bf else float('nan'),
                          head_chosen=int(choose_head.sum()), n=int(sel.sum()))
        cv[vname] = res
    out['crossfit'] = cv
    out['cue_names'] = names
    out['cue_arm'] = arm
    Path(a.out + '.json').write_text(json.dumps(out, indent=1, allow_nan=True))
    with open(a.out + '.per_item.jsonl', 'w') as fh:
        for name, pis in per_item.items():
            for i in pis:
                fh.write(json.dumps(dict(arm=name, **i)) + '\n')
        for i, f, yy in zip(its, F, y):
            fh.write(json.dumps(dict(arm='cues_' + arm, qid=i['qid'], room=i['room'], type=i['type'], head_better=int(yy), **f)) + '\n')
    print('wrote', a.out)


if __name__ == '__main__':
    main()
