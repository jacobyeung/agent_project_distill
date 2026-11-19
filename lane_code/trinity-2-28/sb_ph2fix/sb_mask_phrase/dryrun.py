"""CPU dry run (spec steps 1-4) before any priced number.

    bash run.sh dryrun.py a0        stream the published PER_ITEM once; keep A0_deployed/A2 rows of the 1,037 ids
    bash run.sh dryrun.py report    steps 1-4 from work/caps2 (dry captures) and work/recall2 (all) -> out/DRYRUN.json
"""
import collections, gzip, json, re, sys
from pathlib import Path
import kit as K
T = K.T

DRY = ['arkitscenes/41048124', 'arkitscenes/42897512', 'scannet/scene0201_02', 'scannetpp/036bce3393', 'scannetpp/067e2e4e61',
       'scannetpp/260fa55d50', 'scannetpp/07ff1c45bb']
PARITY5 = DRY[:5]
TRAIN239 = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_CAPTURES_TRAIN_239.txt')
HEAD = T.R.SEL/'work/run_iso'
HEAD_PINS = {'selector_head.json': '63aa0a69', 'selector_head.safetensors': '6d97c524'}
A0_ROWS = K.WORK/'A0_ROWS.json'
DESIGN = dict(raw=1804, P_all=1883, raw_lift=1757, best_single_lift=1828, P_all_lift=1856, operands=2074)


def a0():
    ids = set(T.read(K.IDS).decode().splitlines())
    rows = {}
    with K.PER_ITEM.open() as f:
        for line in f:
            arm = re.match(r'\{"arm": "([^"]+)"', line)[1]
            if arm in ('A0_deployed', 'A2_gt_masks'):
                r = json.loads(line)
                if r['row_id'] in ids:
                    rows.setdefault(arm, {})[r['row_id']] = {k: r[k] for k in ['row_id', 'room', 'capture', 'dataset', 'fold', 'prediction', 'label', 'refusal_code', 'diagnostics']}
    assert all(len(v) == 1037 for v in rows.values()) and len(rows) == 2
    K.WORK.mkdir(exist_ok=True)
    A0_ROWS.write_text(json.dumps(T.clean(dict(rows=rows, input_sha256={str(K.PER_ITEM): K.sha(K.PER_ITEM), str(K.IDS): K.sha(K.IDS)})), allow_nan=False))
    print('A0/A2 rows', {k: len(v) for k, v in rows.items()})


def labels_check(rowids, labels):
    """K1_LABELS_CORRECTED: parse only the lines of the 1,037 training ids."""
    seen = {}
    for line in T.read(K.LABELS).decode().splitlines():
        m = re.search(r'"id"\s*:\s*"([^"\\]+)"', line)
        if m and m[1] in rowids:
            r = json.loads(line); seen[r['id']] = r
    bad = [i for i in rowids if i not in seen or seen[i]['split'] != 'train' or seen[i]['corrected'] != labels[i]['corrected']]
    return dict(rows=len(seen), all_train=all(r['split'] == 'train' for r in seen.values()), mismatched=bad, passed=len(seen) == 1037 and not bad)


def recall_counts(files):
    """Row-weighted operand pool recall (2,074 operands) at the retention floor and at the lifting floor."""
    data = [json.loads(gzip.decompress(T.read(p))) for p in files]
    counts = collections.Counter(); gained = collections.defaultdict(collections.Counter)
    phrase_lift = collections.defaultdict(collections.Counter)
    for d in data:
        assert d['k1_split'] == 'train'
        for r in d['rows']:
            for n in r['operands']:
                pv = d['names'][n]['pools']; counts['operands'] += 1
                for v in ('raw', 'all', 'cap100'):
                    counts[v] += pv[v]['recall']; counts[v+'_lift'] += pv[v]['recall_lift']
                for v, x in pv.items():
                    if v == 'raw' or v.startswith('q:'):
                        phrase_lift[n][v] += x['recall_lift']
                if pv['all']['recall'] and not pv['raw']['recall']:
                    gained[n]['gained'] += 1
                if pv['raw']['recall'] and not pv['all']['recall']:
                    gained[n]['lost'] += 1
                counts['mixed_presence_frames_all'] += pv['all']['mixed_presence_frames']
    best = {n: max(c, key=lambda v: (c[v], v == 'raw')) for n, c in phrase_lift.items()}
    best_single = sum(phrase_lift[n][v] for n, v in best.items())
    got = dict(raw=counts['raw'], P_all=counts['all'], raw_lift=counts['raw_lift'], best_single_lift=best_single,
               P_all_lift=counts['all_lift'], operands=counts['operands'])
    return data, dict(captures=len(files), operands=counts['operands'], raw=counts['raw'], P_all=counts['all'], P_cap100=counts['cap100'],
                      raw_lift=counts['raw_lift'], P_all_lift=counts['all_lift'], P_cap100_lift=counts['cap100_lift'],
                      best_single_lift=best_single,
                      best_single_phrase={n: dict(phrase=v, lift_recall=phrase_lift[n][v], raw_lift_recall=phrase_lift[n]['raw'])
                                          for n, v in sorted(best.items()) if v != 'raw'},
                      P_all_frames_with_mixed_presence=counts['mixed_presence_frames_all'],
                      design=DESIGN, matches_design={k: got[k] == v for k, v in DESIGN.items()},
                      by_name={n: dict(v) for n, v in sorted(gained.items())})


