# Review verdict: sb_callrate `callrate.py`

**ACCEPT WITH FINDINGS.** Every step-200/544 number I recomputed matches the report, and the per-item verdicts match the 22 traces I read. Fix findings 1–3 before the step-400 paste: findings 1 and 2 let partial or mismatched numbers reach results with no visible flag, and finding 3 changes how the headline usage delta reads.

Evidence is in `scratch/` beside this file. `recompute.py` and `recompute.out` hold the independent recomputation, which imports neither sb_callrate nor h1eval. `dump.py` prints traces next to the builder's verdicts. `rob/run.sh` and `rob/out_*.stdout` hold the robustness probes.

## Checks that passed
- **Traces (task 1).** I read 22 items next to the builder's per-item JSON. They were 6 camera items (devs1cam-8a50…, -b8a5…, -138c…, -ca64…, -227f…, -4c8b…) and 9 distance items (vsi590k_168046, 252280, 161834, 163095 and 042674 at step 200; 161821, 045785, 042604 and 168046 at step 544). The other 7 were room items: room_scene0155_00, 0155_02 and 0320_02 in b2, 0155_00 and 0320_02 in B5, and vsi590k_058764 and 059530 in A4. Call, capped, answer, score and usage are right on all 22 under the README definitions. Step-200 room items have no call records (A4 36/36, B5 134/134), and every step-544 room call has `served: false`, so room usage = MISSING is correct.
- **Recompute (task 2).** `python -B scratch/recompute.py` gave these results, and every one equals CALLRATE_REPORT.md:
  - Distance: A4 calls 88/150, capped 0, score 0.502667; b1/read 1 calls 149/150, capped 0, score 0.282667; delta 22.0 [13.149333, 29.609958].
  - Room134: B5 0/134 calls, capped 0, score 0.64403; b2 134/134, capped 115, score 0.065672.
  - Room MRA: dev-S1 68.89/11.11, 57.78 [39.41, 74.12]; R0-dev 62.76/4.90, 57.86 [50.82, 64.69]; all 64.40/6.57, 57.84 [50.75, 64.68].
  - Room36 against b2/read 0: calls 0/36 and 36/36, capped 0/27, delta 55.83 [39.50, 70.50].
- **Robustness (task 3, `rob/run.sh`).**
  - A copy of the return under a new root reproduces the original exactly (t1).
  - Labelling a step-200 return as `--a-step 400` exits 2 with "Requested step differs from export binding" (t1b).
  - These all exit 2: a started segment without a journal (t2c), an uncommitted tail (t2d), duplicate resume rows (t2f), a plan mismatch (t3b) and the wrong package (t3c).
  - A legitimate two-segment resume merges to identical output (t2e), and a missing room segment prints MISSING (t2b).
- **Report claims.** The tar SHA-256 c19ba0a1… matches. Both room134 manifests hash to 607ba579…. The unit-test log shows 45 OK and the reproduction log shows 102 PASS.

## Findings
1. **HIGH: `--summary` hides partial returns.** I cut distance to 100/150 and rooms to 20/36 (t2).
   - Stdout prints `object_abs_distance | 53.00/99.33 | … | 21.50 [10.12, 29.89]` and room `63.00/11.11 | 58.50`, with no PARTIAL marker and no n column. Stderr is empty; only exit code 2 and JSON `status: MISSING` reveal the gap.
   - Each row also mixes populations: B covers all 150/36 planned IDs (`callrate.py:167-173`), while A covers only the 100/20 completed ones. `summary()` (`callrate.py:139-152`) prints no n.
   - The operations lane pastes stdout. Fix: print n/expected on every row with a PARTIAL banner, or refuse in `--summary` without `--allow-partial`.
