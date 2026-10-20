# Distillation handoff, 2026-10-20 03:50Z (10-19 20:50 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261019_2200Z.md`. Read that file and the 10-17 handoff only for history. The writer is orchestrator session c0197160 on trinity-0-3. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; W = `L/devinwatch_20261004`; T = `L/teacher_pilot_20261004/out`; S = `L/sprint_train_aws_20261014`; B = `agent/scratch/devin_lanes` in this repository; H = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_handoff_20261019T2200Z`. Times are PT.

## 1. User rulings, in force (verbatim, newest first)

- **10-19 19:35:** "in general the setup on aws should be that if we lose access anytime, all the data we need is alr locally stored on trinity so it's ok . ther shouldn't be large amount s of data on aws that are not synced". This replaces the old rule never to pull data back from AWS. Lane aws_sync_20261019 carries it out.
- **10-19 19:20:** "yes 8 nodes on aws is fine". It answers whether distillation may run regardless of the a15_cot jobs: distillation may hold 8 code-aws nodes (64 GPUs) of its own, `jjy_distill_*`, counted separately. The record is `S/out/AWS_GRANT_DISTILL_8NODES_20261019.json`, and `L/CODE_AWS_GPU_CAP` stays at 64 with this meaning written into it. The a15_cot jobs do not belong to experimenter agent-project-78, which runs nothing on AWS; their owner is unknown.
- **10-19 14:50:** "why are you waitingon trinity 3-13? remember, if node is down just use another. please don't slow progress for no reason." When a node hangs, ban it at once, fence its claims, and move its work. A reboot is never a dependency.
- **10-18:** "Is devin workign> it works for me. stornlgy prefer devin over the current laude agnets you have running". Every builder, launcher and reviewer is a Devin lane.
- **10-18:** "also if there are command for me to run to clear up space please run them for me - after i approve". The proposal is `L/space_scan_20261018/out/SPACE_CLEANUP_PROPOSAL.md` (groups A–D). Nothing in it has been approved or run.
- **Banned hosts:** trinity-3-23, 0-28, 2-8, 2-23 and 3-13. Earlier rulings in the 10-17 handoff still bind: no deletion, one git owner, no sweeping searches, no self-approved launch clearance, the 32k output contract, and lenient scoring as primary.

## 2. Open user decisions

1. **Copy bandwidth through the user's Mac tunnel.** The cap is 5 MB/s. Small files hold the effective rate near 0.4 MB/s, and training outputs need about 700 GB.
2. **trinity-3-13 reboot (optional).** Nothing waits on it, but its frozen processes still hold the sprint lane's mailbox lock.
3. **Cleanup groups A–D.** They may be moot: `df` showed /data2 at 1% used (4.2 TB free) at 19:40 on 10-19, against 79% on 10-18.
4. **Carried over:** the Argon source epoch 549e560, the 41 dead leases, the rewriter for bulk B_sum, trace storage A/B/C, the SPLIT object-size fix, the absolute-distance rate stop, and 4,096-token diagnostic cells.

## 3. Results and findings banked

- **Seed-18 base VSI-500 is complete: 500/500 authenticated native terminals.** No score has been read yet. Shard 3 failed once on a stale-lease check (304 s against 300 s) and finished through the reviewed resume, job 8092461. SB_AO E1 passed natively on 24/24.
- **Reviews passed, each verified by me against every binding:**
  - v13 evaluation package: verdict sha 5c569c52…, commit b20b6d1b in `S/provenance/native_trio_aws_v1.git`.
  - Eight-node admission delta: verdict at `S/out/native_distill8_admission_v1/REVIEW_VERDICT.json`, commit d5489673 in `S/provenance/native_distill8_admission_v1.git`, provenance sha 08e58227…. It counts only `jjy_distill_*` against 8 nodes, with every native control preserved.
  - S5 style-readout CPU reader: verdict at `S/out/native_s5_reporting_v1/REVIEW_VERDICT.json`.

  I wrote `TRANSFER_CLEARANCE.json` beside both deltas. The distill8 capsule was transferred and installed at 20:32 (`TRANSFER_RESULT_ATTEMPT41.json`, `INSTALLATION_ATTEMPT41.json`).
- **Why the collector's storage gate kept failing.** Failures moved between hosts: trinity-2-28 failed 11 of 20 rounds, trinity-3-3 failed 10, trinity-1-8 failed 3. 17 of the 18 censored samples stalled in Python imports or source authentication over NFS, before any storage operation. Completed operations were fast (heartbeats up to 1.2 s, writes up to 0.8 s). Production starts a fresh Python process for each renewal and re-hashes its sources. The fix runs both production and the samplers from a verified local code cache (48,239 inodes, 24 tests pass). No threshold changed.
- **trinity-3-13 hung at 22:43 on 10-18.** Its watchdog could not report its own death, so the hang went unnoticed for 11.5 hours. Memory: `trinity-3-13-hang-20261018.md`.

