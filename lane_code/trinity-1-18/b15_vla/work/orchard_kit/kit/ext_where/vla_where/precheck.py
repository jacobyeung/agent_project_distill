"""Pre-checks P-1..P-5 (design 4.4, pre-registered) on demonstration replays, every 8th frame. GT is used only for
measurement: the provider under test never reads it (the GTStore feeds only the reference provider and the metrics).

  P-1  the selected agentview instance is the GT target (mask IoU >= 0.5) on >= 85% of frames where the target is
       visible in the agentview (>= 20 GT pixels);
  P-2  median ||X_wrist - X_wrist^GT|| <= 0.03 m over metric records (target and place), GT by the same lift
       definition from GT mask, depth and pose (the `reference` provider);
  P-3  wrist-view presence AUROC >= 0.90 (both entities; labels = GT visibility); otherwise presence.source sam3 and
       P-3 re-runs;
  P-4  s / s_GT in [0.8, 1.25] on >= 75% of frames with a scale, and >= 70% of frames with t >= 8 carry a scale;
       s_GT = median of GT depth / G3T depth over view 0's confident pixels;
  P-5  T-11 passes (read from its result JSON).
tau: refit on training-demo frames as the lowest threshold whose yes-rate on absent views is <= 10% (both views).
"""
import json
import math

import numpy as np

from .types import ROLES

RULES = dict(P1_iou=0.5, P1_rate=0.85, P2_median_m=0.03, P3_auroc=0.90, P4_band=(0.8, 1.25), P4_in_band=0.75,
             P4_coverage=0.70, P4_after=8, tau_false_yes=0.10, visible_px=20, stride=8)


def auroc(scores, labels):
    s, y = np.asarray(scores, dtype=np.float64), np.asarray(labels, dtype=bool)
    if y.all() or not y.any():
        return None
    order = np.argsort(s, kind='mergesort')
    ranks = np.empty(len(s))
    ss = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n1, n0 = y.sum(), (~y).sum()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def refit_tau(scores, labels, max_false_yes=RULES['tau_false_yes']):
    """Lowest threshold (among the observed scores and 1.0) whose yes-rate on absent items is <= max_false_yes."""
    s, y = np.asarray(scores, dtype=np.float64), np.asarray(labels, dtype=bool)
    absent = s[~y]
    if not absent.size:
        return None
    for tau in np.unique(np.concatenate([s, [1.0 + 1e-12]])):
        if (absent >= tau).mean() <= max_false_yes:
            return float(tau)
    return None


def iou(a, b):
    if a is None or b is None:
        return 0.0
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 0.0


def presence_pass(provider, episodes, stride=RULES['stride']):
    """(scores, labels) of P(yes) over both views and entities at every stride-th frame (for the tau refit)."""
    scores, labels = [], []
    for ep, store, _ in episodes:
        for t in range(0, len(ep), stride):
            step = provider.table.step(ep.instruction)
            for role in ROLES:
                phrase = getattr(step, role)
                if phrase is None:
                    continue
                for view, image in (('agent', ep.agent[t]), ('wrist', ep.wrist[t])):
                    m = store.mask((view, t), phrase.phrase)
                    scores.append(provider.presence.p_yes(image, phrase.phrase, (view, t)))
                    labels.append(bool(m is not None and m.sum() >= RULES['visible_px']))
    return scores, labels


def evaluate(provider, reference, episodes, stride=RULES['stride'], t11=None):
    """episodes: iterable of (Episode, GTStore bound to it, episode id). reference: build_provider('reference', store=
    the same store). Returns (rows, summary)."""
    rows = []
    for ep, store, name in episodes:
        for t in range(0, len(ep), stride):
            obs = ep.observation(t, provider.cfg.history_offsets)
            out = provider.where(obs)
            trace = provider.last_trace
            ref = reference.where(obs)
            geo = trace['geometry']
            g_depth = np.asarray(store.view(('wrist', t))['depth'], dtype=np.float64)
            m_depth, conf = geo.depth[0], geo.conf[0] if geo.conf is not None else None
            ok = np.isfinite(g_depth) & np.isfinite(m_depth) & (g_depth > 0) & (m_depth > 0)
            if conf is not None:
                ok &= conf > np.median(conf[np.isfinite(conf)])
            s_gt = float(np.median(g_depth[ok] / m_depth[ok])) if ok.any() else None
            row = dict(episode=name, t=t, scale=out.meta['scale'], scale_gt=s_gt, line=out.line)
            step = provider.table.step(ep.instruction)
            for role in ROLES:
                phrase = getattr(step, role)
                if phrase is None:
                    continue
                e, r = out.by_role(role), ref.by_role(role)
                tr = trace['traces'][role]
                gt_agent = store.mask(('agent', t), phrase.phrase)
                vis = {v: bool(m is not None and m.sum() >= RULES['visible_px']) for v, m in
                       (('agent', gt_agent), ('wrist', store.mask(('wrist', t), phrase.phrase)))}
                err = (float(np.linalg.norm(np.subtract(e.X_wrist, r.X_wrist))) if e.metric and r.metric else None)
                row[role] = dict(reason=e.reason, ref_reason=r.reason, visible=vis,
                                 agent_iou=iou(tr['agent'].mask, gt_agent),
                                 p_yes={v: tr[v].p_yes for v in ('agent', 'wrist')}, error_m=err)
            rows.append(row)
    return rows, summarize(rows, t11)


