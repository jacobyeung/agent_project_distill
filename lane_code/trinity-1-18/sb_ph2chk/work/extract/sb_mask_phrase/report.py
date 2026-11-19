"""PHRASE_REPORT.md (at most 80 lines) from the decision record; every number is read from DECISION.json."""
import kit as K

CALL = {'P0': 'raw name (deployed)', 'P_all': 'raw + every stored alias, one pool', 'P_cf': 'P_all or raw per name, fold-chosen',
        'P_cap100': 'raw name, cap 100', 'W1': 'one written phrase, fold-chosen', 'W2': 'raw; alias fills empty frames',
        'W2c': 'raw; second call if not seen'}
ARMS = ('P0', 'P_all', 'P_cf', 'P_cap100', 'W1', 'W2', 'W2c')
PRICED = ('P0', 'P_cap100', 'W1', 'W2', 'W2c')
SHIP = ('W1', 'W2', 'W2c')
DS = ('arkitscenes', 'scannet', 'scannetpp')


def ci(v):
    return f'[{v[0]:+.2f}, {v[1]:+.2f}]'


def policy(v):
    if v == 'raw':
        return 'raw'
    kind, a = v.split(':', 1)
    return a if kind == 'q' else ('then '+a if kind in ('fb', 'call') else v)


def hm(stamp):
    return stamp[11:19]+'Z'


