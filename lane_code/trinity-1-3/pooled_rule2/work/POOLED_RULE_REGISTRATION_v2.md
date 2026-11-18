# POOLED_RULE_REGISTRATION v2: pooled harm rule of leg R1 (run 673bc60f), ready for the orchestrator to register before any R1 export is read

Lane pooled_rule2 wrote this text on 2026-11-18 from the registration of lane pooled_rule and the fixes the review REVIEW_VERDICT_POOLED_RULE.md asked for. It binds from the moment the orchestrator registers it, and only if that happens before the first R1 export is read. It replaces H1's dev-S1 tests and H2's population in section 4 of `events/r1_ops/PRELAUNCH_CARD_R1.md`. Toward-facing accuracy, relative size, capped distance reads, the efficacy gates, the verdict and the spending rule stay as the card states them. Every probability below is a conditional simulation estimate, not a guarantee.

**H3 is not recalibrated.** Pooling changes H1 and H2 only. H3 keeps the card's rule and levels (a camera type's tower-arm interval at H1's card level wholly below zero, or under 95% of the 450 camera items drawing a call) and stays uncalibrated until paired tower-arm reads exist. This amends the card's prerequisite "with H2 and H3 recalibrated" (section 4, "Before the first export is read") to "with H2 recalibrated".

## 1. Rule

One decision per boundary (steps 200, 400, 600, 800): an R1 export against step 544 (artifact 1d6eeb28), paired by item, both read on the direct arm.

- **Item sets.** dev-S1 (family `main`): 1,050 items in 72 physical rooms, seven types of 150 items. R0-dev (family `a7`): 1,781 items in 98 physical rooms, seven types (counting 385, direction easy 192, medium 194, hard 192, relative distance 279, object size 293, appearance order 246).
- **Physical rooms.** `ROOM_CROSSWALK.json` maps every item of both sets to one canonical physical room: ScanNet `scannet/sceneNNNN` (all rescans of a room), ScanNet++ `scannetpp/<scene id>`, ARKitScenes `arkitscenes/venue<visit_id>` from `3dod/metadata.csv`. dev-S1's room labels (`d1/...`, `d2/...`, `d3/...`) and R0-dev's opaque labels each name exactly one canonical room and each room exactly one label, so the crosswalk partitions the items exactly as the labels do. The sets share no physical room, and no dev-S1 room is on the R0 list (bdb5d402). The tool resolves rooms through the crosswalk and refuses an item it does not map, or a row whose room or scene label names another room.
- **Statistic.** For a type and a set, D is the mean over the set's items of (R1 score minus step-544 score). Six types exist on both sets: counting, direction easy, medium and hard, relative distance, object size. For each, P = w x D(dev-S1) + (1 - w) x D(R0-dev), where w is dev-S1's share of the type's items, so every item counts once: 150/535, 150/342, 150/344, 150/342, 150/429, 150/443. Route planning exists only on dev-S1 and appearance order only on R0-dev; each is tested on its own set (P = D) inside the same family of eight.
- **Bootstrap.** 10,000 accepted joint draws, seed 20261118, Python `random.Random`. Each draw takes 72 dev-S1 rooms and then 98 R0-dev rooms with replacement, in the crosswalk's room order, and recomputes all eight P and their unweighted mean. A draw in which a set holds no item of some type is rejected and redrawn with the next two calls of the generator; only accepted draws count toward the 10,000, and the output reports the number rejected. On the three real reads no draw was rejected. Intervals are two-sided percentile intervals with linear interpolation.
- **H1, types.** STOP if the interval of one of the eight types lies wholly below zero. Level 1 - 0.05/8 = 99.375% at step 200 and 1 - 0.05/32 = 99.844% at steps 400, 600 and 800. Object size is one of the eight and remains a protected outcome under H1.
- **H2, mean.** STOP if the interval of the mean of the eight P lies wholly below zero. Level 95% at step 200 and 98.75% later.
- **Zero.** The tool compares the unrounded bounds with zero. Rounding to three decimals is for display only.
- **Nominal bound for an unchanged model.** H1 0.025 + H2 0.025 at step 200 and 0.00625 + 0.00625 at each later look: 0.0875 over the four looks, the card's figure. It assumes calibrated tails and excludes H3 and the other stopping gates.
- **Printed, stopping nothing.** In the console table and the JSON: each set's own difference per type with its 95% interval; a mark when one set's interval lies wholly below zero while the pooled test of that type is silent; object size split into dev-S1 metric (72 items), dev-S1 imperial (78) and R0-dev (293, centimetres only), each with its 95% interval from the rule's own draws. The unit of each dev-S1 size item is pinned in `SIZE_UNITS_DEV_S1.json`.
- **Unchanged tests.** Toward-facing accuracy and relative size exist only on dev-S1 and keep the card's levels, 99.29% at step 200 and 99.82% later (HOLD the first time, STOP the second). H3 keeps the card's rule and levels, uncalibrated.

