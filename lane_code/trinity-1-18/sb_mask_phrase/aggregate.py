"""Fold choices, arms, bars, decision and outputs from work/caps2 and work/recall2 (bash run.sh aggregate.py)."""
import collections, gzip, json, sys
import numpy as np
import kit as K
T, M, A = K.T, K.M, K.A
import summarize_train as S  # noqa: E402  (contrast: 10,000 room draws, seed 20261119; appearance)

BARS, BARS_SHA = K.OUT/'BARS.json', K.WORK/'BARS.sha256'
FIXED = {'P0': 'raw', 'P_cap100': 'cap100'}
SHIPPABLE = ('W1', 'W2', 'W2c')
PREFIX = {'W1': 'q:', 'W2': 'fb:', 'W2c': 'call:'}
PRICED = ('P0', 'P_cap100', 'W1', 'W2', 'W2c')
OFFLINE = ('P_all', 'P_cf')
TABLE_ARMS = ('P0', 'P_all', 'P_cf', 'P_cap100', 'W1', 'W2', 'W2c')
WORSE = ('refused', 'wrong_object', 'weak', 'poor_priced_frame', 'good')
MODES = {'W1': 'one call with this phrase', 'W2': 'raw call; the alias fills the anchor frames where the raw pool is empty',
         'W2c': 'raw call; a second call with the alias when the first returns not seen'}
ROUTED_DEVS1 = 'sb_ktow3 routed file with sha256 prefix 8855c81e (a dev-S1 return set)'
ORDER_NOTE = ('The stopped session (pid 546869) priced its v1 arms into out/ at 10:11Z, before any bars file existed; this session wrote '
              'out/BARS.json at 10:12:21Z from the spec\'s prospective bars and the brief\'s arms before reading any score, moved the v1 '
              'outputs to work/stale_v1_out unread, and changed no bar or arm afterwards.')


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
    for arm in SHIPPABLE+('P_cf',):
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
    for n, os_ in sorted(byname.items()):
        rec = dict(objects=len(os_), operands=sum(len(o['rows']) for o in os_), aliases=os_[0]['aliases'])
        for arm in SHIPPABLE:
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
                            points=100*sum(M.mra(r['prediction'], r['label'])-M.mra(a0[r['row_id']]['prediction'], r['label']) for r in changed)/1037)
        rec['insample_best_without_min_fit'] = {arm: choose(os_, candidates(arm, os_[0]['aliases']), None, min_fit=0)[0] for arm in SHIPPABLE}
        rec['P_cf'] = dict(all_rooms=choices['P_cf']['all_rooms'][n], folds={k: choices['P_cf'][k][n] for k in map(str, range(5))})
        out[n] = rec
    return out


def rows_to_rewrite(data, choices, names_table, rowids):
    rows = [(d, r) for d in data for r in d['rows']]
    assert len(rows) == 1037 and {r['id'] for _, r in rows} == rowids
    by_arm = {}
    for arm in SHIPPABLE:
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
        by_arm[arm] = dict(names=changed, policies={n: phrases(fit[n], n) for n in changed}, k1_rows=len(ids),
                           k1_rows_by_name=dict(naming.most_common()), second_call_rows=len(sec_ids),
                           second_call_rows_by_name=dict(second.most_common()), under_five_objects_left_raw=small)
    heater_coat = sum(any(n in ('heater', 'coat hanger') for n in r['operands']) for _, r in rows)
    return by_arm, heater_coat


def blocker(misses):
    K.OUT.mkdir(exist_ok=True)
    (K.HERE/'BLOCKER.md').write_text('# BLOCKER: P0 differs from A0_deployed\n\n'+f'{len(misses)} of 1,037 predictions differ. First rows:\n\n'
                                     +'\n'.join(f'- {m}' for m in misses[:20])+'\n\nThe kit stops here; no arm is reported.\n')
    (K.HERE/'STATUS.md').write_text(f'BLOCKED: parity failed on {len(misses)} of 1,037 rows; see BLOCKER.md.\n')
    sys.exit(1)


