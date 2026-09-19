# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 20:45Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified
everything below at write time; re-verify before acting.

## 1. State of the goal

The user restated the lane's goal at about 11:50Z, verbatim:

> "Own the distillation lane: obtain at least 20,000 accepted traces on vsibench training
> using the GT perception data. Fine-tune OneThinker-8B and Qwen3.5-9B with vision and
> language LoRA on a scene-disjoint split of those targets and show better RGB-only,
> tool-free accuracy than the base checkpoints on VSIBench and VSTIBench reporting
> per-question-type results. use Devin Astra max for development, Codex or Luna for ssh
> work and Sonnet for easy tasks, and never touch the other experimenter's state or the
> collector code on main while the collector runs. Maximize the google API key at 8m
> tok/min to collect the reasoning traces. Evidence first: publish per-type results on the
> partial training set for both students before any full-scale run, and report them
> whether or not they beat the base. Paper ready numbers by 2026-9-24Z; when lanes compete
> for GPUs or the key, the collector and the two student fine-tunes win over ablations."

Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Devin lane root: `agent/scratch/devin_lanes/`, with `out/` symlinked to
`/data2/jjyeung/agent_project_data/devin_lane_out/<lane>_out/`.

### The window's headline: eval budget and host allowlist adopted; compact-target pilot rejected, fix lane running

**Evaluation cost.** A capped 16,384-token generation costs about 1,100 s versus 21 s when the
model terminates cleanly; the cap rate is a property of question type, not of the cell (numeric
types about 42 percent, multiple-choice about 2 percent) — evidence at
`D/claude_base_reeval_instructed_onethinker/out/{CAPPED_OUTPUT_ANALYSIS.md,VSTI_PROJECTION.md}`.
VSTI distilled at the 16,384 budget projected 30+ GPU-hours and was abandoned by orchestrator
decision at 19:56Z, recorded as partial evidence rather than a result (3 graded, 2 capped; no
score, no per-type table; see `RESULTS.md`). VSI distilled ran to completion at 16,384 until the
new lineage was ready and is also recorded partial; sharding follows manifest order, so partial
cells are type-skewed (`launch2/partial_table.py` marks a type complete once every shard has
cleared it). The one complete type so far, `obj_appearance_order`, scored 52.00 percent distilled
versus 52.00 percent base — indistinguishable, not a result either way yet.

**Harness lineage moved and was adopted.** Commit `e3e9ffb` (branch `eval-budget-4096-20260919`,
parent `a666e6a`) lowers `DEFAULT_CONFIG['decoding']['max_new_tokens']` from 16,384 to 4,096 —
budget only, 4 files, reviewed PASS at
`D/claude_review_eval_budget_4096/out/VERDICT.md`. New `config_sha256`
`b43a012b7dfebe6dcb798840dd57a632612b5dd4c43fc8a5c2a73d7fa7a4b9f1`; the old hash
(`0324759...`) is now refused by `load_config`. Commit `58794b8` (branch
`eval-host-t213-20260919`, parent `e3e9ffb`) adds `trinity-2-13` to the lease host allowlist in
`student_pilot/benchmark_eval/contracts.py` line 469, reviewed PASS at
`D/claude_review_eval_host_t213/out/VERDICT.md` **with one correction the orchestrator must
carry forward**: the builder's report claimed cells generated on `e3e9ffb` stay pairable with
cells generated on `58794b8`; the reviewer reproduced the refusal and struck that claim —
`core['runtime']` hashes `contracts.py` itself, `require_pair` compares it, and a base cell on
one commit cannot pair with a distilled cell on the other, nor can a run begun on one commit
resume on the other. **Cells never pair across harness commits**, full stop. Production checkout,
adopted 20:30Z: `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`
(`ORCHESTRATOR_ADOPTED.md` in both `claude_eval_budget_4096/out` and `claude_eval_host_t213/out`).
Every paper cell for both students, both benchmarks, runs from this one checkout path; packages
prepared under `e3e9ffb` remain valid in provisional mode (the paper's artifact-root pin is
skipped for provisional work), but `e3e9ffb` itself produced no paper cells.

