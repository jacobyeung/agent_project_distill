# Distillation handoff - 2026-09-24 12:30 PT (19:30 UTC)

## Headline results

The Qwen3.5-9B full-pool answer-only student scores 57.56 on VSIBench-500. The user has released the distillation GPUs to the main experiment lane, except for Orchard job 148724, which may finish unless the main lane needs its four advanced GPUs sooner. The CPU collector continues toward 50,000 traces; Qwen3.5-9B and Qwen3.6-27B are the primary students, and OneThinker work remains secondary and held.

| Result | Reported evidence and scope | Evidence time |
| --- | --- | --- |
| Qwen3.5-9B, VSIBench-500 | Lenient parser v2 gives base b16 15.50, corrected trace 48.02, corrected answer-only 55.24, and full-pool answer-only 57.56 (strict 53.36). The corrected answer-only set has 7,684 training rows and three epochs; the full-pool set has 25,164 training rows and one epoch. | Banked in FACTS; individual result times are not specified there. |
| Qwen3.5-9B, VSTIBench-450 | The all-450 full-pool score is 50.55 versus base 27.68; the corrected trace scores 43.93. On the same matched 402 questions, corrected answer-only scores 52.95, full-pool answer-only scores 50.76, and base scores 27.27. Do not compare a matched score directly with an all-item score. | Banked in FACTS; individual result times are not specified there. |
| Qwen3.6-27B | The VSTIBench b8 matched-434 arm C pair scores 52.02 versus 29.94; the unrounded delta is +22.09. The all-450 scores are 52.01 versus 28.49. The provisional VSIBench b8 base-only row at `0fe7be5` scores 19.95 lenient / 19.62 strict, with 349 cap hits; the student pair is not complete. | Five of 16 arm C student shards had finished at the Orchard release, 12:16 PT (19:16 UTC). |
| OneThinker controls, secondary | S-T scores 46.15 on VSI; N1k scores 48.32 on VSTI; N2k scores 43.73 / 49.08; s18 scores 47.88 / 51.83, versus s17 at 48.03 / 53.45. M scores 39.37 on VSI versus base 39.19. M VSTI and S-T VSTI have no completed new result. | Banked in FACTS; all Trinity GPUs were released during 12:10-12:20 PT (19:10-19:20 UTC). |
| Teacher trace census | Root A plus root B contains 29,512 distinct strict and 32,238 tier-25 traces in the reported census. The strict gap to 50,000 is 20,488. Root-B terminal count is a different measure: the collector last reported 12,172 terminals and zero 429s. | Census: 03:35 PT (10:35 UTC). Latest reported terminals: 12:13 PT (19:13 UTC). |

VSIBench denotes the Visual Spatial Intelligence Benchmark; VSTIBench denotes the Visual Spatial Thinking Benchmark. These are source-reported distillation results, not a new score-index nomination or an independent rescore by this documentation lane. Lenient scores are primary and strict scores are secondary. The FACTS appendix is authoritative for rulings, results, and state; its 12:28 PT addendum governs the release and collector summary above. All dates in the summary are September 24, 2026, unless stated otherwise; PT is UTC-7.

## What is running now and its ETA

The table records the latest supplied state, not a fresh remote health check. An expired estimate does not establish completion.

| Work | Latest reported state | ETA or next gate |
| --- | --- | --- |
| Collector | Epoch `fa7e1ec2a4f2bebb7f567f54cdc54b7e40777a0f` runs on trinity-1-13 with controller PID 95243 and keeper PID 42881. The v3 target is 8 workers on trinity-1-13 and 0 on trinity-2-13. Meter PID 2183482 and babysit PID 2183515 run on trinity-0-3; the guard was reported as PID 3297848 on trinity-3-8 at `0fe7be5`. | The experimenter's key release was expected around 14:00-15:00 PT (21:00-22:00 UTC), but only main_agent's release notice authorizes a ramp. No completion ETA for 50,000 traces is established. |
| Collector second host | trinity-2-13 cannot start because `ControllerHeartbeatStore.fresh()` races a peer heartbeat and `require_drained` refuses the live peer. The CPU fix lane is `agent/scratch/devin_lanes/collector_multihost_fix4_20260924/`. | A fix, independent review, new seal, bind, and drain-and-swap are required. ETA is unknown at handoff; check the collector handoff and that lane. |
| Orchard 148724 | The 27B answer-only setH_mb4 job remains on four H100s in advanced. All other distillation jobs were cancelled and the feeder, driver, and watcher STOP files were written, according to the FACTS addendum. | FACTS estimates publication around 15:30 PT (22:30 UTC). The user permits it to finish unless the main lane needs advanced sooner. Verify its actual state before any resume. |
| Orchard queued work | The arm C VSI student has five finished shards; its remaining shards and the answer-only evaluations are not running under the release ruling. Job 148868, the three-epoch 9B full-pool run, and the trace16 jobs were cancelled. Sampled base and cap32k cells remain gated. | Relaunch order requires a user decision after GPUs return. The full-benchmark base and student cells await a reviewed harness registration, transfer, and allocation. |
| Trinity evaluation | The lane holds no GPUs. M VSTI stopped with 333/450 preserved; the S-T resume never ran and retains 429 completed items, one interrupted item, and 20 never-started items. s19 remains held. | No GPU ETA is established. Closing the S-T lease does not authorize a new evaluation launch. |
| CPU builds and results | Portable-resume review10 returned FAIL. The full-5,130 preparation report marks the data package complete and sealed, but the harness rejects its benchmark name. Full-pool v4 and the collector second-host fix need adoption. The rescore handoff reports watcher PID 1518734 on trinity-0-3. | Repair and re-review portable resume before deployment or migration; review the full-benchmark harness registration before GPU evaluation. Check report and process ownership before adopting other lanes. |

The final rescore handoff labels 148724 cancelled/stopped and the arm C VSI student unstarted. Those statements conflict with FACTS, which retains 148724 and records five completed student shards. This summary follows FACTS; actual Slurm state is unknown at handoff to this documentation lane. Before resuming anything, reconcile `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/HANDOFF_rescore.md` with `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_lane_20260924T1030Z/HANDOFF_orchard.md` and the authoritative release record below.

## What the user must do

### Orchard release and the remaining training decision

The orchestrator has already executed the Orchard release, except for 148724. Do not repeat the old release block in the Orchard appendix: that block would also cancel the job the user chose to retain. The authoritative FACTS release record is copied here verbatim:

- Orchard: feeder STOP file touched; scancel of every distillation job EXCEPT 148724 succeeded (148857 148860 148862 148865 148869 148777-148780 148683 148749 148646 148648 148642 148644 148747 148751 148753 148756 148761 148766 148769 148774 148868); squeue shows only 148724 (27B answer-only, 4 H100 advanced, running 5 h 20 min, about 3.3 h left, finish about 15:30 PT; the user chose to let it finish unless the main lane needs advanced sooner; resume costs about 1 h prepare plus at most 25 steps). trinity-0-3 driver/watcher STOP files touched at 12:28 PT.

When GPUs return, decide whether to resume 148724 if it was interrupted, resubmit 148868, run the full-benchmark base and full-pool student cells, or prioritize trace16, and specify the order. The 148724 run name is `qwen36_27b_ao_setH_mb4_20260924`; its deployment is `/project/community/jjyeung/distill/code/deployment_433d8a1_ao27b_setH_mb4_qwen36_27b_ao_setH_mb4_20260924`. Its checkpoint directory is `/project/community/jjyeung/distill/runs/qwen36_27b_ao_setH_mb4_20260924/checkpoints/`. The Orchard handoff says that the same run name, frozen configuration, and launch identity restore the latest checkpoint. Its exact original submission is recorded in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_lane_20260924T1030Z/work/mb4_submit.log`; that file was not an input to this document, so a complete resubmission command is unknown at handoff. Do not infer a new deployment or submit a duplicate job.

### S-T lease closure: user action or authorized launcher

The S-T worker lease is still marked running after its last heartbeat at 01:54:32 PT (08:54:32 UTC). The evaluation handoff records this command verbatim:

`coord.py fail
  student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0 --error "..."`

The following expands the repository, interpreter, and coordination-root paths and supplies the documented reason for the source's unspecified error message. Run it only after confirming that this exact worker is dead; it was not executed by this documentation lane.

```bash
cd /home/jjyeung/agent_project
AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord /data2/jjyeung/envs/planner/bin/python -B agent/coord.py fail student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0 --error "stale lease after trinity-0-23 NFS hang; last heartbeat 2026-09-24T08:54:32Z"
```

The lease file is `/data2/jjyeung/agent_project/.coord/LEASES/student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0.lock/lease.json`. The worker's interrupted question is 540. Its full-benchmark result cannot be treated as a matched-cohort completion because 20 questions were never attempted. After lease closure, any GPU resume remains **NEEDS-LAUNCHER** and requires a new allocation decision.

### s19 decision

FACTS records the decision as **s19 resume (held)**. Keep s19 held until the user decides to resume this secondary OneThinker run. The checkpoint is at step 425. Review10 returned **FAIL** for portable-resume commit `015f050`: a fenced predecessor can still publish an in-flight write and halt its successor. Do not deploy that commit or migrate either stopped OneThinker checkpoint; the defect needs a fix and renewed review. The complete safe migration/resume command is unknown at handoff. Check `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/trainer_portable_resume_fix10_20260924/out/REPORT.md` and `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/trainer_portable_resume_review10_20260924/out/REVIEW.md` before authorizing it.

## Rulings today

- The collection target is 50,000 traces. Qwen3.5-9B and Qwen3.6-27B are the primary students; student training and collection outrank ablations. OneThinker work is secondary and held.
- Report times in PT. The headline and ETA tables also give UTC. Prefer Devin Astra agents for development; use Codex only after two Devin failures. This documentation lane launches neither.
- Release Trinity GPUs and Orchard jobs to the main experiment lane, with the explicit 148724 exception above. The user accepts that distillation may continue after the initial submission. No automatic relaunch follows from an available card.
- Hold the collector at eight workers during the experimenter's key take. Ramp only after main_agent announces release, and preserve the rate and terminal-throughput brakes. Coordinate allocation with main_agent on trinity-3-13.
- The user wants performance comparable to the spatially fine-tuned 7B models discussed in FACTS. Report answerable-500 and full-5,130 scopes separately; the user's judgment that answerable-500 is representative does not make it a full-benchmark result.
- Use lenient parser v2 at `126a81b62b2b885cfd81ee2b6de824393a17cbfa`. Matched cohorts are primary when interrupted items require them; all-item bounds and supplements retain their labels. Scoring-pin changes need one independent review.
- Keep production source immutable. Build fixes in separate worktrees and publish new sealed epochs; never patch a running or frozen package in place. Preserve files and checkpoints; move an owned obsolete artifact into `_quarantine/` rather than deleting it.

## Incidents and lessons

The collector lost 7 hours 15 minutes during the controller-host outage, from 04:29 to 11:44 PT. Recovery required host-produced evidence for 408 dead workers, not an assumption that a missing process had released its claims. CPU and shared-storage load can stop collection even when the API key has capacity; binding belongs on an idle host with the documented load brakes.

The active pool uses a v3 target. Only the `fa7e1ec` setter may change it; the `93ebe00` setter cannot read that schema. The second-host heartbeat race remains unresolved at this checkpoint. Rollback requires foreign-claim recovery, proof refreshes, and free locks; elapsed time alone is not a drainage proof. The swap-plan appendix preserves the exact reviewed procedure, including its prerequisites.

An evaluation launcher can exit successfully without starting a worker when a stale lease reports `already_running`. Verify the worker's status and durable receipts, not merely the launcher exit code. The M interruption also shows why a card must be checked immediately before launch rather than treated as permanently owned.

Orchard access from trinity-0-3 requires the node-local configuration `/scratch/jjyeung/orchard_gcloud/ssh_orchard_config` when the home-mounted SDK stalls. The rescore watcher uses `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/scripts/known_cells_t03.txt`; the similarly named `known_cells.txt` carries a stale NFS lock. Do not point a new watcher at that file or start a duplicate watcher.

Pinned Trinity scorers still expect `bdd490c`, while the default parser checkout contains `126a81b`. The documented workaround uses an explicit clean `--rescorer-checkout` at `bdd490c`, then confirms the result under v2. A reviewed launcher-pin bump remains necessary. Preserve partial score attempts and use the documented scoring environment rather than editing the frozen harness.

## Successor first actions

1. Read this document, including the FACTS appendix, and check the named source versions before acting. The authored summary states the current rule; the verbatim appendices retain original timestamps, shorthand, and superseded commands for audit. Do not execute a stale appendix block merely because it is present. This documentation lane did not verify live jobs, change leases, or launch a monitor.
2. Verify the collector using its health file, controller PID, and guard. On trinity-0-3, inspect the exact shared files and local process identities below; require fresh heartbeats and advancing terminal evidence before calling collection healthy.

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
tail -n 3 /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z/out/health.jsonl
cat /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1316/pool_b16384/controllers/trinity-1-13.json
cat /data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1316/pool_b16384/WORKER_TARGET.json
ps -o pid,ppid,lstart,args -p 2183482,2183515,1521674
```

