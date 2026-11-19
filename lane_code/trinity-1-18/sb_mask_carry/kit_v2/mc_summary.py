"""Arms, contrasts and the frozen bars (out/v2/BARS_FROZEN.json) through sb_kbox4's summarize_train, unchanged.

final: out/v2/price/<seed set>_<frame set> -> CARRY_REPORT.md, CARRY_DECISION.json, K1_CARRY.json, PER_ITEM.jsonl (out/v2)
dry  : out/v2/dry/price stub arms -> dry-run steps 1 and 2 (STUB_PARITY.json) and the same report code on the stubs
       (out/v2/dry/CARRY_REPORT_STUB.md), labelled as stubs.
Usage: python mc_summary.py final|dry   (p1cpu interpreter)
"""
import json, sys, time
from pathlib import Path
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_measure as MS

TAGS = [f'{s}/{f}' for s in ('S_A0', 'S_GT', 'S_PHR') for f in ('D64', 'A32')]
NCAP = 209


def load_arm(root, tag):
    d = Path(root)/tag.replace('/', '_')
    if not (d/'PRICE_INDEX.json').exists():
        return None
    index = C.read_json(d/'PRICE_INDEX.json')
    arm = dict(tag=tag, rows={'C_best1': [], 'C_fused': []}, captures={})
    for e in index['captures']:
        p = d/(C.stub(e['capture'])+'.json.gz')
        rec = C.read_json(p)
        if C.PINS[str(p)] != e['sha256']:
            raise ValueError(f'{p} differs from PRICE_INDEX.json')
        for r in rec['items']:
            arm['rows'][r['arm'].split('/')[0]].append(r)
        arm['captures'][rec['capture']] = dict(fold=rec['fold'], status=rec['track_status'], partial=rec.get('track_partial', False),
                                               skipped=rec.get('skipped_objects', []), records=rec['records'], table=rec['table'])
    ok = [k for k, v in arm['captures'].items() if v['status'] == 'OK' and not v['partial']]
    arm['complete'] = len(ok) == NCAP and all(len(v) == 1037 for v in arm['rows'].values())
    arm['reached'] = len(ok)
    return arm


def objects(rows):
    return L.S().objects(rows)


def iou_precision(rows):
    """predicted.member_precision summed over objects, for all seeds and for seeds on target (seed IoU >= 0.5)."""
    out = {}
    for which in ('all_seeds', 'on_target_seeds'):
        obs = [o for o in objects(rows) if o.get('carry_status') == 'OK' and (which == 'all_seeds' or o.get('on_target'))]
        n = sum(o['iou_member_precision']['members'] for o in obs)
        hit = sum(o['iou_member_precision']['correct'] for o in obs)
        out[which] = dict(objects=len(obs), members=n, correct=hit, precision=hit/n if n else None)
    return out


def measure(arm, a0, a0_sizes, captures=None):
    """Every number of one arm; `captures` limits records to a capture subset (cross-fit folds)."""
    S, mf = L.S(), MS.maskfail()
    caps = arm['captures'] if captures is None else {k: arm['captures'][k] for k in captures}
    records = [r for v in caps.values() for r in v['records']]
    out = {}
    for kind, rows in arm['rows'].items():
        out[kind] = dict(rows=len(rows), mra=S.mean(rows), refusals=sum(r['prediction'] is None for r in rows),
                         vs_A0=S.contrast(rows, a0) if len(rows) == len(a0) else None)
    fused = arm['rows']['C_fused']
    out['member_precision'] = S.precision(fused)
    out['iou_member_precision'] = iou_precision(fused)
    out['size'] = S.contrast(S.sizes(fused), a0_sizes) if len(fused) == len(a0) else None
    first = S.appearance(fused)
    out['first_seen'] = {k: first[k] for k in ('pairs', 'correct', 'rate', 'objects', 'exact', 'within_one')}
    st = mf.stats(records)
    out['mask_iou'] = st
    out['frame_recall'] = MS.frame_recall(records)
    out['false_presence'] = MS.false_presence(records)
    out['positive_empty'] = sum(o.get('positive_empty', 0) for o in objects(fused))
    return out


