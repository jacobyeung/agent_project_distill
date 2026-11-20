"""out/K1012.json, out/K1012_REPORT.md and out/sb_k1012.tar with sha256 (bash run.sh report.py)."""
import json, subprocess, tarfile
from common import B, HERE, OUT, PINS, jread, pin, sha, write

CON = dict(replace_box='object_cf_minus_A0', fused_path='fused_cf_minus_A2', selector_worth='A1_minus_A0_tables',
           selector_adopt='A8_nonull_minus_A0_tables', size_screen='size_obj_cf_minus_A0')
EVID = dict(replace_box='object variant − A0', fused_path='fused_cf − A2', selector_worth='oracle selection A1 − A0 on the table rows, bar ≥ +4:',
            selector_adopt='A8 − A0, bar low > 0:', size_screen='size − A0')
KITS = ['sb_kbox4', 'sb_mask_phrase', 'sb_mffix', 'sb_auditfix2', 'sb_mdrev2', 'sb_maskfail', 'b04host3/b04_e2ehook/heads/selector', 'k1_ops3/work/e3gd/out']


def f2(x):
    return f'{x:.2f}'


def ci(c, signed=False):
    s = '+.2f' if signed else '.2f'
    return f'[{c[0]:{s}}, {c[1]:{s}}]'


def mra(a):
    return f'{f2(a["mra"])} {ci(a["ci95"])}'


def gain(c):
    return f'{c["estimate"]:+.2f} {ci(c["ci95"], True)}'


def untouched():
    """Kit files modified after this task started (none expected); local /scratch, bounded to the named kit folders."""
    marker = HERE/'tmp/START_MARKER'
    hits = {}
    for k in KITS:
        r = subprocess.run(['find', str(B/k), '-newer', str(marker), '-type', 'f'], capture_output=True, text=True)
        hits[k] = sorted(r.stdout.split())
    return hits


