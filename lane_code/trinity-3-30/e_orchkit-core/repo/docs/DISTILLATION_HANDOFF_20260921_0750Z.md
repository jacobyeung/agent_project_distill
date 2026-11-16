# Distillation lane handoff (REQ-20260917-232), written 2026-09-21 07:50Z

## Command

This session runs on trinity-3-8 and owns the distillation lane only. The trinity-3-13 session owns
every other lane, including the sam3 daemons, the vLLM servers and the experiment request queue's
other rows; this session never touches that state and never runs `git status` in
`/home/jjyeung/agent_project`. Lane root (P below):
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`. Collector control root (R
below):
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
Target sets live under (S below) `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918`.
Devin builder lanes live under (L below) `/home/jjyeung/agent_project/agent/scratch/devin_lanes`.

This is a state checkpoint, not a pass-off. The session keeps command. A successor who must take
over starts at section 8 (watchers to re-arm) and section 9 (pending tasks).

User rulings since the 15:30Z checkpoint of 2026-09-20 that bind this one: run the teacher collector
at about 4 million input tokens per minute, which is 44 workers, pinned (2026-09-21 01:40Z); Claude
sessions and their subagents now have ssh, so cross-node work no longer routes through Codex Luna;
trinity-0-3 and trinity-0-8 are reported back online (0-3 answers but its cards are occupied; 0-8
refused ssh when probed). Every earlier ruling stands: the collector and the two student fine-tunes
win over ablations; never wait on an unresponsive node; evidence first, reported whether or not it
beats the base; paper-ready numbers by 2026-09-24Z.

## 1. State of the goal

The goal is unchanged: at least 20,000 accepted VSIBench training traces from the ground-truth
perception teacher; OneThinker-8B and Qwen3.5-9B fine-tuned with vision and language LoRA on a
scene-disjoint split of targets built from those traces; RGB-only, tool-free accuracy above the base
checkpoints on VSIBench and VSTIBench, reported per question type.

### Headline: the collector recovered from a one-hour pool block and holds 44 workers; two corrected target sets passed independent review (v2.4.3, then v2.5); a reviewed OneThinker pair and the Qwen v2.5 student are trained; the first evidence table shows the matched control barely above base, and the corrected-format tables land this morning

**Collector.** The live counter read 18,183 finalized at 06:48Z and rises about 387 per hour. The
counter overstates accepted traces (section 2), so the strict 20,000 mark falls between 2026-09-22
13:00Z and 2026-09-23 00:00Z (estimated 06:25Z, uncertain).

**Targets.** Four consecutive reviews had failed on converter correctness. v2.4.3 broke that run at
03:21Z and v2.5 followed at 05:57Z with 1,155 training rows across five question types. v2.5 is the
current training set. It still holds no distance, size, room-size or route rows; the v2.6 builder is
adding the distance and size families now.

**Students.** Four OneThinker adapters are published: a diagnostic pair on v2.4.2 (corrected targets
and the matched v1c control) and a reviewed pair on v2.4.3. Qwen arm A r6 is published and
republished for the evaluation harness. Qwen v2.5 published at 07:44Z. The OneThinker v2.5 launcher
was waiting on trinity-0-23 for clean cards at 07:44Z. Qwen arm C is at step 232 of 288.

**Evidence so far.** One table exists: the matched control (RUN B) on VSIBench scores 33.71 strict
against base 31.47 strict and 39.19 lenient, and against arm C's 42.35 (section 5). The corrected
run's table (RUN A) is due about 08:40Z (estimated 07:30Z).

## 2. Collector

**Outage and recovery.** A stray file inside `collector/` failed the package census at 01:15Z; three
strikes wrote `BLOCKED.json` and the pool stopped drawing until 02:13Z. Recovery lane:
`P/claude_collector_recovery_20260921T0135Z/out/` (`RECOVERY_LOG.md`, `BABYSIT_LOG.md`,
`GUARD_LOG.md`, `package_dir_guard.py`). The controller came up at 02:12:49Z and the first new trace
finalized at 02:21:22Z. The supervisor's first tick rereads every terminal trace (about 8 GB over
NFS) before it does anything else, and the warm asset rehash took four minutes; a relaunch that
looks hung for ten minutes is probably reading.

**Processes on trinity-3-8.** Supervisor `watchdog_v5_remediation.py` pid 195531; controller
`collect.py start` pid 233991; package-directory guard pid 199208, which renames stray untracked or
ignored files out of `collector/` and logs each rename. The old lease keeper (pid 178090) exited at
02:28:38Z on a kill the user issued. The obsolete watch16 watcher (pid 3063625) is retired, with a
note in `P/claude_collector_relaunch_20260920T1330Z/out/ALARM_COLLECTOR.md`.

**The 44-worker pin.** The supervisor adds 8 workers per 10 clean minutes toward a hard-coded 64. It
reads only `enabled` and `workers` from `R/watchdog_control_v5.json`, and a `workers` value that
differs from its own latches `cooldown` and stops the ramp. This session wrote `workers: 44` at
02:51:05Z (atomic replace, nothing else changed); the resize finished at 02:54:08Z and
`R/WATCHDOG_HEALTH.json` has shown `target: 44, cooldown: true` since. Do not write the control file
again unless the user changes the budget or 429s appear.

**Rates and health.** Two-hour watch 04:48Z to 06:48Z: 17,407 to 18,171, 387 per hour, zero
rate-limit lines in `R/controller_v5.log` (that log has not been written since about 02:15Z; its
`Error` lines date from the outage). A slow stretch around 05:30Z came from heavy episodes (20 to 28
CPU-minutes each), not a fault. The 44 episodes use about two cores each, so trinity-3-8 runs at load
50 to 100 on 96 cores.

**Step-down rule.** If 429 or `RESOURCE_EXHAUSTED` lines appear in any 15-minute window, step down by
8 workers; REQ-234 on the shared key keeps priority. The other session was told in
`P/INBOX_TO_NONTRAINING_ORCHESTRATOR_20260921T0255Z_collector_pinned_44.md` and answers through
`P/INBOX_FROM_*` files.

**Counter versus accepted.** The last census (2026-09-20 20:19Z) found 8,481 strict and 9,349
tolerance-tier accepted of 11,101 attempted while the counter read far higher; accepted runs at 0.59
to 0.64 of the counter and the gap is unexplained. A fresh census is due. It is a bulk read of
`/data2`, so it runs after the v2.6 render finishes, one bulk job at a time.

**Next-epoch code items** (never on `main` while the collector runs): run episode tool code from a
scratch working directory so it cannot drop files in `collector/`; count strikes per epoch; make the
census error name the offending file; make the supervisor's package path configurable. Root B
(r1316, sealed at f053b9b) binds after root A drains.

## 3. Target lineage

| Set | Commit and branch | Rows admitted / train / held-out | Review | Notes |
|-----|-------------------|----------------------------------|--------|-------|
| v2.4.2 | 195bc60 | 860 / 760 / 100 | FAIL 02:07Z on three constructed gate counterexamples; no wrong admitted row | Exhaustive replay `P/claude_compact_v242_exhaustive_replay_20260921T0210Z/out/EXHAUSTIVE_REPLAY.md`: answers 860 of 860; nine rows with sourcing or unit-label blemishes (eight train). Ruling file beside it. |
| v2.4.3 | 0f086eb04172ca3ee2e35f5f2872bd478fc1b779 on `compact-v2-4-3-20260921` (lane `L/devin_compact_v243_clone`) | 659 / 570 / 89 (114 train rows in each of five types) | PASS 03:21Z, `P/claude_compact_v243_review/out/verdict.json` | Set `S/diagnostic_set_compact_v2_4_3_20260921_full`; MEMBERSHIP sha256 e90f2e308f6317ba559b2272c604447b1a67bc3511b68b38b6e5117654f34b64; split digest a901a0b0…34c086. The builder's own report says FAIL only because one heartbeat gap reached 309 s; every content check passed. |
| v2.5 | 5411443032a449fe6d3181b0aab2ca07c88fa55d on `compact-v2-5-20260920` (lane `L/devin_compact_v25_clone`, round 6) | 1,378 / 1,155 / 223 (231 train rows in each of five types) | PASS 05:57Z, `P/claude_compact_v25_review/out/verdict.json`; receipt `codex_runs/20260921T053328Z_compact_v25_review_20260921` | Set `S/diagnostic_set_compact_v2_5_20260921_full`; MEMBERSHIP sha256 begins 84145144; split digest 67f1172c5193c931bd8dd621f9965439b9763bed3804f61bf96046add3f36e5b. **Current training set.** |
| v2.6 | branch `compact-v2-6-20260921` off 5411443 (lane `L/devin_compact_v26_clone`, worktree `work/compact_v2_6`) | building | not yet dispatched | Launched 05:36:31Z (wrapper pid 717043, Devin pid 717044). Heartbeat 07:27Z: waiting at the render I/O gate. |

v2.5 per type, admitted / train / held-out: counting 279 / 231 / 48; appearance order 283 / 231 /
52; relative direction easy 304 / 231 / 73, medium 257 / 231 / 26, hard 255 / 231 / 24. Absolute
distance, relative distance, object size, room size and route planning have zero rows.

**How v2.5 was built.** The code that produced the archived targets is lost: commits e8fb89e and
5708469 exist in no repository. Round 6 therefore dropped the hard byte-parity gate for a two-path
construction. Frozen rows come only from the archive path
(`/data2/jjyeung/agent_project_data/devin_lane_out/converter_zero_call_v3_20260918_out/diagnostic_set/recovery_20260919_0309Z/targets/<qid>/`),
so the 659 reviewed v2.4.3 rows stay byte-identical. Extension rows (719) come from fresh ingestion
under the cherry-picked reviewed gate. Source-observation parity stays hard at 3,431 of 3,431, and an
oracle replays every admission.

**v2.6 plan.** It adds a fail-closed derived-measurement class for distance and size rows, holds the
five existing families at 231, and reports cap headroom. When `L/devin_compact_v26_clone/out/REPORT.md`
lands: rule on its `PREPARATION_STEPS.json` (NaN filter, zero-length guards); consider a supplement
that spends the cap headroom; dispatch one independent Astra review at `--effort xhigh` reusing
`P/claude_compact_v25_review/BRIEF.md` with paths changed; retrain both students only after PASS.

**Provisional orchestrator rulings awaiting the user's confirmation.**
1. A scalar distance returned by a tool is a legitimate observation that a target may cite.
2. Coverage does not gate a review; the review protects against wrong targets, not few targets.
3. Relevance rule: a reviewer's newly constructed counterexample blocks only if a real admitted row
   instantiates it; otherwise it becomes a hardening note for the next version.
4. The v2.4.2 pair trained as a diagnostic with a stated caveat (review FAIL on gate closure; replay
   860 of 860; 8 of 760 training rows blemished).
5. The two-path construction replaces hard byte parity in v2.5.
6. Qwen trains once, on v2.5; the Qwen v2.4.3 run was dropped after its card faulted.
7. Evaluation priority (section 5): the v2.5 students come first; matched-format ablations give way
   when cards are short.

## 4. Student runs

Every OneThinker run uses arm C's configuration: LoRA r=32, alpha 64, dropout 0.05 on all text
attention and MLP, vision attention and MLP, and the mergers (104,987,648 trainable parameters);
AdamW, learning rate 1e-4, cosine schedule with 3 percent warmup, no weight decay, clip 1.0,
effective batch 32, 3 epochs, bf16, sequence cap 16,384, target cap 8,192, DDP world 4. Qwen runs
FSDP at world 6 with the same 36 shared fields. Trainer b084aaf (`--inherit-split`; checkpoint
cadence recorded in `run_control`). The original OneThinker recipe, for comparison, is
full-parameter SFT at 1e-5 with the vision tower frozen, batch 32, cutoff 16,384
(`P/claude_onethinker_original_hparams_20260921T0605Z/out/ORIGINAL_ONETHINKER_HPARAMS.md`); a
language-only LoRA ablation is an option the user has not asked for.

| Run | Student, targets | Publish path | Status | Adapter weights sha256 |
|-----|------------------|--------------|--------|------------------------|
| Arm C | OneThinker, v1c compact (3,052 rows) | see the 2026-09-20 handoffs | published 09-20; evaluated | n/a here |
| RUN B | OneThinker, matched v1c control, 760 rows | `/data3/jjyeung/ddp_onethinker_v1cm242_onethinker_20260921T0145Z` | published 02:59:45Z | 8e198d72… |
| RUN A | OneThinker, v2.4.2, same 760 qids | `/data3/jjyeung/ddp_onethinker_v242_onethinker_20260921T0145Z` | published 04:01Z; diagnostic with caveat | 52e57f8f… |
| RUN A3 | OneThinker, v2.4.3, 570 rows | `/data3/jjyeung/ddp_onethinker_v243_onethinker_20260921T0330Z` | published 05:37:33Z, verify ACCEPTED, 736 tensors, final loss about 0.145 | d2635e46…81cd93 |
| RUN B3 | OneThinker, matched v1c control, same 570 qids | `/data3/jjyeung/ddp_onethinker_v1cm243_onethinker_20260921T0330Z` | published 06:00:38Z; verify line not yet received | unknown |
| Qwen arm A r6 | Qwen, format A (dense) | `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6`; republish `/data3/jjyeung/ddp_qwen35_a_qwen_20260920T0400Z_r6_republish_20260921T041852Z` | published 03:58:42Z; republish ACCEPTED by harness 58794b8 | PUBLISHED sha ed55dde8… |
| Qwen arm C | Qwen, v1c compact | trains on trinity-0-13 GPUs 0 to 5 | step 232 of 288 at 07:28:51Z, 277 s per step, checkpoint step_225; finish about 11:45Z (estimated 07:30Z); needs the same cadence republish | n/a |
| Qwen v2.4.3 | Qwen, v2.4.3 | none | stopped at step 14 of 54 when trinity-0-23 GPU 2 faulted; dropped | n/a |
| Qwen v2.5 | Qwen, v2.5, 1,155 rows, 111 steps | `/data3/jjyeung/ddp_qwen35_v25_qwen_20260921T0530Z` | launched 06:01:03Z on trinity-0-23 cards 0,1,3,4,5,6; 52.7 s per step; `PUBLISHED.json` at 07:44Z; verify pending in the evaluation lane | unknown |
| OneThinker v2.5 | OneThinker, v2.5, 111 steps | `/data3/jjyeung/ddp_onethinker_v25_onethinker_20260921T0530Z` | launcher `run_otv25.sh` (pid 208804 on trinity-0-23) waiting for three clean readings at 07:44:19Z, `OTV25_GPUS="0,1,3,4"`; about 1.2 h once it starts | n/a |

Staging and launch records: v2.4.2 pair `P/claude_onethinker_v242_launch_20260921T0145Z/out/`;
reviewed pair `P/claude_onethinker_v243_launch_20260921T0330Z/out/` (the `_t023` launcher copies and
`launch/DIFF_RECEIPT_T023.md`); Qwen v2.4.3 `P/claude_qwen_v243_launch_20260921T0330Z/out/`
(`run_qwen_v243_r3.sh` carries the lease-issuer fix that skips card 2); v2.5 students
`P/claude_v25_students_launch_20260921T0530Z/{qwen,onethinker}/out/` (`READY.md`, `CPU_GATE.md`,
`GATE_FACTS.json`; Qwen launch records and stall alarm under `qwen/out/launch/`); Qwen arm C
heartbeat `P/claude_qwen_resume2_20260920T1445Z/out/HEARTBEAT_c1_resume2.log`.

## 5. Evaluations

Harness 58794b8: instructed prompt, 4,096-token budget, strict parser primary with lenient
sensitivity, RGB only, 32 frames, greedy. Its acceptance gate refuses adapters whose protocol
`training` block holds `checkpoint_every_steps` (trainer ad96f47); the reviewed remedy is a cadence
republish into a new `/data3` directory that leaves the original byte-unchanged
(`P/claude_trainer_publish_cadence/out/QWEN_R6_NOTE.md`). Adapters from trainer b084aaf should need
no republish; the Qwen v2.5 evaluation lane proves that before it launches.

| Evaluation | Lane dir | Cards | Progress at last reading | Done marker and tables |
|------------|----------|-------|--------------------------|------------------------|
| RUN B | `P/claude_onethinker_v242_eval_20260921T0300Z/out/` | none now | VSIBench done; VSTIBench held (preflight passed, no lease) | `RESULTS_VSIBENCH_V1CM242.md` |
| RUN A | same root, `out_run_a/` | trinity-1-13 cards 2 to 4 | VSIBench 402 of 500 at 07:28:57Z, 86 items per hour; table about 08:40Z (estimated 07:30Z); VSTIBench follows on the same cards | `EVAL_A_DONE`; `RESULTS_VSIBENCH_V242.md`; progress `EVAL_A_PROGRESS.log` |
| RUN A3 | same root, `out_run_a3/` | trinity-1-13 cards 5 to 7, since 06:10:28Z | VSIBench 167 of 500 at 07:28:50Z, about 102 per hour; table about 10:45Z (estimated 07:30Z) | `EVAL_A3_DONE`; `RESULTS_VSIBENCH_V243.md`, `RESULTS_VSTIBENCH_V243.md`; progress `EVAL_A3_PROGRESS.log` |
| Qwen arm A r6 | `P/claude_qwen_r6_eval_20260921T0400Z/out/` | trinity-0-23 card 7 | VSTIBench 93 of 450 at 07:29:29Z, about 30 per hour; VSIBench not started | `EVAL_R6_DONE`; progress `EVAL_R6_PROGRESS.log`, `RATE_r6_vsti.log` |
| Qwen v2.5 | `P/claude_qwen_v25_eval_20260921T0735Z/out/` | trinity-0-23 cards 5, 6 | lane dispatched 07:35Z; nothing verified yet | `EVAL_QV25_DONE`; `RESULTS_VSTIBENCH_QV25.md`, `RESULTS_VSIBENCH_QV25.md`; `PUBLISHED_VERIFY_QV25.md`, `ACCEPTANCE_58794b8_qv25.txt`, `DIFF_RECEIPT_QV25.md`, `HANDOFF_QV25.md` |
| Unscheduled | | | RUN B3 (both benchmarks), RUN B VSTIBench, OneThinker v2.5, Qwen arm C | |

Measured rates: OneThinker 29 to 34 items per GPU-hour on VSIBench for these adapters (earlier
readings of 45 to 60 came from short windows; the first minutes of any shard read about three times
too fast); Qwen about 27 to 32 on VSTIBench and about 16 on VSIBench. One Qwen adapter costs about
46 GPU-hours across both benchmarks.

**Priority ruling (provisional).** The v2.5 students are the partial-set evidence the goal asks for,
so their evaluations take cards first. When OneThinker v2.5 publishes, its evaluation takes
trinity-0-23 cards 0,1,3,4 and preempts RUN A's VSTIBench on trinity-1-13 cards 2 to 4 (shards
resume). The A3 against B3 comparison is a format ablation and runs second; RUN A and RUN B VSTIBench
run last or not at all.

**The one table that exists: RUN B (matched v1c control, 760 rows), VSIBench answerable 500.**
Overall strict: base 31.47, arm C 42.35, RUN B 33.71. Overall lenient: base 39.19, arm C 42.35, RUN B
33.71. Of RUN B's 500 generations, 67 hit the 4,096-token cap with no answer.

| Question type | Base strict | Arm C strict | RUN B strict |
|---------------|-------------|--------------|--------------|
| appearance order | 52.0 | 56.0 | 48.0 |
| absolute distance | 12.8 | 36.8 | 29.8 |
| counting | 21.6 | 41.6 | 29.6 |
| relative direction easy | 36.0 | 58.0 | 56.0 |
| relative direction medium | 36.0 | 40.0 | 32.0 |
| relative direction hard | 22.0 | 16.0 | 22.0 |
| relative distance | 42.0 | 48.0 | 40.0 |
| object size | 45.0 | 52.0 | 31.8 |
| room size | 21.0 (lenient 51.8) | 38.4 | 27.8 |
| route planning | 26.0 | 28.0 | 26.0 |

RUN B loses most on types its 760 rows do not contain. Earlier result kept for reference: arm C on
VSTIBench scored 43.59 against base 40.16, with parse-failure caveats recorded in the 2026-09-20
handoffs.

## 6. GPUs

| Node | Cards | Holder at 07:45Z |
|------|-------|------------------|
| trinity-0-23 (8 x RTX 6000 Ada) | 0, 1, 3, 4 | OneThinker v2.5 launcher is claiming them |
| | 2 | **FAULTY.** Two `Xid 109 CTX SWITCH TIMEOUT` faults (PCI 0000:41:00), at 23:52Z 09-20 and about 04:24Z 09-21. Never place work on it. Another user ran a 5.5 GB process there at 07:44Z. The user may want to tell the admins. |
| | 5, 6 | Qwen v2.5 evaluation lane is claiming them |
| | 7 | Qwen arm A r6 evaluation (pid 206749) |
| trinity-1-13 | 2 to 4; 5 to 7 | RUN A evaluation; RUN A3 evaluation. Cards 0 and 1 belong to other users. |
| trinity-0-13 | 0 to 5; 6 | Qwen arm C fine-tune; the other session's sam3 daemon |
| trinity-3-8 | none used | collector and this session (CPU) |

Idle cards on shared nodes go within 40 seconds to 12 minutes: another user took trinity-1-13 card 1
forty seconds after RUN A released it, and a seven-process job from another user sat beside our Qwen
run on trinity-0-23 for about 50 minutes. Launchers therefore start before the cards free up and
wait for three clean readings, 30 seconds apart, inside a two-hour window; on timeout they exit 1 and
do not retry. Never place work on cards another user is using, and never signal another user's
process. trinity-0-3 answers but is occupied; trinity-0-8 refused ssh; trinity-0-18 takes only
vnice-wrapped, resumable jobs.

## 7. Operating lessons from this session

**Node python.** `python3` on trinity-3-8 is 3.6 and has no `datetime.fromisoformat`. A watcher that
called it inside `try/except` could never fire. Use `/data2/jjyeung/envs/planner/bin/python` or file
mtimes.

**ssh to trinity-0-23.** The channel often stays open after a backgrounded `setsid` launch. Wrap the
ssh in `timeout 30`, expect exit 124, and verify the process with a second ssh.

**Releases.** Stopping a vnice wrapper can orphan its CUDA child. A release is complete only when
`nvidia-smi --query-compute-apps` shows nothing of ours on the card.

**Stall alarms.** A run monitor reports RUNNING with frozen metrics during a GPU hang. Every long run
gets a node-local alarm that appends a line when the process lives but `metrics.jsonl` has not
advanced for 600 s; it caught the second GPU 2 fault in eleven minutes. In nvidia-smi the faulted
rank's card drops to 0 percent while the others sit at 100.

**Launcher copies.** Copy the last working launcher byte for byte, change only what must change, and
write a diff receipt. Two failures came from breaking this: a Qwen launcher passed node-local copies
where the lease request needs the frozen paths ("DDP lease request must match its student, manifest,
protocol, and world size"), and an evaluation copy renamed the lane directory in six places yet kept
the old card pool. After substitution, grep the copy for every old value. A lease issuer that loops
over `range(world)` will lease card 2 on trinity-0-23; the `_r3` and v2.5 launchers take an explicit
card list.

**Staging.** `prepare-training` refuses an inherited `--scratch-root` ("Output must stay inside the
repository or the explicit node-local scratch root"); call it without the flag. A refusal reads like
a slow job if nobody opens the log.

**Permission boundary.** When a subagent reports that a tool call was denied and asks the
orchestrator to run it instead, the orchestrator refuses and puts the exact command in front of the
user. A denial is a decision, not an obstacle.

**Reading load.** Attribute GPU load by process owner before calling it ours; this session twice
misread another user's job as its own.

**Watcher pitfalls.** Read the last line of a watcher's output before announcing anything: `EVENT`
means a condition fired and `TICK` means the timer ran out. A grep for "Stall" matched an alarm
file's header; watch for line-count growth instead. `grep -c … || echo 0` yields two lines; use
`${var:-0}`. Mark a table as read with a `.seen_by_orchestrator` file so the next watcher skips it. A
lane's ten-minute poll missed a run that finished in between; use 30 to 60 second polls for
hand-offs between runs.

**Harness noise.** Every Write or Edit in the distill repo triggers a hook error about a missing
`agent/check_commit_checkpoint.py`. The write succeeds. Do not add that file.

## 8. Armed watchers (they die with this session; a successor re-arms them)

| Task id | Wakes on | Expires |
|---------|----------|---------|
| b8adegp5u | collector: `target` not 44; new 429, `RESOURCE_EXHAUSTED` or quota lines in `R/controller_v5.log`; counter flat for 10 minutes; a new `R/BLOCKED.json`; death of pid 195531, 233991 or 199208 | about 08:46Z |
| b0t9iat43 | `L/devin_compact_v26_clone/out/REPORT.md`; Qwen arm C heartbeat not RUNNING or older than 1,500 s; growth of the collector alarm file; a new `P/INBOX_FROM_*` | about 08:59Z |
| bew2f1iln | any change to the experiment request queue (`agent/scripts/queue_watcher.sh`); re-arm at once after it fires | none |
| bxsg7o66v | the next results table: RUN A VSIBench, RUN A3 VSIBench or RUN B VSTIBench | two hours from its start, which I could not recover from context |
| baoj4pn3l | OneThinker v2.5 `PUBLISHED.json`, or an `ALARM*.md` under its `launch/` directory passing six lines | about 10:15Z |

Node-local helpers that outlive the session: the package-directory guard (pid 199208 on
trinity-3-8); the Qwen v2.5 stall alarm on trinity-0-23 (pid 184982, which may have exited with the
run); the evaluation drivers and progress loggers of each evaluation lane.

Live lane directories a successor adopts: the collector recovery lane; the three evaluation roots in
section 5; `P/claude_v25_students_launch_20260921T0530Z/onethinker/out/launch/` (OneThinker v2.5
babysit notes and, at publication, `PUBLISHED_VERIFY.md`); `P/claude_qwen_v25_eval_20260921T0735Z/out/`;
`P/claude_qwen_resume2_20260920T1445Z/out/` (Qwen arm C); `L/devin_compact_v26_clone/`. Subagent ids
do not survive the session; the directories and their logs do.

## 9. Pending tasks, in priority order

1. Hold the collector at 44 workers; re-arm its watcher every two hours; step down by 8 on 429s.
2. Confirm the OneThinker v2.5 launcher took cards 0,1,3,4 and steps are landing; verify its
   publication (about 09:15Z, estimated 07:35Z).
3. Confirm the Qwen v2.5 evaluation lane verified the adapter, passed acceptance and has items
   landing on cards 5 and 6. When OneThinker v2.5 publishes, start its evaluation on trinity-0-23
   cards 0,1,3,4 and on trinity-1-13 cards 2 to 4.
4. Report RUN A against RUN B against base on VSIBench per question type, with the cap-hit count,
   whether or not the corrected targets win; then RUN A3 when its table lands.
5. Qwen arm C: verify publication (about 11:45Z, estimated 07:30Z), run the cadence republish,
   evaluate.
6. v2.6: read the builder's report, rule on its preparation steps, dispatch the independent review,
   and retrain both students on PASS.
7. Run a fresh acceptance census after the v2.6 render, and reconcile it with the counter.
8. Not started: build targets from the full accepted census under the reviewed gate, then train both
   students at full scale. Paper-ready numbers are due 2026-09-24Z, so this must begin on 09-22.
9. Remaining evaluations as cards allow: RUN B3, more cards for Qwen arm A r6, RUN A and RUN B
   VSTIBench.
10. Tell the user again that trinity-0-23 GPU 2 is faulty. Ask for confirmation of the seven
    provisional rulings in section 3.
11. Land this document: fast-forward `main` to branch `handoff-20260921T0750Z` (it touches only
    `docs/` and `CLAUDE.md`, never `collector/`).

## 10. What I could not verify from context

- Whether the OneThinker v2.5 launcher acquired its cards after 07:44:19Z, and whether the Qwen v2.5
  evaluation lane has launched.
- RUN B3's verify result and weights hash; Qwen v2.5's verify result and weights hash.
- The file name of RUN A's VSTIBench table, and where the Qwen base evaluation cells live (the arm A
  evaluation lane's launch receipt names them).
- What heartbeats the collector's coordination lease since the old keeper exited; the supervisor has
  run six hours without a lease alarm, so something does.
- Whether the queue rulings and the closed-loop ledger row from the session's first instructions
  were committed in the main repository. A 19:30Z handoff commit cited in my notes as `635e1c6ee` is
  not on this repository's `main`, whose head was 37b1a5b when this branch was cut.
- The full 64-character forms of the hashes abbreviated above; each publish directory's
  `PUBLISHED.json` and `SHA256_MANIFEST.json` hold them.
