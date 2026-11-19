"""PHRASE_REPORT.md (at most 80 lines) from the decision record; every number is read from DECISION.json."""
import json
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


def write(decision, rows, phrase_set):
    D = decision; R = D['arms']; B = D['bars']; ck = D['checks']
    a0 = R['P0']['gain']['right_mra']; n_ops = R['P0']['operands']
    L = ['# Mask phrase kit, part 1: written phrases on stored SAM 3 pools, K1 training captures', '',
         f'K1 training captures only: 1,037 distance rows, 209 captures, 192 rooms, {n_ops:,} row operands; refusals score 0; A0 (deployed) = {a0:.2f}. '
         f'Contrasts are paired against A0 over 10,000 room draws (seed 20261119). Safe rows: the {D["both_good_rows"]} rows whose two operands are good under A0. '
         f'Bars were frozen in BARS.json (sha256 {D["bars_file"]["sha256"][:16]}...) before any score. W arms choose each name\'s phrase on the other four folds\' captures.',
         '',
         f'| Arm | The ground call | MRA [95% CI] | minus A0 [95% CI] | Refusals | Safe rows minus A0 [95% CI] | Pool recall of {n_ops:,}: floor / lift | phrase_worth | phrase_safe |',
         '|---|---|---:|---:|---:|---:|---:|---|---|']
    for a in ARMS:
        r = R[a]; rec = f'{r["pool_recall"]:,} / {r["pool_recall_lift"]:,}'
        if a in ('P_all', 'P_cf'):
            tag = 'ceiling, held-out' if a == 'P_cf' else 'in-sample'
            L.append(f'| {a} | {CALL[a]} | not priced | not priced | - | - | {rec} ({tag}) | - | - |')
            continue
        g, s = r['gain'], r['safe']
        if a == 'P0':
            worth, safe = f'parity {D["parity"]["verdict"]} {D["parity"]["matched"]:,}/1,037', '-'
        else:
            tag = '' if a in SHIP else ' (diag.)'
            worth, safe = B[a]['phrase_worth']['verdict']+tag, B[a]['phrase_safe']['verdict']+tag
        L.append(f'| {a} | {CALL[a]} | {r["mra"]:.2f} [{r["mra_ci95"][0]:.2f}, {r["mra_ci95"][1]:.2f}] | {g["estimate"]:+.2f} {ci(g["ci95"])} | '
                 f'{r["refusals"]} | {s["estimate"]:+.2f} {ci(s["ci95"])} | {rec} | {worth} | {safe} |')
    chosen = D['chosen_arm']
    passing = D['shippable_passing']
    L += ['', f'**Decision.** {D["verdict"]} Shippable arms passing both bars: {", ".join(passing) or "none"}; the passing arm with the highest MRA is chosen. '
          f'The ceiling P_cf puts {R["P_cf"]["pool_recall_lift"]:,} of {n_ops:,} operands in reach at the lifting floor (W1: {R["W1"]["pool_recall_lift"]:,}; '
          f'P0: {R["P0"]["pool_recall_lift"]:,}). P_all and P_cf are not priced: their frames mix presences, and routed_features.cache_for keeps only '
          'the first instance\'s presence, so they appear as pool recall only (floor: score x presence >= 0.05; lift: score >= 0.3 as well).']
    names = D['by_name']
    moved = [n for n, x in names.items() if any(x[a]['all_rooms'] != 'raw' or any(v != 'raw' for v in x[a]['folds'].values()) for a in SHIP)
             or any(v != 'raw' for v in x['insample_best_without_min_fit'].values())]
    moved.sort(key=lambda n: -max(abs(names[n][a]['points']) for a in SHIP))
    L += ['', '## Phrases that carry it', '',
          'Frozen phrase set (PHRASE_SET.json, '+(f'arm {chosen}, refit on all rooms): ' if chosen else 'no arm passes): ')
          + (', '.join(f'{p["name"]} -> {" then ".join(p["phrases"])}' for p in phrase_set if p['variant'] != 'raw') or 'every name keeps its raw name') + '.',
          '', '| Name | Objects | All-room policy W1 / W2 / W2c | W1 folds 0-4 | W1 on target, all rooms: best alias / raw | W1 held-out on target, fold policy / raw | Rows | Paired gain of its rows W1 / W2 / W2c |',
          '|---|---:|---|---|---:|---:|---:|---|']
    for n in moved[:10]:
        x = names[n]; w1 = x['W1']; fc = w1['fit_counts']
        best = max((v for v in fc if v != 'raw'), key=lambda v: fc[v], default=None)
        gains = ' / '.join(f'{x[a]["gain"]["estimate"]:+.2f} {ci(x[a]["gain"]["ci95"])}' if x[a]['gain'] else '-' for a in SHIP)
        L.append(f'| {n} | {x["objects"]} | {" / ".join(policy(x[a]["all_rooms"]) for a in SHIP)} | {",".join(policy(w1["folds"][k]) for k in map(str, range(5)))} | '
                 f'{policy(best) + " " + str(fc[best]) if best else "-"} / {fc["raw"]} of {w1["fit_objects"]} | '
                 f'{w1["heldout_on_target"]["policy"]} / {w1["heldout_on_target"]["raw"]} of {w1["heldout_on_target"]["objects"]} | {w1["rows"]} | {gains} |')
    L += ['', 'Paired gain: arm minus A0 on every row that names the object, 10,000 room draws. Fit counts are all-room; held-out counts use each fold\'s own choice. '
          'Every name, arm and fold: DECISION.json by_name.']
    ra = rows['arms']
    L += ['', '## Rows to rewrite', '',
          '| Arm | Names whose phrase changes | K1 training rows that name them (of 1,037) | By name | Rows needing the second call |', '|---|---|---:|---|---:|']
    for a in SHIP:
        x = ra[a]
        L.append(f'| {a}{" (chosen)" if a == chosen else ""} | {", ".join(f"{n} -> {" then ".join(x["policies"][n])}" for n in x["names"]) or "none"} | {x["k1_rows"]} | '
                 f'{", ".join(f"{n} {k}" for n, k in x["k1_rows_by_name"].items()) or "-"} | {x["second_call_rows"] if a != "W1" else "-"} |')
    small = sorted({n for a in SHIP for n in ra[a]['under_five_objects_left_raw']})
    rr = rows['routed_rows_of_N']
    def best_of(n):
        return ', '.join(f'{a} {policy(names[n]["insample_best_without_min_fit"][a])}' for a in SHIP)
    L += ['', f'Names whose in-sample best policy differs but that have fewer than five objects stay raw: '
          + ('; '.join(f'{n} ({names[n]["objects"]} objects, {names[n]["operands"]} operands; best {best_of(n)})' for n in small) or 'none') + '. '
          f'K1 rows naming heater or coat hanger: {rows["k1_rows_naming_heater_or_coat_hanger"]} (design lane: {rows["design_lane_count"]}). '
          f'Routed training rows of N: {rr["status"]} (owner {rr["owner"]}; expected: {rr["expected"]}). Not opened: {"; ".join(rr["not_opened"])}.']
    L += ['', f'## Operands and served masks ({n_ops:,} row operands)', '',
          '| Arm | Good | Wrong object | Weak | Poor priced frame | Refused | Served IoU >= 0.5, visible frames | Priced-frame IoU mean | Masks on raster-absent frames |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for a in PRICED:
        r = R[a]; c = r['operand_categories']; s = r['served_iou']
        L.append(f'| {a} | {c.get("good", 0)} | {c.get("wrong_object", 0)} | {c.get("weak", 0)} | {c.get("poor_priced_frame", 0)} | {c.get("refused", 0)} | '
                 f'{100*s["rate_05"]:.1f}% of {s["visible_frames"]:,} | {s["priced_frame_mean"]:.3f} | {r["served_absent_frames"]:,} |')
    L += ['', '## Merge member precision and first-seen order (bars 90%), contrasts by dataset', '',
          '| Arm | Member precision tau 0.25 / 0.15 / 0.40 | First-seen pair rate | ' + ' | '.join(f'{d} minus A0 ({R["P0"]["by_dataset"][d]["rows"]} rows)' for d in DS) + ' |',
          '|---|---:|---:|---:|---:|---:|']
    for a in PRICED:
        r = R[a]; mp = r['member_precision']; ds = r['by_dataset']
        p = ' / '.join(f'{100*mp[t]["precision"]:.1f}%' if mp[t]['precision'] is not None else 'n/a' for t in ['0.25', '0.15', '0.4'])
        L.append(f'| {a} | {p} | {100*r["first_seen"]["rate"]:.1f}% | ' + ' | '.join(f'{ds[d]["delta"]:+.2f} {ci(ds[d]["ci95"])}' for d in DS) + ' |')
    mp_pass = [a for a in PRICED if any(R[a]['member_precision'][t]['passes_90'] for t in ['0.25', '0.15', '0.4'])]
    fs_pass = [a for a in PRICED if (R[a]['first_seen']['rate'] or 0) >= .9]
    wt = D['worse_operand_table']
    L += ['', f'Arms reaching 90% member precision at some threshold: {", ".join(mp_pass) or "none"}; reaching 90% first-seen pair order: {", ".join(fs_pass) or "none"}. '
          'Member precision is the ladder\'s test (added members whose majority raster instance equals the seed\'s).',
          '', '## Checks and caveats', '',
          f'- Dry run PASS (out/DRYRUN.json): parity on 5 captures (42/42 rows); pool recall reproduces the design counts (raw 1,804, P_all 1,883; lift: raw 1,757, best single phrase 1,828, pooled 1,856); '
          'alias calls accepted with the alias as call name; folds disjoint by room; every capture k1_split == train.',
          f'- Reader contract on {ck["pools"]:,} priced pools ({ck["alias_calls"]:,} alias calls): one presence per frame in each; per-proposal score and presence survive cache_for and lift '
          f'({ck["survival_failed"]} failures); candidate identities and selector labels rebuilt per pool ({ck["identities_failed"]} mismatches); on raw pools the fresh labels equal the serving tables '
          f'({ck["raw_fresh_labels_equal_table"]:,} of {ck["raw_fresh_labels_equal_table"]+ck["raw_fresh_labels_differ"]:,}); reader refusals {ck["reader_refused"]}.',
          '- The stage-1 cache merged an alias instance into a raw one above IoU 0.95, so a stored alias pool lacks objects the raw name also found; W1 understates the alias called alone (part 2 reruns it).',
          '- W2 needs a call that carries two phrases (the tool fills empty frames); W2c is two calls in today\'s syntax. The selector head (run_iso) has name_mode none, so the call\'s name does not move selection.',
          f'- Rows by worse operand under A0: ' + ', '.join(f'{w.replace("_", " ") if w != "good" else "both good"} {v["rows"]}' for w, v in wt.items())
          + ' (design record: refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456).',
          f'- {D["bars_file"]["order"]}',
          '- Part 2 (W_exact, W_new, R_cond; SAM 3 on GPU) was not run.']
    assert len(L) <= 80, len(L)
    (K.OUT/'PHRASE_REPORT.md').write_text('\n'.join(L)+'\n')
