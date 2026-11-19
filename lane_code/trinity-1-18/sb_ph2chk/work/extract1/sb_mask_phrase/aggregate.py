"""Fold choices, arms, bars, decision and outputs from work/caps2 and work/recall2 (bash run.sh aggregate.py)."""
import collections, gzip, json, sys
import numpy as np
import kit as K
T, M, A = K.T, K.M, K.A
import summarize_train as S  # noqa: E402  (contrast: 10,000 room draws, seed 20261119; appearance)

BARS, BARS_SHA = K.OUT/'BARS.json', K.WORK/'BARS.sha256'
FIXED = {'P0': 'raw', 'P_cap100': 'cap100'}
W_ARMS = ('W1', 'W2', 'W2c')
ELIGIBLE = ('W1', 'W2c')
ROLE = {'W1': 'bar', 'W2c': 'bar', 'P_cap100': 'diagnostic (reads no bar)',
        'W2': 'tool-change diagnostic (review sb_phrev): its pool joins raw and alias frames, which needs a call carrying two phrases; '
              'the current call syntax has none, so W2 is not eligible'}
STATUS = 'diagnostic pending orchestrator ruling on registration'
WITHHELD = frozenset('scannet/'+c for c in ('scene0201_02', 'scene0478_00', 'scene0478_01', 'scene0614_02', 'scene0692_03'))
WITHHELD_RULE = ('Orchestrator ruling 1056Z: all K1-train pricing is decided on the rows outside the 80 withheld rooms, with the all-row '
                 'figures beside them. Five K1 training captures lie in those rooms (review sb_phrev finding 6); they are dropped from '
                 'every fit and every decision figure. K1 train membership alone does not certify downstream teaching eligibility.')
OPEN_PAIRS = (('table', 'desk'), ('chair', 'seat'), ('bookshelf', 'shelf'))
OPEN_REASON = ('The stage-1 cache drops an alias proposal whose IoU with an earlier retained instance exceeds 0.95, so where the alias '
               'finds the object the raw name already found, the stored alias pool lacks it. The raw name\'s lead on the stored pools '
               'therefore cannot tell a weaker alias from deduplication. Open until part 2 reruns the alias alone; the default pass '
               'reruns only fold-chosen phrases, so these need sam3_pass.py pass --all-aliases (2,004 calls against 1,540).')
SERVING_NOTE = 'W1 prices a deduplicated subset; the exact serving score is unverified (standalone rerun = part 2).'
PREFIX = {'W1': 'q:', 'W2': 'fb:', 'W2c': 'call:'}
PRICED = ('P0', 'P_cap100', 'W1', 'W2', 'W2c')
OFFLINE = ('P_all', 'P_cf')
TABLE_ARMS = ('P0', 'P_all', 'P_cf', 'P_cap100', 'W1', 'W2', 'W2c')
WORSE = ('refused', 'wrong_object', 'weak', 'poor_priced_frame', 'good')
MODES = {'W1': 'one call with this phrase', 'W2': 'raw call; the alias fills the anchor frames where the raw pool is empty',
         'W2c': 'raw call; a second call with the alias when the first returns not seen'}
ROUTED_DEVS1 = 'sb_ktow3 routed file with sha256 prefix 8855c81e (a dev-S1 return set)'


def candidates(arm, aliases):
    return [PREFIX[arm]+a for a in aliases]


def choose(objs, cands, fold=None, min_fit=5, key='on_target'):
    """The spec's per-name rule. Fit objects are those outside `fold` (all objects when fold is None). Each candidate
    policy counts the fit objects it puts on target; the best candidate (first in sorted alias order on a tie) replaces
    the raw name only on a strictly larger count and only when the name has at least `min_fit` fit objects."""
    fit = [o for o in objs if fold is None or o['fold'] != fold]
    counts = {v: sum(bool(o[key].get(v, False)) for o in fit) for v in ['raw']+list(cands)}
    evidence = dict(fit_objects=len(fit), counts=counts)
    if len(fit) < min_fit or not cands:
        return 'raw', evidence
    best = max(cands, key=lambda v: (counts[v], -cands.index(v)))
    return (best if counts[best] > counts['raw'] else 'raw'), evidence


