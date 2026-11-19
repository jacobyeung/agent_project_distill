"""Phrase kit (sb_mask_phrase) on the 1,012 rows outside the withheld rooms (bash run.sh phrase_1012.py).
Part A re-scores P0, W1, W2, W2c from the kit's PER_ITEM.jsonl with its bar code. Part B reruns its fold choice with the
withheld captures removed from every fit fold, rebuilds the W arms from its priced pools (work/caps2) and applies the bars."""
import gzip, json, sys
from common import B, OUT, PINS, pin, sha, write, rowset

PHRASE = B/'sb_mask_phrase'
sys.path.insert(0, str(PHRASE))
import aggregate as AG  # noqa: E402  (imports kit, train_pricing, summarize_train read-only)
K, S, T, M = AG.K, AG.S, AG.T, AG.M
BARS_SHA = '150d16a232b42d86b33c6df792133f3a001d92f7b3b723c96dfc3391f0f17bc6'
ARMS = ('P0', 'W1', 'W2', 'W2c')


def bars_of(reports):
    """aggregate.main's bar block, verbatim in its thresholds."""
    bars = {}
    for a in AG.SHIPPABLE:
        g, s = reports[a]['gain'], reports[a]['safe']
        bars[a] = dict(phrase_worth=dict(verdict='PASS' if g['estimate'] >= 1.5 and g['ci95'][0] > 0 else 'FAIL', estimate=g['estimate'], ci95=g['ci95']),
                       phrase_safe=dict(verdict='PASS' if s['ci95'][0] > -1.0 else 'FAIL', rows=s['rows'], estimate=s['estimate'], ci95=s['ci95']))
    passing = [a for a in AG.SHIPPABLE if bars[a]['phrase_worth']['verdict'] == 'PASS' and bars[a]['phrase_safe']['verdict'] == 'PASS']
    chosen = max(passing, key=lambda a: (reports[a]['mra'], -AG.SHIPPABLE.index(a))) if passing else None
    return bars, passing, chosen


def score(arms, a0, good, ids):
    out = {}
    for a, rows in arms.items():
        rows = [r for r in rows if r['row_id'] in ids]; assert {r['row_id'] for r in rows} == ids, a
        safe = [r for r in rows if r['row_id'] in good]
        out[a] = dict(rows=len(rows), rooms=len({r['room'] for r in rows}), mra=AG.mra(rows), refusals=sum(r['prediction'] is None for r in rows),
                      gain=S.contrast(rows, [a0[r['row_id']] for r in rows]), safe=S.contrast(safe, [a0[r['row_id']] for r in safe]))
    return out


