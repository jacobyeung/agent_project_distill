"""Box ladder (sb_kbox4) on the 1,012 rows outside the withheld rooms (bash run.sh kbox_1012.py).
Imports summarize_train read-only; decide() is its 'final' block with the rowsets as arguments and is checked
for exact parity against the kit's FREEZE.json, DECISION.json and SUMMARY_TRAIN.json on the 1,037 rows first."""
import json, sys
from common import B, OUT, PINS, pin, write, rowset, clean

KBOX = B/'sb_kbox4'
sys.path.insert(0, str(KBOX))
import summarize_train as S  # noqa: E402
import serving_reference as R  # noqa: E402
import math_v2 as M  # noqa: E402


def norm(x):
    return json.loads(json.dumps(clean(x), allow_nan=False))


def decide(base, extras, rowids, tableids, a8=None):
    arms = S.byarm(base)
    for a, rows in arms.items():
        assert {r['row_id'] for r in rows} == (tableids if a == 'A1_oracle_select' else rowids), a
    frozen, cf = S.freeze(arms)
    items = base+extras+cf
    if a8 is not None:
        assert {r['row_id'] for r in a8} == tableids
        items = [r for r in items if r['arm'] != 'A8_nonull_best1']+a8
    arms = S.byarm(items); missing = []
    if frozen['frozen_variant']:
        items += [dict(r, arm='obj_frozen', chosen_arm=frozen['frozen_variant']['arm']) for r in arms[frozen['frozen_variant']['arm']]]
        arms = S.byarm(items)
    a0 = arms['A0_deployed']; a0t = [r for r in a0 if r['row_id'] in tableids]
    contrasts = {'object_cf_minus_A0': frozen['object_gain'], 'fused_cf_minus_A2': frozen['fused_gain'],
                 'A1_minus_A0_tables': S.contrast(arms['A1_oracle_select'], a0t), 'A2_minus_A0': S.contrast(arms['A2_gt_masks'], a0),
                 'A8_nonull_minus_A0_tables': S.contrast(arms['A8_nonull_best1'], a0t),
                 'size_obj_cf_minus_A0': S.contrast(S.sizes(arms['obj_cf']), S.sizes(a0)),
                 'A9_today_minus_A0': S.contrast(arms['A9_s4_today'], a0)}
    if 'obj_frozen' in arms:
        # The kit priced A5, A8 object, A7 frozen and A9 object only for a frozen variant; none existed on 1,037.
        missing.append('frozen object variant on 1,012: A5/A8_obj/A7_frozen/A9_obj need pricing')
    p = frozen['merge_safe']['precision']; sz = contrasts['size_obj_cf_minus_A0']; sel = contrasts['A8_nonull_minus_A0_tables']
    decisions = dict(replace_box=dict(verdict='PASS' if frozen['replace_box_part1'] else 'FAIL', scope='part 1 only; tower_frames part 2 required', evidence=frozen['object_gain']),
        fused_path=dict(verdict='PASS' if frozen['fused_gain']['estimate'] >= 3 and frozen['fused_gain']['ci95'][0] > 0 else 'FAIL', evidence=frozen['fused_gain']),
        merge_safe=dict(verdict='NA' if p is None else 'PASS' if p >= .9 else 'FAIL', evidence=frozen['merge_safe']),
        selector_worth=dict(verdict='PASS' if contrasts['A1_minus_A0_tables']['estimate'] >= 4 else 'FAIL', evidence=contrasts['A1_minus_A0_tables']),
        selector_adopt=dict(verdict='PASS' if sel['ci95'][0] > 0 else 'FAIL', evidence=sel, primary_arm='A8_nonull_best1; fixed before scoring'),
        size_screen=dict(verdict='PASS' if sz['estimate'] >= 5 and sz['ci95'][0] > 0 else 'FAIL', evidence=sz),
        first_seen_screen=dict(verdict='PASS' if max(frozen['first_linker']['rate'] or 0, frozen['first_object_cf']['rate'] or 0) >= .9 else 'FAIL',
                               linker=frozen['first_linker'], object_oof=frozen['first_object_cf'], object_frozen=frozen['first_object_frozen']),
        tower_challenger=dict(verdict='REPORT_ONLY', evidence={k: v for k, v in contrasts.items() if k.startswith('A7')}))
    if frozen['fused_gain']['estimate'] < 1:
        decisions['fused_path']['interpretation'] = 'the single view is not the limit under this tower'
    if not frozen['frozen_variant']:
        decisions['tower_challenger'] = dict(verdict='SKIPPED', reason='No eligible frozen object variant; best1 tower rows remain diagnostic')
    summary = {a: dict(rows=len(rs), rooms=len({r['room'] for r in rs}), mra=S.mean(rs), refusals=sum(r['prediction'] is None for r in rs),
                       size_mra=S.mean(S.sizes(rs)), objects=len(S.objects(rs)), precision=S.precision(rs), first_seen=S.appearance(rs),
                       ci95=S.contrast(rs, [dict(r, prediction=None) for r in rs])['ci95'],
                       selection='cross-fitted' if a in ('obj_cf', 'fused_cf', 'first_object_cf') else 'OOF selector' if a.startswith('A8') else 'in-sample')
               for a, rs in arms.items()}
    eligibility = []
    for tau in M.TAUS:
        rs = arms[f'A4_obj_{tau:.2f}_best1']
        eligibility.append(dict(tau=tau, all_train=S.precision(rs), other_four_folds={str(k): S.precision([r for r in rs if r['fold'] != k]) for k in range(5)}))
    return dict(freeze=frozen, contrasts=contrasts, bars=decisions, arms=summary, merge_eligibility=eligibility, missing=missing)


