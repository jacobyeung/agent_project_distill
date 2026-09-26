# Code-aws student results — 2026-09-26

The best single-model VSI-500 cell is now r1813, Qwen3.5-9B trained for one epoch on the v3 answer-only rows plus 9,795 trace-evidence rows, at 59.99 lenient / 56.97 strict.
Its lead over the 1-epoch full-pool student 148598 (+2.36) and over the 27B r1647 (+1.60) is within noise, because retraining one recipe moves VSI-500 by 2 to 5 points.
The 73.00 bar applies to a single model on VSI-500 under lenient parser v2 (user ruling, 06:10 PT); ensembles do not count, and r1813 sits 13.01 points below it.
On VSTI-450, r1813 scores 52.47 / 52.47, the highest Qwen3.5-9B row so far, which is also within noise of 148598 (+2.19).
Three trains that close the 2x2 around r1813 (97k GT pool with and without trace-evidence rows) and the corrected-ARKit coverage set are still running; their rows land in this document as they are scored.

## Headline results

The metric of record is lenient parser v2 (primary), with strict parsing secondary, on VSI-Bench answerable-500 and VSTIBench verifiable-450 (`vstibench_repr450_v2`).
Every cell uses the banked greedy protocol (4,096 new tokens, decode batch 16 for 9B, config `b43a012b...`) and scores all 500 or 450 items, with failed generations counted as zero.
Scores are percentages under each benchmark's official aggregation.

| Round | Model | Training set | Epochs | VSI-500 lenient / strict | VSTI-450 lenient / strict |
|---|---|---|---:|---:|---:|
| - | Qwen3.5-9B base | - | - | 15.66 / 15.32 | 29.97 / 29.61 |
| 148598 (Orchard) | Qwen3.5-9B | full-pool v3 answer-only (25,164) | 1 | 57.63 / 53.52 | 50.28 / 49.48 |
| r1805 | Qwen3.5-9B | coverage v1 without ARKit + s25k evidence (49,669) | 1 | 57.78 / 56.12 | 50.67 / 50.67 |
| **r1813** | Qwen3.5-9B | **v3 answer-only (25,135) + s25k trace-evidence rows (9,795)** | 1 | **59.99 / 56.97** | **52.47 / 52.47** |
| r1647 | Qwen3.6-27B | full-pool v3 answer-only | 1 | 58.39 / 58.31 | 50.67 / 50.67 |

The 9B base, 148598, r1805 and r1647 rows are banked in [RESULTS_CODEAWS_20260925.md](RESULTS_CODEAWS_20260925.md); r1813 is new today.
Noise: trainer73's yardstick shows that retraining the 1k recipe moves VSI-500 by 2 to 5 points, so any single-run difference under about 3 points is flagged as within noise.

## r1813 per question type

r1813 isolates what the trace-evidence rows add to the v3 answer-only rows: its training set is the v3 train side (minus 29 count-audit exclusions) plus the s25k evidence rows, and its heldout side is v3's 4,235 rows.
The reference 148598 trained on the full v3 set for one epoch on Orchard, so cluster differs along with the added rows.

### VSI-Bench answerable-500 (n = 50 per type)

| type (lenient / strict) | base | 148598 | r1813 | r1813 - 148598 (len) | r1813 - base (len) |
|---|---:|---:|---:|---:|---:|
| obj_appearance_order | 30.0 / 28.0 | 78.0 / 78.0 | 78.0 / 78.0 | +0.0 | +48.0 |
| object_abs_distance | 9.6 / 9.6 | 40.2 / 40.2 | 46.0 / 46.0 | +5.8 | +36.4 |
| object_counting | 10.2 / 10.2 | 49.2 / 49.0 | 54.2 / 54.0 | +5.0 | +44.0 |
| object_rel_direction_easy | 22.0 / 20.0 | 76.0 / 76.0 | 78.0 / 78.0 | +2.0 | +56.0 |
| object_rel_direction_hard | 4.0 / 4.0 | 38.0 / 2.0 | 56.0 / 38.0 | +18.0 | +52.0 |
| object_rel_direction_medium | 6.0 / 6.0 | 62.0 / 10.0 | 62.0 / 8.0 | +0.0 | +56.0 |
| object_rel_distance | 36.0 / 36.0 | 62.0 / 60.0 | 64.0 / 64.0 | +2.0 | +28.0 |
| object_size_estimation | 12.6 / 12.6 | 54.8 / 53.4 | 58.8 / 58.8 | +4.0 | +46.2 |
| room_size_estimation | 0.2 / 0.2 | 66.2 / 66.2 | 65.6 / 65.6 | -0.6 | +65.4 |
| route_planning | 16.0 / 16.0 | 52.0 / 52.0 | 48.0 / 48.0 | -4.0 | +32.0 |
| **official** | **15.66 / 15.32** | **57.63 / 53.52** | **59.99 / 56.97** | **+2.36** | **+44.33** |

The evidence rows target distance, size, counting and direction, and those are the types that rise: rel_direction hard gains 18 points, abs_distance 5.8, counting 5.0 and size 4.0.
The per-type gains of 2 to 6 points each sit inside the per-type noise at n = 50; only the rel_direction hard gain clearly exceeds it.
Route planning falls 4 points, and rel_direction medium still answers with the option text instead of the letter (strict 8.0, lenient 62.0).
Strict parse failures fall to 61 and lenient recovers all of them; 6 generations run on after the end-of-turn token and 1 hits the 4,096-token cap.

### VSTIBench verifiable-450 (n = 50 per type)