def verdicts(m, complete):
    if not complete:
        return dict(carry_precision='MISSING', carry_fusion='MISSING', size_screen='MISSING', first_seen_screen='MISSING')
    p, f, s, a = m['member_precision']['precision'], m['C_fused']['vs_A0'], m['size'], m['first_seen']['rate']
    return dict(carry_precision='PASS' if p is not None and p >= .90 else 'FAIL',
                carry_fusion='PASS' if f['estimate'] >= 2. and f['ci95'][0] > 0 else 'FAIL',
                size_screen='PASS' if s['estimate'] >= 5. and s['ci95'][0] > 0 else 'FAIL',
                first_seen_screen='PASS' if a is not None and a >= .90 else 'FAIL')


def crossfit(d64, a32):
    """Frame set per fold on the fit rooms: fold k takes the set with the higher C_fused MRA on the other four folds."""
    S = L.S()
    choice = {}
    arm = dict(tag=d64['tag'].split('/')[0]+'/cf', rows={'C_best1': [], 'C_fused': []}, captures={}, complete=True, reached=NCAP)
    for k in range(5):
        fit = {name: S.mean([r for r in a['rows']['C_fused'] if r['fold'] != k]) for name, a in (('D64', d64), ('A32', a32))}
        name = 'A32' if fit['A32'] > fit['D64'] else 'D64'
        choice[k] = dict(frame_set=name, fit_mra=fit)
        src = d64 if name == 'D64' else a32
        for kind in arm['rows']:
            arm['rows'][kind] += [dict(r, arm=f"{kind}/{arm['tag']}") for r in src['rows'][kind] if r['fold'] == k]
        arm['captures'].update({c: v for c, v in src['captures'].items() if v['fold'] == k})
    return arm, choice


def subset(arm, keep_rows):
    return dict(arm, rows={k: [r for r in v if r['row_id'] in keep_rows] for k, v in arm['rows'].items()})


def fmt(m, v, frozen_tag):
    if m is None:
        return f'| {frozen_tag} | MISSING | | | | | | | MISSING |'
    f, p, s, a = m['C_fused'], m['member_precision'], m['size'], m['first_seen']
    ci = lambda x: f"{x['estimate']:+.2f} [{x['ci95'][0]:+.2f}, {x['ci95'][1]:+.2f}]" if x else 'n/a'
    prec = f"{p['precision']:.4f} ({p['correct']}/{p['added']})" if p['precision'] is not None else f"n/a (0 added)"
    return (f"| {frozen_tag} | {m['C_best1']['mra']:.2f} | {f['mra']:.2f} | {ci(f['vs_A0'])} | {prec} | {ci(s)} | "
            f"{a['rate']:.4f} | {m['frame_recall']['rate']:.4f} | {v['carry_precision']}/{v['carry_fusion']}/{v['size_screen']}/{v['first_seen_screen']} |")


def report(arms, results, decision, dest, title, extra):
    lines = [f'# {title}', '',
             '| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |',
             '|---|---|---|---|---|---|---|---|---|']
    for tag in results:
        r = results[tag]
        reach = f" ({arms[tag]['reached']}/{NCAP} captures)" if tag in arms and not arms[tag]['complete'] else ''
        lines.append(fmt(r['metrics'], r['verdicts'], tag+reach))
    lines += ['', f"Bars (BARS_FROZEN.json): carry_precision >= 0.90; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; "
              "size_screen estimate >= 5 with lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.", '']
    lines += [f'- {k}: {v}' for k, v in decision.items()]
    lines += [''] + extra
    Path(dest).write_text('\n'.join(lines)+'\n')


def published():
    pub = L.published(('A0_deployed', 'A2_gt_masks', 'fused_cf'))
    by = {}
    for (arm, rid), r in pub.items():
        by.setdefault(arm, []).append(r)
    return by