def phrases(variant, name):
    if variant == 'raw':
        return [name]
    kind, alias = variant.split(':', 1)
    return [alias] if kind == 'q' else [name, alias]


def gz(p):
    return json.loads(gzip.decompress(T.read(p)))


def load():
    caps, ctx = K.setup()
    files = sorted(K.CAPS.glob('*.json.gz')); assert len(files) == 209, len(files)
    rfiles = sorted(K.RECALL.glob('*.json.gz')); assert len(rfiles) == 209, len(rfiles)
    data = [gz(p) for p in files]; recall = {d['capture']: d for d in map(gz, rfiles)}
    for d, p in zip(data, files):
        d['_file'] = str(p)
        assert d['k1_split'] == 'train' and all(b['passed'] for b in d['builder_parity'])
    a0 = json.loads(T.read(K.WORK/'A0_ROWS.json'))
    assert a0['input_sha256'][str(K.PER_ITEM)].startswith('3bc7f87f')
    return caps, ctx, data, recall, a0['rows']['A0_deployed'], a0['rows']['A2_gt_masks']


def objects_of(data, recall):
    objs = []
    for d in data:
        for name, o in d['names'].items():
            rp = recall[d['capture']]['names'][name]['pools']
            objs.append(dict(capture=d['capture'], room=d['room'], fold=d['fold'], dataset=d['dataset'], name=name,
                             instance=o['instance'], aliases=o['aliases'], in_dictionary=o['in_dictionary'],
                             variants=o['variants'], calls=o['calls'], fills=o['fills'], keys=o['keys'], prompts=o['prompts'],
                             on_target={v: o['keys'][k]['on_target'] for v, k in o['variants'].items()},
                             seen={v: o['keys'][k]['seen'] for v, k in o['variants'].items()},
                             recall={v: x['recall'] for v, x in rp.items()}, recall_lift={v: x['recall_lift'] for v, x in rp.items()},
                             rows=[r['id'] for r in d['rows'] if name in r['operands']]))
    return objs


def fold_choices(objs):
    byname = collections.defaultdict(list)
    for o in objs:
        byname[o['name']].append(o)
    choices, evidence = {}, {}
    for arm in W_ARMS+('P_cf',):
        choices[arm] = {}; evidence[arm] = {}
        for k in [*range(5), None]:
            key = 'all_rooms' if k is None else str(k)
            choices[arm][key] = {}; evidence[arm][key] = {}
            for name, os_ in sorted(byname.items()):
                if arm == 'P_cf':
                    v, ev = choose(os_, ['all'] if os_[0]['aliases'] else [], k, key='recall_lift')
                else:
                    v, ev = choose(os_, candidates(arm, os_[0]['aliases']), k)
                choices[arm][key][name] = v; evidence[arm][key][name] = ev
    return choices, evidence, byname


def arm_rows(data, arm, variant_of):
    rows = []
    for d in data:
        idx = {(it['row_id'],)+tuple(it['keys'].values()): it for it in d['items']}
        for r in d['rows']:
            a, b = r['operands']; va, vb = variant_of(d, a), variant_of(d, b)
            ka, kb = d['names'][a]['variants'][va], d['names'][b]['variants'][vb]
            it = idx[(r['id'], ka, kb)]
            assert list(it['keys'].items()) == [(a, ka), (b, kb)]
            rows.append(dict({k: v for k, v in it.items() if k != 'keys'}, arm=arm, variants={a: va, b: vb}, keys={a: ka, b: kb},
                             calls={a: d['names'][a]['calls'][ka], b: d['names'][b]['calls'][kb]}, source_file=d['_file']))
    return rows


def mra(rows):
    return 100*float(np.mean([M.mra(r['prediction'], r['label']) for r in rows])) if rows else None


def operand_view(data, rows):
    caps = {d['capture']: d for d in data}
    out = []
    for r in rows:
        d = caps[r['capture']]
        for n, k in r['keys'].items():
            o = d['names'][n]
            out.append((r, n, o['keys'][k], o['records'][k]))
    return out