| type (lenient / strict) | base | 148598 | r1813 | r1813 - 148598 (len) | r1813 - base (len) |
|---|---:|---:|---:|---:|---:|
| camera_displacement | 6.2 / 6.2 | 27.6 / 27.6 | 27.2 / 27.2 | -0.4 | +21.0 |
| camera_movement_direction | 16.0 / 16.0 | 30.0 / 30.0 | 30.0 / 30.0 | +0.0 | +14.0 |
| camera_obj_abs_dist | 23.0 / 21.2 | 51.8 / 51.8 | 49.8 / 49.8 | -2.0 | +26.8 |
| camera_obj_rel_dist_v1 | 28.0 / 28.0 | 68.0 / 64.0 | 76.0 / 76.0 | +8.0 | +48.0 |
| camera_obj_rel_dist_v2 | 40.0 / 40.0 | 68.0 / 66.0 | 76.0 / 76.0 | +8.0 | +36.0 |
| camera_obj_rel_dist_v3 | 56.0 / 56.0 | 70.0 / 66.0 | 76.0 / 76.0 | +6.0 | +20.0 |
| obj_obj_relative_pos_lr | 60.0 / 60.0 | 78.0 / 78.0 | 90.0 / 90.0 | +12.0 | +30.0 |
| obj_obj_relative_pos_nf | 54.0 / 54.0 | 58.0 / 56.0 | 66.0 / 66.0 | +8.0 | +12.0 |
| obj_obj_relative_pos_ud | 76.0 / 76.0 | 84.0 / 84.0 | 82.0 / 82.0 | -2.0 | +6.0 |
| **official** | **29.97 / 29.61** | **50.28 / 49.48** | **52.47 / 52.47** | **+2.19** | **+22.49** |

VSTI-450 uses the official 5-subtask metric, in which camera_obj_rel_dist v1/v2/v3 collapse into one subtask.
The object-relation types gain most (left/right +12, near/far +8, camera-object relative distance +6 to +8); camera motion does not move.
r1813 emits bare answers on VSTI: strict equals lenient, with no parse failures, run-on or cap hits.

## Provenance

| Item | Value |
|---|---|
| Round and run | r1813, `q9_v3s25k_traceev_caws_w8_e1_r1813` |
| Training set | `q9_v5_traceev_s25k_20260925_trainer` (trace-evidence lane): candidate_index sha256 `4c8d4544...`, 39,165 rows = 25,135 v3 train + 9,795 evidence train + 4,235 v3 heldout; review PASS, builder verify PASS, code-aws transfer gate `.done` |
| Recipe | trainer `abddf4a` (orchard_trainer_caws_433d8a1), deployment `deployment_caws_w8_e1` (world 8, micro-batch 4, effective batch 32, LR 1e-4, LoRA r32 / alpha 64, 1 epoch = 1,092 steps), live environment |
| Jobs | prepare 7438407 + 40-way shard 7438494 (merged), train 7438893 (aml_high, pool0-1043, 06:59-10:37 PT, about 11.4 s per step wall), VSI-500 eval 7441007, VSTI-450 eval 7441116 (both aml_low) |
| Adapter | publication `adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW`, weights sha256 `c10c34aa...`, training receipt `418220d2...` |
| Eval integrity | both cells `TERMINAL_CENSUS_COMPLETE` (500/500, 450/450), all `ok`, 0 media errors; tree hash over run/ score/ evalq/ `25d2deb8...` (2,066 files) and `df3fb538...` (1,866 files), fetched by compute-node pack jobs 7441142 and 7441442 |
| Scoring | `orchard_lenient_rescore.py` with lenient parser v2 from the SENS harness at 126a81b; the strict replay reproduced each cell's receipt; commands in the code-aws lane `returns/_scores_9b_{vsi,vsti}_r1813/COMMAND.txt`, narrative in `returns/SCORES.md` passes 13a and 13b |

## Runs in flight (distillation holds 4 of the 8 code-aws pool0 nodes under the 64-GPU cap)

| Round | Model and set | Job | Environment | State at 11:39 PT | Projected train end |
|---|---|---|---|---|---|
| r1801 | 9B, 97k GT answer-only pool (91,593 rows), 1 epoch, resumed from step_450 | 7438379 | live | 1,779 / 2,730 steps, about 14 s per step wall | about 15:20 PT |
| r1807 | 9B, coverage v2 with corrected ARKit + s25k evidence (61,035 rows), 1 epoch | 7438397 | live | 1,445 / 1,775 steps, about 13.7 s per step wall | about 12:55 PT |
| r1812 | 9B, G97E: 97k GT pool + s25k evidence (101,388 rows), 1 epoch | 7440783 | fast kernels (venv_fk_20260926, guard v9) | 289 / 3,037 steps since 11:05 PT, about 7.1 s per step wall (5.8 logged) | about 17:05 PT |

With r1813, r1801 and r1812 form a 2x2 over data scale (25k v3 versus 97k GT pool) and trace-evidence rows (with or without).
Held with intact state and a resume command in the code-aws `ROUNDS.md`: r1806 (27B, r1805 set, step_25), r1808 (27B, r1807 set), r1814 (27B on r1813's set, prepared), the r1815 RL adapter eval, r1811 and r1646.
The full 5,130-question VSI-Bench runs only for the final headline candidate (user ruling relayed 11:15 PT); its media is now staged on code-aws (`scripts/evalq/full5130_media.json`).
Since about 06:00 PT the code-aws login VM cannot read Lustre OST00e0, so every submit and every cell copy runs through a short CPU job on a compute node.
