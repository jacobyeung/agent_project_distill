# Mask phrase kit, part 1: written phrases on stored SAM 3 pools, K1 training captures

**Status: diagnostic pending orchestrator ruling on registration.** The bars file was written after the first scores existed, so it records written_before_any_score = false (review sb_phrev). The numeric bars (phrase_worth: estimate >= +1.5 with lower bound > 0; phrase_safe: lower bound > -1.0) already stood in the design lane's spec: first version in/KIT_SPEC_mask_phrase.md (sha256 d35055c1c11245ff..., mtime 09:50:47Z, bars on P_cf) and in/v2/KIT_SPEC_mask_phrase.md (sha256 5f099b8314cb2199..., mtime 10:06:34Z, bars on the cross-fitted W arm). The earliest score file is a v1 capture of the stopped session (work/caps/arkitscenes__41048124.json.gz, mtime 10:03:18Z, row predictions with labels); its first aggregate (work/stale_v1_out/DECISION.json) has mtime 10:11:27Z; out/BARS.json says it was written at 10:12:21Z (mtime 10:12:42Z). The reader judges the registration from these times.

Decision population: the 1,012 K1 training rows outside the withheld rooms (204 captures, 188 rooms); every fit excludes the withheld captures. Five K1 training captures lie in withheld rooms (scene0201_02, scene0478_00, scene0478_01, scene0614_02, scene0692_03; ScanNet): 25 rows, 0 heater rows, 14 both-good rows. Excluding them moves no policy. All 1,037 rows stand beside. Refusals score 0; A0 (deployed) = 56.93 on 1,012 rows (56.77 on 1,037). Contrasts are paired against A0 over 10,000 room draws (seed 20261119). Safe rows: both operands good under A0 (442 of 1,012; 456 of 1,037). W arms choose each name's phrase on the other four folds' captures.

| Arm | The ground call | 1,012 rows: MRA [95% CI] | minus A0 [95% CI] | Safe rows minus A0 [95% CI] | phrase_worth / phrase_safe | 1,037 rows: minus A0 [95% CI] | Safe rows minus A0 [95% CI] | Refusals 1,012 / 1,037 | Pool recall of 2,074 (1,037 rows): floor / lift |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| P0 | raw name (deployed) | 56.93 [52.52, 61.34] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | parity PASS 1,037/1,037 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 36 / 36 | 1,804 / 1,757 |
| P_all | raw + every stored alias, one pool | not priced | not priced | - | - | not priced | - | - | 1,883 / 1,856 (in-sample) |
| P_cf | P_all or raw per name, fold-chosen | not priced | not priced | - | - | not priced | - | - | 1,867 / 1,844 (ceiling, held-out) |
| P_cap100 | raw name, cap 100 | 56.93 [52.52, 61.34] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | FAIL / PASS (diag.) | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | 36 / 36 | 1,804 / 1,757 |
| W1 | one written phrase, fold-chosen | 60.75 [56.12, 65.17] | +3.82 [+2.16, +5.63] | +0.48 [+0.00, +1.23] | PASS / PASS | +3.73 [+2.05, +5.48] | +0.46 [+0.00, +1.22] | 22 / 22 | 1,867 / 1,820 |
| W2 | raw; alias fills empty frames | 60.60 [55.97, 65.04] | +3.68 [+2.01, +5.48] | +0.43 [+0.00, +1.18] | PASS / PASS (tool-change diag.) | +3.59 [+1.91, +5.35] | +0.42 [+0.00, +1.17] | 22 / 22 | 1,860 / 1,813 |
| W2c | raw; second call if not seen | 58.04 [53.42, 62.68] | +1.12 [+0.04, +2.50] | +0.00 [+0.00, +0.00] | FAIL / PASS | +1.09 [+0.04, +2.40] | +0.00 [+0.00, +0.00] | 22 / 22 | 1,818 / 1,771 |

**Decision.** W1 passes phrase_worth and phrase_safe on the 1,012 decision rows; its policies, refit on the 188 rooms outside the withheld rooms, are in PHRASE_SET.json. Status: diagnostic pending orchestrator ruling on registration. Eligible arms: W1, W2c; passing both bars on 1,012 rows: W1 (on 1,037 rows: W1). W2c fails phrase_worth (+1.12 [+0.04, +2.50]). W2 passes numerically (+3.68 [+2.01, +5.48]) but is a tool-change diagnostic: its pool joins raw and alias frames, which needs a call carrying two phrases, and the current call syntax has none. The ceiling P_cf puts 1,844 of 2,074 operands in reach at the lifting floor (W1: 1,820; P0: 1,757). P_all and P_cf are not priced: their frames mix presences, and routed_features.cache_for keeps only the first instance's presence, so they appear as pool recall only (floor: score x presence >= 0.05; lift: score >= 0.3 as well).

## Phrases that carry it (1,012 decision rows)

