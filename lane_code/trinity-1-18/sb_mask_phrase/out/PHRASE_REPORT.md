# Mask phrase kit, part 1: written phrases on stored SAM 3 pools, K1 training captures

K1 training captures only: 1,037 distance rows, 209 captures, 192 rooms, 2,074 row operands; refusals score 0; A0 (deployed) = 56.77. Contrasts are paired against A0 over 10,000 room draws (seed 20261119). Safe rows: the 456 rows whose two operands are good under A0. Bars were frozen in BARS.json (sha256 150d16a232b42d86...) before any score. W arms choose each name's phrase on the other four folds' captures.

| Arm | The ground call | MRA [95% CI] | minus A0 [95% CI] | Refusals | Safe rows minus A0 [95% CI] | Pool recall of 2,074: floor / lift | phrase_worth | phrase_safe |
|---|---|---:|---:|---:|---:|---:|---|---|
| P0 | raw name (deployed) | 56.77 [52.48, 61.04] | +0.00 [+0.00, +0.00] | 36 | +0.00 [+0.00, +0.00] | 1,804 / 1,757 | parity PASS 1,037/1,037 | - |
| P_all | raw + every stored alias, one pool | not priced | not priced | - | - | 1,883 / 1,856 (in-sample) | - | - |
| P_cf | P_all or raw per name, fold-chosen | not priced | not priced | - | - | 1,867 / 1,844 (ceiling, held-out) | - | - |
| P_cap100 | raw name, cap 100 | 56.77 [52.48, 61.04] | +0.00 [+0.00, +0.00] | 36 | +0.00 [+0.00, +0.00] | 1,804 / 1,757 | FAIL (diag.) | PASS (diag.) |
| W1 | one written phrase, fold-chosen | 60.50 [56.02, 64.81] | +3.73 [+2.05, +5.48] | 22 | +0.46 [+0.00, +1.22] | 1,867 / 1,820 | PASS | PASS |
| W2 | raw; alias fills empty frames | 60.36 [55.87, 64.67] | +3.59 [+1.91, +5.35] | 22 | +0.42 [+0.00, +1.17] | 1,860 / 1,813 | PASS | PASS |
| W2c | raw; second call if not seen | 57.86 [53.34, 62.32] | +1.09 [+0.04, +2.40] | 22 | +0.00 [+0.00, +0.00] | 1,818 / 1,771 | FAIL | PASS |

**Decision.** W1 passes phrase_worth and phrase_safe; its all-room policies are frozen in PHRASE_SET.json for the model to write in its ground call. Shippable arms passing both bars: W1, W2; the passing arm with the highest MRA is chosen. The ceiling P_cf puts 1,844 of 2,074 operands in reach at the lifting floor (W1: 1,820; P0: 1,757). P_all and P_cf are not priced: their frames mix presences, and routed_features.cache_for keeps only the first instance's presence, so they appear as pool recall only (floor: score x presence >= 0.05; lift: score >= 0.3 as well).

## Phrases that carry it

Frozen phrase set (PHRASE_SET.json, arm W1, refit on all rooms): heater -> radiator.

| Name | Objects | All-room policy W1 / W2 / W2c | W1 folds 0-4 | W1 on target, all rooms: best alias / raw | W1 held-out on target, fold policy / raw | Rows | Paired gain of its rows W1 / W2 / W2c |
|---|---:|---|---|---:|---:|---:|---|
| heater | 20 | radiator / then radiator / then radiator | radiator,radiator,radiator,radiator,radiator | radiator 16 / 4 of 20 | 16 / 4 of 20 | 84 | +46.07 [+33.92, +58.26] / +44.29 [+30.80, +57.39] / +13.45 [+0.56, +29.26] |
| coat hanger | 3 | raw / raw / raw | raw,raw,raw,raw,raw | coat rack 1 / 0 of 3 | 0 / 0 of 3 | 8 | - / - / - |

Paired gain: arm minus A0 on every row that names the object, 10,000 room draws. Fit counts are all-room; held-out counts use each fold's own choice. Every name, arm and fold: DECISION.json by_name.

## Rows to rewrite

