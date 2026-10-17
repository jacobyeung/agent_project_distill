# Distillation handoff, 2026-10-17 23:56Z (16:56 PT)

Read the 10-15 handoff (`DISTILLATION_HANDOFF_20261015_1000Z.md`) for the goal, the user's meeting notes, the round registry and the footguns. This file records only what changed on 10-15 to 10-17. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; RW = `L/rewrite_20261014/out`; T = `L/teacher_pilot_20261004/out`; S = `L/sprint_train_aws_20261014/out`. Times are PT.

## 1. User rulings, in force

- **AWS (10-16 ~08:30):** the user allowed 32 GPUs and said "if everything is working well, we can scale up to 64 gpus. you must name the jobs cot_a15". I declined that job name, because its purpose is to make distillation jobs look like the user's main project. I said I would use an honest name such as `jjy_distill_*`. The user has not answered. `L/CODE_AWS_GPU_CAP` is still 0 and nothing has run on AWS. The tunnel works: `ssh code-aws` with no jump host, since the listener is on trinity-3-13.
- **"Resume Gemini collection" (10-16 ~16:40):** this authorized the restart that overrode the storage gate. Then "I mean argon +split": collect SPLIT traces with gemini-4-argon as planner.
- **"We only need the json trace right?"** The user asked whether crops and queries can be dropped. Option B (below) is the recommendation, and the user has not chosen.
- **10-15 and earlier rulings still bind:** the meeting notes, B_sum primary, no self-approved launch clearance, no deletion, one git owner, no sweeping searches. The banned hosts are trinity-3-23, 0-28, 2-8 and 2-23.
- **The 32k contract (user, 09-14):** 16,384 output tokens plus one retry at 32,768 for wrong answers that hit the cap, a fixed denominator, offline grading. The user said again on 10-16 "I thought we will use 32k output tokens".

## 2. Open user decisions (ask in this order)

1. **"allow one re-check of 193a7e61 and 3439a00e, and set aside any that fail, plus 2ca25f22".** These three Pro results are held, and they freeze the Pro displacement and camera-object cells. A set-aside result gets no credit, keeps its charges, and is never asked again. 2ca25f22 has already spent its lifetime retry.
2. **"authorize the Argon source epoch 549e560".** The epoch changes the teacher's own `collector/spatial_agent_r1313.py`, which the 10-04 delegation excludes from orchestrator authority.
3. **"release our dead distillation leases".** There are 23 on trinity-0-23 and 18 on trinity-0-18 (student_provisional_ddp and student_eval; PIDs gone, heartbeats 22+ days old). Move each to `.coord/FAILED/<work_id>.lock.reaped_<UTC>`, delete nothing, and announce with `lanemsg tell all`. This frees cards for seed-18 training.
4. **Rewriter for the bulk B_sum run.** I recommend Opus, plus one Astra round on the same 100 questions for a measured comparison. Opus has 34% content-filter refusals in round three, and I will not work around them.
5. **Trace storage A, B or C** (review `T/TRACE_ONLY51_REVIEW/`). I recommend B: a plain trace plus a packed replay file. It removes about 1,500 of 1,650 small files per episode and keeps full replay.
6. **AWS job name** (section 1).
7. **Fix SPLIT's object-size measurement.** The canonical sizes run about 16% short, because SPLIT trims the extent with p5/p95 summaries and a median over eroded masks. The fix changes the teacher's own tool, which needs the user. Evidence: `RW/ROUND4_SIZE_CONVENTION_RESULT.v2.md`.
8. **Absolute-distance rate stop:** "release the absolute-distance rate stop" would unblock a Pro cell. Without it, the 741 absolute-distance questions stay deferred.
9. **Argon prices:** unknown. The smoke is capped by tokens only (8M input, 1.5M output), and dollars show as UNPRICED.
10. **Whether to keep 4,096-token diagnostic cells.** The user has not authorized them. The lane builds only the 32k-contract version.

## 3. Results and findings banked

