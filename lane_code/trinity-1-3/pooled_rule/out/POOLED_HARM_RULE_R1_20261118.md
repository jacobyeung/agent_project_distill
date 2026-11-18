# Pooled harm rule for leg R1: one test per direct type on dev-S1 and R0-dev together (lane pooled_rule, 2026-11-18)

**Question.** Leg R1's harm rule reads dev-S1 alone and sees a loss the size of D0's object-size loss only 0.51 to 0.72 of the time. Does one test per direct type on dev-S1 and R0-dev together, with rooms resampled over both sets, stop an unchanged model no more often and catch real losses more often, and do the card's validity conditions hold?

**Answer.** Adopt the pooled rule. On the same pseudo-reads it stops an unchanged model less often than the dev-S1 rule (0.055 against 0.064 at step 200, 0.016 against 0.024 at each later look, at most 0.094 against 0.120 over the four looks; the nominal bound stays 0.0875) and it catches every loss the brief names more often: D0's size loss 0.70 to 0.88 against 0.51 to 0.74, a 9.5-point loss on another shared type 0.73 to 0.98 against 0.41 to 0.65, a uniform 2-point loss 0.59 against 0.42. It also tests appearance order, which dev-S1 does not hold. It sees less in one case, a loss confined to dev-S1 (0.17 to 0.24 against 0.41 to 0.65), and the report prints a mark for that case. The card's validity conditions hold, with two remainders: the read-to-read noise of an unchanged model is unmeasured, and the R0 exposure audit covers 98.8% of the VQA rows and all unit rows by direct scan and rests on the R0 census for the rest. The registration text is `events/pooled_rule/POOLED_RULE_REGISTRATION.md`; it binds only if the orchestrator registers it before the first R1 export is read.

## The rule

- **Statistic.** For each type and set, D is the mean paired difference (R1 minus step 544) over the set's items. Counting, direction easy, medium and hard, relative distance and object size exist on both sets; their statistic is P = w x D(dev-S1) + (1 - w) x D(R0-dev) with w the dev-S1 share of the type's items (0.280, 0.439, 0.436, 0.439, 0.350, 0.339), so every item counts once. Route planning exists only on dev-S1 (150 items, 40 rooms) and appearance order only on R0-dev (246 items, 83 rooms); each is tested on its own set inside the same family, because R1 trains rows of both types and a rule that left one out would be blind to it.
- **Bootstrap.** 10,000 joint draws, seed 20261118: 72 dev-S1 rooms and 98 R0-dev rooms, each set resampled with replacement, all eight statistics and their mean recomputed from the same draw. Resampling inside each set keeps the dataset weights fixed.
- **H1.** A type's two-sided percentile interval wholly below zero stops the leg: level 1 - 0.05/8 at step 200, 1 - 0.05/32 later. **H2.** The interval of the unweighted mean of the eight wholly below zero stops it: 95% at step 200, 98.75% later. Nominal: 0.025 + 0.025, then 0.00625 + 0.00625 per look, 0.0875 over four looks.
- **Protected outcomes.** Object size stays under H1 as one of the eight. Toward-facing accuracy and relative size exist only on dev-S1 and keep the card's tests and levels (99.29%, 99.82%). H3 is untouched.
- **Reference implementation.** `pooled_harm_rule.py` (sha256 a144e2cc) pins both baselines, both item sets, the room list, the weights, the seed and the levels, and refuses a read that differs on any of them.

## Evidence

**Method.** Lane card_fix's double bootstrap, extended to both sets (`pr_sim.py`). The noise model is the paired D0 m200 read against step 544: 1,050 dev-S1 items in 72 rooms and 1,781 R0-dev items in 98 rooms. Each of 8,000 pseudo-reads draws whole rooms with replacement inside each set and is scored with the rule's own 10,000-draw interval, so the rates include the tool's noise. "Unchanged" exchanges the two arms inside each drawn room with probability 1/2; "flips" sets a later-arm item to zero with probability loss / mean score; "shifted" moves a null by the loss; "D0 noise" centres D0's observed differences instead of exchanging arms. The dev-S1 rule runs on the same pseudo-reads and reproduces the card: 0.064 and 0.024 for an unchanged model (card 0.063, 0.023), 0.51 and 0.34 for the size loss with flips (0.51, 0.33), 0.42 and 0.24 for a uniform 2-point loss (0.42, 0.23). Monte Carlo standard errors are printed beside each rate.