def arm_report(data, rows, a0, good_rows):
    ops = operand_view(data, rows)
    gain = S.contrast(rows, [a0[r['row_id']] for r in rows])
    safe_l = [r for r in rows if r['row_id'] in good_rows]
    safe = S.contrast(safe_l, [a0[r['row_id']] for r in safe_l])
    st = A.stats([dict(rec, row=r['row_id']) for r, n, s, recs in ops for rec in recs])
    uniq = {(r['capture'], n): s for r, n, s, recs in ops}
    taus = {}
    for tau in M.TAUS:
        t = str(tau); added = sum(s['taus'][t]['added'] for s in uniq.values()); hit = sum(s['taus'][t]['correct'] for s in uniq.values())
        gm = sum(s['taus'][t]['gt_members'] for s in uniq.values()); gc = sum(s['taus'][t]['gt_correct'] for s in uniq.values())
        taus[t] = dict(added=added, correct=hit, precision=hit/added if added else None, passes_90=bool(added and hit/added >= .9),
                       gt_iou_members=gm, gt_iou_correct=gc, gt_iou_precision=gc/gm if gm else None)
    by_ds = {}
    for ds in sorted({r['dataset'] for r in rows}):
        sub = [r for r in rows if r['dataset'] == ds]
        c = S.contrast(sub, [a0[r['row_id']] for r in sub])
        by_ds[ds] = dict(rows=len(sub), mra=mra(sub), a0_mra=c['right_mra'], delta=c['estimate'], ci95=c['ci95'])
    return dict(rows=len(rows), rooms=len({r['room'] for r in rows}), mra=mra(rows),
                mra_ci95=S.contrast(rows, [dict(r, prediction=None) for r in rows])['ci95'],
                refusals=sum(r['prediction'] is None for r in rows), gain=gain, safe=safe,
                operand_categories=dict(collections.Counter(s['category'] for _, _, s, _ in ops)),
                pool_recall=sum(s['pool_recall'] for _, _, s, _ in ops), pool_recall_lift=sum(s['pool_recall_lift'] for _, _, s, _ in ops),
                operands=len(ops), on_target=sum(s['on_target'] for _, _, s, _ in ops),
                served_absent_frames=sum(s['served_absent'] for _, _, s, _ in ops),
                served_absent_frames_unique_objects=sum(s['served_absent'] for s in uniq.values()),
                served_iou=dict(visible_frames=st['visible_valid'], mean=st['object_frame']['mean'], rate_05=st['object_frame']['rates']['0.5'],
                                priced_frame_mean=st['pricing_best_frame_iou']['mean'], priced_frame_rate_05=st['pricing_best_frame_iou']['rates']['0.5'],
                                failure_05=st['failure']['0.5']),
                member_precision=taus, first_seen=S.appearance(rows), by_dataset=by_ds, stats=st)


def offline_report(objs, choice_of, heldout):
    """P_all / P_cf: row-weighted operand pool recall only; never priced through the reader."""
    pick = [(o, choice_of(o)) for o in objs for _ in o['rows']]
    by, n = collections.Counter(), collections.Counter()
    for o, v in pick:
        by[o['dataset']] += o['recall_lift'][v]; n[o['dataset']] += 1
    return dict(operands=len(pick), pool_recall=sum(o['recall'][v] for o, v in pick), pool_recall_lift=sum(o['recall_lift'][v] for o, v in pick),
                pool_recall_lift_by_dataset={d: dict(hit=by[d], operands=n[d]) for d in sorted(n)}, heldout=heldout, mra=None, priced=False,
                reason='mixed presence per frame: routed_features.cache_for keeps the first instance\'s presence (sb_mdrev finding 9)')