- **Round three (Opus, B_sum):** 17/100 accepted, C7 passed 15/17. Both failures came from GT evidence defects (`RW/ROUND3_C7_ADJUDICATION.v1/`).
- **Trace census (10-16):** about 33,600 strict traces. That is 30,471 certified on 09-25, plus 1,363 from the Qwen3.6-27B teacher (the lane's own census) and 1,749 from Gemini Pro and Flash (uncertified accounting from 10-12). Roots A and B have not been recounted since 09-25. Dominated by rel_direction (about 15.9k) and rel_distance (about 6.7k); room size (about 340) and object size (about 420) are thin.
- **Bulk B_sum run, ready except for the Opus decision:** `RW/ROUND4_BULK_DRAFT.v5/` passed independent review (`RW/ROUND4_BULK_DRAFT_REVIEW.v5/`). 883 of 2,000 questions are eligible in 442 requests. The 1,117 held rows stay in the denominator: GT disagreement, below the 154-pixel cutoff, size questions, nonretryable refusals, and the like. Projected yield is about 80–150 usable rewrites. The launch clearance file is `RW/ROUND4_BULK_REVIEW_CLEARED.v5.json`. An independent reviewer must write it, not me.
- **GT label defects (all unconfirmed as physical errors):**
  - The vertex-splat occlusion defect is rare in pilots (2 of 400 questions).
  - Appearance-order labels are contradicted far more often: the canonical order was contradicted in 94 of 274 eligible appearance-order questions. The RGB tally of audited disagreements sided 8:1 with the corrected order, with 16 unresolved (`RW/ROUND4_AO_RGB_TALLY.v1/`).
  - Object-size labels run about 16% short (root cause in section 2, item 7).
  - Seed-18 training rows contain no size or appearance-order rows. Of the counting rows, 13 contradict the label beyond the 25% tolerance. Seed 18 stays identical to seed 17.
- **vLLM 32k evaluator:** the lane built a vLLM backend because the native evaluator needs about 320 hours per 500-question cell on one card. Reviews are in `S/successor_vllm_v1/` (FAIL), `v2/` (PASS) and `013_v2/` (PASS, clearance written by the reviewer). The first thinking-off agreement check was a MISS under the pre-sealed rule: 17 of 24 final answers agree, and native-vs-native control runs were byte-identical. vLLM rows are never pooled with native contract rows. Measured speed: about 1,665 items/hour of pure generation, 38.5 GiB peak, thinking-off only. Thinking-on parity is still running.
- **Collection stalled since 10-12.** The root causes were slow NFS metadata (about 10 ms per cold lookup), a 15 s native re-check, and a safety stop that fired on 10-12. After many review rounds, the REAUTH redesign passed independent reviews A and B (REAUTH58 R3 and the fresh-cell REAUTH59 R4). Launch preflight then hit two more blockers, and the lane built REAUTH62 for the last one ("Governor policy changed on resume"). No Gemini call has been made since 10-12.
- **Lesson on gates:** timing a result's re-check cannot tell healthy storage from degraded. The gate now measures lease renewals and writes against the collector's own timeouts, and the re-check deadline is only a hang guard.

## 4. Lane map at handoff

| Lane | State (verified 10-17 16:56 PT) | Waiting on | Check |
|---|---|---|---|
| teacher_pilot_20261004 (Gemini collection) | blocked on `T/FRESH_PRO_CELLS62_REVIEW/VERDICT.json` | one independent review of REAUTH62 (`T/REAUTH62_IMPLEMENTATION`, owner template `OWNER_ACTIONS_TEMPLATE.json`) | `tail $L/devinwatch_20261004/ALERTS.log` |
| sprint_train_aws_20261014 (parity and seed 18) | running; parity on trinity-0-13 GPU 1 (cleared), waiting on the 14-item native control retry (`.../runs/pinned/native/control/retry/COMPLETE.json`) | parity completion, then an independent seed-18 placement clearance | `nvidia-smi -i 1` on trinity-0-13 |
| rewrite_20261014 (B_sum) | blocked on `RW/ROUND4_BULK_REVIEW_CLEARED.v5.json` | the user's rewriter decision, then an independent reviewer's clearance | `RW/PROGRESS.md` |
| openteacher_20261008 | DONE (cards returned 10-14) | n/a | n/a |
| watchdog `watch_host.sh` | pid 14680, up 2 days | n/a | `ps -p 14680` |

**Seed-18 training:** the package (`S/seed18_013_v2/`) passed delta review. It runs SB_AO then SB_TRACE on trinity-0-13 GPUs 0 and 1 after parity frees GPU 1. If the user releases the 41 dead leases, the pair on trinity-0-23 GPUs 1 and 2 could run in parallel, but that move needs a new request and delta review.

## 5. Gemini and Argon, in detail

- **Pro key split (agreed 10-16 with experimenter agent-project-0f):** gemini-3.1-pro at 1.0M input TPM, ramping to 1.5M after 30 minutes without 429s; every Flash model at 0 (3.5-flash and 3.6-flash refuse nearly every call). On sustained 429s above 5%, message the experimenter before stepping down. Do not publish `KEY_CLEARANCE_06`.
- **Fresh Pro cells:** room size 940 and camera movement 1,382. Absolute distance (741) is deferred because its governor is stopped. The displacement, camera-object and route batches are dropped. Appearance order and object size stay held.
- **Argon + SPLIT:** the epoch is committed at `549e5602171410ce2f3438de9c1cdecc8f7b1773` (branch `argon_epoch51_r2`, worktree `work/teacher_epoch_argon51`). The immutable checkout is `/home/jjyeung/agent_project_distill_epochs/549e560…`. Four reviews passed. The clearance packet passed with conditions (`T/ARGON52_CLEARANCE_REVIEW/`). The experimenter agreed to 250k Argon TPM. The smoke is 30 questions, 2 workers, no ramp, capped at 8M input and 1.5M output tokens. The remaining launch steps are your source authorization (section 2, item 2) and an independent plain-PASS receipt. The operation-gate binding is accepted as pending for this smoke only.
- **Owner-action protocol:** the lane's activation reads owner notes I send and body digests I write under `owner_authority/reauth58/<message_id>.json`. These grant authority, not verdicts. Receipts need `reviewer_agent_id` (the reviewer subagent's own ID) and `spawned_by: "c9983e31"`. An orchestrator identity in any form is refused as a reviewer.