def dry():
    t0 = time.monotonic()
    S = L.S()
    pub = published()
    a0 = sorted(pub['A0_deployed'], key=lambda r: r['row_id'])
    a0_sizes = S.sizes(a0)
    root = C.OUT/'dry/price'
    seed, raster = load_arm(root, 'S_A0/STUBSEED'), load_arm(root, 'S_GT/STUBRASTER')

    def same(rows, ref):
        ref = {r['row_id']: r for r in ref}
        eq = [r['row_id'] in ref and r['prediction'] == ref[r['row_id']]['prediction'] and r['refusal_code'] == ref[r['row_id']]['refusal_code']
              for r in rows]
        return dict(rows=len(rows), equal=int(sum(eq)), mra=S.mean(rows), reference_mra=S.mean(list(ref.values())),
                    first_differences=[r['row_id'] for r, e in zip(rows, eq) if not e][:5])
    checks = dict(
        step1_seed_stub_C_best1_vs_A0_deployed=same(seed['rows']['C_best1'], pub['A0_deployed']),
        step2_raster_stub_C_best1_vs_A2_gt_masks=same(raster['rows']['C_best1'], pub['A2_gt_masks']),
        step2_raster_stub_C_fused_vs_fused_cf=same(raster['rows']['C_fused'], pub['fused_cf']))
    for v in checks.values():
        v['passed'] = v['equal'] == v['rows'] == 1037
    base = [r for v in L.maskfail_records().values() for r in v]
    deployed = dict(frame_recall=MS.frame_recall(base), frame_recall_unique_object_frames=MS.frame_recall(MS.unique(base)),
                    false_presence=MS.false_presence(base), reference='spec: deployed frame recall 57.9% (per operand-frame records)')
    arms = {'S_A0/STUBSEED': seed, 'S_GT/STUBRASTER': raster}
    results = {t: dict(metrics=measure(a, a0, a0_sizes), verdicts=verdicts(measure(a, a0, a0_sizes), a['complete'])) for t, a in arms.items()}
    C.code_pins()
    C.write_json(C.OUT/'dry/STUB_PARITY.json', dict(step='dry-run steps 1 and 2 (stub trackers)', checks=checks, deployed_reference=deployed,
                                                    stub_metrics=results, seconds=time.monotonic()-t0))
    report(arms, results, dict(note='stub trackers only; these numbers test the pricing and report code and are not carry results'),
           C.OUT/'dry/CARRY_REPORT_STUB.md', 'DRY RUN on stub trackers (not results)',
           [f"- step 1 seed stub C_best1 = A0_deployed on {checks['step1_seed_stub_C_best1_vs_A0_deployed']['equal']}/1037 rows",
            f"- step 2 raster stub C_best1 = A2_gt_masks on {checks['step2_raster_stub_C_best1_vs_A2_gt_masks']['equal']}/1037, "
            f"C_fused = fused_cf on {checks['step2_raster_stub_C_fused_vs_fused_cf']['equal']}/1037"])
    print(json.dumps(dict(checks={k: (v['equal'], v['rows'], round(v['mra'], 4), round(v['reference_mra'], 4)) for k, v in checks.items()},
                          deployed=deployed, seconds=time.monotonic()-t0)), flush=True)
    C.status('Dry-run steps 1-2 (STUB_PARITY.json): ' + '; '.join(f"{k.split('_', 1)[0]} {v['equal']}/{v['rows']}" for k, v in checks.items()) +
             f"; deployed frame recall {deployed['frame_recall']['rate']:.4f} (spec 57.9%).")


