# POOLED_RULE_REGISTRATION: pooled harm rule of leg R1 (run 673bc60f), ready for the orchestrator to register before any R1 export is read

Lane pooled_rule wrote this text on 2026-11-18. It binds from the moment the orchestrator registers it, and only if that happens before the first R1 export is read. It replaces H1's dev-S1 tests and H2's population in section 4 of `events/r1_ops/PRELAUNCH_CARD_R1.md`. H3, the protected outcomes on toward-facing accuracy, relative size and capped distance reads, the efficacy gates, the verdict and the spending rule stay as the card states them. Every probability below is a conditional simulation estimate, not a guarantee.

## 1. Rule

One decision per boundary (steps 200, 400, 600, 800): an R1 export against step 544 (artifact 1d6eeb28), paired by item, both read on the direct arm.

- **Item sets.** dev-S1 (family `main`): 1,050 items in 72 rooms, seven types of 150 items. R0-dev (family `a7`): 1,781 items in 98 rooms, seven types (counting 385, direction easy 192, medium 194, hard 192, relative distance 279, object size 293, appearance order 246). The sets share no room.
- **Statistic.** For a type and a set, D is the mean over the set's items of (R1 score minus step-544 score). Six types exist on both sets: counting, direction easy, medium and hard, relative distance, object size. For each, P = w x D(dev-S1) + (1 - w) x D(R0-dev), where w is dev-S1's share of the type's items, so every item counts once: 150/535, 150/342, 150/344, 150/342, 150/429, 150/443. Route planning exists only on dev-S1 and appearance order only on R0-dev; each is tested on its own set (P = D) inside the same family of eight.
- **Bootstrap.** 10,000 joint draws, seed 20261118. Each draw takes 72 dev-S1 rooms and then 98 R0-dev rooms with replacement and recomputes all eight P and their unweighted mean. Intervals are two-sided percentile intervals.
- **H1, types.** STOP if the interval of one of the eight types lies wholly below zero. Level 1 - 0.05/8 = 99.375% at step 200 and 1 - 0.05/32 = 99.844% at steps 400, 600 and 800. Object size is one of the eight and remains a protected outcome under H1.
- **H2, mean.** STOP if the interval of the mean of the eight P lies wholly below zero. Level 95% at step 200 and 98.75% later.
- **Nominal bound for an unchanged model.** H1 0.025 + H2 0.025 at step 200 and 0.00625 + 0.00625 at each later look: 0.0875 over the four looks, the card's figure.
- **Printed, stopping nothing.** Each set's own difference per type with its 95% interval; a mark when one set's interval lies wholly below zero while the pooled test of that type is silent; object size split into dev-S1 metric (72 items), dev-S1 imperial (78) and R0-dev (293, centimetres only).
- **Unchanged tests.** Toward-facing accuracy and relative size exist only on dev-S1 and keep the card's levels, 99.29% at step 200 and 99.82% later (HOLD the first time, STOP the second). H3 keeps the same two levels and its call floor.

The reference implementation is the rule: `pooled_harm_rule.py` refuses a read whose baselines, item keys, paired metadata, rooms or step differ from the pins. One boundary is read with
`python pooled_harm_rule.py --step 200 --read <ITEMS.jsonl of the R1 read, families main and a7> --output R1_200_POOLED.json`.
The step-100 export has no decision; `--calibration --step 200` prints it at the step-200 levels and decides nothing.

## 2. Pins

| Pin | Value |
|---|---|
| Step-544 artifact | sha256 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef (run 469ddece, m544) |
| dev-S1 baseline read | `A544.jsonl`, sha256 8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be (Orchard 169526) |
| R0-dev baseline read | `ITEMS.jsonl` of Orchard 171197, sha256 a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233 |
| dev-S1 item set (id, room, type; `ITEMS_DEV_S1.tsv`) | sha256 22ad2765e8e9a69b7395ff98ff578aaa2fb36d454f5ed4cf47f6b935166412a4, 1,050 items |
| R0-dev item set (`ITEMS_R0_DEV.tsv`) | sha256 630cd8691a2c36ce5c7f6d58e8d7fcbfff1c01521105b926f2f82c8d16e73e71, 1,781 items |
| Room list (`ROOM_LIST.txt`, 72 + 98 rooms) | sha256 3440f7cfa19d2b70c05d38b949809e33fa90b770bf1ee9c17737fa78abde7e07 |
| Reference implementation `pooled_harm_rule.py` | sha256 a144e2cc093bbbfd4137b79dedc2be40ac29f3efcb910654d4125e77dc6cfc1b |
| Seed, draws, generator | 20261118, 10,000, Python `random.Random` (same output under Python 3.6.8 and 3.12.13) |
| Reader | evaluator digest d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa, `PROTOCOL.json` a2db00df (greedy, 32 anchors duplicated, 16,384 tokens, thinking on), scores at budget 2048 |

Files: `events/pooled_rule/pooled_harm_rule.py` and `events/pooled_rule/pooled_rule_evidence.tgz` (the item lists, room list, baselines, simulation code and results).

## 3. Estimated behaviour, against the card's dev-S1 rule on the same pseudo-reads

Method of lane card_fix: double bootstrap on the paired D0 m200 reads of both sets against step 544, 8,000 pseudo-reads, each scored with the rule's own 10,000-draw interval; Monte Carlo standard error at most 0.006. "Unchanged" resamples whole rooms and exchanges the two arms inside each drawn room; "flips" sets a later-arm item to zero with probability loss / mean score; "shifted" moves the null by the loss.