2. **HIGH: pairing different populations exits 0 with status OK.**
   - `--a A4 --b B5` (t4) prints room `66.94/64.40 | -1.94 [-4.50, 0.42]`. A covers 36 items, B covers 134, and the delta covers the 36 shared. Camera and distance show B = MISSING, yet the status is OK.
   - `analyze()` (`callrate.py:71-77`) summarizes each side over its own IDs. `paired()` lists `a_only_ids` and `b_only_ids` but never fails.
   - Fix: refuse when a type's A and B ID sets differ, and compute marginals on the shared set.
3. **HIGH (affects decisions): distance "usage" measures unit conversion, not whether the answer follows the response.**
   - Every usage=0 distance item copies the printed metre value verbatim into a cm, ft or in question: 12/12 at step 200 and 70/70 at step 544. For example, vsi590k_163095 prints `distance 2.24 m`, asks for feet and answers 2.24.
   - The usage drop from 85.88 to 50.70 (+31.76 pp) is therefore entirely a conversion failure. Counting "copied the printed number" as usage gives 100% at both steps.
   - `follows()` (`measurements.py:103-127`) accepts only the requested unit. `score_r5.py:103-123` already counted unconverted metres separately.
   - Fix: report three categories, follow_converted, copied_unconverted and other.
4. **MEDIUM: the room36 row departs from the registered pairing without saying so.**
   - `registered()` (`return_reader.py:160-165`) replaces b1/read 0 with b2/read 0 for A4's 36 rooms. A4's read 0 is the 636-item, five-type read, matching b1/read 0; b2/read 0 is a separate 134-room read.
   - Against b1/read 0 (`score_r5`, `scoresAB/scores.txt:5`), B = 0.116667, capped 29/36, delta 55.28 [38.82, 70.39]. The report gives 0.111111, 27/36, 55.83 [39.50, 70.50] and only states that camera and distance match bit for bit.
   - Fix: pick one baseline, record why, and print the other or flag the difference.
5. **MEDIUM: symlink relocation breaks valid new packages.**
   - `Inputs.path` (`return_reader.py:21-39`) rewrites every absolute link under `--original-root` (default `/scratch/jjyeung/orch_n30`) into `--input-root`, even when the target exists.
   - I placed a package beside its return under a new token directory, with `src` as an absolute link into `in/`. The run failed with `MISSING: …/in/sb_callrate/in/cont_ops/…/scorers.py` (t3). The same run with `--original-root /nonexistent_prefix` reproduced t0 exactly.
   - B5's own `src` is a link of this kind. Step-400/600 packages built the same way will be refused, or will silently read the stale copy in `in/` whenever the relative path exists there.
   - Fix: relocate only links inside the copied tree, or only when the target is missing.
6. **LOW: two different step-200 "dev-S1" MRAs share one label.** The A4 run (A-package read) gives 66.94 and the B5 run (room package) gives 68.89, on the same 36 IDs. Label room populations with their source read.
7. **LOW: answer rate counts non-numeric answers.** At b1/read 1, vsi590k_161821, 161827 and 161834 answer `not seen`, and all three count as answered.
8. **LOW: distance wording strata depend on the output.** They are trace-phrase tags (`measurements.py:82-85`). `ground_boxes_intro` appears exactly when the model calls, so its call delta is 0 by construction. Do not read these strata as question-wording effects.
9. **LOW: some future code paths are untested.**
   - Room calls count only `<ground mode="room">` or family `room` (`measurements.py:25-26`), not `<area>` or a `<ground>` without a mode. This has no effect today: room calls equal any-record calls, 134/134.
   - With `--b`, B is scored with A's package scorer (`callrate.py:160`). The `scorers.py` files are byte-identical today.
   - No real record exercises the room parser `room_v314.parse_response`.
10. **INFO: test hygiene and an inherited score override.**
    - The tests write uuid fixture directories into the source tree (`tests/test_callrate.py:225`); 68 are present now.
    - `:417` asserts an absolute path, so 1/45 fails when the tree is reached through a symlink (44/45 in my copy).
    - Score uses the package's `scores.answer` override. It differs from the MRA of the released answer on 39/150 A4 distance items. h1eval and score_r5 do the same, so this is not the builder's defect.