**Read provenance.** Every read comes with one manifest per set (`PROVENANCE_SCHEMA.md`), written by `build_manifest.py` from the read kit's receipts. The tool refuses a read whose manifest is missing, disagrees with its receipts, its fetched archive or its rows, or differs from the registered step-544 manifest of its set anywhere outside the `run` block (run, artifact, step and the read job, token and plan hash that carry them, since the kit's plan hashes the export). The two manifests of a read must name one export, and a decision read must be of run 673bc60f at the boundary's step. Each decision read is logged in `READ_LEDGER.jsonl`; a second read of the same boundary and arm with another read file or manifest is refused. One difference from the step-544 manifest is registered as allowed: the type filter. dev-S1's baseline was read unfiltered and R1 reads with the `direct` filter; the filter removes only absolute distance and room size, which the rule does not read, so the tool compares the rule's population (equal on both) and checks that a `direct` read holds neither removed type.

The reference implementation is the rule. One boundary is read with
`python3 pooled_harm_rule_v2.py --step 200 --read <ITEMS.jsonl of the R1 read> --manifest-s1 <dev-S1 manifest> --manifest-r0 <R0-dev manifest> --ledger events/pooled_rule/READ_LEDGER.jsonl --output R1_200_POOLED.json`,
with each manifest written by `python3 build_manifest.py kit <read-kit build dir> dev-S1|R0-dev <manifest>`. The step-100 export has no decision; `--calibration --step 200` prints it at the step-200 levels, checks the manifests, writes no ledger line and decides nothing.

## 2. Pins

| Pin | Value |
|---|---|
| Step-544 artifact | sha256 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef (run 469ddece, m544) |
| dev-S1 baseline read | `A544.jsonl`, sha256 8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be (Orchard 169526, evalx read e193c2a3c) |
| R0-dev baseline read | `ITEMS.jsonl` of Orchard 171197 (token adff67f7ae9), sha256 a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233 |
| dev-S1 baseline manifest | `BASE_MANIFEST_dev-S1_544.json`, sha256 e08a1d3427cf2adc31c96544d08913ed5ca173f7a08129a57f2d8759592a584b |
| R0-dev baseline manifest | `BASE_MANIFEST_R0-dev_544.json`, sha256 86c8f993b5b799fc29f183bb295db136f2a4cac43c4ce8dbe10deb6656f530a1 |
| Reader identity in both manifests | evaluator source digest d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa; greedy, 32 anchors duplicated, 16,384 tokens, thinking on, temperature 0, engine 0.32.0, budget 2048; item files dev-S1 `TASKS.jsonl` a2f3fdbd, R0-dev `e52a690b.jsonl` 1d8b29a7 |
| Room crosswalk | `ROOM_CROSSWALK.json`, sha256 994902af7647a52f7c288c975226305d91ea4875fdcc312456e8db79c4140c3b (72 + 98 rooms; sources: both baselines, ID map aff009a0, ARKitScenes metadata, R0 lists bdb5d402 and 855ef477) |
| dev-S1 size units | `SIZE_UNITS_DEV_S1.json`, sha256 2a0d756bdb65093e6e55e508ba12b022fd5805e5274d4b45fb6c629400b2867f (72 metric, 78 imperial) |
| dev-S1 item set (id, room label, type) | sha256 22ad2765e8e9a69b7395ff98ff578aaa2fb36d454f5ed4cf47f6b935166412a4, 1,050 items |
| R0-dev item set | sha256 630cd8691a2c36ce5c7f6d58e8d7fcbfff1c01521105b926f2f82c8d16e73e71, 1,781 items |
| Reference implementation `pooled_harm_rule_v2.py` | sha256 4b6e3280eba87774d8cc151aa6708a86c74fa43061985fd7dedce768992b0e5b |
| Manifest writer `build_manifest.py` | sha256 699cacd7b80608af41f3f5f533b6f12fdd3adaad1e99cde3de065bde9db9b755 |
| Seed, draws, generator | 20261118, 10,000 accepted draws, Python `random.Random` |