def report():
    caps, ctx = K.setup(); labels, rowids, folds, truth, head, table, producer = ctx
    for f, p in HEAD_PINS.items():
        assert T.PINS[str(HEAD/f)].startswith(p), f
    for path, p in K.EXPECTED.items():
        assert K.pin(path).startswith(p), path
    train239 = set(T.read(TRAIN239).decode().split())
    # Step 4: folds by room, k1_split, rowsets.
    room_folds = collections.defaultdict(set)
    for c in caps:
        room_folds[c['room']].add(folds[c['room']])
    step4 = dict(captures=len(caps), rooms=len(room_folds), all_k1_train=all(c['k1_split'] == 'train' and c['split'] == 'train' for c in caps),
                 captures_in_train239=all(c['canonical'] in train239 for c in caps),
                 rows=sum(r['id'] in rowids for c in caps for r in c['rows']),
                 rooms_in_one_fold=all(len(v) == 1 for v in room_folds.values()),
                 fold_rooms={str(k): sum(1 for v in room_folds.values() if k in v) for k in range(5)},
                 fold_captures={str(k): sum(folds[c['room']] == k for c in caps) for k in range(5)},
                 fold_rows={str(k): sum(folds[c['room']] == k for c in caps for r in c['rows'] if r['id'] in rowids) for k in range(5)})
    step4['labels'] = labels_check(rowids, labels)
    step4['passed'] = (step4['captures'] == 209 and step4['rooms'] == 192 and step4['all_k1_train'] and step4['captures_in_train239']
                       and step4['rows'] == 1037 and step4['rooms_in_one_fold'] and step4['labels']['passed'])
    # Steps 1 and 3 on the dry captures.
    a0rows = json.loads(T.read(A0_ROWS))['rows']['A0_deployed']
    step1, step3 = [], dict(alias_calls=[], refused=[], survival_failed=[], identities_failed=[], table_mismatch=[], builder_failed=[], pools=0)
    for name in DRY:
        d = json.loads(gzip.decompress(T.read(K.CAPS/(name.replace('/', '__')+'.json.gz'))))
        for it in d['items']:
            if all(k == d['names'][n]['variants']['raw'] for n, k in it['keys'].items()) and name in PARITY5:
                step1.append(dict(capture=name, row_id=it['row_id'], p0=it['prediction'], a0=a0rows[it['row_id']]['prediction'],
                                  passed=it['prediction'] == a0rows[it['row_id']]['prediction']))
        step3['refused'] += d['reader_refused']
        step3['builder_failed'] += [dict(capture=name, **b) for b in d['builder_parity'] if not b['passed']]
        for ch in d['checks']:
            step3['pools'] += 1
            if ch['call'] != ch['name']:
                step3['alias_calls'].append(dict(capture=name, name=ch['name'], call=ch['call'], key=ch['key']))
            if not ch['survival']:
                step3['survival_failed'].append(dict(capture=name, **ch))
            if not ch['identities']:
                step3['identities_failed'].append(dict(capture=name, **ch))
            if ch['table'] is False:
                step3['table_mismatch'].append(dict(capture=name, **ch))
    step3['passed'] = bool(step3['alias_calls']) and not any(step3[k] for k in ('refused', 'survival_failed', 'identities_failed', 'table_mismatch', 'builder_failed'))
    step3['meaning'] = ('Every alias pool ran through StageOne with the alias as the call name (selector features built, no exception); per-proposal '
                        'score and presence after cache_for and lift equal the pool entries for every pool; fresh labels match the pool\'s candidate '
                        'identities; on the raw pool they equal the serving tables.')
    # Step 2: pool recall, all captures.
    _, step2 = recall_counts(sorted(K.RECALL.glob('*.json.gz')))
    step1_ok = len(step1) > 0 and all(r['passed'] for r in step1)
    passed = step4['passed'] and step1_ok and step3['passed'] and step2['captures'] == 209
    out = dict(status='PASS' if passed else 'FAIL', step1_parity_5_captures=dict(rows=len(step1), passed=sum(r['passed'] for r in step1), detail=step1),
               step2_pool_recall=step2, step3_reader_accepts_written_phrase=step3, step4_folds=step4, heldout_opened=False,
               note='Step 1 on all 1,037 rows is the parity bar in out/DECISION.json; step 2 reports the counts, it does not force them.')
    K.OUT.mkdir(exist_ok=True)
    (K.OUT/'DRYRUN.json').write_text(json.dumps(T.clean(dict(out, input_sha256=dict(T.PINS))), indent=1, allow_nan=False))
    print(json.dumps(T.clean({k: v for k, v in out.items() if k not in ('step1_parity_5_captures', 'step3_reader_accepts_written_phrase')}), indent=1)[:5000])
    print('step1', out['step1_parity_5_captures']['rows'], out['step1_parity_5_captures']['passed'])
    print('step3', {k: (len(v) if isinstance(v, list) else v) for k, v in step3.items() if k != 'meaning'})


if __name__ == '__main__':
    dict(a0=a0, report=report)[sys.argv[1]]()
