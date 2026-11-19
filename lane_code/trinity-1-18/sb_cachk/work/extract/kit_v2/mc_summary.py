"""Arms, contrasts and the frozen bars through sb_kbox4's summarize_train, unchanged, on the approved population.

Population (out/v2/POPULATION.json, RULING 1056Z; registered in BARS_AMENDMENT.json): every bar, completeness rule and
the A32 per-fold choice read the decision population (204 captures, 1,012 rows); the 209 captures / 1,037 rows are
reported beside it and decide nothing. Priced files of captures outside the population are ignored.
Every measurement is also reported by dataset (ARKitScenes, ScanNet, ScanNet++), beside the deployed track's mask
numbers, and the report states the native-frame spacing of anchors and dense frames by dataset (FRAME_SETS.json).
final: out/v2/price/<seed set>_<frame set> -> CARRY_REPORT.md, CARRY_DECISION.json, K1_CARRY.json, PER_ITEM.jsonl, and
       TIMING_RECEIPT.json published from out/v2/track (out/v2)
dry  : out/v2/dry/price stub arms -> dry-run steps 1, 1b and 2 (STUB_PARITY.json) and the same report code on the stubs
       (out/v2/dry/CARRY_REPORT_STUB.md), labelled as stubs.
Usage: python mc_summary.py final [price_root dest] | dry   (p1cpu interpreter; final with arguments is a code test)
"""
import json, shutil, sys, time
from pathlib import Path
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_measure as MS

TAGS = [f'{s}/{f}' for s in ('S_A0', 'S_GT', 'S_PHR') for f in ('D64', 'A32')]
DATASETS = ('arkitscenes', 'scannet', 'scannetpp')
SPEC_ANCHOR_GAP = {'scannetpp': 272, 'scannet': 35, 'arkitscenes': 25}
SCOPES = ('decision', 'beside')


def scopes(pop):
    """{scope: (captures, row ids)} for the decision and beside populations."""
    return {s: (set(pop[s]['captures']), set(pop[s]['rows'])) for s in SCOPES}


def load_arm(root, tag, pop):
    d = Path(root)/tag.replace('/', '_')
    if not (d/'PRICE_INDEX.json').exists():
        return None
    index = C.read_json(d/'PRICE_INDEX.json')
    if index.get('population_id') != pop['population_id']:
        raise ValueError(f'{d} was priced under another population')
    keep = set(pop['track_order'])
    arm = dict(tag=tag, rows={'C_best1': [], 'C_fused': []}, captures={}, ignored=[])
    for e in index['captures']:
        if e['capture'] not in keep:
            arm['ignored'].append(e['capture'])
            continue
        p = d/(C.stub(e['capture'])+'.json.gz')
        rec = C.read_json(p)
        if C.PINS[str(p)] != e['sha256']:
            raise ValueError(f'{p} differs from PRICE_INDEX.json')
        for r in rec['items']:
            arm['rows'][r['arm'].split('/')[0]].append(r)
        arm['captures'][rec['capture']] = dict(fold=rec['fold'], dataset=C.dataset(rec['capture']), status=rec['track_status'],
                                               partial=rec.get('track_partial', False), skipped=rec.get('skipped_objects', []),
                                               records=rec['records'], table=rec['table'])
    completeness(arm, pop)
    return arm


def completeness(arm, pop):
    ok = {k for k, v in arm['captures'].items() if v['status'] == 'OK' and not v['partial']}
    for s, (caps, rows) in scopes(pop).items():
        arm[f'reached_{s}'] = len(ok & caps)
        arm[f'complete_{s}'] = caps <= ok and all({r['row_id'] for r in v if r['capture'] in caps} == rows for v in arm['rows'].values())


def restrict(arm, caps):
    return dict(arm, rows={k: [r for r in v if r['capture'] in caps] for k, v in arm['rows'].items()},
                captures={k: v for k, v in arm['captures'].items() if k in caps})


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


