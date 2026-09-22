# Distillation lane handoff (REQ-20260917-232), written 2026-09-22 01:10Z

## Command

This session runs on trinity-0-23 as Fable 5.1, pid 2938474, and has commanded the distillation lane
alone since 23:19Z. The user closed the prior session on trinity-3-8 (pid 3015054) at 23:39Z; the
ownership note sits at `P/INBOX_FROM_ORCHESTRATOR_20260921T2330Z_session_ownership.md`. The REQ-232
teacher-supervision alarm is acknowledged at
`P/INBOX_ACK_REQ232_TEACHER_SUPERVISION_20260921T222445Z.json`. Shorthand used below: P =
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`.

Between 23:30Z and 23:40Z the user reissued the collector goal verbatim (8M tokens per minute at the
key), set an explicit cap of 6M tokens per minute, approved teacher traces on VSTIBench-style
questions, and confirmed this session as the sole orchestrator.

This checkpoint supersedes `DISTILLATION_HANDOFF_20260921_1945Z.md` for everything that changed
since 19:45Z; that document still holds the full results detail, the arm C recipe evidence and the
standing constraints. A successor starts at section 7 (next steps) and section 8 (watchers).

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

### 1.7 The honest reading

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

## 2. Converter fix landed

The Devin Astra max lane `agent/scratch/devin_lanes/answer_line_unit_fix_20260921T2355Z` landed the
answer-line unit-normalization fix as commit `d9e3d57` on main; 121 tests passed, and an independent
Codex Astra review returned PASS
(`agent/scratch/codex_runs/20260922T001040Z_answer_line_unit_fix_admission_review`). The fix leaves
arm C's targets unchanged at the byte level (3,431 hashes, 3,852 dispositions, 8,470 answers) and
moves the renderer's `config_sha256` from `c96512de…` to `0be55936…`. Commit `5759735` (the
matched-pair results doc, section 1.3 above) also landed on main since 19:45Z.

Two independent readers of `generations.jsonl` lines 280-287 trace OneThinker's VSTIBench parse
failures on `camera_obj_abs_dist` to bare option letters emitted on numeric questions, not trailing
units. The landed fix guards against trailing units going forward but is a no-op on the current
pool: a scan of the candidate index finds 7,392 letter answers, 1,078 numeric answers and 11
non-string answers, none of which the guard touches. A labelled answer-line variant remains an open
ruling; the primary build keeps arm C's current format by default, with the variant prepared as a
converter option and trained after both primary students if GPUs allow.

## 3. Collector and census

The collector held 44 workers and averaged 336 finalized items per hour through the day. A ramp to
52 workers at 23:38Z lifted throughput to 524 per hour for ten clean minutes with zero 429s, but
trinity-3-8 — the node the collector runs on — froze at 23:50Z; by 23:57Z its lease, health checks,
terminals and heartbeats had all stopped, and it remains frozen at this writing. Load on the node
was already 76 of 96 cores at 44 workers before the ramp, with the full census also reading from it
at the time. The session wrote a target of 44 workers back via `setw.sh` at 00:10Z, but the frozen
node has not adopted it. The collector had finalized 24,111 of 27,506 questions at the freeze.

Ramp evidence sits at `P/claude_collector_ramp_20260921T2335Z/RAMP_LOG.md`; a thaw probe watches for
recovery at `P/claude_orchestrator_watchers_20260921T2330Z/trinity38_thaw_watch.sh`. Contingency
scoping for a relaunch, should the node not thaw, is under way at
`P/claude_collector_relaunch_contingency_20260922T0105Z/`, with a decision point around 02:30Z.

The light census taken at 21:21Z found 17,776 strict-accepted and 19,461 tolerance-25-accepted
questions of 23,028 finalized (`P/claude_light_census_20260921T2035Z/out/`).

## 4. Operating lessons

The collector's supervisor reads its control file at the top of each tick and rewrites it at the
end, so a write made mid-tick gets clobbered; every worker-count change goes through `setw.sh`,
never a direct edit. Counting 429 responses from collector logs must read only per-worker logs and
exclude `[finalized]` lines, because some finalized question ids themselves contain the digits 429.

The package guard (pid 2440530) exited at 23:36Z when the repository HEAD moved from `5860f02` to
`5759735`; the orchestrator relaunched it as pid 2813724 at 23:36:42Z. That guard process froze along
with trinity-3-8, and because HEAD has since advanced to `d9e3d57`, it will exit again on thaw and
needs a fresh restart at that point.

## 5. Running and paused cells

Qwen arm A r6 scored 25.67 strict on VSTIBench with 212 of 450 items unparseable
(`RESULTS_VSTIBENCH_QWEN_R6.md` in its lane); its VSIBench leg relaunched at 23:27Z on trinity-0-23
card 7.

The Qwen direct-answer base control on VSIBench froze at 125 of 500 items from 18:12Z, when a card
release killed its shards but left their leases active; it resumed at 23:37Z after the coordinator
failed four stale leases, reached 143 of 500 at 00:10Z, and runs at 72 items per hour on
trinity-0-13 cards 0, 2 and 3, with a finish around 05:10Z
(`P/claude_qwen_base_control_20260921T1305Z/out/`). A marker rename on card 1 needs the user's
permission to run; cards 4 and 5 hold another experimenter's vLLM server.

The final-set build plan is ready and pinned to `d9e3d57`
(`P/claude_final_set_readiness_20260921T2335Z/BUILD_PLAN.md`). Both arm C configs confirm vision
LoRA on (targets `exact_text_attention_mlp_vision_attention_mlp_mergers`, rank 32, alpha 64), and
the plan uses `inheritance_gate.py` with arm C's split `4dd7467f`; if the full census has no
`ACCEPTED.json` by about 26,000 finalized questions, the plan falls back to a fresh light census for
membership.

Scoping for VSTIBench-style teacher collection is at
`P/claude_vsti_teacher_scoping_20260921T2345Z/SCOPING.md`: nine camera-anchored question families
are absent from VSI-590K, the ground-truth assets suffice, object-object left-right and up-down
questions are derivable with current tools, and near-far and camera families need a pose tool; the
scoped set shares zero scenes with the 142 VSTIBench groups. A Devin Astra max lane
(`agent/scratch/devin_lanes/vstigen_membership_v4_20260922T0000Z`, branch
`vstigen-membership-v4-20260922`, commits `37794c0`, `e2f387e`, `642d484`, `5c0d55d`) is running its
final generation as of 01:02Z; it needs one admission review before the pool seals as epoch r1317
at exhaustion.

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

## 7. Next steps, in priority order

1. Watch trinity-3-8 for thaw; if it has not thawed by about 02:30Z, execute the relaunch
   contingency scoped at `P/claude_collector_relaunch_contingency_20260922T0105Z/`.
2. On thaw, restart the package guard, confirm the collector adopts the 44-worker target written at
   00:10Z, and pause the census so the collector can ramp back to 52 workers.
3. Take the VSTIBench-style generation lane (`vstigen-membership-v4-20260922`) through one
   admission review, then seal it as epoch r1317 at pool exhaustion.
4. Finish the Qwen VSIBench base control (`P/claude_qwen_base_control_20260921T1305Z/out/`, due
   about 05:10Z) and the Qwen arm A r6 VSIBench leg on trinity-0-23 card 7.
5. Build the final training set from `BUILD_PLAN.md`
   (`P/claude_final_set_readiness_20260921T2335Z/`) once the census, or its light fallback, reports
   membership at about 26,000 finalized questions.
6. Bring four deletions to the user: the renamed stale index lock, the link-latency probe
   directory, the stray `.nfs_probe` file, and the stray placeholder file (all named in the 19:45Z
   checkpoint, section 9 item 7).
7. Get the user's confirmation on the section 6 rulings, the labelled answer-line variant, and
   subset scoring.

## 8. Armed watchers

This session watches collector health through the package guard (pid 2813724, holding the ramp band
to 44-64 workers), the census process's exit, the Qwen r6 evaluation's progress, the experiment
request queue for new rows, and trinity-3-8's thaw. None of the closed trinity-3-8 session's
watchers survived it; a successor re-arms all five from scratch.

## 9. Not verified when this was written

Whether trinity-3-8 has thawed since 23:57Z is unknown; its lease, health, terminals and heartbeats
had not resumed as of this checkpoint. The census had not finished reading, so the 21:21Z
light-census figures stand without an update. The VSTIBench-style generation lane's final run had
not completed at 01:02Z, and no admission review of it had started. The Qwen VSIBench base control
and the arm A r6 VSIBench leg had not reported a finish.

The user has not yet ruled on pausing the census on thaw to free 52 workers for the collector, the
labelled answer-line variant, subset scoring, the four deletions in section 7, or the section 6
rulings. The post-edit hook calls `agent/check_commit_checkpoint.py`, which does not exist in this
repository; it errors harmlessly on every write.