Phrase set (PHRASE_SET.json, arm W1, refit on the 188 rooms outside the withheld rooms): heater -> radiator.

| Name | Objects | All-room policy W1 / W2 / W2c | W1 folds 0-4 | W1 on target, all rooms: best alias / raw | W1 held-out on target, fold policy / raw | Rows | Paired gain of its rows W1 / W2 / W2c |
|---|---:|---|---|---:|---:|---:|---|
| heater | 20 | radiator / then radiator / then radiator | radiator,radiator,radiator,radiator,radiator | radiator 16 / 4 of 20 | 16 / 4 of 20 | 84 | +46.07 [+33.92, +58.26] / +44.29 [+30.80, +57.39] / +13.45 [+0.56, +29.26] |
| coat hanger | 3 | raw / raw / raw | raw,raw,raw,raw,raw | coat rack 1 / 0 of 3 | 0 / 0 of 3 | 8 | - / - / - |

Paired gain: arm minus A0 on every row that names the object, 10,000 room draws. Fit counts are all-room; held-out counts use each fold's own choice. Every name, arm and fold: DECISION.json by_name (by_name_1037 beside).

**Open until part 2: table/desk, chair/seat, bookshelf/shelf.** The stored alias cache cannot decide these. On the stored pools the raw name puts more fit objects on target than the alias called alone (table 33, desk 6 of 54; chair 16, seat 8 of 32; bookshelf 5, shelf 1 of 10), but the stage-1 cache dropped every alias proposal whose IoU with an earlier retained instance exceeded 0.95, so the lead cannot tell a weaker alias from deduplication. They keep the raw name until part 2 reruns each alias alone; the default pass reruns only fold-chosen phrases, so this needs part2/sam3_pass.py pass --all-aliases (2,004 calls against 1,540).

## Rows to rewrite (1,012 decision rows)

| Arm | Names whose phrase changes | K1 training rows that name them (of 1,012) | By name | Rows needing the second call | Withheld rows naming them |
|---|---|---:|---|---:|---:|
| W1 (chosen) | heater -> radiator | 84 | heater 84 | - | 0 |
| W2 (tool-change diag.) | heater -> heater then radiator | 84 | heater 84 | 84 | 0 |
| W2c | heater -> heater then radiator | 84 | heater 84 | 14 | 0 |

Names whose in-sample best policy differs but that have fewer than five objects stay raw: coat hanger (3 objects, 8 operands; best W1 coat rack, W2 then coat rack, W2c then coat rack). K1 rows naming heater or coat hanger: 91 of 1,012 (91 of 1,037; design lane: 91). K1 train membership alone does not certify that a row may teach downstream. Routed training rows of N: MISSING (owner tree_rebuild; expected: N's routed training rows (rows carrying <ground obj=...> calls), held by tree_rebuild; not on trinity-1-18). Not opened: sb_ktow3 routed file with sha256 prefix 8855c81e (a dev-S1 return set): the binding brief keeps it closed; /scratch/jjyeung/n30_mirror/rows_r1 (store v7 and its slices): unrouted store rows; its STATUS.md records rows on K1 held-out rooms in the store family (v6), so the kit did not open it.

## Operands and served masks (2,074 row operands, all 1,037 rows)

| Arm | Good | Wrong object | Weak | Poor priced frame | Refused | Served IoU >= 0.5, visible frames | Priced-frame IoU mean | Masks on raster-absent frames |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P0 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| P_cap100 | 1356 | 319 | 188 | 175 | 36 | 44.2% of 13,793 | 0.560 | 976 |
| W1 | 1408 | 270 | 188 | 186 | 22 | 46.7% of 13,793 | 0.582 | 901 |
| W2 | 1396 | 272 | 193 | 191 | 22 | 46.8% of 13,793 | 0.580 | 913 |
| W2c | 1369 | 319 | 188 | 176 | 22 | 44.7% of 13,793 | 0.565 | 976 |

## Merge member precision and first-seen order (bars 90%), contrasts by dataset (all 1,037 rows)

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
- W1 prices a deduplicated subset; the exact serving score is unverified (standalone rerun = part 2). The stage-1 cache dropped alias proposals above IoU 0.95 against earlier retained instances; restoring them can move linking and selection in either direction.
- W2 needs a call that carries two phrases (the tool fills empty frames); W2c is two calls in today's syntax. The selector head (run_iso) has name_mode none, so the call's name does not move selection.
- Rows by worse operand under A0 (all 1,037 rows): refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456 (design record: refused 36, wrong object 287, weak 153, poor priced frame 105, both good 456).
- out/BARS.json (sha256 3157ad3e46fc70f0...) differs from the file the arms were priced under (150d16a232b42d86...) only in written_before_any_score and the registration record. A matching hash shows that a file did not change after it was written, not when it was written.
- Part 2 (W_exact, W_new, R_cond; SAM 3 on GPU) was not run.