def measure(arm, a0, caps):
    """Every number of one arm on the captures `caps`; contrasts only when the arm holds every row of A0 there."""
    S, mf = L.S(), MS.maskfail()
    sub = restrict(arm, caps)
    a0s = [r for r in a0 if r['capture'] in caps]
    ids = {r['row_id'] for r in a0s}
    records = [r for v in sub['captures'].values() for r in v['records']]
    out = dict(captures=len(sub['captures']), a0_rows=len(a0s))
    for kind, rows in sub['rows'].items():
        full = bool(rows) and {r['row_id'] for r in rows} == ids
        out[kind] = dict(rows=len(rows), mra=S.mean(rows) if rows else None, refusals=sum(r['prediction'] is None for r in rows),
                         vs_A0=S.contrast(rows, a0s) if full else None)
    fused = sub['rows']['C_fused']
    full = bool(fused) and {r['row_id'] for r in fused} == ids
    out['member_precision'] = S.precision(fused)
    out['iou_member_precision'] = iou_precision(fused)
    out['size'] = S.contrast(S.sizes(fused), S.sizes(a0s)) if full else None
    first = S.appearance(fused) if fused else None
    out['first_seen'] = {k: first[k] for k in ('pairs', 'correct', 'rate', 'objects', 'exact', 'within_one')} if first else None
    out['mask_iou'] = mf.stats(records)
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


def evaluate(arm, a0, pop):
    """Bars on the decision population, the same numbers beside on all 209, and every measurement per dataset."""
    out = {}
    for s, (caps, rows) in scopes(pop).items():
        m = measure(arm, a0, caps) if arm is not None and arm[f'reached_{s}'] else None
        out[s] = dict(metrics=m, verdicts=verdicts(m, arm is not None and arm[f'complete_{s}']), captures=len(caps), rows=len(rows),
                      reached=arm[f'reached_{s}'] if arm else 0, role='bars' if s == 'decision' else 'reported beside; decides nothing')
        out[f'per_dataset_{s}'] = {ds: measure(arm, a0, {k for k in caps if C.dataset(k) == ds})
                                   for ds in DATASETS} if m is not None else None
    return out


def deployed_reference(pop):
    """The deployed track's mask numbers (sb_maskfail records of A0's served masks) by scope and dataset."""
    mf = MS.maskfail()
    base = [r for v in L.maskfail_records().values() for r in v]
    out = {}
    for s, (caps, _) in scopes(pop).items():
        for ds in (None,) + DATASETS:
            rec = [r for r in base if r['capture'] in caps and (ds is None or C.dataset(r['capture']) == ds)]
            st = mf.stats(rec)
            out[f'{s}/{ds or "all"}'] = dict(frame_recall=MS.frame_recall(rec), false_presence=MS.false_presence(rec),
                                             object_frame_iou_mean=st['object_frame']['mean'],
                                             pricing_best_frame_iou_mean=st['pricing_best_frame_iou']['mean'])
    return out


def frame_spacing(raw_frame_sets, caps):
    """Native frame index gaps by dataset: consecutive anchors (anchor_indices) and consecutive dense frames."""
    by = {}
    for c in raw_frame_sets['captures']:
        if c['capture'] not in caps:
            continue
        d = by.setdefault(C.dataset(c['capture']), dict(captures=0, anchor=[], dense=[], span=[], capture_anchor_median=[]))
        a = np.diff(c['anchor_indices']); g = np.diff([x['index'] for x in c['dense']])
        d['captures'] += 1; d['anchor'] += a.tolist(); d['dense'] += g.tolist()
        d['span'].append(c['anchor_indices'][-1] - c['anchor_indices'][0]); d['capture_anchor_median'].append(float(np.median(a)))
    q = lambda x: dict(median=float(np.median(x)), mean=float(np.mean(x)), p10=float(np.percentile(x, 10)), p90=float(np.percentile(x, 90)),
                       min=int(np.min(x)), max=int(np.max(x)))
    return {ds: dict(captures=d['captures'], anchor_gap=q(d['anchor']), dense_gap=q(d['dense']), anchor_span=q(d['span']),
                     median_of_capture_anchor_medians=float(np.median(d['capture_anchor_median'])),
                     spec_anchor_gap_median=SPEC_ANCHOR_GAP[ds], spec_dense_gap_median=SPEC_ANCHOR_GAP[ds]/2)
            for ds, d in sorted(by.items())}


