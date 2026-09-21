# Distillation lane handoff (REQ-20260917-232), written 2026-09-21 19:45Z

## Command

This session runs on trinity-3-8 and owns the distillation lane only. The trinity-3-13 session owns
every other lane, including the sam3 daemons and the experiment request queue's other rows; this
session never touches that state and never runs `git status` in `/home/jjyeung/agent_project`.
Shorthand used below: P = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`;
R = `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`;
S = `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918`;
L = `/home/jjyeung/agent_project/agent/scratch/devin_lanes`.

This checkpoint supersedes `DISTILLATION_HANDOFF_20260921_0750Z.md` for everything that changed since
07:50Z; that document still holds the v2.4.x and v2.5 lineage detail, the collector recovery and the
standing constraints. The session keeps command. A successor starts at section 9 (next steps) and
section 10 (watchers to re-arm). No user ruling arrived between 07:50Z and 19:45Z; every ruling in
section 8 is the orchestrator's and provisional.

## 1. Results (fixed protocol unless a row says otherwise)

Fixed protocol: harness `58794b8`, instructed prompt, 4,096-token generation budget, strict parser
as the metric of record with a lenient rescore as sensitivity, RGB-only, tool-free, greedy, 32
frames. "Capped" counts generations that reached the budget without an answer. Every cell scored all
of its items (VSIBench answerable-500, VSTIBench 450).

### Headline: arm C's recipe (v1c compact targets, all families) is the only one above base in every cell; every corrected-format student is below base except Qwen v2.5 on VSIBench; scaling arm C's recipe from 3,052 to 5,055 rows gave no clear gain; OneThinker on VSTIBench is the weak cell; most of Qwen's fixed-protocol gain is termination and answer format, with a real VSIBench margin of about 3.5 to 12 points

### 1.1 OneThinker-8B, VSIBench

| cell | training set | steps | strict | lenient | capped |
|---|---|---:|---:|---:|---:|
| base | none | 0 | 31.47 | 39.19 | 0 (93 strict parse failures, 9 lenient) |
| arm C | v1c, all families, 3,052 rows | 288 | 42.35 | 42.35 | 4 |
| RUN B (matched control) | v1c, 760 rows | 72 | 33.71 | 33.71 | 67 |
| RUN A | v2.4.2, same 760 questions | 72 | 25.52 | 25.52 | 87 |
| RUN A3 | v2.4.3 reviewed, 570 rows | 54 | 22.18 | 22.18 | 89 |
| v2.5 | v2.5 reviewed, 1,155 rows | 111 | 27.83 | 27.83 | 46 |
| v1c-XL | v1c, seven families, 5,055 rows | 474 | **44.81** | 44.81 | 0 (0 parse failures) |
| RUN B3 (control for A3) | v1c, 570 rows | 54 | pending | | 424 of 500 generated at 19:01Z |

| question type | base (lenient) | arm C | RUN B | RUN A | RUN A3 | v2.5 | v1c-XL |
|---|---:|---:|---:|---:|---:|---:|---:|
| appearance order | 52.0 (52.0) | 56.0 | 48.0 | 46.0 | 46.0 | 46.0 | 68.0 |
| absolute distance | 12.8 (32.8) | 36.8 | 29.8 | 17.0 | 17.4 | 22.4 | 31.6 |
| counting | 21.6 (29.6) | 41.6 | 29.6 | 16.0 | 14.8 | 31.4 | 48.8 |
| relative direction, easy | 36.0 (36.0) | 58.0 | 56.0 | 62.0 | 38.0 | 54.0 | 64.0 |
| relative direction, hard | 22.0 (22.0) | 16.0 | 22.0 | 34.0 | 26.0 | 26.0 | 20.0 |
| relative direction, medium | 36.0 (36.0) | 40.0 | 32.0 | 28.0 | 40.0 | 24.0 | 38.0 |
| relative distance | 42.0 (42.0) | 48.0 | 40.0 | 30.0 | 26.0 | 32.0 | 42.0 |
| object size | 45.0 (48.0) | 52.0 | 31.8 | 21.4 | 10.2 | 16.2 | 45.8 |
| room size | 21.0 (51.8) | 38.4 | 27.8 | 4.4 | 8.4 | 10.0 | 59.6 |
| route planning | 26.0 (26.0) | 28.0 | 26.0 | 28.0 | 20.0 | 30.0 | 22.0 |

### 1.2 OneThinker-8B, VSTIBench

| cell | strict | lenient | capped | parse failures |
|---|---:|---:|---:|---:|
| base | 40.16 | 45.40 | 1 | 55 strict, 14 lenient |
| arm C | 43.59 | 43.59 | 1 | 1 |
| v2.5 | 29.41 | 29.41 | 28 | 30 |
| v1c-XL | 37.48 | 37.48 | 0 | 29, all in camera-object absolute distance |
| RUN A3 | pending | | | 121 of 450 generated at 19:01Z |

| question type | base | arm C | v2.5 | v1c-XL |
|---|---:|---:|---:|---:|
| camera displacement | 20.8 | 15.2 | 4.6 | 16.4 |
| camera movement direction | 30.0 | 40.0 | 24.0 | 38.0 |
| camera-object absolute distance | 10.0 | 45.4 | 23.8 | 11.0 |
| camera-object relative distance v1 | 52.0 | 62.0 | 32.0 | 56.0 |
| camera-object relative distance v2 | 72.0 | 62.0 | 44.0 | 72.0 |
| camera-object relative distance v3 | 70.0 | 66.0 | 64.0 | 72.0 |
| object-object position, left/right | 60.0 | 38.0 | 48.0 | 52.0 |
| object-object position, near/far | 74.0 | 56.0 | 52.0 | 48.0 |
| object-object position, up/down | 92.0 | 68.0 | 44.0 | 66.0 |

### 1.3 Qwen3.5-9B, VSTIBench (lenient equals strict in every Qwen cell)

| cell | score | capped | unparseable | median generated tokens |
|---|---:|---:|---:|---:|
| fixed-protocol base | 28.59 | 203 | 205 | 3,084 |
| direct-answer base control (sensitivity row: one sentence added to the prompt, thinking on) | 31.47 | 187 | 187 | 2,622 |
| thinking-off base control (sensitivity row: harness `4066507`) | 35.80 | 0 | 107 | 44 |
| v2.5 | 22.73 | 123 | 128 | not recorded here |
| arm C | **46.56** | 0 | 0 | 407 |
| v1c-XL | 43.63 | 0 | 0 | 244 |

| question type | base | direct-answer | thinking-off | v2.5 | arm C | v1c-XL |
|---|---:|---:|---:|---:|---:|---:|
| camera displacement | 3.6 | 4.4 | 14.2 | 3.6 | 28.2 | 18.0 |
| camera movement direction | 18.0 | 22.0 | 34.0 | 10.0 | 36.0 | 20.0 |
| camera-object absolute distance | 20.0 | 25.6 | 24.8 | 17.4 | 32.6 | 46.8 |
| camera-object relative distance v1 | 26.0 | 28.0 | 50.0 | 36.0 | 40.0 | 52.0 |
| camera-object relative distance v2 | 34.0 | 46.0 | 62.0 | 44.0 | 68.0 | 60.0 |
| camera-object relative distance v3 | 52.0 | 48.0 | 62.0 | 62.0 | 68.0 | 70.0 |
| object-object position, left/right | 50.0 | 54.0 | 40.0 | 38.0 | 86.0 | see table |
| object-object position, near/far | 66.0 | 62.0 | 26.0 | 28.0 | 56.0 | see table |
| object-object position, up/down | 76.0 | 78.0 | 78.0 | 40.0 | 90.0 | 78.0 |

### 1.4 Qwen3.5-9B, VSIBench

| cell | score | capped | unparseable | median generated tokens |
|---|---:|---:|---:|---:|
| fixed-protocol base | 15.47 | 373 | 378 | 4,096 |
| thinking-off base control (sensitivity row) | 29.09 | 4 | 160 | 102 |
| direct-answer base control | not scored: cell interrupted at the 18:05Z card release, resumable | | | |
| v2.5 | 38.13 (lenient 38.28) | 32 | 39 | not recorded here |
| arm C | **49.25** | 0 | 0 | 375 |
| v1c-XL | 47.89 | 1 | 1 | 188 |

| question type | base | v2.5 | arm C | v1c-XL |
|---|---:|---:|---:|---:|
| appearance order | 26.0 | 58.0 | 70.0 | see table |
| absolute distance | 12.6 | 23.4 | 33.6 | see table |
| counting | 7.4 | 53.0 | 56.0 | 47.0 |
| relative direction, easy | 28.0 | 44.0 | 54.0 | see table |
| relative direction, hard | 0.0 | 20.0 | 28.0 | 36.0 |
| relative direction, medium | 8.0 | 46.0 | 44.0 | see table |
| relative distance | 34.0 | 48.0 | 52.0 | 44.0 |
| object size | 17.6 | 40.6 | 47.6 | see table |
| room size | 0.2 | 23.4 | 68.8 | see table |
| route planning | 14.0 | 22.0 | 24.0 | 34.0 |

"See table" marks cells this document's author did not hold; the tables in section 3 carry them.

### 1.5 Paired diagnostics (aggregates; `P/claude_qwen_paired_diag_20260921T1230Z/out/`)

| comparison | subset | n | base or control | student |
|---|---|---:|---:|---:|
| Qwen arm C vs fixed-protocol base, VSTIBench | both answered | 245 | 70.5 | 63.7 |
| same | base gave no answer | 205 | 0 by construction | 47.0 |
| Qwen arm C vs fixed-protocol base, VSIBench | both answered | 122 | 60.6 | 57.8 |
| same | base gave no answer | 378 | 0 by construction | 44.6 |
| Qwen v2.5 vs fixed-protocol base, VSTIBench | both answered | 161 | 72.2 | 51.1 |
| Qwen arm C vs thinking-off control, VSTIBench | both parse | 343 | 57.0 | 54.2 |
| same | control unparseable | 107 | 0 by construction | 62.1 |
| Qwen arm C vs thinking-off control, VSIBench | both parse | 340 | 42.3 | 45.8 |
| same | control unparseable | 160 | 0 by construction | 52.1 |
| OneThinker v1c-XL vs lenient base, VSIBench | both parse | 491 | 38.3 | 44.1 |
| OneThinker v1c-XL vs lenient base, VSTIBench | both parse | 407 | 59.6 | 51.3 |

What-if bounds, which are NOT scores: scoring every unparseable thinking-off output that holds
exactly one extractable answer lifts that control from 35.80 to 46.2 on VSTIBench (level with arm C)
and from 29.09 to 37.6 on VSIBench (arm C still 11.7 ahead). The control's unparseable outputs are
mostly prose that never states the option letter (77 VSTIBench items, 35 VSIBench items); 28 and 110
items hold one extractable answer. For OneThinker v1c-XL on VSTIBench, 27 of the 29 parse failures
state one clear number followed by a stray trailing letter; scoring them lifts camera-object
absolute distance from 11.0 to 41.2 and the category macro from 47.93 to 51.29, still under the
lenient base macro of 56.33. Predicted-to-reference ratios (base 0.67, arm C 0.91, XL 1.37; 71 to 84
percent within a factor of two) rule out a metre-centimetre scale error.

### 1.6 The honest reading

Under the fixed protocol, the arm C recipe beats the base for both students on both benchmarks
(OneThinker VSTIBench only under the strict parser). Three controls qualify that claim. First, the
Qwen base fails to terminate on 45 percent of VSTIBench items and 75 percent of VSIBench items; on
the items both models answer, arm C trails the base slightly (selection flatters the base, which
finishes the items it finds easy). Second, a Qwen base that terminates (thinking off) still trails
arm C by 10.8 and 20.2 points as scored, but most of the VSTIBench gap is the control's answer
format; on VSIBench a real margin of about 3.5 (paired) to 11.7 (what-if bound) points survives.
Third, OneThinker's VSIBench gain survives every control we have: v1c-XL leads the leniently parsed
base by 5.6 points overall and 5.8 on the paired subset.

Scaling from 3,052 to 5,055 rows moved OneThinker VSIBench +2.5 and VSTIBench -6.1 (mostly the
stray-letter defect), Qwen VSIBench -1.4 and VSTIBench -2.9. With 450 to 500 items per cell the
standard error is about 2.2 points, so no difference except OneThinker VSTIBench is clear.
OneThinker on VSTIBench is the weak cell of the paper claim: below the lenient base under every
recipe, with the loss concentrated in the object-object position families, which the teacher pool
(VSIBench-style questions only) never covers. The corrected-format lineage (v2.4.2, v2.4.3, v2.5)
lost everywhere except Qwen VSIBench, for three measured reasons: non-termination from frame-list
enumeration loops, invented coordinates on question families absent from training, and counts tied
to a generated roster; v2.5's bounded enumeration cut the caps but could not fix coverage.

## 2. Targets since 07:50Z

| item | state | where |
|---|---|---|
| v2.6 (derived-measurement class for distance and size) | built 09:30Z, commit `7e084c9`, 1,391 admitted (only 13 more than v2.5: 10 absolute, 3 relative distance; zero size, room, route); technical gates pass; self-verdict FAIL on two heartbeat gaps; PARKED, no review, no retrain | `L/devin_compact_v26_clone/out/REPORT.md`; set `S/diagnostic_set_compact_v2_6_20260921_full`, MEMBERSHIP `ac9a3754…` |
| error analysis of the corrected format | 69 percent of RUN A's deficit to RUN B is non-termination, 31 percent wrong values; reusable `analyze_cell.py` with partial-cell, compare and pattern modes | `P/claude_v242_error_analysis_20260921T0855Z/out/` (ERROR_ANALYSIS_V242.md, BREAKDOWN.md, PARTIAL_V25_READ.md) |
| v1c-XL (arm C's exact converter over the 8,481-question strict snapshot) | rendered 10:52Z; converter pin `2ad2d70` (blob `99e3ee10…`; NOT `f5ce7a0`, which landed the rejected v1 selection rule); 8,470 staged by hard link, 11 ingestion refusals; 7,622 admitted; regression PASS (3,431 targets shared with arm C byte-identical, 3,852 dispositions agree); answer, marker and token gates 7,622 of 7,622 | lane `L/devin_compact_v1cxl_clone` (brief `inputs/BRIEF_v2_abspaths.md`); set `S/diagnostic_set_compact_v1c_xl_20260921`, MEMBERSHIP `7403e79b…`; staged sources `S/compact_v1c_xl_sources_20260921`; source index `S/compact_v2_5_strict_sources_20260921_round2/candidate_index.jsonl`; brief lane `P/claude_v1c_xl_brief_20260921T0915Z/` |

v1c-XL admitted rows per family: relative direction medium 4,165; relative distance 2,018;
appearance order 597; absolute distance 436; counting 363; object size 43; room size 0 (38
candidates, no selected observations); no route planning and no easy or hard direction labels in the
pool. Released manifests (Devin lane `out/`): `TRAIN_DEFAULT40.jsonl` 5,055 rows, 474 steps, sha256
`afe9a07714e8fcabf51b9594b4e7c1a321f4cec81b6ab611e286862e2e7a1c99` (a 40-percent fixed-point cap
removed 1,842 medium-direction rows and nothing else); `TRAIN_NATURAL.jsonl` 6,897 rows, 648 steps,
sha256 `51c8a12fc569d92586baebab2c3d69339672f21af01028a537601f6b68521bf5` (never trained);
`HELDOUT.jsonl` 725 rows, sha256 `b8d6b89907ebc554b0df15d319e54e84093979deecea60a2f9fe2b0e91b5edc1`.
Trainer `b084aaf` prepared both selections with `--inherit-split` on arm C's published run split
(`4dd7467f…`); split digests `30801d1739b3…` (default) and `bd7e8743853f…` (natural).

The build's one failed gate was the hash-only holdout checker at `058368c`, which re-hashes
published scenes and so disagrees with 12 published scene sides. The orchestrator ruled that the
inheritance ruling of 2026-09-20 governs; an independent checker
(`P/claude_v1cxl_students_launch_20260921T1115Z/jobA/inheritance_gate.py`, output
`INHERITANCE_GATE.json` in the Devin lane) passed all four conditions: 75 published scenes keep
their sides, 71 new scenes match the documented hash, no scene or question on both sides, no
training row from any published held-out scene. The ruling and the release receipt sit in the Devin
lane's `out/` as `ORCHESTRATOR_RULING_HOLDOUT_20260921T1110Z.md` and
`ORCHESTRATOR_RELEASE_20260921T1120Z.md`.

## 3. Student adapters (all LoRA r=32, alpha 64, text and vision attention and MLP plus mergers, lr 1e-4 cosine, effective batch 32, 3 epochs; equal to arm C field for field)

| adapter | publish path under `/data3/jjyeung/` | steps | harness acceptance | tables |
|---|---|---:|---|---|
| OneThinker RUN B (v1c control, 760) | `ddp_onethinker_v1cm242_onethinker_20260921T0145Z` | 72 | accepted | `P/claude_onethinker_v242_eval_20260921T0300Z/out/` |
| OneThinker RUN A (v2.4.2) | `ddp_onethinker_v242_onethinker_20260921T0145Z` | 72 | accepted | same lane, `out_run_a/` (VSTIBench cancelled: no matched control) |
| OneThinker RUN A3 (v2.4.3) | `ddp_onethinker_v243_onethinker_20260921T0330Z` | 54 | accepted | `out_run_a3/` |
| OneThinker RUN B3 (control for A3) | `ddp_onethinker_v1cm243_onethinker_20260921T0330Z` | 54 | accepted, weights `3fb1f26a…49abe1` | `out_run_b3/` |
| OneThinker v2.5 | `ddp_onethinker_v25_onethinker_20260921T0530Z` | 111 | accepted, 736 tensors, weights `78db4a4c…` | `P/claude_onethinker_v25_eval_20260921T0820Z/out_vsi/`, `out_vsti/` |
| OneThinker v1c-XL | `ddp_onethinker_v1cxl_onethinker_20260921T1115Z_t113` | 474 | accepted as published, 736 tensors, weights `4d730ab5…` | `P/claude_onethinker_v1cxl_eval_20260921T1705Z/out_vsi/`, `out_vsti/` |
| Qwen arm A (format A, run r6) | `ddp_qwen35_a_qwen_20260920T0400Z_r6`; republish `…_r6_republish_20260921T041852Z` | 246 | accepted after the cadence republish | `P/claude_qwen_r6_eval_20260921T0400Z/out/` (still evaluating) |
| Qwen arm C | `ddp_qwen35_c_qwen_20260920T0800Z_r1`; republish `…_r1_republish_20260921T114101Z` | 288 | original refused (trainer `ad96f47` wrote `checkpoint_every_steps` into `training`); republish accepted 11:41Z; original byte-unchanged (314 files, nine hashes) | `P/claude_qwen_armc_eval_20260921T1020Z/out/` (REPUBLISH_ARMC.md, HANDOFF_QARMC.md) |
| Qwen v2.5 | `ddp_qwen35_v25_qwen_20260921T0530Z` | 111 | accepted as published, 716 tensors, weights `dc65d733…` | `P/claude_qwen_v25_eval_20260921T0735Z/out/` |
| Qwen v1c-XL | `ddp_qwen35_v1cxl_qwen_20260921T1115Z` | 474 | accepted as published 18:47Z, 716 tensors, protocol `b21886f6…` | `P/claude_qwen_v1cxl_eval_20260921T1705Z/out/` |

OneThinker arm C's publish path is recorded in the 2026-09-20 handoffs, not here. Staging, READY
notes, launchers and release records for the XL students:
`P/claude_v1cxl_students_launch_20260921T1115Z/{onethinker,qwen}/out/`. The two OneThinker host
variants (trinity-0-23, trinity-1-13) share one lease request, so only one could launch; the
trinity-1-13 variant ran (42.6 s per step on A6000). Qwen XL ran at 47 to 50 s per step on six Ada
cards. Lesson for the next launcher copy: the stall alarm exits after three checks without
`torchrun`, so start it after `torchrun` appears.

## 4. Harness control branch

Branch `eval-base-control-20260921`, single commit `40665074528cc05c087587f1c5c82150016e1c2a` on the
frozen harness `58794b87…`, lives in the clone `L/devin_harness_basectl_clone/work/harness_clone`
(the harness itself lives in `S/trainer_repo`, not in this repository). It adds `--thinking
{pinned,off}`, `--max-new-tokens` and `--items-file` to `generate` and `cpu-check`; each enters the
protocol identity only when non-default; controls are refused for the distilled variant without
`--allow-distilled-controls`; `score.py` is untouched; 137 tests pass. The builder's literal
"byte-identical core" lock is impossible because `core['runtime']` pins the hashes of the edited
source files; the adopted ruling is that the lock covers the protocol hash, the authority digest and
every non-runtime core field, all of which are equal. Consequence: cells generated at `4066507`
cannot resume or pair, through the harness, with cells from `58794b8`; tables juxtapose score files.

Independent review (Codex Astra, `P/claude_harness_basectl_review/out/verdict.json`): q1 default
identity PASS, q2 authorities PASS, q4 guards PASS, q5 scoring untouched PASS, q3 FAIL on one
finding: OneThinker-8B's pinned chat template has no thinking switch, so `--thinking off` renders a
byte-identical prompt yet mints a second authority. Ruling: the thinking-off control is authorised
for Qwen3.5-9B base cells only; `--thinking off` stays forbidden for OneThinker until a fail-closed
fix (refuse the option when the rendered prompt equals the pinned one) lands and its delta is
reviewed. The reviewer also found subset scoring unimplemented (`score.py` refuses a run whose
membership differs from the cohort), so the larger-budget control on a pre-registered subset is
parked; a full 16,384-token base rerun projects to 44 to 66 GPU-hours on VSTIBench alone. Control
cells: `qwen35_base_nothink` (frozen checkout `eval_base_control_40665074…`, a detached worktree of
`S/trainer_repo`) and `qwen35_base_directanswer` (harness `58794b8`, instruction string sha256
`815f752c…`), lane `P/claude_qwen_base_control_20260921T1305Z/out/` (HANDOFF_BASECTL.md,
THINKOFF_PROMPT_PROOF.json, CODE_CHANGE_NEEDED.md). The fixed-protocol base score files are
hash-identical before and after.

## 5. Collector and census

The collector holds the user's 4M-token pin: target 44 workers, `cooldown` latched, counter 22,357
finalized at 18:48Z, about 400 to 415 per hour all day, zero rate-limit lines. Processes on
trinity-3-8: supervisor 195531, controller 233991, package guard 1041011. The guard renames stray
untracked files out of `collector/` and EXITS whenever the repository HEAD changes, so every commit
or fast-forward on `main` (including the one that lands this document) must be followed at once by
a guard restart with the original arguments and by putting the new pid into the hold watcher (memory
note `collector-package-guard`). The other session marked REQ-234 DONE at about 09:20Z, so the
shared Gemini key may have headroom above the pin; raising the worker count is a user decision, asked
three times today and unanswered.

The live counter is not the accepted count (last census, 2026-09-20 20:19Z: 8,481 strict and 9,349
tolerance-tier accepted of 11,101 attempted; accepted ran at about 0.6 of the counter). A fresh
census launched at 11:53Z (pid 1595879 on trinity-3-8, `collector/census.py` under `ionice -c3 nice
-n 19`, babysitter pid 1600988 that pauses it if the collector stalls; lane
`P/claude_accepted_census_20260921T1155Z/out/`, BABYSIT.md). At 19:02Z it was still reading: 748 GB
read in 7 hours, never paused, no progress line until it ends; its cost grows faster than linearly
with the pool, so the next count should be incremental. When the process exits, a new timestamp
directory appears under `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313/`;
the tolerance-tier tables and CENSUS.md still have to be written from the snapshot JSON (the
previous lane's commands: `P/claude_accepted_census_20260920T1810Z/out/COMMAND.txt`).

## 6. Running and paused cells (19:01Z readings unless stated)

| cell | host and cards | state | resume or release recipe |
|---|---|---|---|
| RUN B3 VSIBench (resumed 18:00Z) | trinity-1-13 cards 2,3,4 | 424 of 500 at 48 items per hour; table `out_run_b3/RESULTS_VSIBENCH_V1CM243.md` about 20:30Z (estimated 19:01Z) | record dir `P/claude_matched_pair_resume_20260921T1800Z/`; first release record `P/claude_v1cxl_students_launch_20260921T1115Z/onethinker/out/launch/RELEASED_B3.md` |
| RUN A3 VSTIBench | trinity-1-13 cards 5,6,7 | 121 of 450 at 122 per hour; about 21:45Z (estimated 19:01Z) | `out_run_a3/LAUNCH_RECEIPT_EVAL_A3.md`; stop = SIGTERM workers, leave supervisors to record and fail the lease |
| RUN B3 VSTIBench | trinity-1-13 cards 2,3,4 after B3's VSIBench | not started; the matched-pair lane launches it | same lane |
| Qwen arm A (r6) VSTIBench then VSIBench | trinity-0-23 card 7 | slow, lowest priority; 152 of 450 at 10:24Z is the last reading this author holds; process alive at 19:38Z | `P/claude_qwen_r6_eval_20260921T0400Z/out/` |
| Qwen direct-answer control, VSIBench | none | interrupted 18:11Z when its orphaned shards exited; VSTIBench finished (31.47) | HANDOFF_BASECTL.md: clear the card's release marker by renaming, arm a wait-first loop; shards resume by dead-owner takeover |

Idle at 19:40Z and verified clean with `nvidia-smi`: trinity-0-13 cards 0 to 5 and trinity-0-23
cards 0,1,3,4,5,6. All XL evaluation processes have exited.

## 7. GPU facts and the day's operating lessons

trinity-0-23 GPU 2 is faulty (two Xid 109 faults; another user's process sits on it); every launcher
for that node refuses index 2. trinity-0-13 has seven RTX 6000 Ada cards, 0 to 6; card 6 runs the
other experimenter's sam3 daemon (pid 48578) and is never touched. trinity-1-13 has A6000 cards;
0 and 1 belong to other users. `/data3` is an NFS export readable from every node (a lane wrongly
reported it node-local). Everything the evaluation harness reads is on shared NFS. Node `python3` is
3.6; use `/data2/jjyeung/envs/planner/bin/python`. Measured rates: short-answer students evaluate at
about 175 (OneThinker) to 250 (Qwen XL) items per GPU-hour on Ada and about 35 to 40 on A6000; the
Qwen base and looping students run at 16 to 35; early-minute rates read about three times too fast.

Lessons, each of which cost time today. A long-lived watcher whose command line names a compact
target lane's path counts as a competing reader at that builder's render gate; three of the
orchestrator's wake loops blocked the v2.6 render for 2.3 hours. Watch the builder's pid instead, and
never obfuscate a path to slip past the scan: the permission classifier refuses that as evasion, and
it is right. A zero-byte `.git/index.lock` left by a killed `git status` blocks merges but not
status; rename it aside only when no git process runs. A Devin brief must give the lane's absolute
path, OUT directory and heartbeat file, with the first heartbeat inside 60 seconds; a brief with a
`<lane>` placeholder cost one full attempt. NFS readdir caching made a healthy staging loop look
stalled three times: count with `ls -U` and cross-check directory mtimes; `/proc/<pid>/io` counts only
reads and writes, so a `link()` loop moves none of them; hard-link latency on `/data2` was 0.1 to
0.4 ms in every nice and ionice class, so scheduling class explained nothing. The stock
`card_loop.sh` claims a shard BEFORE it waits for its card: arm loops through a wait-first wrapper
(`P/claude_qwen_v25_eval_20260921T0735Z/out/pool_ext_20260921T0935Z/arm_card.sh`), and match `pgrep`
on the lane's absolute path, because identically named loop scripts from two lanes on one host
collide. Stopping a vnice wrapper or a loop can orphan its CUDA child: a release is complete only
when `nvidia-smi --query-compute-apps` shows nothing of ours on the card. Resuming a cell on another
host needs dead-owner handling for the old host (with a heartbeat-staleness guard) and a
`coord.py fail` for leases the killed supervisors still hold. When the permission system denies an
action (killing four orphaned shards at 18:10Z), surface it to the user with the exact command and
do not route it through a subagent; those processes exited by themselves two minutes later. Check a
cell's LIVE rate before preempting it: the orchestrator released the Qwen v2.5 VSIBench cell at
359 of 500, 25 to 40 minutes from done, on a stale rate estimate.

## 8. Provisional orchestrator rulings awaiting user confirmation

1. A scalar tool-returned distance is a legitimate observation; coverage does not gate a review; a
   constructed counterexample blocks a review only if a real row or a cell we will run instantiates
   it (all from 2026-09-20 and 09-21 morning, carried forward).
2. v2.6 is parked: 13 new rows cannot change a student.
3. v1c-XL is the full-scale path; the inheritance-aware holdout gate replaces the hash-only checker
   for it; the default selection is the 40-percent fixed-point cap.
4. Evaluation order and preemptions: v2.5 students, then Qwen arm C, then matched pairs, then Qwen
   arm A; RUN A's VSTIBench cancelled; RUN A3's VSTIBench held, then run; RUN B3 and the Qwen v2.5
   VSIBench cell preempted for the XL fine-tunes and later resumed.
5. The thinking-off control runs for Qwen only, despite a review verdict of FAIL whose one finding
   concerns OneThinker; the byte lock covers the protocol hash, the authority digest and the
   non-runtime core fields.
6. The larger-budget base control stays parked until subset scoring is decided; the likely route is
   the validated receipt-based credit in `analyze_cell.py`, disclosed as a diagnostic.
7. The collector stays at 44 workers until the user says otherwise.

## 9. Next steps, in priority order

1. Read the census when it exits; write CENSUS.md (strict and tier accepted, per type, accepted per
   hour, what the live counter counts that the census does not, ETAs to 20,000).
2. Build the final training set on all accepted traces with the same converter (pin `2ad2d70`), the
   same inheritance-aware split, and one answer-line fix: no trailing unit letter after a numeric
   answer (the defect behind OneThinker XL's 29 VSTIBench parse failures). Reuse the v1c-XL brief,
   staging plan and checklist in `P/claude_v1c_xl_brief_20260921T0915Z/`; the new traces need fresh
   ingestion from the census snapshot first (the v2.5 round-2 ingestion produced the current index).
3. Fine-tune both students on it (launchers and READY notes in
   `P/claude_v1cxl_students_launch_20260921T1115Z/`), then evaluate with the base, the thinking-off
   control (Qwen) and arm C columns and the paired diagnostics from the start (parameterised script:
   `P/claude_qwen_paired_diag_20260921T1230Z/out/COMMANDS.txt`).
4. Decide what, if anything, addresses the weak cell (OneThinker on VSTIBench): the teacher pool has
   no object-object position or camera-motion questions; options are a mixing ratio that protects
   base ability, fewer steps, or teacher traces on VSTIBench-style training questions (outside the
   current goal text; a user decision).
5. Land the fail-closed fix for `--thinking off` with a delta review; decide subset scoring.
6. Finish the matched-pair tables (section 6) and report RUN A3 against RUN B3.
7. Deletions only the user can make: `.git/index.lock.stale_20260921T0526Z` in this repository;
   `P/claude_link_latency_probe_20260921T1000Z/` (its extra hard links leave eight source files of
   vsi590k_216663, 216665, 216666, 227563 and 227565 with a link count of 3); a `.nfs_probe` file in
   `P/claude_v1c_xl_brief_20260921T0915Z/`; `STRAY_placeholder_20260921T0928Z.txt` in the pool
   extension directory. The harness hook that calls the missing `agent/check_commit_checkpoint.py`
   errors on every write in this repository and is harmless; do not add that file.
8. Land this document on `main` by fast-forward, then restart the package guard (section 5).

## 10. Armed watchers (they die with this session; re-arm on takeover)

| wakes on | armed | window |
|---|---|---|
| experiment request queue change (`agent/scripts/queue_watcher.sh`); all six changes today belonged to the other session | 18:36Z | until it fires |
| collector hold: target not 44, a rate-limit line, a 10-minute flat counter, a pool block, death of 195531, 233991 or 1041011 | 18:49Z | 4 h |
| collector alarm file growth or a new `P/INBOX_FROM_*` note | 18:42Z | 6 h |
| census process 1595879 exit | 16:27Z | 4 h |
| a new results table in the older evaluation lanes, or a complete `RESULTS_VSIBENCH_BASECTL.md` | 17:00Z | 6 h |

A `.seen_by_orchestrator` marker beside a table means the orchestrator has read it. The results
watcher's glob covers the matched-pair tables in `out_run_a3/` and `out_run_b3/`. No watcher names a
compact lane path.

## 11. Not verified when this was written

The census had not finished, so the accepted count is unknown. The XL per-type cells marked "see
table", the thinking-off control's VSIBench per-type row and the v2.5 median token counts were not
in the author's hands. The OneThinker XL done markers had not appeared at 19:09Z although both
tables had; the matched-pair lane had not reported; Qwen arm A's progress since the morning was not
re-read. Whether the stale index lock file and the idle cards are still as described after 19:40Z
was not re-checked. OneThinker arm C's publish path was not re-derived.