Cell order under the 4,096 budget on trinity-1-3 GPUs 1 to 6: OneThinker base VSI (4 shards) plus
VSTI (2 shards); VSI distilled baseline (4 shards) plus Qwen base VSI (2 shards); VSTI distilled
baseline (4 shards); arm A attempt 10 adapter cells; Qwen base VSTI and Qwen adapters after.
`trinity-2-13` (eight idle 24 GB cards; OneThinker peaks about 21 GiB at 4,096) will take whole
cell pairs — never split shards — via a Luna ssh lane: the recipe is written
(`out/REMOTE_CELL_RECIPE_t213.md`, feasibility in `out/REMOTE_CELLS_FEASIBILITY.md`); `cohort.lock`
is an NFS flock and bind-lease output is exclusive, so a remote lane must claim an entire cell, not
shards within one.

**Compact targets landed, but the pilot review rejected the render.** Converter
`student/compact_targets/compact_counted_v1.py` merged to `main` at `f5ce7a0` (branch
`converter-compact-v1-20260919`, commits `63a0daf` and `5907fd6`; 88 tests). Set v1b:
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1b/candidate_index.jsonl`,
3,514 candidates, 338 deferred over budget, median 428 tokens, p90 945, max 1,536; the trainer's
`prepare-protocol` exits 0 against it (train_rows 3,152, heldout 362). The independent 16-target
pilot review (`D/claude_review_compact_pilot/out/REVIEW_compact_pilot.md`) **REJECTED** it: only
11 of 16 clean against the 14-of-16 bar. Systematic defect: when the source trace has no
Calculations section, the selection rule emits only appearance frame-lists and the answer loses
all visible support — it hit 3 of 3 `object_counting` targets in the pilot plus one
`object_rel_direction_medium` target, and the design's own measurement puts 23 percent of targets
at zero operand-named lines, so this is not a pilot accident. Two smaller defects: one operand
over-attribution (a derivation names operands it does not use) and citations to visibility-only
operands that carry no quantity. The citation-format question is resolved as a side effect:
sidecar-only citations are sufficient (`own_record_binding` holds byte-for-byte in all 16
targets); inline derivation citations were measured to cost 1.0-3.9x tokens for no verification
gain and are not needed. A fix lane (Opus) is running on the same branch: add a roster line for
counting types, defer calculation-free types under a `no_calculations` reason where a roster
line isn't the fix, filter `Uses observations` to operand records whose quantity can enter the
operation, and flag per-target when the answer is not reproducible from any emitted derivation;
it re-renders to `diagnostic_set_compact_v1c/` and writes `REPORT_selection_fix.md`. Next: pilot
review 2 against the same 14-of-16 rule, then arm C.

**Arm C brief is written but not dispatched.**
`D/codex_luna_launch_ddp_v4_c_onethinker/BRIEF.md` (Luna) stops arm A attempt 10 at a checkpoint
boundary through its own supervisor, records `PREEMPTED_FOR_ARM_C_r10.md`, then launches
OneThinker on the compact index with identical trainer settings, wrapped, trainer `ad96f47`,
GPUs 2 to 5 on trinity-1-13, RUN_TAG `ddp_onethinker_c_onethinker_20260919T2100Z`, publish root
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z`. It still points at
`diagnostic_set_compact_v1b`; **the candidate index must be updated to `v1c` before dispatch**,
and dispatch itself waits on the fix lane and pilot review 2 above.

### Collector (r1315 teacher traces, target 20,000; 8,772 finalized at 20:08Z)