def main():
    frozen = T.read(BARS_SHA).decode().split()[0]
    assert K.sha(BARS) == frozen, 'out/BARS.json changed after it was frozen'
    rules = json.loads(T.read(BARS))
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
    objs = objects_of(data, recall)
    consistent = sum(o['keys'][o['variants']['raw']]['pool_recall'] == o['recall']['raw']
                     and o['keys'][o['variants']['raw']]['pool_recall_lift'] == o['recall_lift']['raw'] for o in objs)
    check_summary['raw_recall_caps_equals_recall_pass'] = f'{consistent}/{len(objs)}'
    choices, evidence, byname = fold_choices(objs)
    arms = {a: arm_rows(data, a, lambda d, n, v=v: v) for a, v in FIXED.items()}
    for a in SHIPPABLE:
        arms[a] = arm_rows(data, a, lambda d, n, a=a: choices[a][str(d['fold'])][n])
    p0 = {r['row_id']: r for r in arms['P0']}
    assert set(p0) == rowids == set(a0)
    misses = [dict(row=i, p0=p0[i]['prediction'], a0=a0[i]['prediction']) for i in sorted(rowids) if p0[i]['prediction'] != a0[i]['prediction']]
    if misses:
        blocker(misses)
    assert all(p0[i]['label'] == a0[i]['label'] and p0[i]['room'] == a0[i]['room'] for i in rowids)
    cat = {(d['capture'], n): o['keys'][o['variants']['raw']]['category'] for d in data for n, o in d['names'].items()}
    worse = {r['id']: min((cat[(d['capture'], n)] for n in r['operands']), key=WORSE.index) for d in data for r in d['rows']}
    good_rows = {i for i, w in worse.items() if w == 'good'}
    reports = {a: arm_report(data, rows, a0, good_rows) for a, rows in arms.items()}
    reports['P_all'] = offline_report(objs, lambda o: 'all', False)
    reports['P_cf'] = offline_report(objs, lambda o: choices['P_cf'][str(o['fold'])][o['name']], True)
    worse_table = {}
    for w in WORSE:
        ids = [i for i in sorted(rowids) if worse[i] == w]
        worse_table[w] = dict(rows=len(ids), a0=mra([a0[i] for i in ids]), a2=mra([a2[i] for i in ids]),
                              points_of_gap=(mra([a2[i] for i in ids])-mra([a0[i] for i in ids]))*len(ids)/1037 if ids else 0.)
    bars = {}
    for a in SHIPPABLE+('P_cap100',):
        g, s = reports[a]['gain'], reports[a]['safe']
        bars[a] = dict(phrase_worth=dict(verdict='PASS' if g['estimate'] >= 1.5 and g['ci95'][0] > 0 else 'FAIL', estimate=g['estimate'], ci95=g['ci95']),
                       phrase_safe=dict(verdict='PASS' if s['ci95'][0] > -1.0 else 'FAIL', rows=s['rows'], estimate=s['estimate'], ci95=s['ci95']),
                       role='bar' if a in SHIPPABLE else 'diagnostic (reads no bar)')
    passing = [a for a in SHIPPABLE if bars[a]['phrase_worth']['verdict'] == 'PASS' and bars[a]['phrase_safe']['verdict'] == 'PASS']
    chosen = max(passing, key=lambda a: (reports[a]['mra'], -SHIPPABLE.index(a))) if passing else None
    final = choices[chosen]['all_rooms'] if chosen else {n: 'raw' for n in byname}
    names_table = name_table(byname, arms, a0, choices, evidence)
    rewrite, heater_coat = rows_to_rewrite(data, choices, names_table, rowids)
    routed = dict(status='MISSING', owner='tree_rebuild', count=None,
                  expected='N\'s routed training rows (rows carrying <ground obj=...> calls), held by tree_rebuild; not on trinity-1-18',
                  not_opened=[ROUTED_DEVS1+': the binding brief keeps it closed',
                              '/scratch/jjyeung/n30_mirror/rows_r1 (store v7 and its slices): unrouted store rows; its STATUS.md records rows on '
                              'K1 held-out rooms in the store family (v6), so the kit did not open it'])
    rows_out = dict(chosen_arm=chosen, chosen=rewrite.get(chosen) if chosen else None, arms=rewrite,
                    k1_rows_naming_heater_or_coat_hanger=heater_coat, design_lane_count=91, k1_rows_total=1037, routed_rows_of_N=routed,
                    definition=rules['rows_to_rewrite'])
    phrase_set = [dict(name=n, phrases=phrases(final[n], n), variant=final[n], mode=MODES[chosen] if chosen and final[n] != 'raw' else 'raw name',
                       evidence=evidence[chosen]['all_rooms'][n] if chosen else None) for n in sorted(byname)]
    decision = dict(bars_file=dict(path=str(BARS), sha256=frozen, written_utc=rules['written_utc'], verified_unchanged=True, order=ORDER_NOTE),
                    parity=dict(verdict='PASS', rows=1037, matched=1037-len(misses)),
                    bars=bars, shippable_passing=passing, chosen_arm=chosen,
                    ceiling=dict(arm='P_cf', priced=False, pool_recall=reports['P_cf']['pool_recall'], pool_recall_lift=reports['P_cf']['pool_recall_lift'],
                                 operands=reports['P_cf']['operands'], reason=reports['P_cf']['reason']),
                    verdict=(f'{chosen} passes phrase_worth and phrase_safe; its all-room policies are frozen in PHRASE_SET.json for the model to write in its ground call.'
                             if chosen else 'No shippable arm passes phrase_worth and phrase_safe; the model keeps writing the raw name.'),
                    both_good_rows=len(good_rows), worse_operand_table=worse_table, checks=check_summary,
                    fold_choices={a: {k: {n: v for n, v in c.items() if v != 'raw'} for k, c in choices[a].items()} for a in choices},
                    fold_evidence=evidence, arms={a: {k: v for k, v in r.items() if k != 'stats'} for a, r in reports.items()},
                    by_name=names_table, rows_to_rewrite=dict(chosen=rows_out['chosen'], routed_rows_of_N=routed),
                    rules=rules, heldout_opened=False, devs1_opened=False)
    K.OUT.mkdir(exist_ok=True)
    code = {str(p): K.sha(p) for p in sorted(K.HERE.glob('*.py'))+[K.HERE/'run.sh', K.HERE/'launch.sh']}
    pins.update(code); pins[str(K.WORK/'A0_ROWS.json')] = K.sha(K.WORK/'A0_ROWS.json'); pins[str(BARS)] = frozen
    for p in list(K.CAPS.glob('*.json.gz'))+list(K.RECALL.glob('*.json.gz')):
        pins[str(p)] = K.sha(p)
    def dump(name, obj):
        (K.OUT/name).write_text(json.dumps(T.clean(dict(obj, input_sha256=pins)), indent=1, allow_nan=False)+'\n')
    dump('DECISION.json', decision)
    dump('STATS.json', dict(stats={a: r['stats'] for a, r in reports.items() if 'stats' in r}))
    dump('PHRASE_SET.json', dict(status='frozen' if chosen else 'raw_name', arm=chosen, refit='all 192 training rooms, same rule', bars_sha256=frozen,
                                 names=phrase_set, changed={p['name']: p['phrases'] for p in phrase_set if p['variant'] != 'raw'}))
    dump('ROWS_TO_REWRITE.json', rows_out)
    obj_out = [dict({k: o[k] for k in ['capture', 'room', 'fold', 'dataset', 'name', 'instance', 'aliases', 'in_dictionary', 'variants', 'calls',
                                       'fills', 'keys', 'prompts', 'rows', 'recall', 'recall_lift']},
                    arm_variant={a: choices[a][str(o['fold'])][o['name']] for a in choices}) for o in objs]
    dump('OBJECTS.json', dict(objects=obj_out, count=len(obj_out)))
    with (K.OUT/'PER_ITEM.jsonl').open('w') as f:
        for a in PRICED:
            for r in arms[a]:
                src = r.pop('source_file')
                r['input_sha256'] = {src: pins[src], str(K.WORK/'A0_ROWS.json'): pins[str(K.WORK/'A0_ROWS.json')], str(BARS): frozen}
                r['a0_prediction'] = a0[r['row_id']]['prediction']
                f.write(json.dumps(T.clean(r), allow_nan=False)+'\n')
    import report
    report.write(decision, rows_out, phrase_set)
    (K.HERE/'STATUS.md').write_text(f'Stage 3 (priced): parity 1,037/1,037. Bars file sha256 {frozen[:16]} verified unchanged. '
                                    f'Chosen arm: {chosen or "none (raw name)"}; passing shippable arms: {", ".join(passing) or "none"}. '
                                    'Arms, bars and decision in out/DECISION.json; report out/PHRASE_REPORT.md. Tests and archive next.\n')
    print(json.dumps({a: dict(mra=round(reports[a]['mra'], 3), d=round(reports[a]['gain']['estimate'], 3), lo=round(reports[a]['gain']['ci95'][0], 3),
                              safe_lo=round(reports[a]['safe']['ci95'][0], 3)) for a in PRICED}, indent=1))
    print('offline', {a: (reports[a]['pool_recall'], reports[a]['pool_recall_lift']) for a in OFFLINE})
    print('chosen', chosen, 'good rows', len(good_rows), 'checks', check_summary)


if __name__ == '__main__':
    main()