def name_table(byname, arms, a0, choices, evidence):
    """Per name: all-room policy per arm, fit counts, held-out on-target counts, rows and the paired gain of its rows."""
    out = {}
    total = len(arms['P0'])
    for n, os_ in sorted(byname.items()):
        rec = dict(objects=len(os_), operands=sum(len(o['rows']) for o in os_), aliases=os_[0]['aliases'])
        for arm in W_ARMS:
            allr = choices[arm]['all_rooms'][n]; ev = evidence[arm]['all_rooms'][n]
            held = dict(policy=0, raw=0, objects=len(os_))
            for o in os_:
                v = choices[arm][str(o['fold'])][n]
                held['policy'] += bool(o['on_target'].get(v)); held['raw'] += bool(o['on_target']['raw'])
            sub = [r for r in arms[arm] if n in r['variants']]
            changed = [r for r in sub if r['variants'][n] != 'raw']
            g = S.contrast(sub, [a0[r['row_id']] for r in sub]) if changed else None
            rec[arm] = dict(all_rooms=allr, phrases=phrases(allr, n), fit_objects=ev['fit_objects'],
                            fit_on_target=dict(policy=ev['counts'].get(allr, ev['counts']['raw']), raw=ev['counts']['raw']),
                            fit_counts=ev['counts'], folds={k: choices[arm][k][n] for k in map(str, range(5))},
                            heldout_on_target=held, rows=len(sub), changed_rows=len(changed),
                            gain=dict(estimate=g['estimate'], ci95=g['ci95'], rows=g['rows']) if g else None,
                            points=100*sum(M.mra(r['prediction'], r['label'])-M.mra(a0[r['row_id']]['prediction'], r['label']) for r in changed)/total)
        rec['insample_best_without_min_fit'] = {arm: choose(os_, candidates(arm, os_[0]['aliases']), None, min_fit=0)[0] for arm in W_ARMS}
        rec['P_cf'] = dict(all_rooms=choices['P_cf']['all_rooms'][n], folds={k: choices['P_cf'][k][n] for k in map(str, range(5))})
        out[n] = rec
    return out


def rows_to_rewrite(data, choices, names_table, rowids, withheld_rows):
    """Rows of the decision population that name a changed name; rows of the withheld captures are counted beside, never added."""
    rows = [(d, r) for d in data for r in d['rows']]
    assert len(rows) == len(rowids) and {r['id'] for _, r in rows} == rowids
    by_arm = {}
    for arm in W_ARMS:
        fit = choices[arm]['all_rooms']
        changed = sorted(n for n, v in fit.items() if v != 'raw')
        naming, second = collections.Counter(), collections.Counter(); ids, sec_ids = set(), set()
        for d, r in rows:
            for n in r['operands']:
                if fit[n] == 'raw':
                    continue
                naming[n] += 1; ids.add(r['id'])
                o = d['names'][n]; a = fit[n].split(':', 1)[1]
                need = (not o['keys'][o['variants']['raw']]['seen']) if arm == 'W2c' else (o['fills'][a] > 0 if arm == 'W2' else False)
                if need:
                    second[n] += 1; sec_ids.add(r['id'])
        small = {n: dict(objects=x['objects'], operands=x['operands'], insample_best=x['insample_best_without_min_fit'][arm])
                 for n, x in names_table.items() if x['insample_best_without_min_fit'][arm] != 'raw' and x['objects'] < 5}
        by_arm[arm] = dict(role=ROLE[arm], names=changed, policies={n: phrases(fit[n], n) for n in changed}, k1_rows=len(ids),
                           k1_rows_by_name=dict(naming.most_common()), second_call_rows=len(sec_ids),
                           second_call_rows_by_name=dict(second.most_common()), under_five_objects_left_raw=small,
                           withheld_rows_naming_changed_names=sum(any(n in changed for n in r['operands']) for r in withheld_rows))
    heater_coat = sum(any(n in ('heater', 'coat hanger') for n in r['operands']) for _, r in rows)
    return by_arm, heater_coat