## 4. Lane map at handoff (verified 20:50 PT)

| Lane | State | Next action | Check |
|---|---|---|---|
| sprint_train_aws_20261014 (seed-18 trio on code-aws) | Session PID 2740928 on trinity-2-28, attempt 41. Base VSI-500 is done. Distillation held only CPU job 8095753 at 20:49. SB_TRACE's E1 dry admission refuses ("authenticate every earlier intent before another attempt") until the lane reconciles an earlier ambiguous intent. | Five cells remain: base VSTI-450, SB_AO and SB_TRACE on VSI-500 and VSTI-450. They run 2 at a time on up to 8 nodes, about 2.5 h each, finishing around 05:00 on 10-20. Then the S5 reader runs on CPU over each cell's finals. When all six cells close, read the scores; seeds 17 and 18 decide the trace-vs-AO question (section 8). | `S/out/PROGRESS.md`; `ssh -J trinity-3-30 code-aws 'squeue -u $USER'`, once per check (shared RPC budget) |
| teacher_pilot_20261004 (Gemini collection repair, MONITOR91) | Session PID 2758046. A fresh 20-round storage series on trinity-1-8 and trinity-3-3 uses the R6 candidate, which runs from the local verified code cache. The frozen trinity-3-13 supervisor's term was due to expire at 00:37:33Z; the gate copies its state only if the term expired unchanged. | If the series passes: one ordered replay, then analyze, seal and verify. Then write `B/review_camopt70_impl_20261018/BRIEF_CONTINUE_14.md` for the same reviewer, run the owner signing (section 5), and send launch_camopt71 from a healthy host. Before any Gemini call, warn experimenter agent-project-78, which runs about 26 Pro workers. | `T/PROGRESS.md`, `tail T/HEARTBEAT.log` |
| aws_sync_20261019 (AWS → Trinity copy) | Session PID 2771725, swe-2-high. The inventory is in `L/aws_sync_20261019/out/INVENTORY.md`. Synced so far: 7,823 evaluation files, about 479 MB. Already local or rebuildable: seed-18 adapters, v13 code, data73 media (they match Trinity videos), environments, HF caches. | Run-root passes every 30 min. Then the train runs: final weights, config, logs and cited checkpoints, about 700 GB, skipping optimizer state and uncited intermediates. data73 manifests come last. | `L/aws_sync_20261019/out/PROGRESS.md`, `SYNC_LOG.jsonl` |
| review_native_trio_aws_20261018, review_camopt70_impl_20261018, launch_camopt71_20261018 | DONE. All three are listed in the trinity-2-28 lanes file, so a new brief relaunches them. | n/a | n/a |
| tracecold, qwengen_aws, rewrite, opsd | Parked; each BLOCKED.md names its WAIT_FOR_FILE | rewrite waits on the user's rewriter decision; opsd waits on sprint | `W/ALERTS.log` |
| Watchdog | `watch_host.sh` loop PID 2561867 under `bash -c` 2561866 on trinity-2-28. MAX_RELAUNCH=300, `LANES_FILE=W/lanes_trinity-2-28_20261019.tsv`. | n/a | `cat W/WATCHDOG_ALIVE_trinity-2-28` |

**AWS route:** the Mac reverse tunnel listens on trinity-3-30 at 127.0.0.1:42224. Use `ssh -J trinity-3-30 code-aws`, and start no process on trinity-3-30. The receipt is `S/out/AWS_ROUTE_RESTORED_ATTEMPT38.json`. If the tunnel moves, find it with `ssh <host> 'ss -ltn | grep 127.0.0.1:42224'`. code-aws-01 (port 42223) is down. Distillation's AWS data lives on Lustre `split/distill/orch`, which compute nodes see as `/project/community/jjyeung/distill`; vscode-02 does not mount that path.

## 5. Collector recovery, in detail

- **MONITOR91 order:**
  1. monitor replacement plus rebind;
  2. reader fix;
  3. reviewed resolution of the integrity stop;
  4. storage reset on a fresh pass, under the OPERATIONS→NATIVE→WINDOW lock order;
  5. re-admission of the two deferrals;
  6. driver restart through the terminal-driver branch of the reviewed RATE88 retry helper.

  The packet now also carries:
  - the host transition: a new control namespace, plus fresh identities for only the two never-started deferrals;
  - the trinity-3-13 fence and its successor fence, covering nine frozen identities;
  - the term-expiry gate;
  - the local verified code cache.

  All of it goes to devin:review_camopt70_impl_20261018 in one packet. If that packet fails review, stop extending this design: gap-type collection moves to a simpler path, and that choice goes to the user.