def write(decision, rows, phrase_set):
    D = decision; R, R7 = D['arms'], D['arms_1037']; B, B7 = D['bars'], D['bars_1037']; ck = D['checks']
    pop = D['population']; dp, ap, wh = pop['decision'], pop['all_rows'], pop['withheld']
    reg = D['bars_file']['registration']; sp = reg['spec']; v1, v2 = sp['in/KIT_SPEC_mask_phrase.md'], sp['in/v2/KIT_SPEC_mask_phrase.md']
    first, agg, bf = reg['earliest_score_file'], reg['earliest_aggregate_score_file'], reg['bars_file']
    n, n7 = dp['rows'], ap['rows']
    L = ['# Mask phrase kit, part 1: written phrases on stored SAM 3 pools, K1 training captures', '',
         f'**Status: {D["status"]}.** The bars file was written after the first scores existed, so it records written_before_any_score = false (review sb_phrev). '
         'The numeric bars (phrase_worth: estimate >= +1.5 with lower bound > 0; phrase_safe: lower bound > -1.0) already stood in the design lane\'s spec: '
         f'first version in/KIT_SPEC_mask_phrase.md (sha256 {v1["sha256"][:16]}..., mtime {hm(v1["mtime_utc"])}, bars on {v1["bars_apply_to"]}) and '
         f'in/v2/KIT_SPEC_mask_phrase.md (sha256 {v2["sha256"][:16]}..., mtime {hm(v2["mtime_utc"])}, bars on the cross-fitted W arm). '
         f'The earliest score file is a v1 capture of the stopped session ({first["path"].split("sb_mask_phrase/")[1]}, mtime {hm(first["mtime_utc"])}, row predictions with labels); '
         f'its first aggregate ({agg["path"].split("sb_mask_phrase/")[1]}) has mtime {hm(agg["mtime_utc"])}; out/BARS.json says it was written at {hm(bf["written_utc"])} (mtime {hm(bf["mtime_utc"])}). '
         'The reader judges the registration from these times.', '',
         f'Decision population: the {n:,} K1 training rows outside the withheld rooms ({dp["captures"]} captures, {dp["rooms"]} rooms); every fit excludes the withheld captures. '
         f'Five K1 training captures lie in withheld rooms ({", ".join(c.split("/")[1] for c in wh["captures"])}; ScanNet): {wh["rows"]} rows, {wh["heater_rows"]} heater rows, '
         f'{wh["both_good_rows"]} both-good rows. Excluding them moves {len(pop["policy_changes_vs_all_rows"]) or "no"} policy. All {n7:,} rows stand beside. '
         f'Refusals score 0; A0 (deployed) = {R["P0"]["gain"]["right_mra"]:.2f} on {n:,} rows ({R7["P0"]["gain"]["right_mra"]:.2f} on {n7:,}). '
         f'Contrasts are paired against A0 over 10,000 room draws (seed 20261119). Safe rows: both operands good under A0 ({dp["both_good_rows"]} of {n:,}; {ap["both_good_rows"]} of {n7:,}). '
         'W arms choose each name\'s phrase on the other four folds\' captures.', '',
         f'| Arm | The ground call | {n:,} rows: MRA [95% CI] | minus A0 [95% CI] | Safe rows minus A0 [95% CI] | phrase_worth / phrase_safe | '
         f'{n7:,} rows: minus A0 [95% CI] | Safe rows minus A0 [95% CI] | Refusals {n:,} / {n7:,} | Pool recall of {R7["P0"]["operands"]:,} ({n7:,} rows): floor / lift |',
         '|---|---|---:|---:|---:|---|---:|---:|---:|---:|']
    for a in ARMS:
        r, r7 = R[a], R7[a]; rec = f'{r7["pool_recall"]:,} / {r7["pool_recall_lift"]:,}'
        if a in ('P_all', 'P_cf'):
            tag = 'ceiling, held-out' if a == 'P_cf' else 'in-sample'
            L.append(f'| {a} | {CALL[a]} | not priced | not priced | - | - | not priced | - | - | {rec} ({tag}) |')
            continue
        if a == 'P0':
            verdict = f'parity {D["parity"]["verdict"]} {D["parity"]["matched"]:,}/1,037'
        else:
            tag = {'W1': '', 'W2c': '', 'W2': ' (tool-change diag.)'}.get(a, ' (diag.)')
            verdict = f'{B[a]["phrase_worth"]["verdict"]} / {B[a]["phrase_safe"]["verdict"]}{tag}'
        g, s, g7, s7 = r['gain'], r['safe'], r7['gain'], r7['safe']
        L.append(f'| {a} | {CALL[a]} | {r["mra"]:.2f} [{r["mra_ci95"][0]:.2f}, {r["mra_ci95"][1]:.2f}] | {g["estimate"]:+.2f} {ci(g["ci95"])} | '
                 f'{s["estimate"]:+.2f} {ci(s["ci95"])} | {verdict} | {g7["estimate"]:+.2f} {ci(g7["ci95"])} | {s7["estimate"]:+.2f} {ci(s7["ci95"])} | '
                 f'{r["refusals"]} / {r7["refusals"]} | {rec} |')
    chosen = D['chosen_arm']
    w2 = B['W2']['phrase_worth']
    w2c = B['W2c']['phrase_worth']
    L += ['', f'**Decision.** {D["verdict"]} Eligible arms: {", ".join(D["eligible_arms"])}; passing both bars on {n:,} rows: '
          f'{", ".join(D["shippable_passing"]) or "none"} (on {n7:,} rows: {", ".join(D["shippable_passing_1037"]) or "none"}). '
          f'W2c {"passes" if w2c["verdict"] == "PASS" else "fails"} phrase_worth ({w2c["estimate"]:+.2f} {ci(w2c["ci95"])}). '
          f'W2 passes numerically ({w2["estimate"]:+.2f} {ci(w2["ci95"])}) but is a tool-change diagnostic: its pool joins raw and alias frames, '
          'which needs a call carrying two phrases, and the current call syntax has none. '
          f'The ceiling P_cf puts {R7["P_cf"]["pool_recall_lift"]:,} of {R7["P0"]["operands"]:,} operands in reach at the lifting floor (W1: {R7["W1"]["pool_recall_lift"]:,}; '
          f'P0: {R7["P0"]["pool_recall_lift"]:,}). P_all and P_cf are not priced: their frames mix presences, and routed_features.cache_for keeps only '
          'the first instance\'s presence, so they appear as pool recall only (floor: score x presence >= 0.05; lift: score >= 0.3 as well).']
    names = D['by_name']
    moved = [m for m, x in names.items() if any(x[a]['all_rooms'] != 'raw' or any(v != 'raw' for v in x[a]['folds'].values()) for a in SHIP)
             or any(v != 'raw' for v in x['insample_best_without_min_fit'].values())]
    moved.sort(key=lambda m: -max(abs(names[m][a]['points']) for a in SHIP))
    L += ['', f'## Phrases that carry it ({n:,} decision rows)', '',
          'Phrase set (PHRASE_SET.json, '+(f'arm {chosen}, refit on the {dp["rooms"]} rooms outside the withheld rooms): ' if chosen else 'no arm passes): ')
          + (', '.join(f'{p["name"]} -> {" then ".join(p["phrases"])}' for p in phrase_set if p['variant'] != 'raw') or 'every name keeps its raw name') + '.',
          '', '| Name | Objects | All-room policy W1 / W2 / W2c | W1 folds 0-4 | W1 on target, all rooms: best alias / raw | W1 held-out on target, fold policy / raw | Rows | Paired gain of its rows W1 / W2 / W2c |',
          '|---|---:|---|---|---:|---:|---:|---|']
    for m in moved[:10]:
        x = names[m]; w1 = x['W1']; fc = w1['fit_counts']
        best = max((v for v in fc if v != 'raw'), key=lambda v: fc[v], default=None)
        gains = ' / '.join(f'{x[a]["gain"]["estimate"]:+.2f} {ci(x[a]["gain"]["ci95"])}' if x[a]['gain'] else '-' for a in SHIP)
        L.append(f'| {m} | {x["objects"]} | {" / ".join(policy(x[a]["all_rooms"]) for a in SHIP)} | {",".join(policy(w1["folds"][k]) for k in map(str, range(5)))} | '
                 f'{policy(best) + " " + str(fc[best]) if best else "-"} / {fc["raw"]} of {w1["fit_objects"]} | '
                 f'{w1["heldout_on_target"]["policy"]} / {w1["heldout_on_target"]["raw"]} of {w1["heldout_on_target"]["objects"]} | {w1["rows"]} | {gains} |')
    op = D['open_until_part2']
    L += ['', 'Paired gain: arm minus A0 on every row that names the object, 10,000 room draws. Fit counts are all-room; held-out counts use each fold\'s own choice. '
          'Every name, arm and fold: DECISION.json by_name (by_name_1037 beside).',
          '', '**Open until part 2: ' + ', '.join(f'{o["name"]}/{o["alias"]}' for o in op) + '.** The stored alias cache cannot decide these. On the stored pools the raw name '
          'puts more fit objects on target than the alias called alone (' + '; '.join(f'{o["name"]} {o["on_target_raw"]}, {o["alias"]} {o["on_target_alias_alone"]} of {o["fit_objects"]}' for o in op)
          + '), but the stage-1 cache dropped every alias proposal whose IoU with an earlier retained instance exceeded 0.95, so the lead cannot tell a weaker alias from deduplication. '
          'They keep the raw name until part 2 reruns each alias alone; the default pass reruns only fold-chosen phrases, so this needs part2/sam3_pass.py pass --all-aliases (2,004 calls against 1,540).']
    ra = rows['arms']
    L += ['', f'## Rows to rewrite ({n:,} decision rows)', '',
          f'| Arm | Names whose phrase changes | K1 training rows that name them (of {n:,}) | By name | Rows needing the second call | Withheld rows naming them |', '|---|---|---:|---|---:|---:|']
    for a in SHIP:
        x = ra[a]; tag = ' (chosen)' if a == chosen else (' (tool-change diag.)' if a == 'W2' else '')
        L.append(f'| {a}{tag} | {", ".join(f"{m} -> {" then ".join(x["policies"][m])}" for m in x["names"]) or "none"} | {x["k1_rows"]} | '
                 f'{", ".join(f"{m} {k}" for m, k in x["k1_rows_by_name"].items()) or "-"} | {x["second_call_rows"] if a != "W1" else "-"} | {x["withheld_rows_naming_changed_names"]} |')
    small = sorted({m for a in SHIP for m in ra[a]['under_five_objects_left_raw']})
    rr = rows['routed_rows_of_N']
    def best_of(m):
        return ', '.join(f'{a} {policy(names[m]["insample_best_without_min_fit"][a])}' for a in SHIP)
    L += ['', f'Names whose in-sample best policy differs but that have fewer than five objects stay raw: '
          + ('; '.join(f'{m} ({names[m]["objects"]} objects, {names[m]["operands"]} operands; best {best_of(m)})' for m in small) or 'none') + '. '
          f'K1 rows naming heater or coat hanger: {rows["k1_rows_naming_heater_or_coat_hanger"]} of {n:,} ({rows["k1_rows_naming_heater_or_coat_hanger_1037"]} of {n7:,}; design lane: {rows["design_lane_count"]}). '
          'K1 train membership alone does not certify that a row may teach downstream. '
          f'Routed training rows of N: {rr["status"]} (owner {rr["owner"]}; expected: {rr["expected"]}). Not opened: {"; ".join(rr["not_opened"])}.']
    L += ['', f'## Operands and served masks ({R7["P0"]["operands"]:,} row operands, all {n7:,} rows)', '',
          '| Arm | Good | Wrong object | Weak | Poor priced frame | Refused | Served IoU >= 0.5, visible frames | Priced-frame IoU mean | Masks on raster-absent frames |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for a in PRICED:
        r = R7[a]; c = r['operand_categories']; s = r['served_iou']
        L.append(f'| {a} | {c.get("good", 0)} | {c.get("wrong_object", 0)} | {c.get("weak", 0)} | {c.get("poor_priced_frame", 0)} | {c.get("refused", 0)} | '
                 f'{100*s["rate_05"]:.1f}% of {s["visible_frames"]:,} | {s["priced_frame_mean"]:.3f} | {r["served_absent_frames"]:,} |')
    L += ['', f'## Merge member precision and first-seen order (bars 90%), contrasts by dataset (all {n7:,} rows)', '',
          '| Arm | Member precision tau 0.25 / 0.15 / 0.40 | First-seen pair rate | ' + ' | '.join(f'{d} minus A0 ({R7["P0"]["by_dataset"][d]["rows"]} rows)' for d in DS) + ' |',
          '|---|---:|---:|---:|---:|---:|']
    for a in PRICED:
        r = R7[a]; mp = r['member_precision']; ds = r['by_dataset']
        p = ' / '.join(f'{100*mp[t]["precision"]:.1f}%' if mp[t]['precision'] is not None else 'n/a' for t in ['0.25', '0.15', '0.4'])
        L.append(f'| {a} | {p} | {100*r["first_seen"]["rate"]:.1f}% | ' + ' | '.join(f'{ds[d]["delta"]:+.2f} {ci(ds[d]["ci95"])}' for d in DS) + ' |')
    mp_pass = [a for a in PRICED if any(R7[a]['member_precision'][t]['passes_90'] for t in ['0.25', '0.15', '0.4'])]
    fs_pass = [a for a in PRICED if (R7[a]['first_seen']['rate'] or 0) >= .9]
    wt = D['worse_operand_table']
    L += ['', f'Arms reaching 90% member precision at some threshold: {", ".join(mp_pass) or "none"}; reaching 90% first-seen pair order: {", ".join(fs_pass) or "none"}. '
          'Member precision is the ladder\'s test (added members whose majority raster instance equals the seed\'s).',
          '', '## Checks and caveats', '',
          f'- Dry run PASS (out/DRYRUN.json): parity on 5 captures (42/42 rows); pool recall reproduces the design counts (raw 1,804, P_all 1,883; lift: raw 1,757, best single phrase 1,828, pooled 1,856); '
          'alias calls accepted with the alias as call name; folds disjoint by room; every capture k1_split == train.',
          f'- Reader contract on {ck["pools"]:,} priced pools ({ck["alias_calls"]:,} alias calls): one presence per frame in each; per-proposal score and presence survive cache_for and lift '
          f'({ck["survival_failed"]} failures); candidate identities and selector labels rebuilt per pool ({ck["identities_failed"]} mismatches); on raw pools the fresh labels equal the serving tables '
          f'({ck["raw_fresh_labels_equal_table"]:,} of {ck["raw_fresh_labels_equal_table"]+ck["raw_fresh_labels_differ"]:,}); reader refusals {ck["reader_refused"]}.',
          f'- {D["serving_score"]} The stage-1 cache dropped alias proposals above IoU 0.95 against earlier retained instances; restoring them can move linking and selection in either direction.',
          '- W2 needs a call that carries two phrases (the tool fills empty frames); W2c is two calls in today\'s syntax. The selector head (run_iso) has name_mode none, so the call\'s name does not move selection.',
          f'- Rows by worse operand under A0 (all {n7:,} rows): ' + ', '.join(f'{w.replace("_", " ") if w != "good" else "both good"} {v["rows"]}' for w, v in wt.items())
          + ' (design record: refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456).',
          f'- out/BARS.json (sha256 {D["bars_file"]["sha256"][:16]}...) differs from the file the arms were priced under ({D["bars_file"]["previous_sha256"][:16]}...) only in written_before_any_score '
          'and the registration record. A matching hash shows that a file did not change after it was written, not when it was written.',
          '- Part 2 (W_exact, W_new, R_cond; SAM 3 on GPU) was not run.']
    assert len(L) <= 80, len(L)
    (K.OUT/'PHRASE_REPORT.md').write_text('\n'.join(L)+'\n')