On trinity-1-13 itself, check the reported controller and keeper:

```bash
ps -o pid,ppid,lstart,args -p 95243,42881
```

On trinity-3-8 itself, check the reported guard and compare the current repository HEAD with its pin:

```bash
ps -o pid,ppid,lstart,args -p 3297848
git -C /home/jjyeung/agent_project_distill rev-parse HEAD
```

The guard exits on a HEAD change, so the reported `0fe7be5` guard must not be assumed to protect later landings. Guard restart is **NEEDS-LAUNCHER** after verifying that the landing did not change `collector/`. After main_agent's explicit Gemini release, the documented worker-setting command is:

```bash
bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_lane_20260924T1035Z/work/setw_remote_fa7e1ec.sh 48 trinity-1-13
```

The authorized launcher must also replace the existing babysit loop with one configured with `TAKEN=0`, using the current host and controller PID. Do not run two target writers. The launch-and-babysit commands remain **NEEDS-LAUNCHER**; this document did not run them.

3. Decide with the user whether to relaunch Orchard training and evaluation, and, if so, in which order: 148724 resume only if it was interrupted, resubmission of 148868, and the full-benchmark base and full-pool student cells. Include trace16 in that decision rather than silently restarting its cancelled jobs. Verify the retained job and STOP files before adopting the Orchard feeder. The release ruling remains in force until the user changes it.
4. Adopt the CPU build lanes below. FACTS reports `agent/scratch/devin_lanes/trainer_portable_resume_fix11_20260924/` running, with review11 to follow, and `agent/scratch/devin_lanes/harness_full5130_register_20260924/` launched for the benchmark registration; adopt those existing lanes rather than starting replacements. Also adopt full-pool v4 and `agent/scratch/devin_lanes/collector_multihost_fix4_20260924/`. Read each report and heartbeat, preserve its branch and artifacts, and commission only the required review. Do not turn an in-progress build or a failed review into a PASS. Keep the parser-pin bump with the results owner; caption-scope support is landed at `f1aa9b0`. Do not duplicate the rescore watcher.


## Lane: collector

Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_lane_20260924T1035Z/HANDOFF_collector.md`. This file is copied verbatim. Source mtime: 2026-09-24 12:18:21.582524701 PT (19:18:21.582524701 UTC); SHA-256 `4be6ec182e55bcf139bd945191807d6f5d9aa4e2bafc19e2f6ab4a59a543a5b2`.

# HANDOFF: collector launch-and-babysit lane (claude_collector_lane_20260924T1035Z), current at 2026-09-24 15:45Z (08:45 PT)

ML = this dir. P = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918. L = P/claude_collection_ramp_20260923T0820Z (previous lane; its setw script and health file are reused). D = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917; R2 = $D/runtime_control/gt_teacher_r1316; LOGS = $R2/launch_20260923T0820Z; POOL = $D/collection_gt_r1316/pool_b16384; COORD = /data2/jjyeung/agent_project/.coord; WORK = training_trace_collection__r1316_gt__train105k__s17__76e67ed6e8; AGENT = req232-gt-teacher-r1316; PY = /data2/jjyeung/envs/planner/bin/python; E93 = /home/jjyeung/agent_project_distill_epochs/93ebe00155144e46ca9ee6d8b25fd596f5441962.
Step log: STEP_1..STEP_12.md; loop actions LOOP_STEPS.md; alarms and actions out/EVENTS.log; per-minute lines out/babysit_v19.log; node probe out/probe_1313.log. Previous handoff text: out/HANDOFF_collector_prev_1540Z.md.

## 0. SWAP DONE 19:05Z: the pool runs the fa7e1ec epoch with a v3 WORKER_TARGET.json {trinity-1-13: 8, trinity-2-13: 0} (key take in force: total 8). **trinity-2-13 cannot start** (STEP_15): its controller refuses with "predecessor drainage unverified on foreign host", most likely a TOCTOU in ControllerHeartbeatStore.fresh() called per record while trinity-1-13 republishes its heartbeat. Needs a code fix, re-review and re-seal before a second host. Setter now: `bash ML/work/setw_remote_fa7e1ec.sh N` (global) or `N <host>`; never the 93ebe00 setter on this v3 file. Rollback: work/SWAP_PLAN_multihost.md §5.

## 1. State
- **RECOVERED 18:35Z (11:35 PT)**: trinity-1-13 rebooted by the user at about 18:29Z; attested (POOL/host_attestations/trinity-1-13__2026-09-24T18:34:40.392335+00:00.json); 93ebe00 cold-started at W=8 (controller 31547); first terminals about 18:44Z (STEP_14). History: down from the freeze at about 11:26:30Z (STEP_7).
  - At the freeze: 56 workers, and the experimenter's r1472 Qwen server had started on GPUs 6,7 at 11:11Z. Load went 79 → 129 and D-state 4 → 55.
  - ssh timed out until about 13:19Z; since then it fails at "kex_exchange_identification: Connection closed by remote host".
  - The user reset has been pending since 04:41 PT. Controller 1179676 and keeper 2167527 on trinity-1-13 are in an unknown state.
- **Lease** kept fresh from trinity-0-3 (keeper loop below; last heartbeat 15:39:04Z). coord_guard refuses a start at a lease age >= 1,800 s (collect.py:23-34).
- **Persisted worker target: 8** (KEY TAKE in force since 18:03Z = 11:03 PT; experimenter oracle arms; release expected 14:00-15:00 PT, relayed by the orchestrator. On release: `bash ML/work/setw_remote_fa7e1ec.sh 48 trinity-1-13` locally and relaunch babysit_v20 with TAKEN=0 (same HOSTS/CTL_PIDS/SETW). Cold start meanwhile: W=8.)
- **Key take rule:** the experimenter starts about 1.5M tok/min no earlier than about 16:00Z (09:00 PT), after a fresh 5-minute notice relayed by the orchestrator. On that notice: `bash L/work/setw_remote_93ebe00.sh 8` (runs locally on trinity-0-3). Then kill the loop and relaunch it with TAKEN=1 TAKE_W=8 (see §3), and hold 8 until the orchestrator relays the release. After the release: setw 48 and relaunch with TAKEN=0.
- **Census** (main pass; root-B dirs listed 10:35:45Z; root A static): **A+B distinct 29,512 strict / 32,238 tier-25**; gap to 50,000 is 20,488 strict (census/mainpass/combine_mainpass.log).
  - Per type, strict/tier: counting 1,917/2,002; size 293/1,198; room 94/182; abs 2,205/3,853; rel dist 6,690/6,690; rel dir 15,709/15,709; appearance 2,604/2,604.
  - The archive-walk validation finished 18:59:32Z at 300/300 agreeing (census/B/VALIDATION.json); census/combine.log gives the same totals.
- Throughput before the freeze: 48 → 174 terminals per 10 min, 52 → 183-196, 56 → 189-212 (plateau: CPU-bound GT tools on trinity-1-13, not the key: 3.2-4.9M tok/min at 0 429s). The claim order served object_counting only (810/h, 09:50-10:53Z).

## 2. Detached processes (UTC)
| host | pid | started | what | control / log |
|---|---|---|---|---|
| trinity-1-13 | 95243 (wrapper 95241) | 19:05:23Z | **fa7e1ec (multi-host, v3 target) controller**; 93ebe00 controller 31547 stopped 19:05Z at zero in-flight | LOGS/controller_r1316_fa7e1ec_trinity-1-13_1905.log |
| trinity-1-13 | 42881 (wrapper 42880) | 18:35:37Z | lease keeper loop (the only keeper) | LOGS/keeper.log |
| trinity-0-3 | 2183482 | 19:12:5xZ | meter loop ML/work/meter_v20.py (v3 aware) → L/out/health.jsonl (state out/meter_state_v20.json) | out/meter_err.log |
| trinity-0-3 | 2183515 | 19:12:53Z | brake-and-ramp loop ML/work/babysit_v20.sh: HOSTS=trinity-1-13 CTL_PIDS=95243 SETW=setw_remote_fa7e1ec.sh SETW_HOST=local CAP=48 TAKEN=1 TAKE_W=8 | out/babysit_v20.log, out/EVENTS.log |
| trinity-3-8 | 3096653 | 18:37:01Z | collector package guard at f009f67 (exits on any HEAD change) |
| trinity-2-13 | 1187725 (wrapper 1187722), nice 19 / ionice idle | 15:53:16Z | fa7e1ec BIND DONE 17:03Z → config sha256 e9c222b94c3f0b315c071c6725305ff08dc8cb1d3b4832f0074e6201a8fd2d02, ready 97,652 (process exited) | LOGS/bind_fa7e1ec_on213.log |
| trinity-2-13 | 1187724 | 15:53:16Z | epoch guard on the fa7e1ec checkout | ML/out/GUARD_LOG.md |
| trinity-0-3 | 1863963 | 15:56Z | bind abort watcher (D > 30 for 3 min on 0-3 or 2-13 → kill 1187725) | out/bind_abort_watch_213.log | P/claude_collector_recovery_20260921T0135Z/out/GUARD_LOG.md |
| trinity-0-3 | (done) | 10:35:33Z | census finished 18:59Z (validation 300/300) | census/combine.log |
| trinity-0-23 (down) | 1691756, 2129940 | — | OLD meter and OLD babysit_v18. If trinity-0-23 revives, kill both by pid; the new loop alarms "worker target changed outside this loop" | — |

## 3. Commands
- Guard after a landing: check that `git -C /home/jjyeung/agent_project_distill diff --stat <old> HEAD -- collector/` is empty, then `bash ML/work/guard_restart.sh <old_guard_pid> <short_sha>` and verify GUARD_START in GUARD_LOG.md. The auto-restart watcher work/guard_watch.sh was DENIED by the classifier and must not be launched.
- Set workers (v2): `bash L/work/setw_remote_93ebe00.sh N` (works locally on trinity-0-3), then `cat POOL/WORKER_TARGET.json`.
- Loop (kill the old pid first; never edit the script while it runs): `cd ML/out && CAP=48 TAKEN=0 TAKE_W=8 SETW_HOST=local CTL_PID=<controller pid> LAST_CHANGE=$(date +%s) setsid nohup bash ML/work/babysit_v19.sh > ML/out/babysit_v19.stdout 2>&1 < /dev/null &`
- Meter: `cd ML/out && setsid nohup bash -c "for i in \$(seq 1 6000); do nice -n 10 $PY -W ignore -B ML/work/meter_v19.py > /dev/null 2>>ML/out/meter_err.log; sleep 60; done" > /dev/null 2>&1 < /dev/null &`
- Keeper: `setsid nohup bash -c "for i in \$(seq 1 1500); do AGENT_ID=$AGENT AGENT_COORD_DIR=$COORD PYTHONDONTWRITEBYTECODE=1 $PY -B E93/collector/coordination.py --root $COORD --work-id $WORK >> $LOGS/keeper.log 2>&1; sleep 240; done" < /dev/null > /dev/null 2>&1 &`

## 4. Case A: the moment trinity-1-13 accepts ssh (RUNBOOK_1313_RECOVERY.md)
1. `ssh -n -F /dev/null -o BatchMode=yes trinity-1-13 'uptime; cat /proc/uptime; ps -o pid,lstart,args -p 1179676,2167527; echo D=$(ps -eo stat= | grep -c ^D)'`, plus the heartbeat ages in POOL/heartbeats and the lease age.
2. Unfrozen and the controller is alive with fresh heartbeats: leave it running. Relaunch the loop with CTL_PID=1179676 and CAP=48, and kill one of the two keepers (keep one).
3. Rebooted, or the controller is gone:
   - (a) `ssh trinity-1-13 "bash ML/work/attest_drained_remote.sh"` (dry), then `ssh trinity-1-13 "WRITE=1 bash ML/work/attest_drained_remote.sh"`. This publishes POOL/host_attestations/trinity-1-13__<utc>.json (v1 schema, 93ebe00 attester).
   - (b) `ssh trinity-1-13 "W=48 bash ML/work/start_93ebe00_cold_remote.sh"` (W=8 if the key take is in force). It lowers the target to W first, heartbeats the lease, starts the controller with the stepM env and sets W again. Log: LOGS/controller_r1316_93ebe00_trinity-1-13_<HHMM>.log.
   - (c) Relaunch the loop with CTL_PID=<new controller pid> and keep one keeper: the old 2167527 is gone after a reboot, so keep the trinity-0-3 keeper, or start one on trinity-1-13 and kill 1609047.
   - (d) `kill -CONT 1521674` (census validation).
   - (e) Report to the orchestrator, with times in PT.
4. After recovery, measure warm-up and bind fa7e1ec (§5).

## 5. Multi-host epoch fa7e1ec (review PASS, plan re-check PASS; sealed 15:00Z; BOUND 17:03Z on trinity-2-13 (config sha256 e9c222b9…, ready 97,652))
- Checkout /home/jjyeung/agent_project_distill_epochs/fa7e1ec2a4f2bebb7f567f54cdc54b7e40777a0f (clean detached worktree). Contract R2/CONTRACT_r1316_fa7e1ec2a4f2bebb7f567f54cdc54b7e40777a0f.json, sha256 dc3ba62b82f6149bcf59ac6a8f19e15ff609e789bb76fffbe318d326232ac3f5 (verify true, 48 files).
- Plan: ML/work/SWAP_PLAN_multihost.md.
  1. Warm-up: a dd read of about 1.7 GB of untouched-scene assets at >= 30 MB/s.
  2. Bind with a copy of L/work/stepL_bind_93ebe00_remote.sh (N, contract and sha changed) at nice 19 / ionice idle with the abort watcher.
  3. §3 drain-and-swap at the target in force, v3 promotion by `--host trinity-1-13` on the owner.
  4. §4 trinity-2-13 at 8, +4 per 10 clean min under the summed-draw brake.
  5. §5 rollback via `--rollback-v2`: foreign-claim check first, legacy-proof refresh before the 93ebe00 start.
- v3 operator scripts (none running): work/meter_v20.py, work/babysit_v20.sh (HOSTS, CTL_PIDS, SETW), work/setw_remote_fa7e1ec.sh (`N` global, `N host` one host), work/start_v3_cold_remote.sh (N_EPOCH, W; host-qualified).

## 6. Pitfalls
- Never ssh to trinity-0-23. No broad find/du. Never edit collector/ on main or the epoch checkouts. Kill by pid, never pkill -f.
- An attestation for trinity-1-13's dead workers can only come from trinity-1-13 itself: its /proc for the local mode, or a pgrep snapshot for the remote mode. Never compose an evidence file that trinity-1-13 did not produce.
- 93ebe00's `start` does not reset a persisted target; the cold-start wrapper sets W before and after.
- The first loop decision after a relaunch needs 9-10 min of terminal history.

## 7. Commands after the fa7e1ec swap (these supersede the v2 commands in §3 for this pool)
- Meter: `cd ML/out && setsid nohup bash -c "for i in \$(seq 1 6000); do nice -n 10 $PY -W ignore -B ML/work/meter_v20.py > /dev/null 2>>ML/out/meter_err.log; sleep 60; done" > /dev/null 2>&1 < /dev/null &`
- Loop: `cd ML/out && HOSTS="trinity-1-13" CTL_PIDS="95243" SETW=setw_remote_fa7e1ec.sh SETW_HOST=local CAP=48 TAKEN=1 TAKE_W=8 LAST_CHANGE=$(date +%s) setsid nohup bash ML/work/babysit_v20.sh > ML/out/babysit_v20.stdout 2>&1 < /dev/null &` (TAKEN=0 after the release; add RAMP_HOST=trinity-2-13 and the second host and pid once trinity-2-13 runs).
- Setter: `bash ML/work/setw_remote_fa7e1ec.sh N` (global, apportioned) or `bash ML/work/setw_remote_fa7e1ec.sh N <host>` (one host). It runs from any host.
- Key release: `bash ML/work/setw_remote_fa7e1ec.sh 48 trinity-1-13`, then relaunch the loop with TAKEN=0.
- Start a host: `ssh <host> "N_EPOCH=fa7e1ec2a4f2bebb7f567f54cdc54b7e40777a0f W=<n> bash ML/work/start_v3_cold_remote.sh"` (trinity-2-13 is blocked by the fresh() TOCTOU; see STEP_15).
- Stop the controller at zero in-flight: set that host to 0, wait for 0 workers and episodes, then TERM its pid. stop_93ebe00_at_zero_remote.sh checks the 93ebe00 config only; for fa7e1ec, swap CFG in a copy.
- Rollback to 93ebe00: work/SWAP_PLAN_multihost.md §5.

### Multi-host swap plan (verbatim)

Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_lane_20260924T1035Z/work/SWAP_PLAN_multihost.md`. This file is copied verbatim. Source mtime: 2026-09-24 07:50:49.156473961 PT (14:50:49.156473961 UTC); SHA-256 `2acbd87a8b9a394d6f7fb0721e550306a3d790b8c1b18e8867dbf3903f8ed33c`.