Files: `events/pooled_rule/` holds the executable, the manifest writer, the crosswalk and its builder, the size units, both baseline manifests, `PROVENANCE_SCHEMA.md`, the tests and their output, and `pooled_rule2_evidence.tgz`.

## 3. Estimated behaviour, against the card's dev-S1 rule on the same pseudo-reads

Method of lane card_fix: double bootstrap on the paired D0 m200 reads of both sets against step 544, 8,000 pseudo-reads, each scored with a 10,000-draw interval; Monte Carlo standard error at most 0.006. "Unchanged" resamples whole rooms and exchanges the two arms inside each drawn room; "flips" sets a later-arm item to zero with probability loss / mean score; "shifted" moves the null by the loss. These figures come from `pr_sim.py`, which draws the inner bootstrap with NumPy's generator and fresh draws per pseudo-read and never rejects a draw; the executable uses one fixed `random.Random` stream and rejects draws missing a type. The executable-path check below shows that the difference does not move the figures beyond Monte Carlo error.

| Scenario | Pooled, step 200 | dev-S1 rule, step 200 | Pooled, later look | dev-S1 rule, later look |
|---|---|---|---|---|
| Unchanged model: H1 or H2 stops the leg | 0.055 (H1 0.034, H2 0.027) | 0.064 | 0.016 (H1 0.012, H2 0.006) | 0.024 |
| Unchanged model over the looks (four real reads permuted per room; extrapolated estimate) | 0.054 | 0.061 | 0.077 by step 600; extrapolated estimate 0.094 by step 800, not a measured four-look rate | 0.096; extrapolated 0.120 |
| (a) Size loss of D0's size: dev-S1 -9.5, R0-dev -4.3; flips / D0's noise shifted | 0.70 / 0.88 | 0.51 / 0.74 | 0.53 / 0.78 | 0.34 / 0.59 |
| (b) -9.5 on one other type on both sets (flips): counting, relative distance | 0.98, 0.96 | 0.41, 0.56 | 0.95, 0.90 | 0.25, 0.38 |
| (b) direction easy, medium, hard | 0.84, 0.73, 0.75 | 0.65, 0.61, 0.65 | 0.71, 0.57, 0.60 | 0.48, 0.43, 0.49 |
| (b) route planning (dev-S1 only) / appearance order (R0-dev only) | 0.42 / 0.54 | 0.42 / 0.06 (not tested) | 0.25 / 0.35 | 0.26 / 0.02 |
| (c) Uniform -2 on every type: flips / shifted | 0.59 / 0.61 | 0.42 / 0.49 | 0.37 / 0.39 | 0.24 / 0.29 |
| Uniform -3 and -4, H2 alone | 0.87 and 0.99 | 0.70 and 0.90 | 0.73 and 0.95 | 0.50 and 0.79 |
| Size drift of -3 / -6 on both sets, size test alone | 0.18 / 0.78 | 0.05 / 0.22 | 0.09 / 0.64 | 0.02 / 0.12 |
| -9.5 on size on dev-S1 only (flips) | 0.24 | 0.51 | 0.12 | 0.34 |
| -9.5 on size on R0-dev only (flips) | 0.74 | 0.06 (not tested) | 0.58 | 0.02 |

The four-look row simulates three looks on permuted real reads and adds an estimated marginal for the fourth (`pr_looks.py`, `pr_looks_merge.py`); its step-800 figure is an extrapolated estimate, not a measured four-look error rate or a bound.

**Executable path.** `sim_exec.py` scores pseudo-reads from `pr_sim.py`'s generator through the executable's own statistics (`decide` in `pooled_harm_rule_v2.py`: fixed seed, rejection rule, unrounded bounds). Pseudo-reads come from the D0 m200 pairs as above; the unchanged model has 4,000 of them, the two loss scenarios 1,000 each (`SIM_EXEC_AGREEMENT.json`).