def main():
    assert sha(PHRASE/'out/BARS.json') == BARS_SHA == T.read(K.WORK/'BARS.sha256').decode().split()[0]
    rules = json.loads(T.read(PHRASE/'out/BARS.json'))
    legality = json.loads(open(OUT/'LEGALITY.json').read()); pin(OUT/'LEGALITY.json')
    withheld = {c['capture'] for c in legality['withheld_captures']}
    ids = set(rowset('K1_TRAIN_1012.txt')); full_ids = set(T.read(K.IDS).decode().splitlines())
    files = sorted(K.CAPS.glob('*.json.gz')); rfiles = sorted(K.RECALL.glob('*.json.gz')); assert len(files) == len(rfiles) == 209
    data = []
    for p in files:
        d = json.loads(gzip.decompress(T.read(p))); d['_file'] = str(p); data.append(d)
    recall = {d['capture']: d for d in (json.loads(gzip.decompress(T.read(p))) for p in rfiles)}
    a0 = json.loads(T.read(K.WORK/'A0_ROWS.json'))['rows']['A0_deployed']
    decision = json.loads(T.read(PHRASE/'out/DECISION.json'))
    per = {}
    for line in T.read(PHRASE/'out/PER_ITEM.jsonl').decode().splitlines():
        r = json.loads(line); per.setdefault(r['arm'], []).append(r)
    cat = {(d['capture'], n): o['keys'][o['variants']['raw']]['category'] for d in data for n, o in d['names'].items()}
    worse = {r['id']: min((cat[(d['capture'], n)] for n in r['operands']), key=AG.WORSE.index) for d in data for r in d['rows']}
    good = {i for i, w in worse.items() if w == 'good'}

    # Parity: the kit's registered numbers on 1,037 from PER_ITEM.jsonl, and its fold choice from its own objects.
    rep_full = score({a: per[a] for a in ARMS}, a0, good, full_ids)
    bars_full, passing_full, chosen_full = bars_of(rep_full)
    objs = AG.objects_of(data, recall)
    choices, evidence, byname = AG.fold_choices(objs)
    nonraw = lambda c: {a: {k: {n: v for n, v in x.items() if v != 'raw'} for k, x in c[a].items()} for a in c}
    parity = dict(bars=all(bars_full[a][b]['verdict'] == decision['bars'][a][b]['verdict'] and bars_full[a][b]['estimate'] == decision['bars'][a][b]['estimate']
                           and bars_full[a][b]['ci95'] == decision['bars'][a][b]['ci95'] for a in AG.SHIPPABLE for b in ('phrase_worth', 'phrase_safe')),
                  chosen=chosen_full == decision['chosen_arm'] and passing_full == decision['shippable_passing'],
                  safe_rows=len(good) == decision['both_good_rows'], fold_choices=nonraw(choices) == decision['fold_choices'],
                  fold_evidence=json.loads(json.dumps(evidence)) == decision['fold_evidence'])
    rebuilt = {a: {r['row_id']: r['prediction'] for r in AG.arm_rows(data, a, (lambda d, n, a=a: choices[a][str(d['fold'])][n]) if a in AG.SHIPPABLE else (lambda d, n: 'raw'))} for a in ARMS}
    parity['caps2_rebuild_equals_per_item'] = all(rebuilt[a] == {r['row_id']: r['prediction'] for r in per[a]} for a in ARMS)
    assert all(parity.values()), parity

    # Part A: registered fold policies, 1,012 rows.
    rep_a = score({a: per[a] for a in ARMS}, a0, good, ids)
    bars_a, passing_a, chosen_a = bars_of(rep_a)

    # Part B: fold choice refit without the withheld captures, W arms rebuilt from the priced pools.
    kept = [d for d in data if d['capture'] not in withheld]
    assert {r['id'] for d in kept for r in d['rows']} == ids
    fit = [o for o in objs if o['capture'] not in withheld]
    choices_b, evidence_b, byname_b = AG.fold_choices(fit)
    arms_b = {a: AG.arm_rows(kept, a, (lambda d, n, a=a: choices_b[a][str(d['fold'])][n]) if a in AG.SHIPPABLE else (lambda d, n: 'raw')) for a in ARMS}
    rep_b = score(arms_b, a0, good, ids)
    bars_b, passing_b, chosen_b = bars_of(rep_b)
    final = choices_b[chosen_b]['all_rooms'] if chosen_b else {n: 'raw' for n in byname_b}
    rewrite = {n: sum(n in r['operands'] for d in kept for r in d['rows']) for n, v in final.items() if v != 'raw'}
    heater = dict(objects_1037=len(byname['heater']), objects_fit_1012=len(byname_b['heater']),
                  withheld_heater_objects=[o['capture'] for o in byname['heater'] if o['capture'] in withheld],
                  folds_1037={k: choices['W1'][k]['heater'] for k in choices['W1']}, folds_1012={k: choices_b['W1'][k]['heater'] for k in choices_b['W1']},
                  evidence_1012={k: evidence_b['W1'][k]['heater'] for k in evidence_b['W1']})
    withheld_names = sorted({o['name'] for o in objs if o['capture'] in withheld})
    verdicts = {a: {b: dict(v1037=bars_full[a][b]['verdict'], v1012_registered=bars_a[a][b]['verdict'], v1012_refit=bars_b[a][b]['verdict'],
                            changes=bars_full[a][b]['verdict'] != bars_b[a][b]['verdict']) for b in ('phrase_worth', 'phrase_safe')} for a in AG.SHIPPABLE}
    PINS.update(T.PINS)
    for p in [PHRASE/'aggregate.py', PHRASE/'kit.py', PHRASE/'out/BARS.json', PHRASE/'out/PER_ITEM.jsonl', PHRASE/'out/DECISION.json']:
        pin(p)
    write('PHRASE_1012.json', dict(
        scope='sb_mask_phrase part 1 on K1_TRAIN_1012; bars from out/BARS.json (sha256 150d16a2...), contrast = summarize_train.contrast '
              '(10,000 room draws, seed 20261119); safe rows = both operands good under A0, restricted to the 1,012.',
        bars_rules=rules['bars'], parity_1037=parity, withheld_captures=sorted(withheld), names_in_withheld_captures=withheld_names,
        v1037=dict(arms=rep_full, bars=bars_full, passing=passing_full, chosen=chosen_full),
        v1012_registered_policies=dict(arms=rep_a, bars=bars_a, passing=passing_a, chosen=chosen_a),
        v1012_refit_policies=dict(arms=rep_b, bars=bars_b, passing=passing_b, chosen=chosen_b, fold_choices=nonraw(choices_b),
                                  fold_choices_change=nonraw(choices_b) != nonraw(choices), fold_evidence=evidence_b,
                                  phrase_set_all_rooms={n: AG.phrases(v, n) for n, v in final.items() if v != 'raw'}, rows_to_rewrite=rewrite),
        heater=heater, verdicts=verdicts, safe_rows=dict(v1037=len(good), v1012=len(good & ids))))
    print(json.dumps(dict(parity=parity, verdicts=verdicts, chosen=[chosen_full, chosen_a, chosen_b], heater=heater,
                          fold_change=nonraw(choices_b) != nonraw(choices), names=withheld_names), indent=1))
    for a in ARMS:
        print(a, [round(x, 3) for x in (rep_full[a]['mra'], rep_a[a]['mra'], rep_b[a]['mra'], rep_b[a]['gain']['estimate'], *rep_b[a]['gain']['ci95'], *rep_b[a]['safe']['ci95'])])


if __name__ == '__main__':
    main()