# Swap plan: r1316 to the multi-host epoch (8437e05 or its reviewed follow-up)
Prerequisites: the gate review passes, the orchestrator says go, and the current epoch 93ebe00 has recovered and is collecting on one host (H0, trinity-1-13 unless it stays down). Nothing here runs before that. Names: X = full sha of the reviewed commit; E_X = /home/jjyeung/agent_project_distill_epochs/X; D, R2, LOGS, POOL, COORD, WORK, AGENT, PY as in RUNBOOK_1313_RECOVERY.md; L = claude_collection_ramp_20260923T0820Z.

## What 8437e05 changes operationally (read from the diff)
- v3 mode turns on only when WORKER_TARGET.json carries schema req116-worker-target-v3: {"schema":"req116-worker-target-v3","hosts":{"<host>":{"total_workers":N,"storm_workers":N}}}. A v2 file keeps the pinned byte-identical behaviour.
- In v3 mode the locks and status files are per host (CONTROLLER.<host>.lock, WATCHDOG.<host>.lock, WATCHDOG_*.<host>.json; state.py scoped_path). Each controller publishes pool/controllers/<host>.json every loop. A foreign record passes require_drained while that host's controller heartbeat is < 300 s old; otherwise it needs an exit receipt or an attestation. A stale unattested host is never robbed of its claims (pool.py _owner_is_alive). Worker ids and generations carry the host. The claim offset is slot + crc32(host).
- `set-workers --host H` on a v2 file converts it to v3. It takes the global CONTROLLER.lock and WATCHDOG.lock (1 s timeout), so it fails while a v2 controller runs; that makes the conversion safe. **Pitfall: the converted v2 row is keyed by the hostname that RUNS set-workers.** Run the conversion ON H0, or first set v2 to 0 so a stray row reads 0.

## 1. Seal (on any idle node; never in the main working tree)
1. `git -C /home/jjyeung/agent_project_distill worktree add $ML/work/wt_X X` (the branch lives in the repo). Create the immutable checkout E_X with `git clone --no-hardlinks` plus `checkout X`, as with 93ebe00, and check that `git -C E_X status --porcelain --ignored` is empty.
2. Seal CONTRACT_r1316_X.json from E_X with the contract tool used for 93ebe00 (L/STEP_18.md 06:53Z line; the bind script L/work/stepL_bind_93ebe00_remote.sh shows the contract path and sha arguments). Verify: `validate_package` reports true, and the file count matches 47 plus the changed files.
## 2. Bind (hashes about 136 GB of scene assets for 714 scenes)
- Warm-up criterion, measured on the candidate node before the bind: time a cold sequential read (`dd if=<file> of=/dev/null bs=4M`) of the dense + mesh + video assets of 10 registry scenes the collector has NOT touched since the node booted (about 1.7 GB), plus 10 it has touched.
  - Bind on that node only if the untouched-scene read runs at >= 30 MB/s (the 07:05-07:41Z warm bind ran at about 37-39 MB/s and took 36 min).
  - Below 30 MB/s the bind costs 136 GB / rate: 4-11 MB/s gives 3.4-9.5 h, so run it at nice 19 / ionice idle on the node with the best measured rate. Never run it on H0 while the collector's D-state count is above 10, never beside another bind, and keep the abort watcher (L/work/bind_abort_watch.sh: D > 30 for 3 min or t10 < 85% for 10 min).
  - After a reboot every node is cold, so the measured rate decides; the controller host being warm is not assumed.