| Scenario: H1 or H2 stops (MC se) | Executable, step 200 | `pr_sim.py`, step 200 | Executable, later look | `pr_sim.py`, later look |
|---|---|---|---|---|
| Unchanged model (H1 / H2 at step 200) | 0.053 (0.004); 0.031 / 0.027 | 0.055 (0.003); 0.034 / 0.027 | 0.015 (0.002) | 0.016 (0.001) |
| (a) D0's size loss, flips | 0.689 (0.015) | 0.700 (0.005) | 0.531 (0.016) | 0.533 (0.006) |
| (c) Uniform -2, flips | 0.594 (0.016) | 0.589 (0.006) | 0.383 (0.015) | 0.368 (0.005) |

Every executable figure lies within one combined standard error of the archived one (largest |z| 0.99, H1 and H2 components included). On the first 1,000 unchanged-model pseudo-reads alone the later-look rate was 0.008 (z -2.6); the 3,000 further pseudo-reads give 0.015. No draw was rejected on any pseudo-read, so the rejection rule never acted on this noise model.

The pooled rule sees less than the dev-S1 rule in one case: a loss that sits on dev-S1 alone (0.17 to 0.24 against 0.41 to 0.65 for a 9.5-point loss on one type). The printed per-set intervals and the size split show such a loss; they stop nothing.

Applied with the registered seed to the three real later reads, the rule stops each on object size and on nothing else: D0 m200 -6.095 [-10.641, -1.668], D0 m100 -4.695 [-8.345, -0.967], H1-1 m100 -4.357 [-8.326, -0.711] at the step-200 level, and each interval stays below zero at the later-look level (upper bounds -1.208, -0.588, -0.275). The crosswalk leaves the clustering and the room order unchanged, so v2 reproduces v1's intervals on all eight types and the mean exactly. The size split shows where the loss sits: dev-S1 imperial items lose -12.9, -19.6 and -18.6 points, dev-S1 metric items -5.8, -0.4 and -3.2, R0-dev items -4.3, -1.8 and -0.9.

## 4. Validity conditions of the card

| Condition | Status | Evidence |
|---|---|---|
| The baseline is the exact step-544 artifact on both sets | Holds; the tool enforces it | Both baseline manifests bind artifact 1d6eeb28 and step 544 to `SPEC.json` of Orchard 169526 and 171197; every baseline row carries step 544 |
| Both arms use the same item keys | Holds; the tool enforces it | The four reads of each set carry identical keys and paired metadata on 1,050 + 1,781 items |
| Same arm, reader build, decoding and scoring | Holds for R1 through the manifests, with two things unmeasured | The tool refuses a read whose arm, evaluator digest, decoding, selector, scale rule, tower weights or item file differs from the step-544 manifest; the D0 and H1-1 reads of both read kits pass. The same prediction earns the same score on 2,341 dev-S1 and 3,084 R0-dev item pairs across builds. Unmeasured: no filtered `main` read has run in production, and step 544 has one read per set, so the read noise of an unchanged model is unknown |
| One read per boundary and arm, of R1's export | Holds; the tool enforces it | Run 673bc60f at the boundary's step, one export for both sets, read file equal to the decoded fetched archive, ledger refuses a second, different read |
| Physical rooms and dataset weights fixed in advance | Holds; the tool enforces it | `ROOM_CROSSWALK.json` pinned; every item maps to one room, rooms cluster scenes as the labels do, the sets share no room, no dev-S1 room is on the R0 list; weights are constants |
| R0 exposure: no R1 row on an R0 room | Holds for the rows lane pooled_rule could resolve; the remainder rests on the R0 census | Store v7 (210b2534): 201,980 of 204,413 rows resolve to a capture, none on an R0 room; 2,433 rows on 52 ScanNet++ scene tokens resolve only through the census (kit07 frame map 17aa3e9e); unit rows 5f9383fa: 0 hits; routing selection, pose and pointing streams on Orchard unread |

Conditions on R1's reads: the h1read kit at fix 5, or a later fix that leaves the 72 pinned reader files (`evidence/FINAL_PINS.json`, f8911c19 at fix 5) unchanged outside `chain.py`, `paired_read.py`, `worker.py`, `x7.py` and `read_filter.py`; families `main` and `a7` complete; the read run on trinity-1-3, where the receipts, the fetched archive and the baselines live. A serving-pin change forces a new step-544 read of both sets, new baseline manifests and a new registration of their pins.