def main():
    base, extras = S.load('base'), S.load('extras')
    ids = set(R.read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    tables = set(R.read(R.ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    keep = set(rowset('K1_TRAIN_1012.txt')); keep_t = set(rowset('K1_TRAIN_TABLES_868.txt'))
    assert len(keep) == 1012 and len(keep_t) == 868 and keep_t == tables & keep

    full = decide(base, extras, ids, tables)
    kit_freeze = json.loads(R.read(R.OUT/'FREEZE.json')); kit_dec = json.loads(R.read(R.OUT/'DECISION.json'))
    kit_sum = json.loads(R.read(R.OUT/'SUMMARY_TRAIN.json')); kit_elig = json.loads(R.read(R.OUT/'MERGE_ELIGIBILITY.json'))
    parity = dict(freeze=all(norm(full['freeze'][k]) == kit_freeze[k] for k in full['freeze']),
                  bars=norm(full['bars']) == kit_dec['bars'], contrasts=norm(full['contrasts']) == kit_sum['contrasts'],
                  arms=norm(full['arms']) == kit_sum['arms'],
                  merge_eligibility=all(norm(e['all_train']) == k['all_train'] and norm(e['other_four_folds']) == k['other_four_folds']
                                        for e, k in zip(full['merge_eligibility'], kit_elig['rows'])))
    assert all(parity.values()), parity
    print('parity 1,037', parity, flush=True)

    sub = lambda rs: [r for r in rs if r['row_id'] in keep]
    registered = decide(sub(base), sub(extras), keep, keep_t)
    refit = json.loads(open(OUT/'A8_REFIT.json').read()); pin(OUT/'A8_REFIT.json')
    assert refit['parity']['passed']
    repriced = {r['row_id']: r for r in refit['repriced_rows']}
    a8 = [repriced.get(r['row_id'], r) for r in sub(extras) if r['arm'] == 'A8_nonull_best1']
    strict = decide(sub(base), sub(extras), keep, keep_t, a8=a8)

    bars = {}
    for k in full['bars']:
        v0, v1, v2 = full['bars'][k]['verdict'], registered['bars'][k]['verdict'], strict['bars'][k]['verdict']
        bars[k] = dict(v1037=v0, v1012=v2, v1012_registered_selector=v1, changes=v0 != v2)
    freeze_changes = {k: dict(v1037=norm(full['freeze'][k]), v1012=norm(strict['freeze'][k]))
                      for k in ['frozen_variant', 'fused_frozen', 'object_folds', 'fused_folds', 'appearance_tau', 'appearance_folds',
                                'appearance_source', 'replace_box_part1', 'merge_safe']}
    for k, v in freeze_changes.items():
        a, b = v['v1037'], v['v1012']
        if k == 'fused_frozen' or k == 'fused_folds':  # selection-train MRA moves with the rows; the choice is the rule
            pick = (lambda x: x and x['arm']) if k == 'fused_frozen' else (lambda x: {f: y and y['arm'] for f, y in x.items()})
            v['choice_changes'] = pick(a) != pick(b)
        else:
            v['choice_changes'] = a != b
    PINS.update(R.PINS)
    write('KBOX_1012.json', dict(
        scope='sb_kbox4 LADDER_TRAIN re-reported on K1_TRAIN_1012 (tables: K1_TRAIN_TABLES_868); same code, registered folds, '
              '10,000 room draws, seed 20261119. Cross-fitted choices (object variant, GT fusion rule, appearance tau) are refit on '
              'the 1,012 rows; the A8 selector is refit with withheld-room objects removed from every fit fold (A8_REFIT.json).',
        parity_1037=parity, bars=bars, freeze=freeze_changes,
        v1037=dict(contrasts=full['contrasts'], arms=full['arms'], merge_eligibility=full['merge_eligibility']),
        v1012=dict(contrasts=strict['contrasts'], arms=strict['arms'], merge_eligibility=strict['merge_eligibility'], bars=strict['bars'],
                   freeze=strict['freeze'], missing=strict['missing']),
        v1012_registered_selector=dict(contrast=registered['contrasts']['A8_nonull_minus_A0_tables'], arm=registered['arms']['A8_nonull_best1'],
                                       note='A8 OOF choices from the kit folds, whose fits saw withheld-room objects; diagnostic only')))
    print(json.dumps(bars, indent=1))
    print(json.dumps({k: v['choice_changes'] for k, v in freeze_changes.items()}))


if __name__ == '__main__':
    main()