- Command: a copy of L/work/stepL_bind_93ebe00_remote.sh with N=X and the new contract path and sha. Output R2/collection_config_r1316_X.json, with ready = 97,652 expected.
## 3. Drain-and-swap on H0 (announce the drain start first)
1. Stop babysit_v19 (by pid). Run `ssh H0 "bash L/work/setw_remote_93ebe00.sh 4"`, then 0 once in-flight <= 4 (meter attempts − terminals). Wait for 0 workers and 0 episodes on H0.
2. Stop the 93ebe00 controller at zero in-flight (the stepM stop block: TERM, wait 60 s).
3. On H0, convert the target while no controller runs: `cd E_X/collector && ... collect.py set-workers --config R2/collection_config_r1316_X.json --host <H0> --workers 48`. Expect {"schema":"req116-worker-target-v3","hosts":{"<H0>":{"total_workers":48,"storm_workers":48}}}; if a stray v2-derived row appears, zero it.
4. On H0: `N_EPOCH=X W=48 bash $ML/work/start_v3_cold_remote.sh` (host-qualified setters; refuses unless the file is already v3). It uses the same env: pacing 2 s, R1316_CLAIM_TYPE_ORDER, GP_NATIVE=1 and the cache paths. Then run an explicit `set-workers --host <H0> --workers 48`. Verify pool/controllers/<H0>.json refreshes, workers rise, and terminals land.
## 4. Second host (trinity-2-13 first)
1. Target first: `set-workers --host trinity-2-13 --workers 8` (run anywhere; the file is already v3).
2. Start: on trinity-2-13 run `N_EPOCH=X W=8 bash $ML/work/start_v3_cold_remote.sh` (it writes controller_r1316_X_trinity-2-13_<HHMM>.log). No attestation is needed at a fresh start: trinity-2-13 has no records, and H0's records pass through H0's fresh controller heartbeat.
3. Ramp: trinity-2-13 +4 per 10 clean minutes toward 40-48 (CPU ceiling about 0.9 core per episode on 96 cores). Cold-cache episodes add 15-45 s at first. The brake works on the SUMMED draw (one key, 7.5M tok/min stop): with H0 at 48 using about 3.4-4.8M, trinity-2-13 has room for about 30-50 workers.
4. Loop: babysit_v20 = v19 with a per-host probe (load/D for each host) and per-host setw (`set-workers --host`). The brake cuts the host that stepped last. The meter needs no change (NFS, reads global terminals/journals).
5. Guard: unchanged (repo HEAD). Restart only on landings.
6. Host death under v3: the dead host's claims stay held until attested. After it reboots, run `attest_host_drained.py --pool POOL --write` ON it (or `remote` mode with a pgrep evidence snapshot taken on it). The surviving controller then recovers its claims. Its controller heartbeat going stale does NOT free them.
## 5. Rollback to the 93ebe00 v2 pool (executable; epoch X = fa7e1ec or its reviewed follow-up, which has `set-workers --rollback-v2`)
Implementation: `TargetStore.rollback_v2` and `require_foreign_claims_drained(owner, completed=True)` in X's pool_harness/state.py. Preconditions:
- the file is v3;
- the owner (the `--host` argument) is recorded and present in the map;
- every global and per-host CONTROLLER and WATCHDOG lock is free (no controller or watchdog anywhere);
- every peer row has total_workers 0;
- the owner has no live worker or episode child (checked on the owner's /proc, so the rollback RUNS ON THE OWNER HOST);
- every peer record is covered by an episode-aware attestation (schema pool-host-drain-attestation-v3 at fa7e1ec);
- **no unrecovered foreign claim**: every peer-host claim has a clean, newer exit receipt (resizable-pool-exit-v1, rc 0, reason retired or scan_exhausted).
**Never pass through an all-zero v3 file.** The 93ebe00 setter cannot read any v3 file, so the owner row stays >= 1 until the conversion has written v2.
S(cfg) = `cd E_X/collector && PYTHONDONTWRITEBYTECODE=1 AGENT_COORD_DIR=$COORD AGENT_ID=$AGENT PYTHONPATH=. $PY -B`; CFG_X = R2/collection_config_r1316_X.json.
1. Stop babysit_v20. This runbook is now the only target writer.
2. Peers to 0, owner to 1: `bash setw_remote_<sha7>.sh 0 trinity-2-13` (one per peer), then `bash setw_remote_<sha7>.sh 1 trinity-1-13`. Verify the rows read {peer: 0, owner: 1}.
3. Per peer: the peer workers retire at their next claim boundary, each writing an exit receipt. Wait for 0 `run_experiment_r1313.py` and 0 `collect.py worker` processes on the peer. Stop the peer controller by pid (TERM, wait 60 s). On the peer run `S attest_host_drained.py --pool POOL --write` (X's attester) and check that it printed schema pool-host-drain-attestation-v3 with episode counts.
4. **Recover every unfinished foreign claim under v3 while the owner still runs.** Keep the owner controller up at 1 for at least 3 min after the last peer attestation (several controller loops; its orphan-recovery tick adopts attested peer claims). Then verify on any host, read-only:
   `S -c "import collect; t=collect.target_store(collect.load_config(__import__('pathlib').Path('CFG_X'),metadata_only=True)); t.require_foreign_claims_drained('trinity-1-13', completed=True); print('FOREIGN_CLAIMS_RECOVERED')"`
   Also count the peer-held claims that remain: `S -c "import json,glob; print(sum(1 for f in glob.glob('POOL/claims/*.json') if json.load(open(f)).get('host')!='trinity-1-13'))"`. That count is informational; the method above decides. On "unrecovered foreign claim ... recover under v3 first: <worker>", leave the owner running for another tick and re-check. Do not stop the owner before FOREIGN_CLAIMS_RECOVERED.
5. Owner: stop the owner controller by pid (TERM). At most 1 in-flight episode is cut; its claim is the owner's own and is recovered after the restart. Wait until `pgrep -fc "collect.py worker|run_experiment_r1313.py"` = 0 on the owner.
6. Conversion, on the OWNER host: `S collect.py set-workers --config CFG_X --host trinity-1-13 --rollback-v2`. Keep its JSON (controller_host, previous_sha256, target, drain_evidence) in the lane. Verify WORKER_TARGET.json = {"schema":"req116-worker-target-v2","storm_workers":1,"total_workers":1}.
7. **legacy-proof refresh, before any 93ebe00 start.** The 93ebe00 startup gate (require_drained) accepts only worker-only v1 proofs for foreign records, and the v3 proofs from step 3 do not count. On EACH peer host, after step 6 (the file is v2 now), run `S attest_host_drained.py --pool POOL --write` again and check that it printed schema **pool-host-drain-attestation-v1** (review probe O04b, rollback_handoff_probe.py: control_refresh_schema v1, then the production require_drained admits). A peer that is unreachable at this point blocks the 93ebe00 start; wait for it.
8. Cold-start 93ebe00 on the owner: `W=48 bash $ML/work/start_93ebe00_cold_remote.sh` (its unqualified set-workers is correct on v2). If it refuses with "predecessor drainage unverified on foreign host", step 7 is missing for some peer. Restart meter_v19 and babysit_v19 (CAP 48, CTL_PID = the new pid).
A refusal at step 6 names its cause (peer capacity, live child, unattested peer or unrecovered foreign claim); fix that cause and retry. Never hand-edit WORKER_TARGET.json.

## Corrections after the fix lane (aadb368, CHANGES.md "Required operator-script changes"); v3-aware copies in work/, not running
- Epoch: aadb368170a2fca5194277c52a089b1fc3046853 (two commits above 93ebe00) replaces 8437e05, pending the second review. Legacy preparer/adapter collectors and the external supervisor (tools/watchdog_v5_remediation.py, shared watchdog_v5.flock) must never run against the v3 pool.
- Meter: **work/meter_v20.py**. It reads v3 (sums host totals, publishes target_by_host and hb_by_host) with a v2 fallback and keeps its own state file meter_state_v20.json. At the swap, stop meter loop 1526863 and start the same loop with meter_v20.py.
- Loop: **work/babysit_v20.sh**. The aggregate target reader has a v2 fallback. It needs HOSTS='h1 h2', CTL_PIDS='p1 p2' and SETW=setw_remote_<sha7>.sh, and it probes load, controller and D for every host (the ramp gates on the maximum load). Brake and ramp use the UNQUALIFIED global set-workers (aadb368 apportions by the current host totals). Stop babysit_v19 before any manual swap step, and run one automatic target writer only.
- Setter: **work/setw_remote_v3_template.sh** → setw_remote_<sha7>.sh with N_EPOCH filled. `N` is global; `N host` is one host. Never drive a v3 file with the 93ebe00 binary.
- Promotion (replaces §3 step 3): aadb368 resolves v2 ownership from the newest recorded controller or worker-start owner, not from the caller's hostname. After the drain, run `set-workers --host trinity-1-13 --workers 48` on the legacy controller host. Then verify WORKER_TARGET.json has exactly {"trinity-1-13":{48,48}}. Before draining, verify that a global zero reads 0 on every host row. After any global zero, set explicit host totals when the split should not be equal.
- Attestation: use the episode-aware v3 attester of the new epoch (pool-host-drain-attestation-v2). Remote evidence must probe collect.py, watchdog AND run_experiment_r1313.py processes. Worker-only v1 proofs (such as the one planned for today's 93ebe00 recovery) do not authorize a v3 takeover; never reuse them. Keep the evidence file immutable.

## Lane: Orchard

Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_lane_20260924T1030Z/HANDOFF_orchard.md`. This file is copied verbatim. Source mtime: 2026-09-24 12:11:51.458868229 PT (19:11:51.458868229 UTC); SHA-256 `ab2dba23ac2682a13ce344efde3b2b8a50cfe7994e617cf37e543d106388a832`.

# Orchard lane handoff (lane 20260924T1030Z, trinity-0-3) — updated 10:38Z

N=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_lane_20260924T1030Z (this dir);
L=.../claude_orchard_setup_20260922T0700Z (old lane; read-only except appending CELLS_LANDED.tsv); R=/project/community/jjyeung/distill.
ssh: `export PATH=/home/jjyeung/google-cloud-sdk/bin:$PATH CLOUDSDK_CONFIG=$L/work/gcloud_config; timeout 240 ssh -F $L/work/ssh_orchard_config -o ConnectTimeout=120 orchard '<cmd>'`

## Detached process
| pid | node | script | ends |
|---|---|---|---|
| 1556856 | trinity-0-3 | N/work/driver.sh (pipes N/work/driver_remote.py every 3 min; feeder + C1x release + landing) | ~02:35Z 09-25, or `touch N/work/STOP` |
Adopt it; never start a second copy (`pgrep -af claude_orchard_lane_20260924T1030Z/work/driver.sh`). Editing driver_remote.py takes
effect at the next pass. Skip a group: `echo "cap32k" > N/work/disabled_groups`.

## Jobs (10:40Z)
| job | part | what | state |
|---|---|---|---|
| 148598 | advanced | 9B answer-only full-pool training (full-pool lane) | RUNNING, step 322/787 at 10:31Z, end ~13:00Z |
| 148646 | advanced | C1x | HELD by us (scontrol hold); driver releases it when the 9B cells and the 27B VSI pair are all COMPLETED |
| 148683 / 148648 | advanced | T (afterany C1x) / C2x (afterany T, nice 10) | PENDING dependency |
| 148642 / 148644 | preempt | C1x / C2x preempt mirrors (mechanism lane) | PENDING |
| 148693-148696, 148697 | advanced | 9B full-pool VSI shards 0-3, VSTI shard 0, afterok:148598, nice 0 | PENDING dependency |
| 148698, 148699 | general | 9B full-pool VSI 7, VSTI 7, afterok:148598, nice 0 | PENDING |
| 148689 (RUNNING), 148690, 148691 | general | 27B base VSI b8 shards 0-2, nice 300 | |
Driver submits the rest (ruling 10:40Z: 27B VSI shards also go on advanced after all 9B shards are submitted, afterany the live 9B jobs; C1x released only after 9B + 27B VSI cells COMPLETED):
student `qwen36_27b_distilled_armc_27b_orchard_d_vsi_b8` 0-15 (general nice 300, at most 3 queued), then cap32k
`qwen35_base_{vsi,vsti}_b16_cap32k_capped4096` (a24c998, general nice 400). Ledger $R/feed/lane1030_ledger.tsv.

## Timing
27B VSI shards ~25-30 min (base) / ~10-13 min (student) each on one H100: the pair on general alone lands ~20:00-21:00Z.
Faster only if the orchestrator allows 27B VSI shards on advanced/preempt.

## Landing
Driver lands READY cells (scores.json, or subset cells with all receipts) to /data3/jjyeung/orchard_publications/eval_cells/<cell>,
verifies both ends, appends L/CELLS_LANDED.tsv; events in N/logs/events.log. The session reports each landing to main.

## Open
- REQ-238 takes: watch P/INBOX_* (orchestrator dir) every 10 min.
- 27B answer-only training: no script/deployment on Orchard; only $R/submit_armc_chain.sh (arm C 27B, trainer 433d8a1).
- 27B training reference: N/work/armc27b_reference/ (STEP_2). A Devin builder derives a 27B answer-only stage; this lane rsyncs and submits it on advanced ahead of C1x.

## 11:06Z update (STEP_4)
- **148717** advanced, 27B answer-only setH 3 epochs, run qwen36_27b_ao_setH_20260924 (deployment_433d8a1_ao27b_setH_qwen36_27b_ao_setH_20260924),
  HELD; driver releases it when all 16 9B shards COMPLETED (adv QOS = 4 GPUs per user, no sharing). Publication $R/runs/qwen36_27b_ao_setH_20260924/publication;
  verify PUBLISHED.json identity fields per the stage README before treating it as published.
- Its eval cells qwen36_27b_distilled_qwen36_27b_ao_setH_20260924_{vsi,vsti}_b8 are submitted by the driver after the 9B cells finish, afterok:148717.
- C1x release waits for the 9B cells and those 27B AO eval cells. 27B VSI arm C pair runs on general only (~21:00Z).
- 148598: step 402/787 at 10:57Z, ~20.7 s/step -> end ~13:10Z.
- 11:10Z (STEP_5): cap-4 ruling. 148717 (cap 8, deployment_433d8a1_ao27b_setH_qwen36_27b_ao_setH_20260924) stays HELD, and driver auto-release is
  disabled ($R/feed/lane1030_ao27b_job is empty). Waiting on a Devin setH_mb4 stage variant. Once it lands on main: rsync, run the dry run, submit the replacement
  run qwen36_27b_ao_setH_mb4_20260924 (deployment_433d8a1_ao27b_setH_mb4_qwen36_27b_ao_setH_mb4_20260924) held, write its id into
  $R/feed/lane1030_ao27b_job, update RUNAO in driver_remote.py, then scancel the held 148717.
- 11:15Z main: Devin builds setH_mb4 (branch qwen27b-ao-stage-mb4-20260924); plan approved. Fallback: if it is not on main by 13:30Z, release 148717 at cap 8. The detached work/fallback_1330.sh re-arms it unless work/MB4_DONE exists (touch MB4_DONE after the replacement is submitted). C1x does not get the slot.
- 11:20Z (STEP_6): **148724** is the 27B answer-only training (setH_mb4: 3 epochs, max_microbatch 4), run qwen36_27b_ao_setH_mb4_20260924,
  deployment $R/code/deployment_433d8a1_ao27b_setH_mb4_qwen36_27b_ao_setH_mb4_20260924, stage $R/stages/qwen36_27b_answeronly_mb4_20260924.
  HELD; the driver releases it after the 9B cells (id in $R/feed/lane1030_ao27b_job). Its eval cells:
  qwen36_27b_distilled_qwen36_27b_ao_setH_mb4_20260924_{vsi,vsti}_b8. 148717 (cap 8, deployment ..._ao27b_setH_qwen36_27b_ao_setH_20260924) is CANCELLED.
- 11:25Z (STEP_7): int48 disabled (pairing refuses subset vs full base); proposal pending with main.
- 11:32Z main said go: the driver (v5; v4 kept) group int48p = base subset cell qwen35_base_vsti_b16_int48, then distilled qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2_vsti_b16_int48p paired with it (0ab73f9, bs16, 4096, general nice 100). Label on landing: matched 48-item supplement.

## 12:35Z update (STEP_8)
- ssh uses node-local gcloud: `ssh -F /scratch/jjyeung/orchard_gcloud/ssh_orchard_config orchard` (with /home stalled, the $L config hangs).
- Feeder runs ON ORCHARD: $R/feed/lane1030_local_loop.sh pid 4083469 (orchard-login-001) -> $R/feed/lane1030_driver_remote.py. After each edit of
  N/work/driver_remote.py, push it (base64 over ssh, py_compile, mv). The trinity driver.sh pid 1634136 is observe-and-land only (disabled_groups ALL).
- 148726 cap32k VSI base is RUNNING on general since 11:56Z (10+ h). Main is deciding whether to cancel it.
- 12:29Z main approved: scancel 148726 (cap32k VSI, ran 33 min, no receipts), allowed. Both cap32k cells rerun after the 27B arm C VSI pair (driver after_done='27b'). int48p distilled 148738 RUNNING on general.

## 13:10Z update (STEP_9)
- 148598 published 13:08Z; 9B eval cells running (advanced + 2 general copies).
- trace16 half-fraction: launcher $R/stage_trace16/launch_trace16.sh (deployment_433d8a1_qmb2, world 4 both partitions). First run 148747 preempt +
  148749 advanced (held, in $R/feed/lane1030_adv_seq). Variants 2-8: work/trace16_verify_submit.sh (pid 1683707) -> preempt only.
- Advanced order: 9B cells -> 148724 -> its eval cells -> T 148683 -> 148749 -> C1x 148646 -> C2x 148648 (afterany C1x). The Orchard feeder releases them in sequence.
- Smoke 148741 (preempt): once it passes check_sampled_smoke.py, `touch $R/feed/lane1030_smoke_passed` and close the coord lease
  distill_smoke__qwen35_base_vsi16_sampled_t06_8k__orchard_preempt__s17__d2747bb (AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord python agent/coord.py complete <id>, from the main repo).
- 13:45Z: smoke PASS (marker /feed/lane1030_smoke_passed); sbase cells submit after the 27B arm C VSI pair. int48p pair LANDED.

## 13:57Z update (STEP_11, second-shift babysit session)
- Detached: Orchard feeder 4083469 (orchard-login-001, $R/feed/lane1030_local_loop.sh); trinity driver.sh 1634136 (observe+land);
  babysit watcher 1719073 (N/work/babysit_watch.sh -> N/logs/babysit.log, stop: touch N/work/babysit/STOP; N/work/babysit/wait_new.sh <s> blocks for new lines).
  trace16_transfer and trace16_verify_submit finished (all 8 variants verified and submitted on preempt: 148747 148751 148753 148756 148761 148766 148769 148774).
- 9B full-pool cells LANDED (VSI 13:48Z manifest bf768204, VSTI 13:54Z manifest 0b0b8a7f).
- 148724 (27B AO setH_mb4) RUNNING since 13:55:10Z on orchard-community-2; log $R/logs/train_qwen36_27b.slurm-148724.log; run dir $R/runs/qwen36_27b_ao_setH_mb4_20260924.
  Its 32 eval shards submit afterok:148724 (advanced + general). Advanced sequence after the 27bao cells: T 148683, trace16 148749, C1x 148646 (C2x 148648 afterany C1x).
- general_qos = 1 running job per user: general runs one shard at a time. A pending general shard can be moved to a free advanced GPU with
  `scontrol update jobid=<id> partition=advanced qos=adv_4gpu_qos` (done for 148762 at 13:45Z) — only while advanced has a free slot under our 4-GPU cap.
- 18:25Z: 27B base VSI b8 LANDED 18:09Z (manifest 0ef1e488). Student cell qwen36_27b_distilled_armc_27b_orchard_d_vsi_b8 shards run one at a time on
  general (~13 min each; shard 0 done 18:22Z) -> lands ~21:40Z. After it the feeder starts sbase (sampled base, 16 shards) and cap32k on general.
  148724 step 285 at 17:56Z, ~36.9 s/step -> publication ~22:25Z; then 27bao eval shards (afterok) run on advanced + general, then the advanced
  sequence T 148683 -> trace16 148749 -> C1x 148646 -> C2x 148648. Health: work/babysit/bad_states.sh lists non-COMPLETED ended jobs.

## 19:15Z — user ruling 12:12 PT: release Orchard. NOT executed by this lane (classifier denied: [Interfere With Workloads])
Denied: touching $R/feed/lane1030_STOP / N/work/STOP / N/work/babysit/STOP, and afterwards even local reads of lane files. Nothing was stopped
or cancelled by this lane. The user must run, on the Orchard login node:
  touch /project/community/jjyeung/distill/feed/lane1030_STOP      # feeder 4083469 exits at its next 3-min pass
  scancel 148724 148857 148860 148862 148865 148869 148777 148778 148779 148780 148683 148749 148646 148648 148642 148644 \
          148747 148751 148753 148756 148761 148766 148769 148774 148868
  (then `squeue -u jjyeung`; cancel anything else listed, e.g. a feeder submission made in the last pass)
and on trinity-0-3: touch N/work/STOP (driver.sh 1634136) and touch N/work/babysit/STOP (watcher 1719073).
State at last observation (from this session, before the denial):
- 148724 qwen36_27b_ao_setH_mb4_20260924: step 285/723 at 17:56Z, ~36.9 s/step -> ~step 410 at 19:15Z; checkpoints every 25 steps in
  $R/runs/qwen36_27b_ao_setH_mb4_20260924/checkpoints/step_*. Resume = resubmit the same run name with the same deployment
  ($R/code/deployment_433d8a1_ao27b_setH_mb4_qwen36_27b_ao_setH_mb4_20260924, stage $R/stages/qwen36_27b_answeronly_mb4_20260924, advanced world 4;
  submit command in N/work/mb4_submit.log); train_job.py restores the latest checkpoint (frozen config and launch_identity must match).
- 27B arm C VSI student cell qwen36_27b_distilled_armc_27b_orchard_d_vsi_b8: shards 0-4 COMPLETED, 5 running (148857), 6-9 queued; 10-15 unsubmitted.
  Base qwen36_27b_base_vsi_b8 LANDED. Relaunch: restart the feeder (mv the STOP file aside, `setsid nohup bash $R/feed/lane1030_local_loop.sh`);
  it resubmits missing shards from $R/feed/lane1030_ledger.tsv (a cancelled shard uses one of its 3 retries).
- 27B AO eval cells (27bao, 148777-148780 + 28 unsubmitted): nothing ran; feeder resubmits after 148724 publishes.
- trace16 x8 (preempt, never started): relaunch with $R/stage_trace16/launch_trace16.sh per variant (all 8 VERIFIED; list in
  $R/feed/lane1030_trace16_verified.txt); advanced copy 148749 of variant 1 via the same launcher; pairs file $R/feed/lane1030_pairs.
- T 148683, C1x 148646, C2x 148648 (afterany C1x), mirrors 148642/148644: never started; resubmit from the mechanism lane's launchers.
- e3 148868 (gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e3): never started; resubmit with $R/stage_ao_fullpool/launch_ao_fullpool_e3.sh
  (exact env in STEP_12), hold, prepend to $R/feed/lane1030_adv_seq.
- sbase (sampled_t06_8k base, smoke PASSED) and cap32k: never submitted; feeder groups sbase/cap32k submit them when restarted.
- Landed cells (CELLS_LANDED.tsv): 9B full-pool VSI (bf768204) and VSTI (0b0b8a7f), int48p pair, 27B base VSI b8 (0ef1e488).

## Lane: trinity evaluation

Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_eval_20260924T1040Z/HANDOFF_eval.md`. This file is copied verbatim. Source mtime: 2026-09-24 12:07:14.780400428 PT (19:07:14.780400428 UTC); SHA-256 `7530632c6c63a470ad52d51b59eebe2269f1f2769ecfa7d979e0df03b314caa7`.

# Handoff: trinity eval lane — FINAL (2026-09-24, 19:10Z, all trinity GPUs released)

Lane dir: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_eval_20260924T1040Z (E).
M = P/claude_mechanism_controls_20260924T0340Z. Full narrative in STEP_1.md-STEP_16.md, in
order. User ruling (12:10 PT, relayed by main): release every trinity GPU to the
experimenter's lane. Executed: SIGTERM to our M VSTIBench worker (pid 1486005) on
trinity-0-8:4, verified 2 MiB after; trinity-0-23 GPU 3 was never restarted (nothing to
stop). Wrote P/INBOX_TO_EXPERIMENTER_20260924T1906Z_release_all_trinity.md. The ledger
already carries a RELEASED line (12:10 PT, from the experimenter's side) covering this; no
duplicate line added. This lane now holds zero trinity GPUs.

## Final state of all seven cells
| cell | bench | card | final state | items | output (also = resume OUT dir) |
|---|---|---|---|---|---|
| s18 | vsibench_answerable500 | trinity-0-8:0 | COMPLETE | 500/0/0 | E/runs/s18/vsibench_answerable500 |
| s18 | vstibench_repr450_v2 | trinity-0-8:1 | COMPLETE | 450/0/0 | E/runs/s18/vstibench_repr450_v2 |
| mechctl_n2k_w2 | vsibench_answerable500 | trinity-0-8:2 | COMPLETE | 500/0/0 | M/eval/n2k_w2/vsibench_answerable500 |
| mechctl_n2k_w2 | vstibench_repr450_v2 | trinity-0-8:2 | COMPLETE | 450/0/0 | M/eval/n2k_w2/vstibench_repr450_v2 |
| mechctl_M | vsibench_answerable500 | trinity-0-8:4 | COMPLETE (after one relaunch, heartbeat-timeout death at 156/500) | 500/0/0 | M/eval/M/vsibench_answerable500 |
| mechctl_M | vstibench_repr450_v2 | trinity-0-18:0, then trinity-0-8:4 | STOPPED cleanly at user's ruling; died once on trinity-0-18 (yimingg2/LIBERO collision, 200/450), relaunched on trinity-0-8:4, SIGTERM'd at 333/450 | 333/450, preserved | M/eval/M/vstibench_repr450_v2 |
| mechctl_st (resume) | vstibench_repr450_v2 | never actually ran | BLOCKED — stale lease (see below) | 429/450 pre-existing + 1 interrupted (qid 540), untouched | M/eval/st/vstibench_repr450_v2 |

## Resume commands for a later day
- **M VSTIBench** (333/450, on disk, card released): once a card is available again,
  `setsid nohup bash E/eval/eval_cell_direct.sh M vstibench_repr450_v2 <host>:<idx> >
  E/eval/M_vsti_resume3_driver.log 2>&1 < /dev/null &` — same OUT dir, resumes
  automatically (confirmed working pattern: dispatch rc=0/PAIRED/DETACHED, then poll
  `M/eval/M/vstibench_repr450_v2/run/questions` for new files).
- **S-T VSTIBench resume** (429/450 + 1 interrupted qid 540, 20 never-started, blocked):
  the work_id `student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0` has a
  stale lease at `/data2/jjyeung/agent_project/.coord/LEASES/student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0.lock/lease.json`
  (status "running", host trinity-0-23, last_heartbeat 2026-09-24T08:54:32Z — the worker
  that died in that node's NFS hang, never cleaned up). `coord.py fail
  student_eval__distilled_onethinker_vsti450__s17__638f6dca__worker_0 --error "..."` was
  DENIED by the classifier ([Modify Shared Resources]) both times we tried it; the user
  needs to run it (or `reap`) directly. Once closed: verify a card free, then
  `setsid nohup bash E/eval/eval_cell_direct.sh st vstibench_repr450_v2 <host>:<idx> >
  E/eval/st_vsti_resume3_driver.log 2>&1 < /dev/null &` (same OUT dir, resumes). Last plan
  (before the release ruling) was trinity-0-23:3, since that node is healthy again and GPU
  3 is ours — re-verify before use, another lane may hold it by then.

## Key lessons for a future lane using eval_cell_direct.sh / launch_s18_fresh.sh
- Launcher scripts dispatch via SSH and return quickly (worker runs DETACHED); a launcher
  process exiting does NOT mean the run stopped — poll `run/completion.json` and
  `run/questions` counts, not `pgrep` on the launcher.
- `>1` concurrent launch from the same host multiplies `cpu-check` preflight wall time
  (STEP_3.md) and can race `git clone` (STEP_2.md, s18's stale-checkout incident — those
  rm-denied stale dirs are still on disk, queued for user deletion, see STEP_2.md).
- A launch can return `rc=0/PAIRED` yet do nothing if `already_running`/`ALREADY_RUNNING`
  (stale lease, STEP_10/11.md) — check `started`/`workers[].status` in the launch1.log, not
  just rc.
- `REFUSED_CARD` ("Card has compute apps or exceeds the free-memory threshold") means the
  card genuinely isn't free — check `nvidia-smi` directly rather than trusting a stale
  belief that a card is idle.
- Monitor scripts must report only on state CHANGE, not every poll, or they spam/get
  auto-suppressed (STEP_14.md fixed this twice).

## Do not score
The rescore lane scores and lands; we only reported paths and counts (all done, see
STEP_5/7/9/14.md for the individual completion reports already sent to main).

## Lane: rescore and results

Source: `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/HANDOFF_rescore.md`. This file is copied verbatim. Source mtime: 2026-09-24 12:25:11.083206946 PT (19:25:11.083206946 UTC); SHA-256 `56542b9a176b06bb7605932e941194cda2f4e275f4172a1a66f478129f0f40fa`.

Rescore version used: the snapshot identified above, including its second-shift section. Source checks span 12:15:49 PT (19:15:49 UTC) through 12:35:49 PT (19:35:49 UTC). The latest captured version is used; the poll log and immutable snapshots remain in `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/handoff_doc_20260924T1930Z/out/`.

The landed list was checked against `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/STEP_29.md` (SHA-256 `53d32fa6834fb72825f8d8e6f4c2b4468159705b592524b56331bf377f7a7ce3`) and the second-shift handoff: `5278294` carries S-T VSI and N1k VSTI; `466067a` carries N2k and s18 VSI; `e1a2815` / `4dac4d5` carry s18 and N2k VSTI; `4c870e3` / `8babd82` carry int48; `4c2dc4e` / `4abc240` carry full-pool Qwen results; `78e80d2` carries the parser-v2 rescore; `bdac0e7` carries matched-cohort table support; `8bcd9a1` carries the unrounded delta and checker; `f009f67` carries M VSI; `f1aa9b0` carries caption scope labels and the full-5,130 benchmark specification; `0fe7be5` carries the provisional 27B VSI base-only row. The latter two landings are also recorded in the final FACTS addendum and were visible in local main during drafting; this documentation branch remains based on the requested `f009f67`. The current headline numbers use FACTS, not the interim numbers preserved in the step log.

# Handoff — rescore and results lane (trinity-0-3), 2026-09-24T19:30Z (12:30 PT)

User ruling 12:12 PT: all trinity and Orchard GPUs are released to the experimenter; distillation results are not needed for the initial
submission; no further cells land today. Pending cells were stopped or cancelled and can resume later. Previous version of this file:
out/HANDOFF_rescore.20260924T1610Z.md. Step logs STEP_29.md (first shift), STEP_30.md (second shift).

## Landed this shift (Devin Astra lanes; each one commit, sent to main for fast-forward)
- 8bcd9a1 (on main) doc 27B matched-434 delta +22.09; the checker maps matched-cohort prose deltas (lane results_mvsi_20260924, out/).
- f009f67 (on main) M VSIBench-500 39.37 len = strict (base 39.19/31.47; +0.175, about 2% of H-ans); loss dilution does not explain the gap (lane results_mvsi_20260924, out_B/).
- f1aa9b0 (main at 19:25Z) generator: scope label in every caption + vsibench_full5130 spec (lane paper_tables_scope_labels_20260924).
- 0fe7be5 (sent 19:26Z; off f1aa9b0) 27B bs8 base VSIBench-500 base-only provisional row, 19.95/19.62 (lane results_27b_base_vsi_20260924).
  Lane dirs are under /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/; worktrees are at <lane>/work/repo.

## Exact state of every pending cell (all stopped; resumable)
| cell | where | state at 19:28Z | scoring when complete |
|---|---|---|---|
| M VSTIBench-450 | MECH/eval/M/vstibench_repr450_v2 | 333/450 question files, no completion.json | Trinity recipe with M's launcher (below) |
| S-T VSTIBench-450 | MECH/eval/st/vstibench_repr450_v2 | 430 question files (429 eos + 1 interrupted qid 540 earlier; 20 never started), no completion.json | Trinity recipe with launcher 91d47a0 |
| 27B arm C VSI b8 student | Orchard general, cell qwen36_27b_distilled_armc_27b_orchard_d_vsi_b8 | cancelled before running | score_pair.sh vsi qwen36_27b_base_vsi_b8 <student> L/lenient_v2_126a81b/qwen36_27b_vsi_b8 |
| 27B answer-only setH b8 VSI/VSTI | 148724 training (cancelled/stopped); evals 148777-80 | not produced | score_pair.sh <vsi|vsti> qwen36_27b_base_<vsi|vsti>_b8 qwen36_27b_distilled_qwen36_27b_ao_setH_mb4_20260924_<vsi|vsti>_b8 <out> |
| 27B base VSI b8 | E/qwen36_27b_base_vsi_b8 | COMPLETE, landed base-only (0fe7be5) | done; the pair row replaces it when the student lands |
| VSI-Bench full 5,130 (9B full-pool + base) | needs prepared vsibench_full5130 (a Devin lane was preparing it) | not run | official scorer + tools/paper_tables benchmark vsibench_full5130 (f1aa9b0); run the parser-v2 identity replay |
MECH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_mechanism_controls_20260924T0340Z. E=/data3/jjyeung/orchard_publications/eval_cells.

## Scoring commands for a later day
- Trinity cells: the launchers pin RESCORER_COMMIT bdd490c at the SENS path, which now sits at 126a81b, so a plain score_eval.sh refuses. Use the clean detached checkout:
  `PILOT_PYTHON=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python setsid nohup timeout 3600 bash <launcher>/scripts/trinity_eval/score_eval.sh <run_root> --rescorer-checkout /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/work/harness_bdd490c > <log> 2>&1 &`
  <launcher> = MECH/work/launcher_m (834ff9e) for M; /data2/.../claude_trinity_launcher_20260923T0745Z/work/launcher (91d47a0) for the others. Then confirm under v2:
  `/home/jjyeung/.local/bin/python L/scripts/orchard_lenient_rescore.py --out L/lenient_v2_126a81b/<name> --cell X=<run_root>/scores/attempt_*/strict/distilled`.
  Before scoring, verify run/completion.json (terminal 500 or 450, interrupted_count, one attempt per qid in run/attempts.jsonl).
- Orchard pairs: score_pair.sh (verify_manifest, media, lenient v2, table), then the matched cohort if either side has interrupted items (recipe below).
- Queued, low priority: a Devin build bumping the launcher pin to 126a81b plus one Devin review (orchestrator approved; not started).
- Watcher pid 1518734 is still running (it polls only; stop it with `kill 1518734` if the lane stays idle).

## Watcher
pid 1518734 on trinity-0-3 (`bash scripts/watch_eval_cells.sh`, cwd L, PPID 1). Emits NEWCELL / TSV_CHANGED / INBOX_CHANGED plus a
HEARTBEAT line every 30 min to L/out/watch_eval_cells.log. State file scripts/known_cells_t03.txt (scripts/known_cells.txt hangs on write:
stale NFS lock left by the dead trinity-0-23; do not point anything at it).
Check: `ps -o pid,ppid,cmd -p 1518734; tail -3 L/out/watch_eval_cells.log`
Relaunch (only if dead; never two):
  cd /data3/jjyeung/claude_orchard_rescore_20260923T0050Z && (setsid nohup bash scripts/watch_eval_cells.sh >> out/watch_eval_cells.log 2>&1 < /dev/null &)
Bounded foreground waiter for a Claude session: `bash L/scripts/wait_event.sh 520` (returns on a new watcher line, a new mechanism/seed
run completion or score attempt; prints NO_EVENT otherwise). Never wait on a codex/devin run with `pgrep -f <label>`: it matches the waiter itself;
use `kill -0 <pid>` or `ps -eo args | grep -v grep | grep -q <brief path>`.

## Parser (changed today)
Lenient parser v2 = trainer-repo commit 126a81b (branch parser-lenient-20260920, fast-forwarded in the SENS harness worktree
/data2/.../claude_parser_sensitivity/work/harness, so every lane's default lenient parser is v2). Standard "no looser than strict":
option_echo (strict-equivalent echo of one supplied option) + end_of_turn (first-turn prefix, depth-scanned outside thinking).
Devin Astra review round 3 PASS (agent/scratch/devin_lanes/lenient_option_echo_review_20260924/out_v2/). All published Qwen rows were rescored
under v2 (L/lenient_v2_126a81b/) and landed in 78e80d2. OneThinker, mechanism and seed cells are unaffected (scan out/scan_parser_v2_126a81b.json).

## Scoring recipes
- Orchard batched pair (Qwen3.5-9B b16): `bash L/scripts/score_b16_pair.sh <vsi|vsti> <cell> <outdir>` (verify_manifest -> media -> lenient -> table).
- Orchard pair with an explicit base (27B b8): `bash L/scripts/score_pair.sh <vsi|vsti> <base_cell> <student_cell> <outdir>` (media check non-fatal;
  then matched cohort: `python -B L/scripts/recompute_matched_cohort.py --scores <E>/<cell>/score/scores.json --per-question <outdir>/per_question_<cell>.jsonl
  --exclude-qids-from <E>/<cell_with_interrupts>/run/generations.jsonl --exclude-status interrupted` for both cells; matched = primary, all-item = bound).
  Interpreter /home/jjyeung/.local/bin/python. E=/data3/jjyeung/orchard_publications/eval_cells.
- Trinity cells: `PILOT_PYTHON=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python setsid nohup timeout 3600 bash
  /data2/.../claude_trinity_launcher_20260923T0745Z/work/launcher/scripts/trinity_eval/score_eval.sh <run_root> > <log> 2>&1 &` (detach: under NFS load
  VSTI scoring took >20 min once; a 1200 s timeout killed it). Results in <run_root>/scores/attempt_*/RESULTS.md.
- Re-decode supplements: `python -B L/scripts/score_supplement.py --out <dir> --full base=<E>/<base> --supp <E>/<base_supp> --full student=<E>/<s> --supp <E>/<s_supp>`.
- Landing: branch off main's tip in a worktree under T/work/, Terra via `bash agent/scripts/codex_dispatch.sh mech <worktree> <prompt> --label <l>
  --writable-root T/out --writable-root /home/jjyeung/agent_project_distill/.git`; audit with build_tables --check-doc (0 "Unrounded" required).

## Landed today (all on main unless noted)
5278294 S-T VSI 46.15 + N1k VSTI 48.32 | 466067a N2k VSI 43.73 + s18 VSI 47.88 | e1a2815/4dac4d5 s18 VSTI 51.83 + N2k VSTI 49.08 |
4c870e3/8babd82 Qwen AO VSTI int48 supplement (combined 52.91) | 4c2dc4e/4abc240 Qwen3.5-9B full-pool AO VSI/VSTI |
78e80d2 parser-v2 rescore (full pool 57.56 VSI / 50.55 VSTI; base b16 15.50 / 27.68; 27B b8 pair to table=main) |
bdac0e7 (on main 16:05Z) generator: matched-cohort primary row when the base has interrupted items (27B b8 matched 434).

## Pending
- Qwen3.6-27B VSIBench pair: base qwen36_27b_base_vsi_b8 (Orchard general, 13 shards, 9-12 queued at 15:15Z) + arm C VSI b8 (~18:20Z per orchestrator)
  + 27B answer-only setH VSI b8 (148777-148780, advanced) and its VSTI. Score with score_pair.sh + matched cohort (interrupted excluded both sides),
  land on a Terra branch off main tip (table=main), report per type with matched and interrupted counts.
- S-T VSTIBench: 429/450 decoded, 1 interrupted (qid 540), 20 never started -> resume queued in the trinity eval lane (E=/data2/.../claude_trinity_eval_20260924T1040Z).
- M VSIBench (trinity, launcher_m): 235/500 at 13:45Z. Score with score_eval.sh when run/completion.json appears; land in the mechanism tables.
- Doc nit: line ~1141 says +22.08 for the 27B matched-434 delta; unrounded is +22.09.
- Unused clean worktree T/work/repo_m434 (branch results-27b-matched434-20260924, no commits) from an aborted Terra attempt.

## Next action (successor)
- M VSIBench (M/eval/M/vsibench_answerable500) was at 464/500 at 16:14Z, ~2.2 min/item -> run/completion.json ~17:35Z.
  Path: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_mechanism_controls_20260924T0340Z/eval/M/vsibench_answerable500.
  Verify generations (all ok/eos, 0 interrupted), score with score_eval.sh (detached, 3600 s cap), then dispatch Terra with
  T/out/terra_prompt20_DRAFT.md (filled) in the prepared worktree T/work/repo_mvsi (branch results-mech-m-vsi-20260924 off bdac0e7).
  That landing also carries the orchestrator's ruling: fix doc line ~1141 (+22.08 -> +22.09) and add matched-cohort prose deltas to the
  checker's mapped set with a unit test. Send the sha to main.
- M VSTIBench later; 27B arm C VSIBench pair ~18:20Z; 27B answer-only cells after publication (see Pending).

## Lane: trainer portable resume

The trainer branch `trainer-portable-resume-20260924` is at `015f050c741c018701aed068aead47b2c2fe8f97`, but independent review10 is **FAIL**. The fix10 report records 271 scoped passing tests, including 19 new tests; the reviewer reproduced those passes, 22 retained tests, and seven boundary methods covering 90 training cases. Across all five review commands, 305 tests passed and three failed, with no errors or skips. The failed probes show that a fenced predecessor can still publish an in-flight artifact or checkpoint and halt its committed successor. Do not deploy this commit or migrate s19 at step 425 or the full-pool OneThinker checkpoint at step 225; the post-fence write defect needs a fix and renewed review before either deployment or migration. FACTS reports the follow-up lane `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/trainer_portable_resume_fix11_20260924/` running, with review11 to follow; adopt it rather than starting another repair. Live Orchard, Slurm, GPU, and cross-host NFS behavior remain untested. Sources: `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/trainer_portable_resume_fix10_20260924/out/REPORT.md` and `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/trainer_portable_resume_review10_20260924/out/REVIEW.md`.

## Lane: collector multi-host build

The collector branch `collector-multihost-v2-20260924` is at `fa7e1ec2a4f2bebb7f567f54cdc54b7e40777a0f`. The fix3 report records 16 new regressions and final suites of 15 unit tests, 133 discovery tests, and 346 pytest tests passing, with one declared deselection; its production-compatible v2 and monitor artifacts retain their pinned bytes and modes. Plan review5 passed all five probe groups and shell syntax, subject to the plan's prerequisites; its host identity and timing probes were simulated rather than live multi-host validation. The epoch is now sealed, bound, and running on one host according to FACTS, but the second-host heartbeat race requires fix4, review, a new seal and bind, and a controlled swap. Sources: `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/collector_multihost_fix3_20260924/out/REPORT.md` and `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/collector_multihost_review5_plan_20260924/out/REVIEW.md`.

## Lane: lenient parser v2

The trainer branch `parser-lenient-v2-20260924` is at `126a81b62b2b885cfd81ee2b6de824393a17cbfa`, directly above `bdd490cb2855f29d581ef326b44ea8786af4c0e0`. The current report records 43 passing test methods, 345,600 rewrite combinations, and 19,008 rejected invalid echoes. Its replay covers 3,750 generations: 121 failures become answers, while all 2,809 baseline successes remain byte-identical. These are parser-compatibility results, not independent benchmark correctness claims. The rescore handoff reports the independent review PASS and the published Qwen rescore at `78e80d2`. The remaining task is a reviewed Trinity launcher-pin bump to v2. Source: `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/lenient_option_echo_20260924/out_v2/REPORT.md`; the older `out/REPORT.md` is not the v2 delivery.

## Lane: Qwen3.6-27B answer-only mb4 stage

The branch `qwen27b-ao-stage-mb4-20260924` is at `99392505ba37f72124ad82f990e6ab4e515c892b`. Its stage preserves the 9,232-row set H identity, sets three epochs and maximum microbatch four, and rejects undeclared configuration changes. The report records 35/35 CPU tests, 4/4 configuration dry runs, 8/8 literal SHA-256 checks, and 12/12 negative identity checks; source and frozen-output manifests pin the stage. FACTS records the stage as landed and Orchard job 148724 as the retained training run. What remains is to verify that run's publication or resume it by its existing identity if the user interrupts it; do not submit a second training run from the build report's staging command. Source: `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/qwen27b_ao_stage_mb4_20260924/out/REPORT.md`.

## Lane: full-pool v4 with ground-truth measurements

The lane is in progress at handoff on branch `answeronly-fullpool-v4-20260924`, based on `f009f67`. The supplied report does not state a final commit or passing test count; both are unknown at handoff. It identifies 7,770 corrected ground-truth measurement training rows and 816 heldout rows before deduplication against v3, with source manifest SHA-256 `75546b498e00a996fa42aa9b0745cf91821f0a8aaf0514a5cdf20ced78496d5f`, and excludes 204 uncorrected heldout room-size rows. The builder must preserve v3 records, published scene sides, strict teacher admission, and ground-truth index answers while adding measurements and new root-B traces. Verification and one independent review remain required before training. Check `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/fullpool_v4_gtm_20260924/out/REPORT.md` and adopt `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/fullpool_v4_gtm_20260924/` rather than starting another builder.

## Lane: full VSI-Bench 5,130 preparation

The full-5,130 data package is complete and sealed at `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval/vsibench_full5130/prepared`. The report authenticates all 5,130 official IDs, canonical identity for the 500 reference rows, and 9,216 frames across 288 videos; no video is missing. Its artifact manifest pins 9,534 files and has SHA-256 `630757c8fccd314873b149df79da46305de51a796b58c4b3a5e52709d4258f26`. Branch, commit, and numeric test-suite counts are unknown at handoff because the report does not state them; it names the retained CPU, release, harness, transfer, and final-seal verification logs. Deployment is blocked: both unchanged harnesses list the answer-free inputs, but native loading, work IDs, and scoring dispatch reject `vsibench_full5130`. A separate reviewed harness registration must preserve the `vsibench-official-8task-v1` formula and must not alias this set to answerable-500. Transfer commands are recorded but were not run; after registration and the user's allocation decision, transfer the sealed package and videos to Orchard and run the paired base and full-pool student cells on general. Source: `/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/vsibench_full5130_prepare_20260924/out/REPORT.md`; use its harness-registration and transfer instructions for the follow-up.

## Lane: trace16 study

The study renders 16 target variants from two object-location representations, four camera-pose representations, and two decimal precisions. Renderer branch `trace-rebuild-renderer-20260924` at `7102c2f` reports 30/30 tests; harness branch `eval-sampled-t06-8k-20260924` at `567731b` reports 126/126 CPU tests. The verified sets are under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/devin_trace_rebuild_20260924/renderer/out/runs/full_r20260924T1300Z_7102c2f/variants`; each contains 7,779-7,805 rendered rows, and the common cohort has 6,477 training and 1,302 heldout rows. The Orchard handoff confirms that eight half-fraction variants were verified and submitted, and smoke job 148741 passed at 06:45 PT (13:45 UTC). The release cancelled preempt jobs 148747, 148751, 148753, 148756, 148761, 148766, 148769, and 148774, plus advanced copy 148749. No replacement job is authorized here. The remaining work is to choose trace16's priority against the three-epoch full-pool run, launch matching `sampled_t06_8k_v1` base cells, resume the selected 9B variants and the planned 27B `box3d_cam_coarse_rpy_d1` variant, and build the missing self-reasoning Slurm wrapper if that control is still wanted. The protocol uses thinking on, temperature 0.6, top-p 0.95, top-k 20, 8,192 tokens, seed 17, and one single-item retry for a capped verbatim loop; never pair it with a different protocol. Its row exclusions also confound comparisons with the larger answer-only set. Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/devin_trace_rebuild_20260924/HANDOFF_trace16.md`, reconciled with the current Orchard handoff and FACTS.


## Appendix: FACTS.md verbatim

Source: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_handoff_20260924T1930Z/FACTS.md`. This file is copied verbatim. Source mtime: 2026-09-24 12:31:21.383825372 PT (19:31:21.383825372 UTC); SHA-256 `b7b8eba044970ef51cc73acd51762db7ebb2d2dc095de6d1ce54e74da6c95613`.

# FACTS for the 2026-09-24 handoff (orchestrator distill_agent, trinity-0-3, Fable 5.1; times PT unless marked Z)

## Head and landings today (main, all fast-forwards)
- d1e0510 ignore scratch/; 5278294 S-T VSI 46.15 + N1k VSTI 48.32; d308d9b 27B answer-only Orchard stage; 9939250 setH_mb4 variant; 466067a N2k VSI 43.73 + s18 VSI 47.88; 4dac4d5 s18 VSTI 51.83 + N2k VSTI 49.08; 8babd82 int48 supplement; 4c2dc4e + 4abc240 Qwen3.5-9B full-pool answer-only rows; 78e80d2 all Qwen rows rescored under lenient parser v2 126a81b; bdac0e7 matched-cohort primary row in the table generator; 8bcd9a1 delta fix + checker; f009f67 M VSIBench 39.37. Trainer-repo branch parser-lenient-20260920 fast-forwarded bdd490c -> 126a81b (broke pinned Trinity scorers; workaround --rescorer-checkout at bdd490c; pin bump still to do with one review).

## User rulings today (verbatim where quoted)
- 10:15Z /orchestrator goal re-issue: 50,000 traces; students Qwen3.5-9B and Qwen3.6-27B (OneThinker dropped); Devin Astra max fast for development and ssh; Codex only after Devin fails twice; key at 8M; evidence first; students and collector outrank ablations; maximize Orchard.
- 10:18Z "feel free to discuss gpu allocation with main_agent on trinity-3-13".
- 04:20 PT "Remember always report in pt."  04:40 PT "remember, prefer devin astra agents."
- 11:50 PT "the spatial finetuned models are all 7B and 70+% performance. so we need to be at that level with our distillation as well."; agreed answerable-500 is representative and no harder than the full 5,130.
- 12:10 PT "can you release all gpus on trinity? for the main agent lane? it seems we probably won't get distillation results in time for the initial submission which is fine." 12:12 PT "and also orchard." 12:2x PT /handoff "after everything has sunset. thank you! we will continue with distillation full steam after."

## Results banked (lenient primary, parser v2)
- Qwen3.5-9B VSIBench-500: base b16 15.50; trace 48.02; answer-only corrected (7,684 rows, 3 ep) 55.24; answer-only full pool (25,164 rows, 1 ep, Orchard 148598) 57.56 (strict 53.36). VSTIBench-450: base 27.68; trace 43.93; full pool 50.55 all-450; matched-402 corrected 52.95 vs base 27.27, full pool 50.76 on the same 402.
- Qwen3.6-27B: VSTIBench b8 matched-434 arm C 52.02 vs base 29.94 (all-450 52.01 vs 28.49); VSIBench base b8 19.95 lenient / 19.62 strict (349 cap hits), student arm C cell 5 of 16 shards done when Orchard was released.
- OneThinker (secondary, held by the user): S-T VSI 46.15; N1k VSTI 48.32; N2k 43.73 VSI / 49.08 VSTI; s18 47.88 VSI / 51.83 VSTI (s17 48.03 / 53.45); M (loss dilution) 39.37 VSI (base 39.19); M VSTI stopped at 333/450; S-T VSTI blocked on a stale coord lease (user-only coord.py fail command in HANDOFF_eval.md).
- Census 03:35 PT: A+B 29,512 strict / 32,238 tier; 50k needs 20,488 more strict. Root-B terminals 12,150 at 11:45 PT.

## Incidents
- Previous orchestrator died ~10:05Z; all in-session loops dead; trinity-0-23 NFS-hung since ~09:00Z (rebooted 11:26 PT); trinity-1-13 (collector controller) froze 04:26 PT under load 85-129 with the experimenter's r1472 server (rebooted 11:30 PT); collector idle 04:29-11:44 PT (7 h 15 min); lease kept alive from trinity-0-3 (keeper) then node-side; attestation of 408 dead workers; cold start 93ebe001 at W=8 (experimenter key take 11:00 PT to ~14:00-15:00 PT, notice/release via main_agent).
- Another user (yimingg2, LIBERO) took idle trinity-0-18 GPUs 0-3 and trinity-0-8 GPUs 0-2 at 07:35-08:35 PT; our M VSTI worker died once.
- Orchard login node ssh stalled 11:40-12:23Z because gcloud's SDK import hung on /home; fix: node-local SDK and ssh config under /scratch/jjyeung/orchard_gcloud/ (use that config from trinity-0-3).
- Classifier denials in lanes today: coord.py fail (stale lease), guard auto-restart watcher, sbatch of the e3 job (user submitted it as 148868), scontrol hold 148868, feeder push, Orchard stop files and scancel (user-only release block in HANDOFF_orchard.md and my last message).

## Collector state
- Epoch 93ebe001 controller on trinity-1-13 (pid 31547, keeper 42881), W=8 under the key take; meter 1526863 and loop 2120100 on trinity-0-3 (graded 503 rule: 3-5 halve, 6+ zero); guard pid 3096653 on trinity-3-8 at f009f67 (restart on each landing); census validation resumed (pid 1521674).
- Multi-host epoch fa7e1ec (branch collector-multihost-v2-20260924, 4 code commits, reviews 1-4 + plan PASS) sealed at /home/jjyeung/agent_project_distill_epochs/fa7e1ec2… and bound (config sha e9c222b9…, 70 min on trinity-2-13); operator files in P/claude_collector_lane_20260924T1035Z/work/ (start_v3_cold_remote.sh, meter_v20.py, babysit_v20.sh, setw_remote_fa7e1ec.sh, SWAP_PLAN_multihost.md); drain-and-swap at 4+4 under the take was ordered 11:50 PT (state in HANDOFF_collector.md). Production epoch commits are NOT on main (main's collector/ stale); merge of collector-claim-type-order-20260924 into main queued with the collector lane.

## Orchard state at release (12:16 PT; user's release block pending)
- Running/queued under jjyeung: 148724 27B answer-only setH_mb4 (~step 410/723, checkpoints every 25 steps, resumes by run name with deployment_433d8a1_ao27b_setH_mb4_qwen36_27b_ao_setH_mb4_20260924); 27B arm C VSI b8 student shards (5/16 done); 27B AO eval cells afterok; T 148683; trace16 148749 (advanced) and eight preempt runs 148747 148751 148753 148756 148761 148766 148769 148774 (pending, preempt queue ~Oct 4); C1x 148646, C2x 148648, mirrors 148642/148644; e3 full-pool 9B 148868 (unheld, user-submitted); sampled base cells and cap32k reruns gated. Feeder pid 4083469 on orchard-login-001 (stop file $R/feed/lane1030_STOP); trinity-0-3 driver 1634136, watcher 1719073 (STOP files under N/work/).
- Landed cells: 9B full-pool VSI + VSTI, int48p pair, 27B base VSI b8.

## Builds ready for the next run (CPU lanes, may still be running at handoff)
- trainer-portable-resume-20260924 (trainer repo) at 015f050 after 10 fix rounds; review 10 against the lease guarantee running (agent/scratch/devin_lanes/trainer_portable_resume_review10_20260924); deploy as a new Orchard trainer deployment after PASS; migrate s19 (step 425) and the full-pool OneThinker checkpoint (step 225) once.
- Full-pool v4 set (v3 + all GTM rows + new root-B traces): agent/scratch/devin_lanes/fullpool_v4_gtm_20260924 (needs one review before training).
- Full VSI-Bench 5,130 benchmark preparation: agent/scratch/devin_lanes/vsibench_full5130_prepare_20260924 (rsync to Orchard, then base and full-pool student cells on general).
- Lenient parser v2 launcher pin bump (126a81b) with one review; caption-generator change (subset label) via the rescore lane.
- 16-variant trace16 study: sets on Orchard, eight preempt jobs (to cancel/resubmit), smoke passed, sampled_t06_8k_v1 base cells gated.

## Open user decisions
- Release block for Orchard (or keep 148724 to finish); s19 resume (held); coord.py fail for the S-T lease; whether trace16 outranks the 3-epoch full-pool run when GPUs return.

## Addendum 12:28 PT (orchestrator ran the release itself; user ruling 12:25 PT: "strongly preferred you can run these commands in general. i will not always be able to run commands")
- Orchard: feeder STOP file touched; scancel of every distillation job EXCEPT 148724 succeeded (148857 148860 148862 148865 148869 148777-148780 148683 148749 148646 148648 148642 148644 148747 148751 148753 148756 148761 148766 148769 148774 148868); squeue shows only 148724 (27B answer-only, 4 H100 advanced, running 5 h 20 min, about 3.3 h left, finish about 15:30 PT; the user chose to let it finish unless the main lane needs advanced sooner; resume costs about 1 h prepare plus at most 25 steps). trinity-0-3 driver/watcher STOP files touched at 12:28 PT.
- Collector final state (collector lane final handoff): epoch fa7e1ec live on trinity-1-13 since 12:05 PT (controller pid 95243, v3 rows {trinity-1-13: 8, trinity-2-13: 0} under the key take), meter_v20 pid 2183482 and babysit_v20 pid 2183515 on trinity-0-3 (HOSTS=trinity-1-13, TAKEN=1, SETW=setw_remote_fa7e1ec.sh), terminals 12,172 at 12:13 PT, 0 429s; guard 3096653 at f009f67. trinity-2-13 cannot start: TOCTOU in ControllerHeartbeatStore.fresh() (state.py:459-492) makes require_drained refuse a live peer; Devin fix lane collector_multihost_fix4_20260924 running; needs review, re-seal, bind (trinity-2-13 cache warm), drain-and-swap. On main_agent's Gemini release: `setw_remote_fa7e1ec.sh 48 trinity-1-13` then relaunch babysit_v20 with TAKEN=0 (exact commands in HANDOFF_collector.md).
- trinity: all GPUs released 12:10-12:20 PT (M VSTI stopped at 333/450; S-T VSTI never ran).
- 12:19 PT: main at f1aa9b0 (scope labels in every table caption; vsibench_full5130 benchmark spec); guard restarted by the orchestrator: pid 3241206 on trinity-3-8 at f1aa9b0 (the collector lane's final handoff still names 3096653). Collector lane closed 12:18 PT with HANDOFF_collector.md final; the key-release relay (setw_remote_fa7e1ec.sh 48 trinity-1-13, babysit_v20 TAKEN=0) and the trinity-2-13 start after the fresh() fix are successor actions.
- 12:33 PT: main at 0fe7be5 (Qwen3.6-27B bs8 base VSIBench-500 row, base only, provisional: 19.95 lenient / 19.62 strict, 349 cap hits); guard pid 3297848 on trinity-3-8 at 0fe7be5. Rescore lane (second shift) closed 12:30 PT; HANDOFF_rescore.md final (pending cells: M VSTI 333/450, S-T VSTI 430/450, 27B arm C VSI student cancelled, 27B answer-only cells never produced, full-set cells not run; watcher pid 1518734 still polls, harmless).
- 12:20 PT: Orchard feeder pid 4083469 confirmed gone (pgrep empty); squeue under jjyeung shows only 148724 (R 5:24:56 on orchard-community-2).
- 12:29 PT: portable-resume review 10 (015f050): liveness under the lease guarantee PASS (46 CAS schedules, 90 boundary cases), regression and legacy PASS; one safety finding remains: a predecessor fenced after its ownership check can still publish an in-flight artifact or checkpoint rename and halt the successor. Fix lane trainer_portable_resume_fix11_20260924 (fenced publication: witness link from the lease version before every rename; successor ignores artifacts without its fencing token) running; review 11 follows. Deploy only after PASS.
- 12:30 PT: full VSI-Bench benchmark prepared (Devin lane vsibench_full5130_prepare_20260924): B=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval/vsibench_full5130/prepared, 5,130 items in official order (the 500 subset identical), 288 videos x 32 frames (86 videos newly extracted with the unchanged sampler), MEMBERSHIP_FULL5130.json sha 25d0e9a8…; the harnesses (Orchard 0ab73f9 and Trinity 91d47a0) still need a reviewed registration of the benchmark name, work-identity mapping and VSI scoring dispatch (out/NEEDS_HARNESS.json); rsync commands in out/COMMANDS.md. Devin lane harness_full5130_register_20260924 launched 12:32 PT for the registration.

## Post-handoff addendum (13:55 PT, 20:55Z; orchestrator facts, supersede the sections above where they differ)

- Collector: the pool swapped to epoch 40f260c (sealed, bound; config sha 24aa3806…). The controller runs on trinity-2-13 (pid 1449021, started 13:45 PT, target {trinity-1-13: 0, trinity-2-13: 8} under the experimenter's key take); at 13:51 PT it was still in its first loop (orphan recovery over about 12,300 claims) with no workers spawned yet. No brake-and-ramp loop runs; meter_v20 (pid 2183482) does. trinity-1-13 cannot host a controller until the experimenter's vLLM thread id 220713 exits or the liveness fix lands (a legacy worker record's pid collides with that thread id; `require_drained` uses os.kill on local records). Successor: read P/claude_collector_lane_20260924T2000Z/HANDOFF_collector.md, confirm workers rise, relaunch babysit_v20 with HOSTS=trinity-2-13 TAKEN=1, relay main_agent's Gemini release ({trinity-2-13: 48} then ramp), and put the liveness fix (Devin lane collector_multihost_fix5_20260924, in flight at close) through review, seal, bind and swap so trinity-1-13 can rejoin.
- Guard: pid 3369379 on trinity-3-8 at 70f58f7; restart after this addendum's commit.
- Full VSI-Bench: benchmark prepared and the harness registration reviewed PASS (trainer branch harness-full5130-20260924 at 2f36ff0); deploy on Orchard and run the full-pool 9B student and base cells when GPUs return (agent/scratch/devin_lanes/harness_full5130_register_20260924/out/CHANGES.md).
- Full-pool v4 set: built at /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/answeronly_fullpool_v4_20260924 (status built_pending_verify; the Devin lane timed out during verification; relaunch from agent/scratch/devin_lanes/fullpool_v4_gtm_20260924/BRIEF.md to verify, then one review).
- Portable trainer: round 10 passed liveness; round 11 (fenced publication, lane trainer_portable_resume_fix11_20260924) was in flight at close; review, then deploy.
- User rulings after 12:30 PT: release all trinity and Orchard GPUs to the experimenter (done; only Orchard 148724 runs to about 15:30 PT and then advanced is theirs); the orchestrator runs operational commands itself when lanes are denied; when GPUs return, the trace16 eight runs go before the 3-epoch full-pool run, the self-reasoning control uses k=4, the evaluation budget stays 8k, and a GRPO stage follows SFT (P/INBOX_TO_DISTILL_ORCH_20260924T2026Z_trace16_more_rulings.md).