def summarize(rows, t11=None):
    tgt = [r['target'] for r in rows if 'target' in r]
    p1_rows = [x for x in tgt if x['visible']['agent']]
    p1 = float(np.mean([x['agent_iou'] >= RULES['P1_iou'] for x in p1_rows])) if p1_rows else None
    errs = [r[role]['error_m'] for r in rows for role in ROLES if role in r and r[role]['error_m'] is not None]
    p2 = float(np.median(errs)) if errs else None
    w_scores = [r[role]['p_yes']['wrist'] for r in rows for role in ROLES if role in r]
    w_labels = [r[role]['visible']['wrist'] for r in rows for role in ROLES if role in r]
    p3 = auroc(w_scores, w_labels)
    with_scale = [r for r in rows if r['scale'] is not None and r['scale_gt']]
    lo, hi = RULES['P4_band']
    in_band = float(np.mean([lo <= r['scale'] / r['scale_gt'] <= hi for r in with_scale])) if with_scale else None
    late = [r for r in rows if r['t'] >= RULES['P4_after']]
    coverage = float(np.mean([r['scale'] is not None for r in late])) if late else None
    t11_pass = None if t11 is None else bool(t11.get('pass'))
    verdict = dict(
        P1=p1 is not None and p1 >= RULES['P1_rate'],
        P2=p2 is not None and p2 <= RULES['P2_median_m'],
        P3=p3 is not None and p3 >= RULES['P3_auroc'],
        P4=(in_band is not None and in_band >= RULES['P4_in_band'] and coverage is not None
            and coverage >= RULES['P4_coverage']),
        P5=t11_pass)
    verdict['PASS'] = all(v is True for v in verdict.values())
    reasons = {}
    for x in tgt:
        reasons[x['reason']] = reasons.get(x['reason'], 0) + 1
    return dict(rules=RULES, frames=len(rows), P1=dict(rate=p1, n=len(p1_rows)), P2=dict(median_m=p2, n=len(errs)),
                P3=dict(auroc=p3, n=len(w_scores)), P4=dict(in_band=in_band, n=len(with_scale), coverage=coverage,
                                                          n_late=len(late)),
                P5=dict(t11=t11), target_reasons=reasons, verdict=verdict)


def _f(x, nd=3):
    return 'n/a' if x is None or (isinstance(x, float) and not math.isfinite(x)) else f'{x:.{nd}f}'


def report(summary, label='', tau=None):
    s, v, R = summary, summary['verdict'], RULES
    word = lambda b: 'PASS' if b is True else ('NOT RUN' if b is None else 'FAIL')
    lines = [f'PRECHECK {label} frames={s["frames"]} tau={_f(tau, 3)}',
             f'P-1 agent instance = GT target (IoU >= {R["P1_iou"]}): {_f(s["P1"]["rate"])} (n={s["P1"]["n"]}) '
             f'rule >= {R["P1_rate"]} -> {word(v["P1"])}',
             f'P-2 median |X_wrist - X_wrist_GT|: {_f(s["P2"]["median_m"], 4)} m (n={s["P2"]["n"]}) rule <= '
             f'{R["P2_median_m"]} -> {word(v["P2"])}',
             f'P-3 wrist presence AUROC: {_f(s["P3"]["auroc"])} (n={s["P3"]["n"]}) rule >= {R["P3_auroc"]} -> '
             f'{word(v["P3"])}',
             f'P-4 s/s_GT in {list(R["P4_band"])}: {_f(s["P4"]["in_band"])} (n={s["P4"]["n"]}) rule >= '
             f'{R["P4_in_band"]}; scale coverage t >= {R["P4_after"]}: {_f(s["P4"]["coverage"])} (n={s["P4"]["n_late"]}) '
             f'rule >= {R["P4_coverage"]} -> {word(v["P4"])}',
             f'P-5 T-11: {word(v["P5"])}',
             f'target reasons: {s["target_reasons"]}',
             f'VERDICT U1 pre-checks: {"PASS" if v["PASS"] else "FAIL or incomplete"} (PASS = P-1..P-5 all pass)']
    return '\n'.join(lines)


def dump(path, rows, summary):
    with open(path, 'w') as f:
        f.write(json.dumps(dict(summary=summary), sort_keys=True, default=str) + '\n')
        for r in rows:
            f.write(json.dumps(r, sort_keys=True, default=str) + '\n')