| Scenario (noise: D0 m200 against step 544) | dev-S1 rule, step 200 | pooled rule, step 200 | dev-S1 rule, later look | pooled rule, later look |
|---|---|---|---|---|
| Unchanged model, arms exchanged per room | 0.064 ± 0.003 | 0.055 ± 0.003 | 0.024 ± 0.002 | 0.016 ± 0.001 |
| Unchanged model, D0 noise centred | 0.097 ± 0.003 | 0.056 ± 0.003 | 0.059 ± 0.003 | 0.018 ± 0.002 |
| (a) size: dev-S1 -9.5 and R0-dev -4.3, item flips | 0.510 ± 0.006 | 0.700 ± 0.005 | 0.339 ± 0.005 | 0.533 ± 0.006 |
| (a) the same, exchange null shifted | 0.618 ± 0.005 | 0.802 ± 0.004 | 0.449 ± 0.006 | 0.664 ± 0.005 |
| (a) the same, D0 noise shifted | 0.741 ± 0.005 | 0.879 ± 0.004 | 0.588 ± 0.005 | 0.776 ± 0.005 |
| (b) -9.5 on counting, both sets | 0.414 ± 0.005 | 0.980 ± 0.002 | 0.250 ± 0.005 | 0.949 ± 0.003 |
| (b) -9.5 on direction easy, both sets | 0.650 ± 0.005 | 0.841 ± 0.004 | 0.481 ± 0.006 | 0.714 ± 0.005 |
| (b) -9.5 on direction medium, both sets | 0.606 ± 0.005 | 0.734 ± 0.005 | 0.431 ± 0.005 | 0.567 ± 0.005 |
| (b) -9.5 on direction hard, both sets | 0.646 ± 0.005 | 0.753 ± 0.005 | 0.485 ± 0.006 | 0.596 ± 0.005 |
| (b) -9.5 on relative distance, both sets | 0.555 ± 0.006 | 0.961 ± 0.002 | 0.376 ± 0.005 | 0.902 ± 0.003 |
| (b) -9.5 on route planning (dev-S1 only) | 0.423 ± 0.005 | 0.421 ± 0.005 | 0.262 ± 0.005 | 0.249 ± 0.005 |
| (b) -9.5 on appearance order (R0-dev only) | 0.064 ± 0.003 (not tested) | 0.536 ± 0.006 | 0.024 ± 0.002 | 0.352 ± 0.005 |
| (c) -2 on every type, item flips | 0.420 ± 0.005 | 0.589 ± 0.005 | 0.237 ± 0.005 | 0.368 ± 0.005 |
| (c) the same, exchange null shifted | 0.490 ± 0.006 | 0.611 ± 0.005 | 0.293 ± 0.005 | 0.387 ± 0.005 |
| -3 on every type, H2 alone | 0.703 ± 0.005 | 0.871 ± 0.004 | 0.500 ± 0.006 | 0.731 ± 0.005 |
| -4 on every type, H2 alone | 0.905 ± 0.003 | 0.985 ± 0.001 | 0.785 ± 0.005 | 0.949 ± 0.003 |
| Size drift -3 on both sets, size test alone | 0.047 ± 0.002 | 0.178 ± 0.004 | 0.021 ± 0.002 | 0.095 ± 0.003 |
| Size drift -6 on both sets, size test alone | 0.218 ± 0.005 | 0.776 ± 0.005 | 0.122 ± 0.004 | 0.641 ± 0.005 |
| -9.5 on size, dev-S1 only | 0.510 ± 0.006 | 0.242 ± 0.005 | 0.339 ± 0.005 | 0.116 ± 0.004 |
| -9.5 on size, R0-dev only | 0.064 ± 0.003 (not tested) | 0.742 ± 0.005 | 0.024 ± 0.002 | 0.580 ± 0.005 |
| -9.5 on counting, dev-S1 only / R0-dev only | 0.414 / 0.064 | 0.166 / 0.795 | 0.250 / 0.024 | 0.073 / 0.659 |
| -9.5 on direction hard, dev-S1 only / R0-dev only | 0.646 / 0.064 | 0.191 / 0.302 | 0.485 / 0.024 | 0.084 / 0.161 |
| -9.5 on relative distance, dev-S1 only / R0-dev only | 0.555 / 0.064 | 0.227 / 0.661 | 0.376 / 0.024 | 0.106 / 0.484 |