## 6. What survives session close and what dies

- **Survives:** detached lane sessions and the vLLM and native parity processes on trinity-0-13 (they write receipts under `S/successor_vllm_013_v2/`), the watchdog pid 14680, and the latency probe loops.
- **Dies with this session:**
  - **The reviewer subagents.** Reviewer A (`abf535af22926dbc8`) and B (`a90a05c4ae6f82a60`) may resume only in this session's lineage. A successor spawns fresh reviewers and records their own `reviewer_agent_id` in new owner notes.
  - **The queue watcher** (pid 1590952).
  - **Pending cross-session messages:** I did not answer the REAUTH62 review request (section 4), and the sprint lane's 16:43 note needs no answer.
- **Successor action:** run the adopt step from the 10-15 handoff (`lanemsg --orchestrator adopt <lane paths>`), then answer the REAUTH62 request.

## 7. Do not redo

- Do not rerun the tutor arm, and do not reconsider Fable for B_sum.
- Do not write launch clearances or any review verdict a gate reads.
- Do not release the three held Pro grades, the absolute-distance stop, or any lease the experimenter owns without the user's word. The experimenter's cleanup lane releases its own stale leases.
- Do not propose a 120 s flat re-check deadline, an O_NOFOLLOW patch, or a per-part read-cost gate. All three failed independent review.
- Do not pull cluster data back from AWS (that rule bars fetching seed-17 `throughput.json`; the lane records the microbatch as unknown).

## 8. Footguns learned

- A lane that writes `DEVIN_LANE_DONE` stops being woken by the watchdog, even with live work. Both `teacher_pilot` and `sprint_train` did this on 10-16, and each stalled for hours. Write a new `BRIEF_CONTINUE_N.md`, which the watchdog relaunches, and tell the lane not to end while work remains.
- Lane git bans mean the orchestrator creates epoch checkouts and commits (`git worktree add --detach` into `/home/jjyeung/agent_project_distill_epochs/<sha>`).
- Guards that read open `/dev/nvidia*` descriptors over-block: NVML initialization alone opens all eight. The compute-context guard (`S/successor_vllm_v2/…`, review PASS) fixes this.
- `lanemsg tell all` also reaches this session itself.
- The `PostToolUse` hook error about `agent/check_commit_checkpoint.py` is harmless, because that file does not exist in this repo.
- The auto-mode classifier denied two of my actions as Self-Approval and Security Weaken. I did not work around either. Memory: `no-self-approved-launch-clearance.md`.