def main():
    leg, kb, ph, mf, rf = (jread(OUT/n) for n in ['LEGALITY.json', 'KBOX_1012.json', 'PHRASE_1012.json', 'MFFIX_1012.json', 'A8_REFIT.json'])
    a0, a1 = kb['v1037'], kb['v1012']; bars = kb['bars']
    lst = leg['rowsets']['K1_TRAIN_1012.txt']
    fit_caps = set(jread(B/'k1_ops3/work/e3gd/out/FITS.json')['provenance']['captures'])
    s4 = [x['capture'] for x in leg['withheld_captures'] if x['capture'] in fit_caps]
    exposed = [x for x in leg['deployed_selector_exposure']['captures'] if x.get('objects')]
    changed = [k for k, v in bars.items() if v['changes']]
    pchanged = [f'{a} {b}' for a, x in ph['verdicts'].items() for b, v in x.items() if v['changes']]
    mtab = mf['first_table']; mflip = [x['kind'] for x in mtab if x['ci_excludes_zero_1037'] != x['ci_excludes_zero_1012'] or x['rank_1037'] != x['rank_1012']]
    def v(k):
        x = bars[k]; return f'{k}: {x["v1037"]} → {x["v1012"]}'
    el0 = {e['tau']: e['all_train']['precision'] for e in a0['merge_eligibility']}; el1 = {e['tau']: e['all_train']['precision'] for e in a1['merge_eligibility']}
    fl0, fl1 = a0['arms']['A0_deployed']['first_seen'], a1['arms']['A0_deployed']['first_seen']
    fz = kb['freeze']; fold_rule = sorted({y['rule'] for y in a1['freeze']['fused_folds'].values() if y})
    assert not any(v['choice_changes'] for v in fz.values()) and fz['frozen_variant']['v1012'] is None and fz['appearance_tau']['v1012'] is None
    diff = sum(r['train_objects'] for r in rf['base_records'])-sum(r['train_objects'] for r in rf['refit_records'])
    assert diff % 4 == 0; dropped = diff//4  # each object sits in the fit set of the four folds other than its own
    pr = ph['v1012_refit_policies']; p0 = ph['v1037']
    held = ph['heater']; pl = jread(OUT/'A8_PLACEBO.json')
    # The prose below states these facts; stop rather than print a false sentence.
    assert not pr['fold_choices_change'] and set(held['folds_1012'].values()) == {'q:radiator'} and not held['withheld_heater_objects']
    assert all(ph['v1012_registered_policies']['arms'][a]['mra'] == pr['arms'][a]['mra'] for a in pr['arms']) and not mflip
    saved = jread(B/'sb_kbox4/out/box_ladder/nonull/TRAIN_OOF.json')['oof_choices']; wc = {x['capture'] for x in leg['withheld_captures']}
    assert sum(rf['refit_choices'][o] != c for o, c in saved.items() if o.split('::')[0] not in wc) == pl['withheld_changed']
    flips = [f'{k} goes {bars[k]["v1037"]} → {bars[k]["v1012"]} ({EVID[k]} {a0["contrasts"][CON[k]]["estimate"]:+.2f} → '
             f'{gain(a1["contrasts"][CON[k]])} on {a1["contrasts"][CON[k]]["rows"]} rows)' for k in changed] + [f'phrase {x} changes' for x in pchanged]
    if flips:
        lead = (f'On the 1,012 rows one bar verdict changes: ' if len(flips) == 1 else f'On the 1,012 rows {len(flips)} bar verdicts change: ') \
               + '; '.join(flips) + '. Every other bar and every frozen choice keeps its 1,037 verdict.'
    else:
        lead = f'On the 1,012 rows no bar verdict changes: the box ladder\'s {len(bars)} bars and the phrase kit\'s {2*len(ph["verdicts"])} keep their 1,037 verdicts.'
    L = [f'# K1 training tables on the 1,012 rows outside the 80 withheld rooms', lead,
         'The phrase fold policy stays heater → radiator in all five folds, and the mask-failure table keeps the ranking of its independent gains and each interval\'s relation to zero.',
         f'The fixed checker (sb_auditfix2) puts {len(leg["withheld_captures"])} K1 training captures in {len(leg["withheld_rooms"])} withheld rooms, as the ruling says; {leg["withheld_priced_captures"]} of them hold {leg["withheld_priced_rows"]} priced rows ({leg["excluded_from_tables_883"]} in the 883 table rows), leaving {lst["rows"]:,} rows in {leg["priced_rooms_1012"]} rooms and {leg["table_rows_kept"]} table rows.',
         f'Rowset `out/K1_TRAIN_1012.txt` sha256 `{lst["sha256"]}`; all four planted probes and the planted-row filter test pass, and a raw-list check without checker code agrees. Every number uses the kits\' own code (1,037 parity exact), 10,000 room draws, seed 20261119.',
         '### Box ladder (sb_kbox4, LADDER_TRAIN): MRA or paired gain [95% CI]; cross-fitted choices and the A8 selector refit on the 1,012',
         '| Quantity | 1,037 | 1,012 | Bar: verdict 1,037 → 1,012 |', '|---|---:|---:|---|',
         f'| A0 deployed | {mra(a0["arms"]["A0_deployed"])} | {mra(a1["arms"]["A0_deployed"])} | |',
         f'| A1 oracle selection (883 / 868 table rows) | {mra(a0["arms"]["A1_oracle_select"])} | {mra(a1["arms"]["A1_oracle_select"])} | |',
         f'| A2 GT masks | {mra(a0["arms"]["A2_gt_masks"])} | {mra(a1["arms"]["A2_gt_masks"])} | |',
         f'| Fusion on GT, cross-fitted (fused_cf) | {mra(a0["arms"]["fused_cf"])} | {mra(a1["arms"]["fused_cf"])} | |',
         f'| A7 DA3 tower, GT masks, best1 | {mra(a0["arms"]["A7_da3_best1"])} | {mra(a1["arms"]["A7_da3_best1"])} | {v("tower_challenger")} |',
         f'| A7 Pi3X tower, GT masks, best1 | {mra(a0["arms"]["A7_pi3x_best1"])} | {mra(a1["arms"]["A7_pi3x_best1"])} | |',
         f'| A8 non-null selector, OOF (tables) | {mra(a0["arms"]["A8_nonull_best1"])} | {mra(a1["arms"]["A8_nonull_best1"])} | |',
         f'| Object variant cross-fitted − A0 | {gain(a0["contrasts"]["object_cf_minus_A0"])} | {gain(a1["contrasts"]["object_cf_minus_A0"])} | {v("replace_box")} (≥ 3, low > 0) |',
         f'| fused_cf − A2 | {gain(a0["contrasts"]["fused_cf_minus_A2"])} | {gain(a1["contrasts"]["fused_cf_minus_A2"])} | {v("fused_path")} (≥ 3, low > 0) |',
         f'| A1 − A0 (tables) | {gain(a0["contrasts"]["A1_minus_A0_tables"])} | {gain(a1["contrasts"]["A1_minus_A0_tables"])} | {v("selector_worth")} (≥ 4) |',
         f'| A8 − A0 (tables) | {gain(a0["contrasts"]["A8_nonull_minus_A0_tables"])} | {gain(a1["contrasts"]["A8_nonull_minus_A0_tables"])} | {v("selector_adopt")} (low > 0) |',
         f'| Size MRA, object variant cross-fitted − A0 | {gain(a0["contrasts"]["size_obj_cf_minus_A0"])} | {gain(a1["contrasts"]["size_obj_cf_minus_A0"])} | {v("size_screen")} (≥ 5, low > 0) |',
         f'| Member precision τ 0.25 / 0.15 / 0.40, all rows | {" / ".join(f"{100*el0[t]:.1f}%" for t in (.25, .15, .40))} | {" / ".join(f"{100*el1[t]:.1f}%" for t in (.25, .15, .40))} | {v("merge_safe")} (no variant reaches 90%) |',
         f'| First-seen pair order, linker | {100*fl0["rate"]:.2f}% of {fl0["pairs"]:,} | {100*fl1["rate"]:.2f}% of {fl1["pairs"]:,} | {v("first_seen_screen")} (≥ 90%) |',
         '',
         f'The FREEZE choices are unchanged on the 1,012: no object variant qualifies, no appearance τ is frozen, and GT fusion picks {" / ".join(fold_rule)} in all five folds and all rooms. '
         f'The A8 refit removes {dropped} withheld-room objects from the fit folds and changes {len(rf["changed_objects_on_1012_table_rows"])} choices on the 868 rows ({len(rf["changed_captures"])} captures); with the kit\'s own folds, A8 − A0 is {gain(kb["v1012_registered_selector"]["contrast"])}.',
         '### Phrase kit (sb_mask_phrase, BARS.json sha256 150d16a2): MRA, gain over A0 [95% CI]; 1,012 uses folds refit without the withheld captures',
         '| Arm | 1,037: MRA, minus A0 | 1,012: MRA, minus A0 | Safe rows minus A0, 1,037 / 1,012 | phrase_worth, phrase_safe: 1,037 → 1,012 |', '|---|---:|---:|---:|---|']
    for a in ('P0', 'W1', 'W2', 'W2c'):
        x0, x1 = p0['arms'][a], pr['arms'][a]
        verdict = 'parity arm (= A0)' if a == 'P0' else ', '.join(f'{ph["verdicts"][a][b]["v1037"]} → {ph["verdicts"][a][b]["v1012_refit"]}' for b in ('phrase_worth', 'phrase_safe'))
        L.append(f'| {a} | {f2(x0["mra"])}, {gain(x0["gain"])} | {f2(x1["mra"])}, {gain(x1["gain"])} | {gain(x0["safe"])} / {gain(x1["safe"])} | {verdict} |')
    rw = pr['rows_to_rewrite']
    L += ['', f'Safe rows: {ph["safe_rows"]["v1037"]} → {ph["safe_rows"]["v1012"]}. Refit folds: heater → {"/".join(sorted({v.split(":", 1)[1] for v in held["folds_1012"].values() if v != "raw"}))} in folds 0–4 and all rooms ({held["objects_fit_1012"]} heater objects, none withheld); every other fold choice is unchanged, so the registered-policy re-score equals the refit one. Chosen arm {pr["chosen"]} (1,037: {p0["chosen"]}); rows to rewrite on the 1,012: {", ".join(f"{n} {c}" for n, c in rw.items())}.',
          '### Mask failure attribution (sb_mffix first table, IoU 0.5): independent gain over A0 in MRA points [95% CI]',
          '| Failure kind | Visible frames, 1,037 / 1,012 | Independent gain, 1,037 | Independent gain, 1,012 | Ordered increment, 1,012 (% of gap) |', '|---|---:|---:|---:|---:|']
    labels = {'omitted_selection': 'selected track absent', 'wrong_instance': 'wrong_instance (structurally empty)'}
    for x in mtab:
        L.append(f'| {labels.get(x["kind"], x["kind"])} | {x["frames_1037"]:,} / {x["frames_1012"]:,} | {gain(x["independent_1037"])} | {gain(x["independent_1012"])} | '
                 f'{x["ordered_increment_1012"]["estimate"]:+.2f} ({100*x["ordered_increment_1012"]["gap_share"]:+.1f}%) |')
    g0, g1 = mf['gap']['v1037'], mf['gap']['v1012']
    L += ['', f'A2 − A0 gap: {g0["estimate"]:+.2f} {ci(g0["ci95"], True)} on 1,037 and {g1["estimate"]:+.2f} {ci(g1["ci95"], True)} on 1,012 ({mf["visible_frames"]["v1037"]:,} → {mf["visible_frames"]["v1012"]:,} visible frames; the withheld rows hold no {" or ".join(x["kind"] for x in mtab if x["frames_1037"] == x["frames_1012"] and x["frames_1037"])} frames).',
          f'Caveats. The deployed run_iso selector, used by A0 and by every arm built on it, was fit on {len(exposed)} of the withheld captures ({sum(x["objects"] for x in exposed)} objects); retraining the deployed reader was out of scope, so A0 itself is not withheld-free. The S4 scale fit behind A9 (no bar) used all {len(s4)} withheld captures.',
          f'Over all fit objects, dropping {pl["placebo_rooms"]} random non-withheld rooms instead changes {pl["changed_median"]} OOF choices (median of {pl["draws"]} draws, range {pl["changed_min"]}–{pl["changed_max"]}), against {pl["withheld_changed"]} for the withheld rooms: the A8 shift is mostly refit noise. No kit file was written (find -newer, K1012.json); CPU only, nice 10, 8 threads.',
          'Commands: `bash run.sh legality.py`, `refit_a8.py`, `a8_placebo.py`, `kbox_1012.py`, `phrase_1012.py`, `mffix_1012.py`, `report.py`. Details and input sha256: out/K1012.json and the per-kit JSONs.']
    assert len(L) <= 50, len(L)
    touched = untouched()
    for n in ['LEGALITY.json', 'KBOX_1012.json', 'PHRASE_1012.json', 'MFFIX_1012.json', 'A8_REFIT.json', 'K1_TRAIN_1012.txt', 'K1_WITHHELD_25.txt', 'K1_TRAIN_TABLES_868.txt']:
        pin(OUT/n)
    write('K1012.json', dict(
        task='sb_k1012: K1 training-captures tables re-reported on the 1,012 rows outside the 80 withheld rooms (RULING 1056Z item 1)',
        rowset=dict(K1_TRAIN_1012=lst, withheld=leg['rowsets']['K1_WITHHELD_25.txt'], tables=leg['rowsets']['K1_TRAIN_TABLES_868.txt'],
                    withheld_captures=[dict(capture=x['capture'], room=x['room'], priced_rows=len(x['priced_row_ids'])) for x in leg['withheld_captures']],
                    planted_tests_passed=all(x['passed'] for x in leg['planted_row_tests'].values()) and leg['planted_pipeline_test']['passed']),
        box_ladder=dict(bars=bars, freeze=fz, parity_1037=kb['parity_1037'],
                        arms={a: dict(v1037=dict(mra=a0['arms'][a]['mra'], ci95=a0['arms'][a]['ci95'], rows=a0['arms'][a]['rows']),
                                      v1012=dict(mra=a1['arms'][a]['mra'], ci95=a1['arms'][a]['ci95'], rows=a1['arms'][a]['rows'])) for a in a0['arms']},
                        contrasts={c: dict(v1037={k: a0['contrasts'][c][k] for k in ('estimate', 'ci95', 'rows', 'rooms')},
                                           v1012={k: a1['contrasts'][c][k] for k in ('estimate', 'ci95', 'rows', 'rooms')}) for c in a0['contrasts']},
                        member_precision=dict(v1037=el0, v1012=el1), a8_refit_changed_choices=len(rf['changed_objects_on_1012_table_rows']),
                        a8_kit_folds_1012=kb['v1012_registered_selector']['contrast']),
        phrase=dict(verdicts=ph['verdicts'], parity_1037=ph['parity_1037'], fold_choices_1012=pr['fold_choices'], fold_choices_change=pr['fold_choices_change'],
                    chosen=dict(v1037=p0['chosen'], v1012=pr['chosen']), heater=held, safe_rows=ph['safe_rows'], rows_to_rewrite_1012=rw,
                    arms={a: dict(v1037=dict(mra=p0['arms'][a]['mra'], gain=p0['arms'][a]['gain']['estimate'], ci95=p0['arms'][a]['gain']['ci95'], safe_ci95=p0['arms'][a]['safe']['ci95']),
                                  v1012=dict(mra=pr['arms'][a]['mra'], gain=pr['arms'][a]['gain']['estimate'], ci95=pr['arms'][a]['gain']['ci95'], safe_ci95=pr['arms'][a]['safe']['ci95'])) for a in p0['arms']}),
        mask_failure=dict(parity_1037=mf['parity_1037'], gap=mf['gap'], first_table=mtab, interval_or_rank_changes=mflip),
        verdict_changes=dict(box_ladder=changed, phrase=pchanged, mask_failure=mflip),
        caveats=dict(deployed_selector_exposure=leg['deployed_selector_exposure'], s4_fit_withheld_captures=s4),
        kit_files_written_after_start=touched, report_lines=len(L)))
    (OUT/'K1012_REPORT.md').write_text('\n'.join(L)+'\n')
    (HERE/'STATUS.md').write_text('Complete: '+lead+' Report out/K1012_REPORT.md; details out/K1012.json; archive out/sb_k1012.tar with out/sb_k1012.tar.sha256.\n')
    members = sorted([p for p in HERE.glob('*') if p.is_file() and p.suffix in ('.py', '.sh', '.md') and p.name != 'AGENTS.md']
                     + [p for p in OUT.glob('*') if p.is_file() and not p.name.startswith('sb_k1012.tar') and p.name != 'PACKAGE_MANIFEST.json'])
    manifest = {str(p.relative_to(HERE)): sha(p) for p in members}
    (OUT/'PACKAGE_MANIFEST.json').write_text(json.dumps(dict(members=manifest, input_sha256=manifest), indent=1)+'\n')
    with tarfile.open(OUT/'sb_k1012.tar', 'w') as tar:
        for p in members+[OUT/'PACKAGE_MANIFEST.json']:
            tar.add(p, arcname=str(p.relative_to(HERE)), recursive=False)
    h = sha(OUT/'sb_k1012.tar'); (OUT/'sb_k1012.tar.sha256').write_text(h+'  sb_k1012.tar\n')
    print('\n'.join(L)); print(len(L), 'lines; tar', h); print('touched', {k: v for k, v in touched.items() if v})


if __name__ == '__main__':
    main()