**Where the unchanged-model rate comes from.** Pooled rule: H1 0.034 ± 0.002 and H2 0.027 ± 0.002 at step 200, 0.012 ± 0.001 and 0.006 ± 0.001 later. dev-S1 rule: 0.042 and 0.030, then 0.017 and 0.009. The percentile interval stays a little anti-conservative for H1 (nominal 0.025 and 0.00625), less so than on dev-S1's 35 to 59 rooms per type.

**The four looks together** (`pr_looks.py`, 8,000 pseudo-legs). The four real reads of each item (step 544, D0 m100, D0 m200, H1-1 m100) are permuted inside each drawn room; the first serves as baseline and the others as looks that share it. The pooled rule stops an unchanged model with probability 0.054 ± 0.003 at step 200, 0.067 by step 400 and 0.077 ± 0.003 by step 600; adding the fourth look's own rate gives at most 0.094 over four looks. The dev-S1 rule gives 0.061, 0.082, 0.096 and at most 0.120. The pooled statistics of D0 m100 and D0 m200 correlate at 0.47 to 0.68 per type under one bootstrap (0.61 for the mean), which is why the looks overlap.

**Precision.** Bootstrap standard errors on the D0 m200 read, in points: pooled counting 1.73, direction easy 2.17, medium 2.66, hard 2.48, relative distance 1.79, size 1.63, route planning 3.53, appearance order 3.35, mean of eight 0.93. The dev-S1 rule has 4.00, 2.40, 2.58, 2.16, 2.82, 3.08, 3.48 and 1.21 for its mean of seven. Each pooled test detects half the time a loss of about 2.7 standard errors: 4.5 to 7.3 points on the shared types, against 5.9 to 10.8 on dev-S1.

**Other noise models.** With the H1-1 m100 read and with the D0 m100 read as the noise model, an unchanged model is stopped 0.052 / 0.018 and 0.052 / 0.016 of the time (dev-S1 rule 0.061 / 0.020 and 0.060 / 0.023), and the size loss (a) is caught 0.78 and 0.82 with flips (dev-S1 rule 0.56 and 0.56). A uniform 2-point loss is caught 0.55 and 0.54 with flips (0.48 and 0.43). One cell goes the other way: with H1-1 m100's noise shifted by 2 points the dev-S1 rule reaches 0.58 and the pooled rule 0.57. Under each read's own centred noise the dev-S1 rule stops an unchanged model 0.10 to 0.12 of the time at step 200 and the pooled rule 0.06.

**The three real reads under the rule** (`pooled_harm_rule.py --calibration`, registered seed). Each is stopped on object size and on nothing else, at both levels.

| Read against step 544 | dev-S1 size (metric / imperial) | R0-dev size | Pooled size, step-200 level | Later-look level | Mean of eight |
|---|---|---|---|---|---|
| D0 m200 | -9.53 (-5.83 / -12.95) | -4.33 | -6.09 [-10.64, -1.67] | [-11.15, -1.21] | +2.62 [+0.83, +4.48] |
| D0 m100 | -10.40 (-0.42 / -19.62) | -1.77 | -4.70 [-8.35, -0.97] | [-8.95, -0.59] | +2.69 [+0.72, +4.59] |
| H1-1 m100 | -11.20 (-3.19 / -18.59) | -0.85 | -4.36 [-8.33, -0.71] | [-9.28, -0.28] | +2.63 [+0.72, +4.54] |