def crossfit(d64, a32, pop):
    """Frame set per fold on the decision population's fit rooms: fold k takes the set with the higher C_fused MRA on the
    other four folds (ties D64); the choice applies to every capture of fold k, the beside captures included."""
    S = L.S()
    dec = set(pop['decision']['captures'])
    choice = {}
    arm = dict(tag=d64['tag'].split('/')[0]+'/cf', rows={'C_best1': [], 'C_fused': []}, captures={}, ignored=[])
    for k in range(5):
        fit = {name: S.mean([r for r in a['rows']['C_fused'] if r['fold'] != k and r['capture'] in dec]) for name, a in (('D64', d64), ('A32', a32))}
        name = 'A32' if fit['A32'] > fit['D64'] else 'D64'
        choice[k] = dict(frame_set=name, fit_mra=fit, fit_population='decision')
        src = d64 if name == 'D64' else a32
        for kind in arm['rows']:
            arm['rows'][kind] += [dict(r, arm=f"{kind}/{arm['tag']}") for r in src['rows'][kind] if r['fold'] == k]
        arm['captures'].update({c: v for c, v in src['captures'].items() if v['fold'] == k})
    completeness(arm, pop)
    for s in SCOPES:
        arm[f'complete_{s}'] = arm[f'complete_{s}'] and d64[f'complete_{s}'] and a32[f'complete_{s}']
    return arm, choice


num = lambda x, d: 'n/a' if x is None else f'{x:.{d}f}'
ci = lambda x: f"{x['estimate']:+.2f} [{x['ci95'][0]:+.2f}, {x['ci95'][1]:+.2f}]" if x else 'n/a'


def fmt(m, v, tag):
    if m is None:
        return f'| {tag} | MISSING | | | | | | | MISSING |'
    f, p, s, a = m['C_fused'], m['member_precision'], m['size'], m['first_seen'] or {}
    prec = f"{p['precision']:.4f} ({p['correct']}/{p['added']})" if p['precision'] is not None else 'n/a (0 added)'
    return (f"| {tag} | {num(m['C_best1']['mra'], 2)} | {num(f['mra'], 2)} | {ci(f['vs_A0'])} | {prec} | {ci(s)} | "
            f"{num(a.get('rate'), 4)} | {num(m['frame_recall']['rate'], 4)} | {v['carry_precision']}/{v['carry_fusion']}/{v['size_screen']}/{v['first_seen_screen']} |")


def fmt_ds(tag, ds, m, ref):
    p, ip, fp = m['member_precision'], m['iou_member_precision']['all_seeds'], m['false_presence']
    return (f"| {tag} | {ds} | {m['captures']} | {m['C_fused']['rows']} | {num(m['C_best1']['mra'], 2)} | {num(m['C_fused']['mra'], 2)} | "
            f"{ci(m['C_fused']['vs_A0'])} | {num(p['precision'], 4)} ({p['correct']}/{p['added']}) | {num(ip['precision'], 4)} | "
            f"{num(m['mask_iou']['object_frame']['mean'], 3)} ({num(ref['object_frame_iou_mean'], 3)}) | "
            f"{num(m['mask_iou']['pricing_best_frame_iou']['mean'], 3)} ({num(ref['pricing_best_frame_iou_mean'], 3)}) | "
            f"{num(m['frame_recall']['rate'], 4)} ({num(ref['frame_recall']['rate'], 4)}) | {fp['with_mask']}/{fp['absent_frames']} | "
            f"{num((m['first_seen'] or {}).get('rate'), 4)} | {ci(m['size'])} |")


HEAD = ('| seed set / frame set | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry_precision (ladder) | size vs A0 [95% CI] | '
        'first-seen pair rate | frame recall | bars: precision/fusion/size/first-seen |\n|---|---|---|---|---|---|---|---|---|')