| Scenario | Pooled, step 200 | dev-S1 rule, step 200 | Pooled, later look | dev-S1 rule, later look |
|---|---|---|---|---|
| Unchanged model: H1 or H2 stops the leg | 0.055 (H1 0.034, H2 0.027) | 0.064 | 0.016 (H1 0.012, H2 0.006) | 0.024 |
| Unchanged model over the looks (four real reads permuted per room) | 0.054 | 0.061 | 0.077 by step 600; at most 0.094 by step 800 | 0.096; at most 0.120 |
| (a) Size loss of D0's size: dev-S1 -9.5, R0-dev -4.3; flips / D0's noise shifted | 0.70 / 0.88 | 0.51 / 0.74 | 0.53 / 0.78 | 0.34 / 0.59 |
| (b) -9.5 on one other type on both sets (flips): counting, relative distance | 0.98, 0.96 | 0.41, 0.56 | 0.95, 0.90 | 0.25, 0.38 |
| (b) direction easy, medium, hard | 0.84, 0.73, 0.75 | 0.65, 0.61, 0.65 | 0.71, 0.57, 0.60 | 0.48, 0.43, 0.49 |
| (b) route planning (dev-S1 only) / appearance order (R0-dev only) | 0.42 / 0.54 | 0.42 / 0.06 (not tested) | 0.25 / 0.35 | 0.26 / 0.02 |
| (c) Uniform -2 on every type: flips / shifted | 0.59 / 0.61 | 0.42 / 0.49 | 0.37 / 0.39 | 0.24 / 0.29 |
| Uniform -3 and -4, H2 alone | 0.87 and 0.99 | 0.70 and 0.90 | 0.73 and 0.95 | 0.50 and 0.79 |
| Size drift of -3 / -6 on both sets, size test alone | 0.18 / 0.78 | 0.05 / 0.22 | 0.09 / 0.64 | 0.02 / 0.12 |
| -9.5 on size on dev-S1 only (flips) | 0.24 | 0.51 | 0.12 | 0.34 |
| -9.5 on size on R0-dev only (flips) | 0.74 | 0.06 (not tested) | 0.58 | 0.02 |

The pooled rule sees less than the dev-S1 rule in one case: a loss that sits on dev-S1 alone (0.17 to 0.24 against 0.41 to 0.65 for a 9.5-point loss on one type). The printed per-set intervals and the size split show such a loss; they stop nothing.

Applied with the registered seed to the three real later reads, the rule stops each on object size and on nothing else: D0 m200 -6.09 [-10.64, -1.67], D0 m100 -4.70 [-8.35, -0.97], H1-1 m100 -4.36 [-8.33, -0.71] at the step-200 level, and each interval stays below zero at the later-look level (upper bounds -1.21, -0.59, -0.28).

## 4. Validity conditions of the card

| Condition | Status | Evidence |
|---|---|---|
| The baseline is the exact step-544 artifact on both sets | Holds | `SPEC.json` of Orchard 169526 and of 171197 both name `runs/469ddece/m544/artifact.json` with sha256 1d6eeb28; every baseline row carries step 544 |
| Both arms use the same item keys | Holds; the tool enforces it for R1 | The four reads of each set (step 544, D0 m200, D0 m100, H1-1 m100) carry identical keys and paired metadata on 1,050 + 1,781 items |
| Same arm, reader build, decoding and scoring | Holds, with two things unmeasured | Direct arm in every read. The D0 read kit and the h1read kit share 72 reader files, all byte-identical except `chain.py`, `paired_read.py` and `worker.py` (orchestration); both bind prompts byte-equal to the accepted packet (digest d27804f7). The same prediction earns the same score on 2,341 dev-S1 and 3,084 R0-dev item pairs across builds, with no exception. Unmeasured: no filtered `main` read has run in production (review_h1read4 note b: it fails closed), and step 544 has no second read on dev-S1, so the noise between job 169526's packet and the kit is unknown |
| R1's dev-S1 read pairs with `A544.jsonl` under the direct-types filter | Holds by construction | The filter drops only absolute distance and room size after full validation, keeps the seven types at 150 items each and changes no prompt; an unfiltered read pairs as well |
| Rooms and dataset weights fixed in advance | Holds | Pinned in the reference implementation; no dev-S1 room id occurs among the 372 R0 rooms |
| R0 exposure: no R1 row on an R0 room | Holds for the rows I could resolve; the remainder rests on the R0 census | Store v7 (210b2534): its gate found 0 R0 hits on the 8,942 new rows; my scan of all 204,413 rows resolves 201,980 to a capture, none on an R0 room; the other 2,433 rows sit on 52 ScanNet++ scenes that no alias map on trinity-1-3 resolves, and each of those scenes has rows on the kit07 frame map (17aa3e9e), whose rooms the census removed from R0. Unit rows (5f9383fa): 747 rows, 0 hits. Routing selection 5db993b1, pose and pointing rows live on Orchard and I did not read them; they are sealed streams of division A3, another authority of the census |

Conditions on R1's reads: the h1read kit at fix 5, or a later fix that leaves the 72 pinned reader files (`evidence/FINAL_PINS.json`, f8911c19 at fix 5) unchanged outside `chain.py`, `paired_read.py`, `worker.py`, `x7.py` and `read_filter.py`; families `main` and `a7` complete; a serving-pin change forces a new step-544 read of both sets and a new registration of the two baseline pins.