def population(data, recall, a0, keep):
    """Fold choices, priced arms, reports, bars and the decision on the captures `keep` admits. Fits, rows and the
    both-good set read those captures only."""
    sub = [d for d in data if keep(d['capture'])]
    objs = objects_of(sub, recall)
    choices, evidence, byname = fold_choices(objs)
    arms = {a: arm_rows(sub, a, lambda d, n, v=v: v) for a, v in FIXED.items()}
    for a in W_ARMS:
        arms[a] = arm_rows(sub, a, lambda d, n, a=a: choices[a][str(d['fold'])][n])
    cat = {(d['capture'], n): o['keys'][o['variants']['raw']]['category'] for d in sub for n, o in d['names'].items()}
    worse = {r['id']: min((cat[(d['capture'], n)] for n in r['operands']), key=WORSE.index) for d in sub for r in d['rows']}
    good_rows = {i for i, w in worse.items() if w == 'good'}
    reports = {a: arm_report(sub, rows, a0, good_rows) for a, rows in arms.items()}
    reports['P_all'] = offline_report(objs, lambda o: 'all', False)
    reports['P_cf'] = offline_report(objs, lambda o: choices['P_cf'][str(o['fold'])][o['name']], True)
    bars = {}
    for a in W_ARMS+('P_cap100',):
        g, s = reports[a]['gain'], reports[a]['safe']
        bars[a] = dict(phrase_worth=dict(verdict='PASS' if g['estimate'] >= 1.5 and g['ci95'][0] > 0 else 'FAIL', estimate=g['estimate'], ci95=g['ci95']),
                       phrase_safe=dict(verdict='PASS' if s['ci95'][0] > -1.0 else 'FAIL', rows=s['rows'], estimate=s['estimate'], ci95=s['ci95']),
                       role=ROLE[a])
    passing = [a for a in ELIGIBLE if bars[a]['phrase_worth']['verdict'] == 'PASS' and bars[a]['phrase_safe']['verdict'] == 'PASS']
    chosen = max(passing, key=lambda a: (reports[a]['mra'], -ELIGIBLE.index(a))) if passing else None
    return dict(data=sub, objs=objs, choices=choices, evidence=evidence, byname=byname, arms=arms, worse=worse, good_rows=good_rows,
                reports=reports, bars=bars, passing=passing, chosen=chosen, names=name_table(byname, arms, a0, choices, evidence),
                rowids={r['id'] for d in sub for r in d['rows']}, rooms=len({d['room'] for d in sub}))


def ceiling(pop):
    r = pop['reports']['P_cf']
    return dict(arm='P_cf', priced=False, pool_recall=r['pool_recall'], pool_recall_lift=r['pool_recall_lift'], operands=r['operands'], reason=r['reason'])


def nonraw(choices):
    return {a: {k: {n: v for n, v in c.items() if v != 'raw'} for k, c in by_fold.items()} for a, by_fold in choices.items()}


def blocker(misses):
    K.OUT.mkdir(exist_ok=True)
    (K.HERE/'BLOCKER.md').write_text('# BLOCKER: P0 differs from A0_deployed\n\n'+f'{len(misses)} of 1,037 predictions differ. First rows:\n\n'
                                     +'\n'.join(f'- {m}' for m in misses[:20])+'\n\nThe kit stops here; no arm is reported.\n')
    (K.HERE/'STATUS.md').write_text(f'BLOCKED: parity failed on {len(misses)} of 1,037 rows; see BLOCKER.md.\n')
    sys.exit(1)