With 200,000 draws the upper bounds are -1.74, -1.08 and -0.60 at the step-200 level and -0.99, -0.46 and -0.03 later, so the H1-1 m100 stop at the later-look level depends on the seed. The dev-S1 rule stops the same three reads on size alone ([-18.01, -1.37], [-18.13, -3.21], [-19.09, -4.03] at the step-200 level).

**Validity conditions.**
1. *Exact step-544 artifact on both sets: holds.* `SPEC.json` of Orchard 169526 (the read behind `A544.jsonl`) and of 171197 (the R0-dev baseline) both name `runs/469ddece/m544/artifact.json`, sha256 1d6eeb28; every baseline row carries step 544.
2. *Same item keys: holds.* The four reads of each set carry identical keys and paired metadata (task type, room, scene, scoring basis, level, pair, count kind) on 1,050 and 1,781 items; the tool refuses an R1 read that differs.
3. *Same arm, reader build, decoding and scoring: holds, two things unmeasured.* Every read is the direct arm. The D0 read kit and the h1read kit share 72 reader files, byte-identical except `chain.py`, `paired_read.py` and `worker.py`, which order the work; both bind prompts byte-equal to the accepted packet (evaluator digest d27804f7) under `PROTOCOL.json` a2db00df (greedy, 32 anchors duplicated, 16,384 tokens, thinking on). Across builds the same prediction earns the same score on 2,341 dev-S1 and 3,084 R0-dev item pairs, without exception. Unmeasured: step 544 has one read per set, so read-to-read noise between job 169526's packet and the kit is unknown (the card's dev-S1 rule carries the same exposure); and no filtered `main` read has run in production.
4. *R1's dev-S1 read pairs with `A544.jsonl` under the direct-types filter: holds by construction.* The filter (`read_filter.py` 562bc588) drops only absolute distance and room size after full validation, keeps the seven types at 150 items each and changes no prompt. If the filtered `main` read fails closed (review_h1read4 note b), an unfiltered read pairs equally.
5. *Rooms and weights fixed in advance: holds.* They are constants of the reference implementation. No dev-S1 room id occurs among the 372 R0 rooms.
6. *R0 exposure: holds for the rows I could resolve; the rest rests on the census.* Store v7's gate found 0 R0 hits on its 8,942 new rows. My scan of all 204,413 rows of `rows.sqlite` 210b2534 (`r0_exposure.py`) resolves 201,980 to a canonical capture through three alias maps and finds none on an R0 room; controls catch an R0-dev room and an R0 ScanNet room. The other 2,433 rows sit on 52 ScanNet++ scene tokens that no map on trinity-1-3 resolves; every one of those 52 scenes has rows on the kit07 frame map (17aa3e9e), an authority whose rooms the R0 census removed with 0 unresolved keys. The 747 unit rows (5f9383fa) resolve fully, 0 hits. The routing selection 5db993b1 and the pose and pointing rows are on Orchard and I did not read them; they are sealed streams of division A3, also a census authority.

**Files.** Lane folder trinity-1-3:`/scratch/jjyeung/orch_n30/pooled_rule/work/`: `pr_data.py`, `pr_sim.py`, `pr_merge.py`, `pr_looks.py`, `pr_observed.py`, `pooled_harm_rule.py`, `r0_exposure.py`; results `POOLED_POWER_{D0m200,H1m100,D0m100}.json`, `LOOKS.json`, `OBSERVED_READS.json`, `obs/`, `R0_EXPOSURE_V7.json`, `R0_EXPOSURE_UNITS_P.json`, `PAIRS_META.json` (sha256 of the eight reads), `REGISTERED_PINS.json`. Evidence archive `events/pooled_rule/pooled_rule_evidence.tgz` (sha256 in the RESULT event and in `STATUS.md`).

## Options rejected, and why