def final():
    t0 = time.monotonic()
    S = L.S()
    bars = C.read_json(C.OUT/'BARS_FROZEN.json')
    pub = published()
    a0 = sorted(pub['A0_deployed'], key=lambda r: r['row_id'])
    a0_sizes = S.sizes(a0)
    arms = {t: a for t in TAGS if (a := load_arm(C.OUT/'price', t)) is not None}
    results, choices = {}, {}
    for t in TAGS:
        a = arms.get(t)
        m = measure(a, a0, a0_sizes) if a is not None and a['reached'] else None
        results[t] = dict(metrics=m, verdicts=verdicts(m, a is not None and a['complete']))
    for s in ('S_A0', 'S_GT', 'S_PHR'):
        d, q = arms.get(f'{s}/D64'), arms.get(f'{s}/A32')
        if d is not None and q is not None and d['complete'] and q['complete']:
            cf, choices[s] = crossfit(d, q)
            arms[cf['tag']] = cf
            m = measure(cf, a0, a0_sizes)
            results[cf['tag']] = dict(metrics=m, verdicts=verdicts(m, True))
    decide = lambda s: f'{s}/cf' if f'{s}/cf' in results else f'{s}/D64'
    a0row = results[decide('S_A0')]['verdicts']
    joins = a0row['carry_precision'] == 'PASS' and a0row['carry_fusion'] == 'PASS'
    phr = results[decide('S_PHR')]['verdicts']
    gt = results.get(decide('S_GT'), {}).get('metrics')
    decision = dict(
        decision_arm=decide('S_A0'), frame_set_choice=choices.get('S_A0', 'D64 (A32 incomplete or absent)'), bars=a0row,
        carried_fused_track_joins_stack=joins,
        object_arms='stay closed: carry_precision did not pass' if a0row['carry_precision'] != 'PASS' else
                    'size or appearance pass only opens that category\'s registered R0-dev comparison; no route is decided',
        S_PHR=dict(arm=decide('S_PHR'), bars=phr, note='own row; never replaces S_A0'),
        carry_ceiling=dict(arm=decide('S_GT'), C_fused_mra=gt['C_fused']['mra'] if gt else 'MISSING', reference_fused_cf=78.62,
                           frame_recall=gt['frame_recall'] if gt else 'MISSING', role='diagnostic, no bar'))
    guard = C.read_json(C.OUT/'GUARD.json')
    withheld = set(guard['lists']['withheld_80']['hit_captures'])
    keep = {r['row_id'] for r in a0 if r['capture'] not in withheld}
    sens = None
    if decide('S_A0') in arms and arms[decide('S_A0')]['complete']:
        x = subset(arms[decide('S_A0')], keep)
        a0k = [r for r in a0 if r['row_id'] in keep]
        sens = dict(rows=len(keep), C_fused_vs_A0=S.contrast(x['rows']['C_fused'], a0k), member_precision=S.precision(x['rows']['C_fused']),
                    role='sensitivity without the withheld-80 captures; decides nothing')
    decision['withheld_sensitivity'] = sens
    dropped = {t: dict(captures_reached=a['reached'] if (a := arms.get(t)) else 0) for t in TAGS if not (arms.get(t) or {}).get('complete')}
    decision['missing_or_dropped'] = dropped
    C.code_pins()
    C.write_json(C.OUT/'CARRY_DECISION.json', dict(decision, bars_frozen_sha256=C.sha256_file(C.OUT/'BARS_FROZEN.json'),
                                                   spec_sha256=bars['spec_sha256'], results=results))
    with (C.OUT/'PER_ITEM.jsonl').open('w') as f:
        for t, a in arms.items():
            for kind, rows in a['rows'].items():
                for r in rows:
                    f.write(json.dumps(C.clean(r))+'\n')
    carry = [dict(arm=t, **row) for t, a in arms.items() if not t.endswith('/cf') for v in a['captures'].values() for row in v['table']]
    C.write_json(C.OUT/'K1_CARRY.json', dict(fields='per object and anchor: seed, carried flag, tracker score, area, IoU, raster share',
                                             masks='RLE per capture in out/v2/track/<seed set>_<frame set>/<capture>.json.gz',
                                             anchors=carry))
    extra = [f'- carry_ceiling ({decide("S_GT")}): C_fused {decision["carry_ceiling"]["C_fused_mra"]} against fused_cf 78.62 (diagnostic)',
             f'- withheld-80 sensitivity: {json.dumps(C.clean(sens))[:300] if sens else "MISSING"}',
             f'- missing or dropped arms: {json.dumps(dropped)}']
    report(arms, results, {k: decision[k] for k in ('decision_arm', 'bars', 'carried_fused_track_joins_stack', 'object_arms')},
           C.OUT/'CARRY_REPORT.md', 'Mask carry: SAM 3 tracker carries the best mask', extra)
    print(json.dumps(dict(decision={k: decision[k] for k in ('decision_arm', 'bars', 'carried_fused_track_joins_stack')},
                          seconds=time.monotonic()-t0), default=str), flush=True)
    C.status(f"Summary (CARRY_REPORT.md, CARRY_DECISION.json): decision arm {decide('S_A0')} bars {a0row}; joins stack {joins}.")


if __name__ == '__main__':
    {'dry': dry, 'final': final}[sys.argv[1]]()