Held at 36 workers since 19:35Z; the first full cycle at 36 was fully clean (zero 503 for all 30
minutes, zero 429), about 390 finalized per hour, tokens per call back down to 18 to 22K.
`D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. Next ramp step to 40 workers after one more
clean cycle. The Sonnet subagent `collector_watch` keeps observing
(`D/collector_watch/NOTES.md`).

### Trainer v4.7 (branch `trainer-multigpu-v4-20260919`, checkpoint-resume at `ad96f47`, unchanged)

No change this window. Every launch remains wrapped, on `ad96f47`, with checkpoints enabled;
frozen checkout `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`.

### Training runs (both students)

**OneThinker arm A, attempt 10** (`codex_luna_launch_ddp_v4_a_onethinker`): admitted 19:50:36Z on
trinity-1-13, world size 4 (GPUs 2, 3, 4, 5), wrapped, `ad96f47`, `/scratch` had 1,283 GiB free at
admission; first metrics 20:01Z. Latest: step 19 of 246 at 20:30:38Z, loss 0.163, 98.9 s per step,
ETA 6.24 hours (about 02:45Z on 09-20); no checkpoint published yet (first one lands at step 25).
`RESUME_RECIPE_r10.md` (manual same-node resume) is on file. The babysitter's open question
whether the plan calls for 246 or 321 steps is still being settled from the frozen protocol
summary in `launch_r10.log`; arm C may preempt this run at its first checkpoint once the compact
targets pass their second pilot review.

**OneThinker arm E**: unchanged, parked, waiting for trinity-1-13 to free.

**Qwen arm A, r5**: step 81 of 246 at 20:32:21Z, loss 0.0911, mean 216.4 s per step (slower than
the 19:50Z reading), estimated 9.92 hours remaining, ETA about 06:26Z on 09-20.
**Qwen arm E, r2** stays chained behind it on trinity-0-18.

### Evaluation

`claude_base_reeval_instructed_onethinker` now runs from the adopted production checkout
`eval_instructed_provisional_58794b8` (see headline above) rather than `a666e6a`. Hand-backs
unchanged: VSTI 50 items (moot now that VSTI distilled at 16,384 is abandoned), VSI 50 percent,
and scoring — all against the new checkout and the 4,096 budget.

### Rewrite (free-form C-N ablation)

Bulk v3.1 reached 3,309 of 3,852 at 20:08Z (3,437 lines total in the outcomes file at last count,
including non-`target` rows), about 3.7 rows per minute, finishing near 22:30Z. Measured to be 3x
shorter than format A (median 1,738 tokens) but keeps every observation and has no stop cue, so it
is confirmed not the termination fix — the compact-target design is
(`D/claude_design_compact_targets/out/DESIGN.md` section a).

### Other observer lanes

Unchanged: OneThinker DSI base continues on trinity-1-13 GPU 6; Qwen DSI stays dropped.

### Lane table

| Lane | Status at 20:45Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` (collector, watchdog v5) | 36 workers since 19:35Z; 8,772 of 20,000 finalized at 20:08Z; first clean cycle at 36 complete. | Ramp +4 to 40 after one more clean 15-minute cycle. |
| `collector_watch` (Sonnet subagent) | Observing. | Continue; notes at `D/collector_watch/NOTES.md`. |
| `claude_review_eval_budget_4096` | Done, PASS. | Adopted; production checkout moved to `58794b8` (which includes this change). |
| `claude_review_eval_host_t213` | Done, PASS with one correction (cells do not pair across harness commits). | Adopted 20:30Z at `eval_instructed_provisional_58794b8`. |
| `codex_luna_launch_ddp_v4_a_onethinker` (arm A attempt 10) | Training, step 19/246 at 20:30Z, ETA about 02:45Z. | Watch `PROGRESS_r10.md`; yields to arm C at a checkpoint if arm C is ready. |
| `codex_luna_launch_ddp_v4_e_onethinker` (arm E attempt 9) | Parked; unchanged. | Launch on trinity-1-13 once arm A attempt 10 (or arm C) finishes. |
| `codex_luna_launch_ddp_v4_a_qwen` (Qwen arm A r5) | Training, step 81/246 at 20:32Z, ETA about 06:26Z on 09-20. | Watch `PROGRESS_r5.md`. |
| `codex_luna_launch_ddp_v4_e_qwen` (Qwen arm E r2) | Chained behind Qwen arm A. | Launch once Qwen arm A publishes and GPUs free. |
| `codex_rewrite_v3_1_bulk` | 3,309/3,852 at 20:08Z, ETA about 22:30Z. | Keep the lease issuer alive; fidelity audit and 32-row review at completion. |
| `claude_base_reeval_instructed_onethinker` (evaluation lineage lane) | Moved to checkout `eval_instructed_provisional_58794b8`; VSTI distilled at 16,384 abandoned (partial evidence only); VSI distilled partial, one complete type (`obj_appearance_order`, 52.00% both). | Run all remaining paper cells (base and distilled, both benchmarks, both students) from `58794b8` at the 4,096 budget; consider a `trinity-2-13` remote cell via the written recipe. |
| `claude_review_compact_pilot` | Done, REJECT (11/16 clean, need 14/16). | Feeds the fix lane. |
| Compact-target fix lane (Opus, same branch) | Running: roster line for counting, `no_calculations` deferral, operand quantity filtering, per-target unreproducible-answer flag. | Re-render to `diagnostic_set_compact_v1c/`, write `REPORT_selection_fix.md`, then pilot review 2. |
| `codex_luna_launch_ddp_v4_c_onethinker` (arm C, OneThinker on compact targets) | Brief written, not dispatched; still points at `v1b`. | Update index to `v1c` once it passes pilot review 2, then dispatch. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the `collector_watch` Sonnet subagent; the Opus
evaluation-lineage lane (`claude_base_reeval_instructed_onethinker`); the bulk-lease issuer
for `codex_rewrite_v3_1_bulk`; the Gemini TPM readout background process; the remote
babysitter (Claude Opus) for arm A attempt 10 and Qwen arm A r5, and the remote gates chaining
OneThinker arm E and Qwen arm E; the compact-target fix lane (Opus); every Codex and Devin lane,
including the arm C launch-and-babysit lane once dispatched; and the 30-minute orchestrator tick.

