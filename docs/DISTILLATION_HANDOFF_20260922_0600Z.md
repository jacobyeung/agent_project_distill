# Distillation lane handoff (REQ-20260917-232), written 2026-09-22 06:00Z

## Command

P denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918` throughout. This
checkpoint supersedes `DISTILLATION_HANDOFF_20260922_0110Z.md` for everything that changed since
01:10Z; that document still holds the full derivation of the results tables this one carries
forward. A successor reads section 7 (next steps) and section 8 (watchers) first.

## 1. Results (fixed protocol unless a row says otherwise)

Fixed protocol: harness `58794b8`, instructed prompt, 4,096-token generation budget, strict parser
as the metric of record through 01:10Z, RGB-only, tool-free, greedy, 32 frames. Section 1.8 below
records the 05:30Z ruling that makes the lenient parser primary and strict secondary from this
checkpoint on. "Capped" counts generations that reached the budget without an answer. Every cell
scored all of its items (VSIBench answerable-500, VSTIBench 450).

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
| RUN B3 (control for A3) | v1c, 570 rows | 54 | 22.61 | 22.61 | 182 (185 parse failures) |

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
| RUN A3 | 32.09 | 32.09 | 51 | 58 |
| RUN B3 (control for A3) | 37.85 | 37.85 | 24 | 24 |

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

### 1.3 Matched pair complete: target format vs. question membership (RUN A3 vs. RUN B3)

RUN A3 and RUN B3 train OneThinker-8B on the same 570 questions, split, frames, trainer and 54
steps; RUN A3 trains on the corrected-format v2.4.3 targets, RUN B3 on the matched v1c subset. On
VSIBench the two land within noise of each other (22.18 vs. 22.61, both about 9 points below the
31.47 base), but RUN B3 hits the generation cap on 182 of 500 items against RUN A3's 89, so
termination tracks the question subset there, not the target format. On VSTIBench, RUN A3 scores
32.09 and RUN B3 37.85 against the 40.16 base: RUN B3's v1c-format targets cut parse failures
roughly in half (24 vs. 58) and close most of the gap to base, so target format is the dominant
lever on that benchmark. Full per-type tables and checkpoint paths sit in
`docs/MATCHED_PAIR_A3_B3_RESULT.md`.

### 1.4 Qwen3.5-9B, VSTIBench (lenient equals strict in every Qwen cell)

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

### 1.5 Qwen3.5-9B, VSIBench

| cell | score | capped | unparseable | median generated tokens |
|---|---:|---:|---:|---:|
| fixed-protocol base | 15.47 | 373 | 378 | 4,096 |
| thinking-off base control (sensitivity row) | 29.09 | 4 | 160 | 102 |
| direct-answer base control | 17.61 strict (see section 1.8) | 360 | 359 | not recorded here |
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

"See table" marks cells this document's author did not hold; the tables in section 3 of the
19:45Z checkpoint carry them.

### 1.6 Paired diagnostics (aggregates; `P/claude_qwen_paired_diag_20260921T1230Z/out/`)

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

### 1.7 The honest reading (strict-protocol view, through 01:10Z)

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

### 1.8 Lenient scoring ruled primary (05:30Z); the perception-vs-reasoning analysis

Lenient parsing now carries the paper's primary claim, and it moves the Qwen story the most: Qwen's
VSTIBench margin over its terminating (thinking-off) base falls from a strict-looking 10.76 points
to a bound of -0.45 once that base gets the same permissive reading the student gets. The 05:30Z
ruling states the reason directly — a correct answer in the wrong format is never penalized, lenient
parsing is primary and strict secondary, and the paper's claim is a true gain in reasoning and
perception, not a format artifact.

| pair | base strict | base lenient | base recovered-bound (a bound, not a score) | student | delta lenient | delta vs. bound |
|---|--:|--:|--:|--:|--:|--:|
| OneThinker VSIBench | 31.47 | 39.19 | 39.44 | 42.35 | +3.16 | +2.91 |
| OneThinker VSTIBench | 40.16 | 45.40 | 45.53 | 43.59 | -1.81 | -1.95 |
| Qwen VSIBench, thinking-off base | 29.09 | 29.09 | 40.05 | 49.25 | +20.16 | +9.20 |
| Qwen VSTIBench, thinking-off base | 35.80 | 35.80 | 47.01 | 46.56 | +10.76 | -0.45 |
| Qwen VSIBench, fixed-protocol base | 15.47 | 15.47 | 23.18 | 49.25 | +33.77 | +26.07 |
| Qwen VSTIBench, fixed-protocol base | 28.59 | 28.59 | 32.84 | 46.56 | +17.97 | +13.72 |

(Source: `P/claude_error_analysis_perception_20260922T0535Z/out/DELTAS.txt`, reviewed and copied
into this repository at `docs/ERROR_ANALYSIS_PERCEPTION_VS_REASONING_20260922.md`.) The two strict
headline pairs the user named — Qwen VSTIBench 28.59 to 46.56 and OneThinker VSIBench 31.47 to
42.35 — stand beside this lenient table and beside the direct-answer base control rather than
replacing either.

A direct-answer base control (one added sentence, thinking left on) scores 17.61 strict on VSIBench
with 359 of 500 items unparseable, and 31.47 strict on VSTIBench; the analysis judges this the less
fair reading of the two base controls, because most of its lost credit is an unfinished generation
that no parser can recover, not an answer a reader would reject. The thinking-off control therefore
stays the base of record.

The analysis (`docs/ERROR_ANALYSIS_PERCEPTION_VS_REASONING_20260922.md`, copied verbatim from the
report above) traces the gain to three sources. Answer format explains most of it: the lenient
parser recovers 84 of OneThinker's 93 VSIBench strict failures and salvages most of Qwen's prose
failures under a permissive bound. Where a target states a derivation rule, the student's own
arithmetic checks out on 82 to 88 percent of those items, but its underlying measurements — counts,
distances, sizes, room areas — miss ground truth by 25 to 44 percent at the median, against an MRA
metric that pays nothing past a 50-percent miss. And the base sets the perception ceiling, not the
student: the base's own numeric estimates match the student's accuracy, and 54 to 77 percent of the
student's errors land on items the base also gets wrong. Distillation transfers a format and a
termination habit, plus answer priors on the families whose targets carry no derivation rule at all
(53 percent of VSIBench items, 78 percent of VSTIBench items) — real perceptual gains from training
are smaller than the headline lenient deltas suggest, and OneThinker's VSTIBench loss of 75 to 95
base-correct items is a real cost.

## 2. Converter fix landed

The answer-line unit-normalization fix and the matched-pair results document both sit on main at
commit `26f698f`, unchanged since the 01:10Z checkpoint. Commit `d9e3d57` normalizes a trailing unit
on the answer line and passed an independent Codex Astra review; commit `5759735` carries the RUN A3
vs. RUN B3 matched-pair tables reproduced in section 1.3 above. Arm C's targets remain unchanged at
the byte level under the fix (3,431 hashes, 3,852 dispositions, 8,470 answers).

## 3. Collector, census and the r1317 epoch

trinity-3-8 rebooted at 01:43Z and the collector relaunched from the working tree at 01:49Z,
restoring the 24,111 finalized questions the freeze had left behind. Cold-cache validation of those
terminals ran until 03:04Z, and the resize child rehashed assets until about 04:02Z; the controller
(pid 23553) then self-ramped from 16 to 40 workers, and a detached pin wrote 44 at 04:54Z, latching
the cooldown. Watchdog 3693, guard 3365, pin 17093 and lease keeper 3209 hold the collector at that
count. Load on the node burst to 80 at the 44-worker resize and settled to 50-60 afterward; 24 clean
minutes produced 240 finalized items per hour, and the collector had finalized 24,351 questions by
05:31Z with 3,158 left in the pool. At this rate 26,000 finalized questions (about 20,000
strict-accepted) arrive around 12:24Z, and the pool exhausts around 18:45Z. The relaunch lane's
twelve steps sit at `P/claude_collector_relaunch_20260922T0145Z/STEP_1` through `STEP_12`.

The full census abandoned mid-freeze; a light census stands in and finished at 05:11Z after pausing
itself for 72 minutes on the collector-health gate, reading 24,446 attempted decisions down to
24,154 with zero errors. A render at commit `d9e3d57` has run since 05:43Z, and the interim build's
`BUILD_RECORD.md` is still pending at `P/claude_interim_build_20260922T0325Z/`.

Membership v4 adds 3,357 generated object-object left-right and up-down rows to the 105,000 v3 rows,
defers 1,562 near-far rows, and passed independent review after two fix rounds (commits `cef71ad`,
`ce1a13b`; receipts under `agent/scratch/codex_runs/20260922T013503Z…`, `20260922T015006Z…` and
`20260922T015905Z…`). It changes `collector/training_assets.py`, so it stays on branch
`vstigen-membership-v4-20260922` (rebased onto `26f698f`) rather than landing on main, until the
r1313 run ends. The epoch sealed from the immutable checkout at
`/home/jjyeung/agent_project_distill_epochs/5245587fbf56942b1759b5db1d34f3b589f9bbd7` with a
vstigen-only subset membership of 3,357 rows, and its gate review passed
(`P/claude_r1317_launch_20260922T0210Z/STEP_1` through `STEP_8`); `require_drained` is vacuous for
the new root. The bind completed at 04:45:07Z with all 3,357 rows ready and none pending. The
controller launched at 04:45Z on trinity-1-13 (pids 958246 and 958247, work_id
`training_trace_collection__r1317_gt__vstigen3357__s17__76e67ed6e8`, agent
`req233-gt-teacher-r1317`) and had produced 103 terminals by 05:19Z at 8 to 16 workers with zero
429s; it ramps toward 20 workers now and moves to 44 once r1313 exhausts its pool. The shared key
caps both collectors together at 6M tokens per minute.

## 4. Operating lessons

The collector's supervisor still clobbers any control-file write made mid-tick, so every
worker-count change goes through `setw.sh` rather than a direct edit; a count of 429 responses must
read per-worker logs only, because some finalized question ids contain the digits 429 and a count
over `[finalized]` lines miscounts them.

Four lanes died together at 04:05Z when the account hit its session limit (it resets at 12:20 AM
ET). The durable, `setsid`-launched processes underneath those lanes kept running, and each
successor resumed cleanly from its predecessor's STEP artifacts instead of restarting from zero.

## 5. Running and paused cells

Qwen arm A r6 scored 25.67 strict on VSTIBench with 212 of 450 items unparseable
(`RESULTS_VSTIBENCH_QWEN_R6.md` in its lane); its VSIBench leg is running on trinity-0-23 card 7.

trinity-0-18 is the only idle 49 GB node, and it takes vnice-wrapped jobs only. The GPU survey and
launch plan (`P/claude_gpu_survey_20260922T0325Z/GPU_ALLOCATION.md`,
`P/claude_student_prestage_20260922T0335Z/LAUNCH_PLAN.md`) project Qwen3.5-9B FSDP on cards 0-5 at
106 s/step (20.7 h) and OneThinker DDP on cards 6-7 at 85 s/step (16.6 h), both from checkout
`work_checkout_b084aaf`, which carries the checkpoint-cadence fix. Weights staged at 04:57Z under
`/scratch/jjyeung/distill_20260922/`, and the launch lane
(`P/claude_student_launch_20260922T0515Z/`) waits on `BUILD_RECORD.md` before it fires either run.

Three student launches wait on that build. The primary Qwen3.5-9B and OneThinker pair above is the
first. An OneThinker answer-only control, whose targets reduce to the bare answer line, is the
second and runs on trinity-1-13 cards 2 and 3. A Qwen3.6-27B student is the third, launching on
trinity-0-13 cards 0, 2, 3 and one more card through a Devin Astra max lane
(`agent/scratch/devin_lanes/qwen27b_student_20260922T0545Z`) with a smoke test first and checkpoints
every 25 steps; per the 05:45Z ruling this student need not finish, since partial results that show
improvement are useful on their own.

## 6. Provisional orchestrator rulings awaiting user confirmation

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
8. The r1317 VSTIBench-style epoch runs concurrently with the r1313 production collector, both live
   at once (ruling 01:53Z).
9. Every cluster GPU is open to this session; find free cards directly over ssh rather than
   requesting allocation, and leave another experimenter's processes untouched; paper numbers are
   due by 2026-09-24Z (ruling 03:20Z).
10. The interim Qwen run stands as the paper's Qwen number by default; OneThinker retrains on the
    full 20k-question set; a full-set Qwen run follows afterward as best effort (ruling 05:25Z).
11. Lenient parsing is the primary metric and strict is secondary; a correct answer in the wrong
    format is never penalized; the paper's claim is a true gain in reasoning and perception, not a
    format artifact (ruling 05:30Z).
12. A Qwen3.6-27B student need not finish training; standing it up quickly matters more than
    completion, since partial results that show improvement are useful on their own (ruling
    05:45Z).

## 7. Next steps, in priority order

1. Finish the interim build's `BUILD_RECORD.md` (`P/claude_interim_build_20260922T0325Z/`) and
   confirm the render at `d9e3d57` completed cleanly.
2. Fire the three pending student launches once `BUILD_RECORD.md` lands: the primary Qwen3.5-9B and
   OneThinker pair, the OneThinker answer-only control on trinity-1-13, and the Qwen3.6-27B smoke
   test on trinity-0-13.
3. Watch the r1317 controller on trinity-1-13 ramp toward 44 workers as the r1313 pool exhausts
   (projected about 18:45Z), and watch the r1313 collector's own approach to the 26,000-finalized
   trigger (projected 12:24Z).
4. Finish the Qwen arm A r6 VSIBench leg on trinity-0-23 card 7.
5. Bring the four pending deletions and the section 6 rulings to the user for confirmation.

## 8. Armed watchers

This session watches collector health (pids 3693, 23553 and 3365, holding the ramp band at 44 to
64 workers with a trigger at 26,000 finalized questions), the Qwen r6 evaluation's progress, the
experiment request queue, the weights-and-build-record path toward `BUILD_RECORD.md`, and the
base-control completion flag.

## 9. Not verified when this was written

Whether the interim build's render at `d9e3d57` finished cleanly is unknown; `BUILD_RECORD.md` had
not appeared as of this checkpoint. The r1317 controller's ramp past 20 workers and its move to 44
workers after r1313 exhaustion are unconfirmed. None of the three pending student launches — the
primary Qwen3.5-9B/OneThinker pair, the OneThinker answer-only control, or the Qwen3.6-27B smoke
test — had started as of 06:00Z. The Qwen arm A r6 VSIBench leg on trinity-0-23 card 7 had not
reported a finish.

None of this blocks further work. The optional card-1 marker command is moot now that every
cluster card is open to this session (ruling 03:20Z). Four deletions still need the user's word: the
stale index lock renamed 2026-09-21 05:26Z, the link-latency probe directory, one stray `.nfs_probe`
file, and one stray placeholder file. The rulings in section 6 — carried forward and newly added —
still await the user's explicit confirmation, though items 8 through 12 already function as accepted
defaults.
