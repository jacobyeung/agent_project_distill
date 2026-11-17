"""Recompute the K1 kill-rule marks (primary 296) with stored and half-extent-corrected labels.

Trust rule as registered (K1_RULES trust_relative_tolerance .15 plus mask match); fallback = runtime failure label,
independent of GT. The inferred rule must reproduce every stored decision label before corrected labels are used.
"""
import collections, glob, json, math, pathlib
import numpy as np

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
K = LANE / 'work/k1/orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296'
MAN = LANE / 'work/k1/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
LAB = LANE / 'work/k1audit/K1_LABELS_CORRECTED.jsonl'
TH = [.50, .55, .60, .65, .70, .75, .80, .85, .90, .95]


def mra(pred, gt):
    if pred is None or not math.isfinite(pred):
        return 0.0
    return sum(abs(pred - gt) / abs(gt) < 1 - t for t in TH) / 10


def constant(values):
    events = {}
    for g in values:
        for t in TH:
            lo, hi = g * t, g * (2 - t)
            events.setdefault(lo, [0, 0])[0] += 1; events.setdefault(hi, [0, 0])[1] += 1
    score = 0; best = -1; chosen = None
    for x, (s, e) in sorted(events.items()):
        score += s
        if score > best:
            best = score; chosen = x
        score -= e
    return chosen


def main():
    split = {}
    for c in json.load(open(MAN))['captures']:
        for r in c['rows']:
            split[r['id']] = (c['k1_split'], c['canonical'])
    L = {json.loads(l)['id']: json.loads(l) for l in open(LAB)}
    resp = []
    for f in sorted(glob.glob(str(K / 'render/*/responses.json'))):
        resp += json.load(open(f))
    rows = []
    agree = collections.Counter()
    for r in resp:
        if r['type'] != 'object_abs_distance':
            continue
        d = r['decision']; lab = L[r['id']]; mm = bool(r['mask_match'].get('ok'))
        val = d.get('value')
        pred = float(val) if val is not None and d['label'] != 'fallback' else None
        inferred = d['label'] if d['label'] == 'fallback' else ('trust' if (pred is not None and mm and abs(pred - lab['stored']) <= .15 * abs(lab['stored'])) else 'other')
        agree[(d['label'] if d['label'] in ('trust', 'fallback') else 'other') == inferred] += 1
        rows.append(dict(id=r['id'], split=split[r['id']][0], capture=split[r['id']][1], dataset=lab['dataset'], label=d['label'], reason=d.get('reason'),
                         pred=pred, mask_ok=mm, stored=lab['stored'], corrected=lab['corrected'], affected=lab['affected'], convention=lab['convention']))
    out = {'inferred_rule_reproduces_stored_labels': dict(agree), 'decision_labels': dict(collections.Counter(r['label'] for r in rows))}
    for variant in ['stored', 'corrected', 'drop_affected']:
        tr = [r for r in rows if r['split'] == 'train' and (variant != 'drop_affected' or not r['affected'])]
        te = [r for r in rows if r['split'] == 'heldout' and (variant != 'drop_affected' or not r['affected'])]
        g = (lambda r: r['corrected']) if variant == 'corrected' else (lambda r: r['stored'])
        tr = [r for r in tr if g(r) is not None]; te = [r for r in te if g(r) is not None]
        c = constant([g(r) for r in tr])
        lab = lambda r: 'fallback' if r['label'] == 'fallback' else ('trust' if (r['pred'] is not None and r['mask_ok'] and abs(r['pred'] - g(r)) <= .15 * abs(g(r))) else 'other')
        share = sum(lab(r) in ('trust', 'fallback') for r in te) / len(te)
        ans = [r for r in te if r['pred'] is not None]
        prog = float(np.mean([mra(r['pred'], g(r)) for r in ans])); base = float(np.mean([mra(c, g(r)) for r in ans]))
        within = sum(r['pred'] is not None and abs(r['pred'] - g(r)) <= .15 * g(r) for r in te)
        by_ds = {ds: dict(n=sum(r['dataset'] == ds for r in te), trust_fallback=sum(lab(r) in ('trust', 'fallback') for r in te if r['dataset'] == ds),
                          within15=sum(r['pred'] is not None and abs(r['pred'] - g(r)) <= .15 * g(r) for r in te if r['dataset'] == ds),
                          answered_mra=float(np.mean([mra(r['pred'], g(r)) for r in ans if r['dataset'] == ds])) if any(r['dataset'] == ds for r in ans) else None)
                 for ds in sorted({r['dataset'] for r in te})}
        out[variant] = dict(train_rows=len(tr), heldout_rows=len(te), train_constant_m=c, trust=sum(lab(r) == 'trust' for r in te),
                            fallback=sum(lab(r) == 'fallback' for r in te), trust_fallback_share=share, within15=within, answered=len(ans),
                            answered_mra=prog, constant_mra=base, gain=prog - base, kill_rows=share < .4 or prog - base < .10, by_dataset=by_ds)
        print(variant, json.dumps({k: v for k, v in out[variant].items() if k != 'by_dataset'}), flush=True)
    print(out['inferred_rule_reproduces_stored_labels'], out['decision_labels'])
    json.dump(out, open(LANE / 'work/k1audit/K1_KILL_RESCORE.json', 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