The following survive: GPU jobs started through real shells, including OneThinker arm A
attempt 10 and Qwen arm A r5 (both training), the OneThinker single-GPU baseline (already
published), and the base-eval workers dispatched under `setsid`; all lane artifacts; and git.

## 3. Pending user rulings

- RULED about 11:50Z: the goal statement quoted in full in section 1 above supersedes prior
  phrasing of the lane's objective; its priority order and deadline (paper-ready numbers by
  2026-09-24Z) govern GPU and API-key contention.
- RULED, executor preference, applied since 12:36Z: every new lane uses Claude subagents or
  a Devin builder; Codex Luna handles ssh relays only; Codex Astra handles gate reviews and
  escalation only, never routine development; in-flight Codex lanes finish out rather than
  being cut off mid-task.
- RULED, relaunches: a relaunch of a collapsed experiment needs no reviewer round. A new
  design, a new admission or scoring path, or a first launch still gets one.
- RULED 23:50Z (2026-09-18): Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base
  continues.
- RULED 23:58Z (2026-09-18): evidence that distillation works on a partial training set comes
  before full-scale runs.
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid
  intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is about 2026-09-26.
- RULED 03:58Z: fine-tune the 8B and 9B students first; a 27B/31B-class student is a later
  go-or-hold decision.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot as
  a baseline only; maximize Gemini-key throughput once other experiments finish.
- RULED 19:24Z to 20:30Z (this window): the evaluation decode budget is 4,096, landed at `e3e9ffb`
  and reviewed PASS; the earlier decision to withhold the budget cut (recorded WITHDRAWN in the
  19:50Z handoff) is superseded — the harness field was not actually frozen against a reviewed
  source change, only against an arm-specific runtime override. Do not revert to 16,384 for new
  cells.
- RULED 20:27Z to 20:30Z (this window): `trinity-2-13` is adopted into the eval host allowlist at
  `58794b8`; every paper cell for both students runs from the `58794b8` production checkout; cells
  never pair across harness commits.
- RULED 19:56Z (this window): VSTI distilled at the 16,384 budget is abandoned and recorded as
  partial evidence, not a result; it will be regenerated under the 4,096 lineage.
- Open (carried forward): the compact-target reviewer's Tier I citation ruling is now resolved
  (sidecar-only citations are sufficient) but the render itself is REJECTED; open until pilot
  review 2 passes the 14-of-16 bar on `diagnostic_set_compact_v1c`.
- Open (carried forward): whether arm C (compact targets) preempts arm A attempt 10 at a
  checkpoint, or waits for it to finish; unresolved and now also gated on the fix lane finishing.