| Arm | Names whose phrase changes | K1 training rows that name them (of 1,037) | By name | Rows needing the second call |
|---|---|---:|---|---:|
| W1 (chosen) | heater -> radiator | 84 | heater 84 | - |
| W2 | heater -> heater then radiator | 84 | heater 84 | 84 |
| W2c | heater -> heater then radiator | 84 | heater 84 | 14 |

Names whose in-sample best policy differs but that have fewer than five objects stay raw: coat hanger (3 objects, 8 operands; best W1 coat rack, W2 then coat rack, W2c then coat rack). K1 rows naming heater or coat hanger: 91 (design lane: 91). Routed training rows of N: MISSING (owner tree_rebuild; expected: N's routed training rows (rows carrying <ground obj=...> calls), held by tree_rebuild; not on trinity-1-18). Not opened: sb_ktow3 routed file with sha256 prefix 8855c81e (a dev-S1 return set): the binding brief keeps it closed; /scratch/jjyeung/n30_mirror/rows_r1 (store v7 and its slices): unrouted store rows; its STATUS.md records rows on K1 held-out rooms in the store family (v6), so the kit did not open it.

## Operands and served masks (2,074 row operands)

| Arm | Good | Wrong object | Weak | Poor priced frame | Refused | Served IoU >= 0.5, visible frames | Priced-frame IoU mean | Masks on raster-absent frames |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P0 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| P_cap100 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| W1 | 1408 | 270 | 188 | 186 | 22 | 46.7% of 13,793 | 0.582 | 901 |
| W2 | 1396 | 272 | 193 | 191 | 22 | 46.8% of 13,793 | 0.580 | 913 |
| W2c | 1369 | 319 | 188 | 176 | 22 | 44.7% of 13,793 | 0.565 | 976 |

## Merge member precision and first-seen order (bars 90%), contrasts by dataset

| Arm | Member precision tau 0.25 / 0.15 / 0.40 | First-seen pair rate | arkitscenes minus A0 (344 rows) | scannet minus A0 (72 rows) | scannetpp minus A0 (621 rows) |
|---|---:|---:|---:|---:|---:|
| P0 | 72.5% / 73.3% / 73.1% | 76.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| P_cap100 | 72.5% / 73.3% / 73.1% | 76.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| W1 | 72.2% / 73.1% / 73.0% | 78.9% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +6.23 [+3.64, +9.20] |
| W2 | 72.5% / 73.3% / 73.2% | 78.6% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +5.99 [+3.41, +8.99] |
| W2c | 72.5% / 73.3% / 73.1% | 77.5% | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +1.82 [+0.07, +4.16] |

Arms reaching 90% member precision at some threshold: none; reaching 90% first-seen pair order: none. Member precision is the ladder's test (added members whose majority raster instance equals the seed's).

## Checks and caveats

- Dry run PASS (out/DRYRUN.json): parity on 5 captures (42/42 rows); pool recall reproduces the design counts (raw 1,804, P_all 1,883; lift: raw 1,757, best single phrase 1,828, pooled 1,856); alias calls accepted with the alias as call name; folds disjoint by room; every capture k1_split == train.
- Reader contract on 1,471 priced pools (490 alias calls): one presence per frame in each; per-proposal score and presence survive cache_for and lift (0 failures); candidate identities and selector labels rebuilt per pool (0 mismatches); on raw pools the fresh labels equal the serving tables (770 of 770); reader refusals 0.
- The stage-1 cache merged an alias instance into a raw one above IoU 0.95, so a stored alias pool lacks objects the raw name also found; W1 understates the alias called alone (part 2 reruns it).
- W2 needs a call that carries two phrases (the tool fills empty frames); W2c is two calls in today's syntax. The selector head (run_iso) has name_mode none, so the call's name does not move selection.
- Rows by worse operand under A0: refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456 (design record: refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456).
- The stopped session (pid 546869) priced its v1 arms into out/ at 10:11Z, before any bars file existed; this session wrote out/BARS.json at 10:12:21Z from the spec's prospective bars and the brief's arms before reading any score, moved the v1 outputs to work/stale_v1_out unread, and changed no bar or arm afterwards.
- Part 2 (W_exact, W_new, R_cond; SAM 3 on GPU) was not run.
