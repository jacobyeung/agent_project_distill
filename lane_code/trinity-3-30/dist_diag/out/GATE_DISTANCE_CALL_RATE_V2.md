# Gate text v2 for registration: distance call rate with held-out wordings (dist_diag, 2026-11-19; ORCH ORDER 0422Z item 5)

**Sets.** Each set is read on the claimed arm (tower arm, selector candidates_argmax, pinned serving) and reported by asked unit with its call rate and MRA. An item calls when its trace holds at least one served tower call.
- (a) The 62 dev-S1 absolute-distance items in the 8 HELD-OUT wordings (`SPLIT_V2.json`): m 18, ft 16, in 12, cm 16. No training row uses these wordings, and N's coverage v2H asserts it. Step 544 calls on 62/62; step 200 on 28/62 (m 14/18, ft 7/16, in 2/12, cm 5/16).
- (b) The 290 reworded R0-dev items (`R0_HELDOUT_EVAL_V1.json`, d98c9efb): m 73, ft 73, in 72, cm 72; one HELD-OUT wording each, on rooms no lineage trained; their 290 original twins are printed beside them. Step 544 and step 200 are not yet read on (b), so one routed read of each is owed before the first N decision.
- (c) The 80 dev-S1 items in the 10 TRAIN-DEV wordings: m 24, ft 26, in 21, cm 9. Step 544 calls on 79/80; step 200 on 52/80. Printed only, because N trains these wordings.

**Rule.**
- The claim rests on (a) and (b).
- Vehicle P at steps 400 and 600: (a), (b) when read, and (c), all printed only; P cannot take the fix.
- Vehicle N at its entry boundary plus 200: the gate passes when both (a) and (b) pass.
  - (a) passes with at least 59 of 62 calls (95%) and every unit at 90%: m at least 17/18, ft 15/16, in 11/12, cm 15/16.
  - (b) passes with at least 276 of 290 calls (95%) and every unit at 90%: m at least 66/73, ft 66/73, in 65/72, cm 65/72.
  - If (c) passes and (a) or (b) fails, calling has not transferred to unseen wording: the NEW wording family is widened (more wordings, fewer rows each) before the next boundary, and nothing about distance placement enters the claim.
  - If (c) also fails, the coverage family is rebuilt at a higher cell, starting from the unit that misses.
  - While the gate fails, distance MRA is printed split into calling and non-calling items, and no distance gain enters the claim.

**Calibration** (exact per-unit binomial; room clustering widens these figures).
| Skip rate | (a) passes | (b) passes | both pass |
|---|---|---|---|
| 1 in 150 (step 544's rate) | 0.981 | 1.000 | |
| 1% | 0.959 | 1.000 | 0.959 |
| 2% | 0.853 | 0.999 | 0.852 |
| 5% | 0.431 | 0.509 | 0.219 |

A model at step 200's rates fails both sets with probability above 0.999.

**Tool.** `dist_gate.py --coverage COVERAGE.json --split SPLIT_V2.json --rule p|n` prints (a) and (c) by unit from the dev-S1 routed read. Set (b) is scored the same way, per unit, on the routed read of the R0 item file. Its self-test gives the numbers above for steps 544 and 200 (`GATE_SELFTEST_V2.json`).

**Package change for (b)** (cont_ops18; reader in swarm_build):
- Add `R0_HELDOUT_EVAL_V1.json` to the routed package's `src/items/`, with its sha256 in the payload pins, and add one read setting with types [object_abs_distance] over its 580 items.
- Stage the R0-dev frames for those items: their scenes, `frame_indices` and `source_frame_indices` are in the file, and no `frame_paths` are filled, as the room134 R0 items have them.
- Use the scorer `official_vsi_mra`, which takes the unit from the question; the file's ground truth is already in the asked unit.
- Pair each reworded item with its twin by `twin_id`.
- A first-batch CPU check of the package should parse every question's unit and match it to the item's `unit` field.