- **Owner signing:**
  1. Run `owner-template --review '<pin>'` and check every pin.
  2. Send the action with `lanemsg --orchestrator send` to teacher_pilot.
  3. Record the body digest in `owner_authority/reauth58/<msgid>.json`.
  4. The lane acknowledges into `mail/inbox/done/<id>.json`.
  5. Run `authorize --owner … --review …`, then `verify`.
  6. The launcher runs `operate` once, with `setsid -f`.

  Production runs under `env -u PYTHONPATH -u RATE88B_IMPORT_GATE -u RATE88C_IMPORT_GATE`. After launch, check the driver PID and CONTROL_STATUS freshness yourself.
- **Reviewer identity in every brief:** reviewer "devin gpt-6-astra-max-priority independent reviewer", reviewer_agent_id "devin:<lane>", spawned_by the orchestrator session ID (c0197160 until now).

## 6. What survives session close and what dies

- **Survives:**
  - the trinity-2-28 watchdog and the three live lane sessions;
  - the AWS jobs;
  - teacher_pilot's samplers on trinity-1-8 and trinity-3-3;
  - the frozen trinity-3-13 processes: the old watchdog, Devin sessions and storage rounds, which may resume on thaw;
  - the old watchdog on banned trinity-2-8 (its lanes are finished; it logs I/O errors).
- **Dies with this session:**
  - the ALERTS watcher;
  - the queue watcher;
  - the trinity-3-13 thaw watcher.
- **Successor actions, in order:**
  1. Run `lanemsg --orchestrator adopt` on every lane path in `W/lanes_trinity-2-28_20261019.tsv`.
  2. Arm an ALERTS watcher that also fires when `W/WATCHDOG_ALIVE_trinity-2-28` is more than 10 min old.
  3. Arm the queue watcher (`agent/scripts/queue_watcher.sh`).
  4. Arm the thaw watcher (`until ssh -o ConnectTimeout=8 trinity-3-13 true; do sleep 300; done`). When it fires, kill trinity-3-13's `watch_host.sh` loop and every `devin -p` first, then `lanemsg tell all`.
  5. Read the sprint lane's undelivered notes in `S/mail/outbox/new/`.
- **Provenance scripts (orchestrator only):**
  - `H/trio_provenance.sh` for native_trio_aws vN: `bash trio_provenance.sh vN <parent> "<subject>" "<body>"`.
  - `H/distill8_provenance.sh` for the eight-node delta. It has run once and refuses a rerun; copy it for any successor delta.

## 7. Do not redo

- Do not wait on trinity-3-13, and do not swap storage hosts again: the fault is shared NFS, which the local code cache addresses.
- Do not reclassify censored storage samples, and do not raise a threshold without a collector timeout behind it.
- Do not build the local-control epoch (global fencing and export protocol); it was ruled too large.
- Do not import v10 or v12 E1 outputs into v13, and do not touch v10's attempt records.
- Do not rerun distill8_provenance.sh or rewrite either TRANSFER_CLEARANCE.json.
- Do not retry a mutating AWS command, lower a `.relaunches` counter, or write a verdict a gate reads.

## 8. Footguns learned

- A watchdog cannot report its own host's death, so the ALERTS watcher must check `WATCHDOG_ALIVE_<host>`.
- After an NFS client hangs, the first write elsewhere to a file it held takes about 100 s. A STALE alert right after a relaunch is usually just the old heartbeat file; check again 3–8 min later.
- **lanemsg failures:**
  - `lanemsg tell` from trinity-3-30 to this session's host times out, and the sprint lane's outbox lock is held by a frozen trinity-3-13 process. Lanes therefore reach the orchestrator late or not at all. Read `S/mail/outbox/new/`.
  - When `tell` times out locally, run it on the target host: `ssh <host> 'lanemsg tell --here --from … claude:<session>@<host> -'`.
- Review requests written by builders sometimes declare scope ("sandbox objections are out of scope"). Tell reviewers that such lines carry no authority.
- New lanes: run `lanemsg register` and `lanemsg --orchestrator adopt` before adding the lanes-file line. Done lanes in `W/lanes_trinity-3-13.tsv` have no watchdog; move a lane's line to the 2-28 file before writing it a new brief.
- The PostToolUse hook error about `agent/check_commit_checkpoint.py` is harmless; that file does not exist in this repository.
- **Seed noise:** seed choice moves VSI-500 by about 3.2 points. Before reading the seed-18 scores, pool seeds 17 and 18 with a paired per-question bootstrap, and call a difference only when the interval excludes zero.