def report(arms, results, decision, dest, title, extra, pop, spacing, reference):
    n = pop['counts']
    lines = [f'# {title}', '',
             f"Decision population (RULING 1056Z): {n['decision_captures']} captures, {n['decision_rows']} rows; every bar reads it. "
             f"Beside: {n['beside_captures']} captures, {n['beside_rows']} rows; decides nothing. population_id {pop['population_id'][:12]}.", '',
             f"## Bars on the decision population ({n['decision_captures']} captures / {n['decision_rows']} rows)", '', HEAD]
    for s in SCOPES:
        if s == 'beside':
            lines += ['', f"## Beside: {n['beside_captures']} captures / {n['beside_rows']} rows (reported, decides nothing)", '', HEAD]
        for tag, r in results.items():
            a = arms.get(tag)
            reach = f" ({a[f'reached_{s}']}/{r[s]['captures']} captures)" if a is not None and not a[f'complete_{s}'] else ''
            lines.append(fmt(r[s]['metrics'], r[s]['verdicts'], tag+reach))
    lines += ['', "Bars (BARS_FROZEN.json with BARS_AMENDMENT.json): carry_precision >= 0.90 over every added member, positive-score "
              "empty masks counted as incorrect; carry_fusion C_fused - A0 >= +2.0 with lower bound > 0; size_screen estimate >= 5 with "
              "lower bound > 0; first_seen_screen pair rate >= 0.90. MISSING counts as not passed.", '',
              '## Every arm by dataset (decision population; deployed track in parentheses)', '',
              '| arm | dataset | captures | rows | C_best1 MRA | C_fused MRA | C_fused - A0 [95% CI] | carry precision | IoU member precision | '
              'mask IoU per visible frame | mask IoU at priced frame | frame recall | false presence (masks/absent frames) | first-seen | size vs A0 |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for tag, r in results.items():
        for ds, m in (r['per_dataset_decision'] or {}).items():
            if m['captures']:
                lines.append(fmt_ds(tag, ds, m, reference[f'decision/{ds}']))
    lines += ['', '## Frame spacing by dataset (native frame indices; spec: anchor medians 272 ScanNet++, 35 ScanNet, 25 ARKitScenes; dense grid halves them)', '',
              '| population | dataset | captures | anchor gap median (spec) | anchor gap p10-p90 | dense gap median (spec) | anchor span median |',
              '|---|---|---|---|---|---|---|']
    for s in SCOPES:
        for ds, v in spacing[s].items():
            lines.append(f"| {s} | {ds} | {v['captures']} | {v['anchor_gap']['median']:.1f} ({v['spec_anchor_gap_median']}) | "
                         f"{v['anchor_gap']['p10']:.0f}-{v['anchor_gap']['p90']:.0f} | {v['dense_gap']['median']:.1f} ({v['spec_dense_gap_median']:.1f}) | "
                         f"{v['anchor_span']['median']:.0f} |")
    lines += [''] + [f'- {k}: {v}' for k, v in decision.items()] + [''] + extra
    Path(dest).write_text('\n'.join(lines)+'\n')


def published():
    pub = L.published(('A0_deployed', 'A2_gt_masks', 'fused_cf'))
    by = {}
    for (arm, rid), r in pub.items():
        by.setdefault(arm, []).append(r)
    return by


def context():
    pop = C.population()
    raw_fs = C.read_json(C.OUT/'FRAME_SETS.json')
    spacing = {s: frame_spacing(raw_fs, caps) for s, (caps, _) in scopes(pop).items()}
    return pop, spacing, deployed_reference(pop)


def dry():
    t0 = time.monotonic()
    S = L.S()
    pub = published()
    a0 = sorted(pub['A0_deployed'], key=lambda r: r['row_id'])
    pop, spacing, reference = context()
    sc = scopes(pop)
    root = C.OUT/'dry/price'
    seed, raster, empty = (load_arm(root, t, pop) for t in ('S_A0/STUBSEED', 'S_GT/STUBRASTER', 'S_A0/STUBEMPTY'))

    def same(rows, ref, rows_in=None):
        ref = {r['row_id']: r for r in ref if rows_in is None or r['row_id'] in rows_in}
        rows = [r for r in rows if rows_in is None or r['row_id'] in rows_in]
        eq = [r['row_id'] in ref and r['prediction'] == ref[r['row_id']]['prediction'] and r['refusal_code'] == ref[r['row_id']]['refusal_code']
              for r in rows]
        return dict(rows=len(rows), expected_rows=len(ref), equal=int(sum(eq)), mra=S.mean(rows), reference_mra=S.mean(list(ref.values())),
                    first_differences=[r['row_id'] for r, e in zip(rows, eq) if not e][:5])
    dec_rows = sc['decision'][1]
    checks = {}
    for scope, rows_in in (('', None), ('_decision', dec_rows)):
        checks['step1_seed_stub_C_best1_vs_A0_deployed'+scope] = same(seed['rows']['C_best1'], pub['A0_deployed'], rows_in)
        checks['step1b_empty_stub_C_best1_vs_A0_deployed'+scope] = same(empty['rows']['C_best1'], pub['A0_deployed'], rows_in)
        checks['step2_raster_stub_C_best1_vs_A2_gt_masks'+scope] = same(raster['rows']['C_best1'], pub['A2_gt_masks'], rows_in)
        checks['step2_raster_stub_C_fused_vs_fused_cf'+scope] = same(raster['rows']['C_fused'], pub['fused_cf'], rows_in)
    for v in checks.values():
        v['passed'] = v['equal'] == v['rows'] == v['expected_rows']
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    seeded = {(r['capture'], o['instance']) for r in seeds['captures'] for o in r['objects'] if o['S_A0']['status'] == 'OK'}
    prec = S.precision(empty['rows']['C_fused'])
    pe = sum(o.get('positive_empty', 0) for o in objects(empty['rows']['C_fused']))
    checks['step1b_empty_members_in_denominator'] = dict(
        seeded_objects=len(seeded), added=prec['added'], correct=prec['correct'], positive_empty=pe,
        rule='each seeded object carries one positive-score empty member: the ladder counts it added and incorrect',
        passed=prec['added'] == len(seeded) == pe and prec['correct'] == 0)
    arms = {'S_A0/STUBSEED': seed, 'S_A0/STUBEMPTY': empty, 'S_GT/STUBRASTER': raster}
    results = {t: evaluate(a, a0, pop) for t, a in arms.items()}
    C.code_pins()
    C.write_json(C.OUT/'dry/STUB_PARITY.json', dict(step='dry-run steps 1, 1b and 2 (stub trackers)', checks=checks, deployed_reference=reference,
                                                    frame_spacing=spacing, population_id=pop['population_id'], stub_metrics=results,
                                                    seconds=time.monotonic()-t0))
    report(arms, results, dict(note='stub trackers only; these numbers test the pricing and report code and are not carry results'),
           C.OUT/'dry/CARRY_REPORT_STUB.md', 'DRY RUN on stub trackers (not results)',
           [f"- {k}: {v.get('equal', v.get('added'))}/{v.get('rows', v.get('seeded_objects'))} passed={v['passed']}" for k, v in checks.items()],
           pop, spacing, reference)
    print(json.dumps(dict(checks={k: v['passed'] for k, v in checks.items()}, deployed=reference['beside/all'], seconds=time.monotonic()-t0)), flush=True)
    C.status('Dry-run steps 1, 1b, 2 (STUB_PARITY.json): ' + '; '.join(f"{k} {v['passed']}" for k, v in checks.items()) +
             f"; deployed frame recall {reference['beside/all']['frame_recall']['rate']:.4f} (spec 57.9%).")


def final(price_root=None, dest=None):
    price_root, dest = Path(price_root or C.OUT/'price'), Path(dest or C.OUT)
    t0 = time.monotonic()
    bars = C.read_json(C.OUT/'BARS_FROZEN.json')
    amendment = C.read_json(C.BARS_AMENDMENT)
    bars_sha = C.sha256_file(C.OUT/'BARS_FROZEN.json')
    if amendment['bars_frozen_sha256'] != bars_sha:
        raise SystemExit('BARS_AMENDMENT.json amends another BARS_FROZEN.json')
    pub = published()
    a0 = sorted(pub['A0_deployed'], key=lambda r: r['row_id'])
    pop, spacing, reference = context()
    arms = {t: a for t in TAGS if (a := load_arm(price_root, t, pop)) is not None}
    results, choices = {t: evaluate(arms.get(t), a0, pop) for t in TAGS}, {}
    for s in ('S_A0', 'S_GT', 'S_PHR'):
        d, q = arms.get(f'{s}/D64'), arms.get(f'{s}/A32')
        if d is not None and q is not None and d['complete_decision'] and q['complete_decision']:
            cf, choices[s] = crossfit(d, q, pop)
            arms[cf['tag']] = cf
            results[cf['tag']] = evaluate(cf, a0, pop)
    decide = lambda s: f'{s}/cf' if f'{s}/cf' in results else f'{s}/D64'
    a0row = results[decide('S_A0')]['decision']['verdicts']
    joins = a0row['carry_precision'] == 'PASS' and a0row['carry_fusion'] == 'PASS'
    gt = results[decide('S_GT')]['decision']['metrics']
    receipt_src, receipt = C.OUT/'track/TIMING_RECEIPT.json', 'MISSING'
    if dest == C.OUT and receipt_src.exists():
        shutil.copyfile(receipt_src, dest/'TIMING_RECEIPT.json')
        receipt = dict(path=str(dest/'TIMING_RECEIPT.json'), source=str(receipt_src), sha256=C.sha256_file(dest/'TIMING_RECEIPT.json'))
    decision = dict(
        decision_arm=decide('S_A0'), population=dict(population_id=pop['population_id'], **pop['counts'], ruling=pop['ruling']['path']),
        frame_set_choice=choices.get('S_A0', 'D64 (A32 incomplete on the decision population or absent)'), bars=a0row,
        beside_bars=dict(results[decide('S_A0')]['beside']['verdicts'], role='209 captures / 1,037 rows; decides nothing'),
        carried_fused_track_joins_stack=joins,
        object_arms='stay closed: carry_precision did not pass' if a0row['carry_precision'] != 'PASS' else
                    'size or appearance pass only opens that category\'s registered R0-dev comparison; no route is decided',
        S_PHR=dict(arm=decide('S_PHR'), bars=results[decide('S_PHR')]['decision']['verdicts'], note='own row; never replaces S_A0'),
        carry_ceiling=dict(arm=decide('S_GT'), C_fused_mra=gt['C_fused']['mra'] if gt else 'MISSING', reference_fused_cf=78.62,
                           frame_recall=gt['frame_recall'] if gt else 'MISSING', role='diagnostic, no bar'),
        missing_or_dropped={t: dict(decision_captures_reached=a['reached_decision'] if (a := arms.get(t)) else 0)
                            for t in TAGS if not (arms.get(t) or {}).get('complete_decision')},
        ignored_priced_captures={t: a['ignored'] for t, a in arms.items() if a['ignored']},
        timing_receipt=receipt)
    C.code_pins()
    C.write_json(dest/'CARRY_DECISION.json', dict(decision, bars_frozen_sha256=bars_sha, bars_amendment_sha256=C.sha256_file(C.BARS_AMENDMENT),
                                                   spec_sha256=bars['spec_sha256'], frame_spacing=spacing, deployed_reference=reference,
                                                   results=results))
    dec = set(pop['decision']['captures'])
    with (dest/'PER_ITEM.jsonl').open('w') as f:
        for t, a in arms.items():
            for kind, rows in a['rows'].items():
                for r in rows:
                    f.write(json.dumps(C.clean(dict(r, decision_population=r['capture'] in dec)))+'\n')
    carry = [dict(arm=t, dataset=C.dataset(k), decision_population=k in dec, **row)
             for t, a in arms.items() if not t.endswith('/cf') for k, v in a['captures'].items() for row in v['table']]
    C.write_json(dest/'K1_CARRY.json', dict(fields='per object and anchor: seed, carried flag, tracker score, area, IoU, raster share',
                                             masks='RLE per capture in out/v2/track/<seed set>_<frame set>/<capture>.json.gz',
                                             population_id=pop['population_id'], anchors=carry))
    extra = [f'- carry_ceiling ({decide("S_GT")}): C_fused {decision["carry_ceiling"]["C_fused_mra"]} against fused_cf 78.62 (diagnostic)',
             f'- missing or dropped arms (decision population): {json.dumps(decision["missing_or_dropped"])}',
             f'- TIMING_RECEIPT.json: {json.dumps(receipt)}']
    report(arms, results, {k: decision[k] for k in ('decision_arm', 'bars', 'beside_bars', 'carried_fused_track_joins_stack', 'object_arms')},
           dest/'CARRY_REPORT.md', 'Mask carry: SAM 3 tracker carries the best mask' + ('' if dest == C.OUT else ' (CODE TEST, not results)'),
           extra, pop, spacing, reference)
    print(json.dumps(dict(decision={k: decision[k] for k in ('decision_arm', 'bars', 'carried_fused_track_joins_stack')},
                          seconds=time.monotonic()-t0), default=str), flush=True)
    if dest == C.OUT:
        C.status(f"Summary (CARRY_REPORT.md, CARRY_DECISION.json): decision arm {decide('S_A0')} bars {a0row}; joins stack {joins}.")


if __name__ == '__main__':
    {'dry': dry, 'final': final}[sys.argv[1]](*sys.argv[2:])