- **Keep the dev-S1 rule.** It stops an unchanged model more often and catches each named loss less often, it is blind to appearance order and to any loss that shows on the unexposed set alone, and under D0's own noise its false-stop rate reaches 0.10.
- **Equal weights of 0.5 per set.** Same power on (a) and (c) (0.70, 0.58); lower on counting (0.87 against 0.98), relative distance (0.94 against 0.96) and a size drift of 6 points (0.65 against 0.78); higher by 0.02 to 0.04 on the direction types. It halves the dilution of a dev-S1-only loss (0.38 against 0.24 on size) by halving the detection of an R0-dev-only loss (0.41 against 0.74). R0-dev is the unexposed set, so the item-proportional weights, which give it 56% to 72%, are kept.
- **Items concatenated and rooms drawn from the union of 170.** Power within 0.03 of the registered form and lower on the direction types (0.82, 0.71, 0.73); the set shares vary from draw to draw, so the weights are not fixed in advance as the card requires.
- **Leave route planning and appearance order out of H1.** Seven tests would use a level of 1 - 0.05/7 instead of 1 - 0.05/8, a difference of 0.04 standard errors, while R1 trains 9.70 route rows and 14.42 appearance rows per step.
- **A second test on dev-S1 object size or on its 78 imperial items.** It would recover the dev-S1-only case (0.51 against 0.24), but the ruling asks for one test per type, and each added test spends level. The report prints the split and a mark instead.
- **Stricter levels so that the estimated rate over four looks falls under 0.0875.** The estimate is at most 0.094, the brief fixes the nominal bound, and stricter levels would cost power on every loss.

## What might not work, and how we would notice

- **A loss confined to dev-S1 is diluted.** A 9.5-point loss on one type of dev-S1 alone is caught 0.17 to 0.24 of the time. dev-S1 asks 78 of its 150 size items in feet or inches and R0-dev none, so a unit-handling loss is of this kind; D0 m100's was (imperial -19.62, metric -0.42) and the pooled test still fired, by 1 point. We notice through the per-set 95% intervals, the size split and the mark "loss on one set only" that every report prints.
- **H2 is a mean, and R0-dev's direction gains lift it.** The three real reads have a mean of eight of +2.6 while D0 m200's dev-S1 mean of seven is -0.68. Gains on some types hide losses on others from H2; H1 and the per-type table are what catch them.
- **The estimates are conditional on D0's and H1-1's noise.** R1 trains other rows. Each report prints the realised standard errors; if R1's exceed the figures above by more than a quarter, the power figures overstate.
- **The later-look interval rests on the eight largest of 10,000 draws.** A bound within about 0.5 point of zero can change sign with the seed (H1-1 m100 above). The seed is registered so that the verdict is fixed in advance.
- **Read-to-read noise of an unchanged model is unmeasured**, and a filtered `main` read has not run in production. A filtered read that fails closed is rerun unfiltered, which costs time and not validity.
- **The R0 audit has a remainder.** 52 scene tokens and the Orchard streams are excluded from R0 by the census's construction, not by a scan of native ids. The census itself assumes that the kit07 frame map and division A3 cover the T0 and CP1 streams, and ScanNet++ has no cross-scene room key.

## Tests that would settle it

- A second read of step 544 on both sets with R1's exact read configuration (about 45 minutes on one H100, estimated from jobs 171197 and 170320): it measures the noise of an unchanged model, proves the filtered `main` read, and pairs it with `A544.jsonl` item by item.
- `test_exclusion.py` of lane b10_reserve on the scene list of R1's loader audit, covering the routing, pose and pointing rows and the 52 unresolved tokens.
- At step 200, R1's realised standard errors and between-look correlation against the figures here.

## Status

Proposed 2026-11-18T02:50Z; the registration text, the reference implementation and the evidence archive are in `events/pooled_rule/`. The rule binds only if the orchestrator registers it before the first R1 export is read (the step-100 export lands about 08:50Z). I ask for one independent review of the reference implementation and of `pr_sim.py`, since I do not review my own work. Until registration the card's dev-S1 rule binds.
