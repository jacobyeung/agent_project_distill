K1 training pricing is complete. Serving-reference replay passes 149/149 choices across 45 captures (100.00%; bar 95%).
The reference rebuild covers 239 training captures; three manifest GT rasters are MISSING and already excluded from the registered pricing set.
A0 uses R1 own-depth median_ratio scale, float32 exp(log(scale)), and checkpoint gravity under the serving guard.
Both convert-refused captures are accepted and marked: scannetpp/0f69aefe3d and scannetpp/2c7c10379b; direct R1 socket parity is 12/12, with 11 answers.
The replay uses stored step-544 own tensors; it does not rerun a model prefill or claim step-200 numeric equivalence.
All labels were rebuilt from GT rasters with the table producer; isolated features use its unchanged runtime producers. No S4/G1 candidate label was transferred.

| Dataset | Replay choices | Matched | Exact features |
|---|---:|---:|---:|
| arkitscenes | 39 | 39 | 39 |
| scannet | 40 | 40 | 40 |
| scannetpp | 70 | 70 | 70 |

Every primary comparison contains 1,037 train rows / 192 physical rooms; oracle and selector comparisons use the pinned 883 table rows.
Every refusal scores zero. Paired intervals use 10,000 room-bootstrap draws, seed 20261119.

| Arm | Train MRA | Rows | Refusals |
|---|---:|---:|---:|
| A0_deployed | 56.77 | 1037 | 36 |
| A1_oracle_select | 61.65 | 883 | 36 |
| A2_gt_masks | 73.97 | 1037 | 0 |
| obj_cf | 56.77 | 1037 | 36 |
| fused_cf | 78.62 | 1037 | 0 |
| A8_nonull_best1 | 53.74 | 883 | 36 |
| A7_da3_best1 | 77.81 | 1037 | 18 |
| A7_pi3x_best1 | 77.71 | 1037 | 13 |
| A9_s4_today | 52.99 | 1037 | 72 |

| Paired contrast | Gain [95% CI] |
|---|---:|
| object_cf_minus_A0 | +0.00 [+0.00, +0.00] |
| fused_cf_minus_A2 | +4.65 [+3.04, +6.44] |
| A1_minus_A0_tables | +4.10 [+2.06, +6.22] |
| A2_minus_A0 | +17.20 [+13.54, +20.89] |
| A8_nonull_minus_A0_tables | -3.82 [-5.84, -1.83] |
| size_obj_cf_minus_A0 | +0.00 [+0.00, +0.00] |
| A9_today_minus_A0 | -3.78 [-5.99, -1.72] |

| Bar | Verdict |
|---|---|
| replace_box | FAIL |
| fused_path | PASS |
| merge_safe | NA |
| selector_worth | PASS |
| selector_adopt | FAIL |
| size_screen | FAIL |
| first_seen_screen | FAIL |
| tower_challenger | SKIPPED |

| All-train merge eligibility | Precision | Added members |
|---|---:|---:|
| tau=0.25 (requires 90%) | 72.49% | 538 |
| tau=0.15 (requires 90%) | 73.32% | 581 |
| tau=0.40 (requires 90%) | 73.05% | 501 |

Frozen object variant: NONE; dependent object arms skipped. The replace_box verdict covers part 1 only; tower_frames part 2 remains required.
Object/fusion gains and merge precision use room-cross-fitted predictions. Non-null selection uses five room-held-out fits with the fixed run_iso config and seed 20261116.
The appearance bar uses OOF threshold choices to satisfy the task’s cross-fit requirement; the spec’s all-train frozen-threshold rate remains diagnostic. No source is deployed here.
Dry checks reproduce the copied-reader A0 socket, stored-label S4 predictions, corrected-label scorer targets, one-frame fusion, and tau=1.01 identity. Six math tests pass.
Dry pricing covers A0–A4 and A9; the train pass adds A7 best1 and A8 best1. A5 and frozen-object-dependent arms are skipped because no variant qualifies.
First-seen ordering is correct for 1006/1314 linker pairs (76.56%; requires 90%); no object threshold qualifies.
A6 and held-out remain deferred by order 0654Z. The archive remains local under the task’s no-network rule.
LADDER_TRAIN.txt prints all 33 object variants, ten GT fusion variants, paired contrasts, and both-answered diagnostics. SUMMARY_TRAIN.json includes truth/dataset/frame bands.
OBJECT_DIAGNOSTICS.json gives fixed GT full extents, size ratios/MRA, first-seen diagnostics, counts, and added-member precision (GT pixel plurality).
SOURCE_AUDIT.json confirms the active reader/dependencies match the R1 manifest. Unused inherited vendor/stage1.py and grounding.py differ; auxiliary vendor files lack R1 entries.
SCALE_PROVENANCE.md identifies served versus S4/G1 prices; source attribution for the design’s record-only pipeline/selector quotations remains explicitly unverified.

Commands producing the numbers (logs are in out/):
`bash run.sh prepare.py`; `bash run.sh prepare_pinned.py` — pinned train labels and rowsets.
`bash run.sh serving_reference.py` — rebuilt labels, geometry receipts, and replay.
`bash run.sh run_training_stages.py dry`; `bash run.sh confirm_dry.py` — dry pricing, parity checks and saved-gate verification.
`bash run.sh run_training_stages.py base` — four train shards and cross-fitted FREEZE.json.
`bash run.sh verify_restored.py` — direct R1 socket parity on both convert-refused captures.
`bash run.sh run_training_stages.py extras` — five selector fits, dependent arms, tables and DECISION.json.
`bash run.sh audit_sources.py`; `bash run.sh provenance_v2.py`; `bash run.sh finalize_v2.py` — source audit, provenance, verification and archive.
All Python jobs use p1cpu, nice priority, at most eight cores per job, and a virtual-memory limit below 40 GB; the four pricing shards share eight CPU cores.
No GPU, network, SSH, Git, process termination, tmux change, external write, or deletion ran. No K1 held-out or GT-geometry arm was evaluated.
Every JSON carries input SHA256 values; per-item hashes link to per-capture receipts containing the complete input chain.
Archive: out/sb_kbox4.tar; checksum: out/sb_kbox4.tar.sha256. OUTPUT_STATUS.json records the exact missing input paths and deferred outputs.