- Open: whether to overturn the provisional Format E admission (numbered anchors to
  delivered student frames were treated by the orchestrator as grounded facts, not tool
  artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.
- Open: cross-node Devin launch spread stays blocked; see section 6.
- Open: arm E placement — re-check the GPU census before dispatching `BRIEF_r9.md`; no node had
  four free 48 GB cards as of the last census.
- Open (new): whether to route a `trinity-2-13` remote cell through the written Luna recipe now,
  or wait until the local GPU 1-6 order clears the base and baseline-distilled cells first.

## 4. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- The pre-shell guard blocks any command text containing the words for deleting or
  truncating, even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and
  resumes from a preamble rather than depending on the dispatching session's memory. Some
  Codex lanes end without writing a final report while a remote heartbeat loop keeps
  appending; treat a live heartbeat without a report as still running, not done.
- Devin `-p` needs `--respect-workspace-trust false` and a `timeout` wrapper; `-p` processes
  linger after `DEVIN_LANE_DONE` and must be stopped by task.
- The recurring 30-minute orchestrator tick is session-only and must be recreated by each
  successor session.
- Never change `collector/` on `main` while the collector runs, blocked or not; land fixes on
  a branch, seal the contract from an epoch checkout under
  `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, attest, fast-forward (or
  ancestor-merge with an empty `collector/` diff), relaunch (CLAUDE.md production source tree
  rule).
- Lanes never switch branches or create branches in the main working tree; branch work
  happens in a separate `git worktree` under the lane's `work/` directory, landed on `main` by
  fast-forward.
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted.
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere
  With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after
  40 minutes to 2.5 hours, so kill steps route through the user rather than automation; write
  per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts live
  on `/data2` via symlinks.
- A launch lane must name its checkout explicitly, or it risks resolving an old addendum and
  rerunning an already-fixed bug.
- Qwen's chat template trims the terminal newline of format-E targets; the encoder must
  accept that native trim and restore it in supervision, or format-E rows fail to encode.
- Always score a base model under the same answer-format-instructed prompt used for the
  distilled model; an uninstructed prompt collapses most base answers to parse failures and
  makes any fine-tuned student look better than it is on format alone, not task skill.
- Never score a distilled adapter, or run any new paper cell, on harness `86d28d9`, `a666e6a`,
  or `e3e9ffb`. Use the production checkout
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`
  (harness tip `58794b8`, decode budget 4,096, `config_sha256`
  `b43a012b7dfebe6dcb798840dd57a632612b5dd4c43fc8a5c2a73d7fa7a4b9f1`), and keep parser blob
  `e703fe33` intact (it carries `ded50d3`'s trailing-semicolon option fix; dropping it can
  silently change multiple-choice scores).
- Cells never pair across harness commits: `core['runtime']` hashes `contracts.py` itself
  (absolute paths included), and `require_pair` compares it, so a base cell generated on one
  commit cannot pair with a distilled cell generated on another, and a run cannot resume across
  commits either. Run every paper cell — preflight, base, and distilled, both benchmarks, both
  students — from the one `58794b8` checkout.
- Resuming a labeled, sharded, interrupted evaluation cell is untested on this lineage; re-run
  the cell instead of resuming it. A durable start with no terminal receipt is permanently closed
  as `interrupted` on resume and never retried; each stop-and-resume under a labeled/sharded cell
  costs whatever items were mid-flight at the stop.
- A vnice-preempted training process can vanish with no checkpoint and no warning
  (`SignalException` signal 15 after its `/tmp/terminator/<pid>` marker disappears); judge
  training liveness from `metrics.jsonl` growth and the torchrun pid, never the wrapper
  process, since a killed run's wrapper can keep reporting "training" for many minutes.
  Trainer `ad96f47` now checkpoints periodically to mitigate this; resume only on the same
  node that wrote the checkpoint.
- The trainer admits only vnice-wrapped launches beyond the first 16 campaign GPUs
  (`student_pilot/lease.py` line 13, `provisional.py` line 246; main `AGENTS.md` line 189).
  An unwrapped launch is refused after it has already claimed coordination leases (harmless;
  the leases expire on their own), so wrap every launch from `ad96f47` on.
- A capped distilled completion is a parse failure, not evidence the format transfer failed:
  the model entered the trained observation format correctly, it just did not stop before the
  budget. Cap rate is a property of question type (numeric about 42 percent, multiple-choice
  about 2 percent under the old 16,384 budget), not of the cell or the arm.
- Do not admit the `diagnostic_set_compact_v1b` render for training as-is: the independent
  pilot review REJECTED it (11 of 16 clean, need 14 of 16) for a systematic defect on
  calculation-free question types, most severely `object_counting`. Wait for the fix lane's
  `diagnostic_set_compact_v1c` and a second pilot review before arm C.
- Avoid trinity-3-23, trinity-0-3, trinity-0-28, and trinity-1-8 for any launch; trinity-2-28
  is fully held by another user (the r8 waiter parked there must stay read-only and must not
  launch). `trinity-2-13` is newly available for whole eval-cell pairs via a Luna lane (eight
  idle 24 GB cards), not for training (no 48 GB cards there).
- Cross-node Devin launch (`ssh -f` form) still fails silently on other nodes; every Devin
  lane runs locally on trinity-1-3 pending a fix.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Ramp receipts: `D/codex_relaunch_r1315_drain_attest/out/RAMP_LOG.md`. Observer notes:
  `D/collector_watch/NOTES.md`.
- Evaluation cost/cap findings: `D/claude_base_reeval_instructed_onethinker/out/{VSTI_PROJECTION.md,CAPPED_OUTPUT_ANALYSIS.md,RESULTS.md,BUDGET_4096_REFUSED.md}`
  (`BUDGET_4096_REFUSED.md` documents the earlier refusal on the old lineage; the budget change
  has since landed and been reviewed on a fresh branch, see below).
- Eval harness lineage (this window): branch `eval-budget-4096-20260919`, tip `e3e9ffb`
  (parent `a666e6a`), reviewed at `D/claude_review_eval_budget_4096/out/VERDICT.md`; branch
  `eval-host-t213-20260919`, tip `58794b8` (parent `e3e9ffb`), reviewed at
  `D/claude_review_eval_host_t213/out/VERDICT.md`. Adoption records:
  `D/claude_eval_budget_4096/out/ORCHESTRATOR_ADOPTED.md`,
  `D/claude_eval_host_t213/out/ORCHESTRATOR_ADOPTED.md`. Production checkout:
  `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8`.
  Remote-cell plan for `trinity-2-13`: `D/claude_base_reeval_instructed_onethinker/out/REMOTE_CELL_RECIPE_t213.md`,
  feasibility `D/claude_base_reeval_instructed_onethinker/out/REMOTE_CELLS_FEASIBILITY.md`.
- Compact-target design: `D/claude_design_compact_targets/out/DESIGN.md`. Converter, landed on
  `main` at `f5ce7a0` (branch `converter-compact-v1-20260919`, commits `63a0daf`, `5907fd6`):
  `student/compact_targets/compact_counted_v1.py`. Set v1b:
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1b/candidate_index.jsonl`.
  Pilot review (REJECT): `D/claude_review_compact_pilot/out/REVIEW_compact_pilot.md`. Fix lane
  output (in progress): `diagnostic_set_compact_v1c/`, `REPORT_selection_fix.md`, same worktree
  branch.
- Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `ad96f47` (checkpoint-resume, after `06a9664`,
  `b41b597`, `ef2cd59`). Review verdict: `D/claude_review_trainer_v4_7/out/VERDICT.md`. Frozen
  checkout: `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_ad96f47`. Contract/addendum:
  `agent/scratch/devin_lanes/trainer_v4_7_checkpoint_resume_20260919/out/`.
- Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker` (attempt 10; `PROGRESS_r10.md`,
  `RESUME_RECIPE_r10.md`, `launch_r10.log`; publish root
  `/data3/jjyeung/ddp_onethinker_a_onethinker_20260919T0930Z_r10`), `..._e_onethinker` (attempt
  9, parked), `..._a_qwen` (r5; `PROGRESS_r5.md`), `..._e_qwen` (r2, chained),
  `..._c_onethinker` (arm C, compact targets; `BRIEF.md`, written 20:23:43Z, not dispatched;
  update its candidate-index path to `v1c` before dispatch).
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, output
  `/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/OUTCOMES_bulk_v3_1.jsonl`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`, most recently
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md` (warned the other session about
  trinity-0-3); unchanged this window.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

Every new lane uses a Claude subagent or a Devin builder. Codex Luna handles ssh relays to
other nodes only; Codex Astra is reserved for gate reviews and escalation, never for routine
development. In-flight Codex lanes run to completion rather than being cut off mid-task, and
some end without writing a final report while a remote heartbeat loop keeps appending, so check
the heartbeat before assuming a lane died. A relaunch of an already-designed, already-running (or
collapsed) experiment skips independent review; review still gates a new design, a new admission
or scoring path, or a first launch — both harness-lineage changes this window (`e3e9ffb`,
`58794b8`) got their independent review before adoption, and the compact-target render still
needs a second pilot review to pass before arm C launches. Devin sessions spreading across nodes
stays blocked because the cross-node launcher's `ssh -f` form fails silently (no `devin.out`) on
trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin lane still runs locally on
trinity-1-3 pending a diagnosis of that launch form.

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to
this lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them).
Check both files on every tick. The most recent message from this lane,
`D/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260919T1707Z.md`, warned the other session that
trinity-0-3 had stopped accepting ssh; no new exchange this window.

## 8. Memory index

Memory files added or updated since 19:50Z, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`compact-counted-targets` (new: converter landed at `f5ce7a0`, pilot REJECT at 11/16, systematic
no-Calculations defect, sidecar-citation ruling), `distilled-onethinker-observation-loop`
(updated: measured cap cost and per-type cap rate, the `e3e9ffb`/`58794b8` harness lineage, the
cross-commit pairing rule), `student-trainer-readiness` (updated, no structural change this
window), and `MEMORY.md` (index entries for the above).