def main():
    frozen = T.read(BARS_SHA).decode().split()[0]
    assert K.sha(BARS) == frozen, 'out/BARS.json differs from work/BARS.sha256'
    rules = json.loads(T.read(BARS))
    assert rules['written_before_any_score'] is False and rules['registration']['written_before_any_score'] is False
    caps, ctx, data, recall, a0, a2 = load()
    labels, rowids, folds, truth, head, table, producer = ctx
    pins = {}
    for d in data+list(recall.values()):
        for k, v in d['input_sha256'].items():
            assert pins.setdefault(k, v) == v, ('input changed during the pass', k)
    for k, v in T.PINS.items():
        assert pins.setdefault(k, v) == v, ('input changed since the pass', k)
    checks = [dict(capture=d['capture'], **ch) for d in data for ch in d['checks']]
    refused = [dict(capture=d['capture'], **x) for d in data for x in d['reader_refused']]
    check_summary = dict(pools=len(checks), alias_calls=sum(ch['call'] != ch['name'] for ch in checks),
                         survival_failed=sum(not ch['survival'] for ch in checks), identities_failed=sum(not ch['identities'] for ch in checks),
                         raw_fresh_labels_equal_table=sum(ch['table'] is True for ch in checks), raw_fresh_labels_differ=sum(ch['table'] is False for ch in checks),
                         reader_refused=len(refused), builder_parity_names=sum(len(d['builder_parity']) for d in data),
                         uniform_presence='every priced pool passed kit.uniform (a mixed frame raises)')
    assert not refused and not check_summary['survival_failed'] and not check_summary['identities_failed'] and not check_summary['raw_fresh_labels_differ'], check_summary
    full = population(data, recall, a0, lambda c: True)
    dec = population(data, recall, a0, lambda c: c not in WITHHELD)
    objs = full['objs']
    consistent = sum(o['keys'][o['variants']['raw']]['pool_recall'] == o['recall']['raw']
                     and o['keys'][o['variants']['raw']]['pool_recall_lift'] == o['recall_lift']['raw'] for o in objs)
    check_summary['raw_recall_caps_equals_recall_pass'] = f'{consistent}/{len(objs)}'
    p0 = {r['row_id']: r for r in full['arms']['P0']}
    assert set(p0) == rowids == set(a0)
    misses = [dict(row=i, p0=p0[i]['prediction'], a0=a0[i]['prediction']) for i in sorted(rowids) if p0[i]['prediction'] != a0[i]['prediction']]
    if misses:
        blocker(misses)
    assert all(p0[i]['label'] == a0[i]['label'] and p0[i]['room'] == a0[i]['room'] for i in rowids)
    withheld_caps = sorted(d['capture'] for d in data if d['capture'] in WITHHELD)
    assert withheld_caps == sorted(WITHHELD), withheld_caps
    withheld_rows = [r for d in data if d['capture'] in WITHHELD for r in d['rows']]
    policy_changes = [dict(arm=a, fold=k, name=n, all_rows=v, decision=dec['choices'][a][k].get(n, 'raw (no object outside the withheld rooms)'))
                      for a, by_fold in full['choices'].items() for k, c in by_fold.items() for n, v in c.items()
                      if (n in dec['choices'][a][k] and v != dec['choices'][a][k][n]) or (n not in dec['choices'][a][k] and v != 'raw')]
    assert not policy_changes, ('the withheld captures move a fold choice; PER_ITEM.jsonl prices every row under the all-row fits', policy_changes)
    worse_table = {}
    for w in WORSE:
        ids = [i for i in sorted(rowids) if full['worse'][i] == w]
        worse_table[w] = dict(rows=len(ids), a0=mra([a0[i] for i in ids]), a2=mra([a2[i] for i in ids]),
                              points_of_gap=(mra([a2[i] for i in ids])-mra([a0[i] for i in ids]))*len(ids)/1037 if ids else 0.)
    chosen = dec['chosen']
    final = dec['choices'][chosen]['all_rooms'] if chosen else {n: 'raw' for n in dec['byname']}
    rewrite, heater_coat = rows_to_rewrite(dec['data'], dec['choices'], dec['names'], dec['rowids'], withheld_rows)
    routed = dict(status='MISSING', owner='tree_rebuild', count=None,
                  expected='N\'s routed training rows (rows carrying <ground obj=...> calls), held by tree_rebuild; not on trinity-1-18',
                  not_opened=[ROUTED_DEVS1+': the binding brief keeps it closed',
                              '/scratch/jjyeung/n30_mirror/rows_r1 (store v7 and its slices): unrouted store rows; its STATUS.md records rows on '
                              'K1 held-out rooms in the store family (v6), so the kit did not open it'])
    withheld = dict(rule=WITHHELD_RULE, captures=withheld_caps, rooms=sorted({d['room'] for d in data if d['capture'] in WITHHELD}),
                    rows=len(withheld_rows), row_ids=sorted(r['id'] for r in withheld_rows),
                    heater_rows=sum('heater' in r['operands'] for r in withheld_rows), both_good_rows=len(full['good_rows']-dec['good_rows']))
    pop = dict(decision=dict(rows=len(dec['rowids']), rooms=dec['rooms'], captures=len(dec['data']), both_good_rows=len(dec['good_rows']),
                             fits='every fold choice and the all-room refit read only these captures; rooms keep their registered folds'),
               all_rows=dict(rows=len(rowids), rooms=full['rooms'], captures=len(data), both_good_rows=len(full['good_rows'])),
               withheld=withheld, policy_changes_vs_all_rows=policy_changes,
               keys='Plain keys hold the decision population; keys ending _1037 hold all K1 training rows. both_good_rows and '
                    'worse_operand_table are all-row figures (part 2 and the design record read them).')
    rows_out = dict(status=STATUS, population=f'{len(dec["rowids"]):,} K1 training rows outside the withheld rooms', chosen_arm=chosen,
                    chosen=rewrite.get(chosen) if chosen else None, arms=rewrite, withheld_rows=len(withheld_rows),
                    k1_rows_naming_heater_or_coat_hanger=heater_coat,
                    k1_rows_naming_heater_or_coat_hanger_1037=sum(any(n in ('heater', 'coat hanger') for n in r['operands']) for d in data for r in d['rows']),
                    design_lane_count=91, k1_rows_total=len(dec['rowids']), routed_rows_of_N=routed, definition=rules['rows_to_rewrite'])
    phrase_set = [dict(name=n, phrases=phrases(final.get(n, 'raw'), n), variant=final.get(n, 'raw'),
                       mode=MODES[chosen] if chosen and final.get(n, 'raw') != 'raw' else 'raw name',
                       evidence=dec['evidence'][chosen]['all_rooms'].get(n) if chosen else None) for n in sorted(full['byname'])]
    open_names = []
    for n, a in OPEN_PAIRS:
        x = dec['names'][n]
        open_names.append(dict(name=n, alias=a, status='open until part 2', objects=x['objects'], operands=x['operands'],
                               fit_objects=x['W1']['fit_objects'], on_target_raw=x['W1']['fit_counts']['raw'],
                               on_target_alias_alone=x['W1']['fit_counts']['q:'+a], on_target_second_call=x['W2c']['fit_counts']['call:'+a],
                               policy_now='raw', reason=OPEN_REASON))
    verdict = (f'{chosen} passes phrase_worth and phrase_safe on the {len(dec["rowids"]):,} decision rows; its policies, refit on the '
               f'{dec["rooms"]} rooms outside the withheld rooms, are in PHRASE_SET.json. Status: {STATUS}.' if chosen else
               f'No eligible arm passes phrase_worth and phrase_safe; the model keeps writing the raw name. Status: {STATUS}.')
    strip = lambda reports: {a: {k: v for k, v in r.items() if k != 'stats'} for a, r in reports.items()}
    decision = dict(status=STATUS,
                    bars_file=dict(path=str(BARS), sha256=frozen, written_utc=rules['written_utc'], written_before_any_score=False,
                                   hash_matches_work_sha256=True, previous_sha256=rules['registration']['bars_file']['sha256'],
                                   registration=rules['registration']),
                    population=pop, parity=dict(verdict='PASS', rows=1037, matched=1037-len(misses)),
                    bars=dec['bars'], bars_1037=full['bars'], eligible_arms=list(ELIGIBLE), tool_change_diagnostics={'W2': ROLE['W2']},
                    shippable_passing=dec['passing'], shippable_passing_1037=full['passing'], chosen_arm=chosen, chosen_arm_1037=full['chosen'],
                    ceiling=ceiling(dec), ceiling_1037=ceiling(full), verdict=verdict,
                    both_good_rows=len(full['good_rows']), worse_operand_table=worse_table, checks=check_summary,
                    fold_choices=nonraw(dec['choices']), fold_choices_1037=nonraw(full['choices']),
                    fold_evidence=dec['evidence'], fold_evidence_1037=full['evidence'],
                    arms=strip(dec['reports']), arms_1037=strip(full['reports']), by_name=dec['names'], by_name_1037=full['names'],
                    open_until_part2=open_names, serving_score=SERVING_NOTE,
                    rows_to_rewrite=dict(chosen=rows_out['chosen'], routed_rows_of_N=routed),
                    review=rules['registration']['review'], rules=rules, heldout_opened=False, devs1_opened=False)
    K.OUT.mkdir(exist_ok=True)
    code = {str(p): K.sha(p) for p in sorted(K.HERE.glob('*.py'))+[K.HERE/'run.sh', K.HERE/'launch.sh']}
    pins.update(code); pins[str(K.WORK/'A0_ROWS.json')] = K.sha(K.WORK/'A0_ROWS.json'); pins[str(BARS)] = frozen
    for p in list(K.CAPS.glob('*.json.gz'))+list(K.RECALL.glob('*.json.gz')):
        pins[str(p)] = K.sha(p)
    def dump(name, obj):
        (K.OUT/name).write_text(json.dumps(T.clean(dict(obj, input_sha256=pins)), indent=1, allow_nan=False)+'\n')
    dump('DECISION.json', decision)
    dump('STATS.json', dict(population='all 1,037 K1 training rows', stats={a: r['stats'] for a, r in full['reports'].items() if 'stats' in r}))
    dump('PHRASE_SET.json', dict(status=STATUS if chosen else 'raw_name', arm=chosen, bars_sha256=frozen,
                                 refit=f'the {dec["rooms"]} training rooms outside the withheld rooms, same rule; the {full["rooms"]}-room refit gives the same policies',
                                 names=phrase_set, changed={p['name']: p['phrases'] for p in phrase_set if p['variant'] != 'raw'},
                                 open_until_part2=[f'{o["name"]}/{o["alias"]}' for o in open_names], serving_score=SERVING_NOTE))
    dump('ROWS_TO_REWRITE.json', rows_out)
    obj_out = [dict({k: o[k] for k in ['capture', 'room', 'fold', 'dataset', 'name', 'instance', 'aliases', 'in_dictionary', 'variants', 'calls',
                                       'fills', 'keys', 'prompts', 'rows', 'recall', 'recall_lift']},
                    withheld_room=o['capture'] in WITHHELD, arm_variant={a: full['choices'][a][str(o['fold'])][o['name']] for a in full['choices']})
               for o in objs]
    dump('OBJECTS.json', dict(objects=obj_out, count=len(obj_out)))
    with (K.OUT/'PER_ITEM.jsonl').open('w') as f:
        for a in PRICED:
            for r in full['arms'][a]:
                src = r.pop('source_file')
                r['withheld_room'] = r['capture'] in WITHHELD
                r['input_sha256'] = {src: pins[src], str(K.WORK/'A0_ROWS.json'): pins[str(K.WORK/'A0_ROWS.json')], str(BARS): frozen}
                r['a0_prediction'] = a0[r['row_id']]['prediction']
                f.write(json.dumps(T.clean(r), allow_nan=False)+'\n')
    import report
    report.write(decision, rows_out, phrase_set)
    (K.HERE/'STATUS.md').write_text(
        f'Stage 3 rebuilt (review sb_phrev corrections; {STATUS}). Parity 1,037/1,037. Bars file sha256 {frozen[:16]} records '
        'written_before_any_score = false and the registration facts. Decision population: '
        f'{len(dec["rowids"]):,} rows outside the withheld rooms; chosen arm {chosen or "none (raw name)"}; passing eligible arms: '
        f'{", ".join(dec["passing"]) or "none"}; W2 is a tool-change diagnostic. Arms, bars and decision in out/DECISION.json; report out/PHRASE_REPORT.md.\n')
    summary = lambda pop: {a: dict(mra=round(pop['reports'][a]['mra'], 4), d=round(pop['reports'][a]['gain']['estimate'], 4),
                                   ci=[round(x, 4) for x in pop['reports'][a]['gain']['ci95']], safe=round(pop['reports'][a]['safe']['estimate'], 4),
                                   safe_ci=[round(x, 4) for x in pop['reports'][a]['safe']['ci95']], safe_rows=pop['reports'][a]['safe']['rows'],
                                   rows=pop['reports'][a]['rows']) for a in PRICED}
    print(json.dumps(dict(decision=summary(dec), all_rows=summary(full)), indent=1))
    print('chosen', chosen, 'passing', dec['passing'], 'passing_1037', full['passing'], 'withheld rows', len(withheld_rows),
          'heater', withheld['heater_rows'], 'policy changes', policy_changes, 'checks', check_summary)

if __name__ == '__main__':
    main()
