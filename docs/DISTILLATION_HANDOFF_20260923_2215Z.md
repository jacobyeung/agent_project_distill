# Distillation handoff

2026-09-23 22:15Z — distill_orch, session fb40b735

## 1. Headline results table

OneThinker-8B corrected full set, lenient / strict:

| Benchmark | Base | Trace student | Answer-only control |
| --- | --- | --- | --- |
| VSIBench-500 | 39.19 / 31.47 | 38.68 / 38.68 | 48.03 / 48.03 |
| VSTIBench-450 | 45.40 / 40.16 | 38.28 / 38.28 | 53.45 / 53.45 |

- Earlier banked results stay valid: Qwen Set B pilot beats base on both benchmarks (VSI 39.80 vs 12.68; VSTI 44.57 vs 29.93; batched bs16 +26.94/+18.88); arm C stays ahead; swarm (about 30 cells) found no wording beating bare answers at 1,000 rows; the room-size label fix (18b7f3a) is the largest positive effect.

## 2. What is running and its ETA

- Qwen corrected trace run: Orchard job 148295 is at step 452/723 at 22:00Z, with loss 0.18 and 23 s/step; publication is about 23:45Z. Its feeder on deployment 0ab73f9 submits batched bs16 VSIBench-500 and VSTIBench-450 cells paired with the batched base cells when `PUBLISHED.json` appears.
- Qwen answer-only corrected run: Orchard job 148380 is queued on advanced with `afterany:148295`; it expects 15-20 s/step and publication about 04:00-05:00Z 09-24. Its `PUBLISHED.json` also triggers batched cells.
- 27B smoke 148201 runs on Orchard preempt: 68/450 items after five preemptions, 121.9 s/item (about 118 items/h on 4 workers); a full cell needs about 4 h on a non-preempt slot, and it requeues itself.
- Collector r1316 root B: the controller on epoch fc6b364 started 21:37:46Z; 44 workers ran at 4.7M tok/min and load 19, then stepped to 60 at 22:01Z. A 429 burst of 42 in 15 min at 22:10Z ordered the brake: back to 44, hold 15 clean minutes, retry 52.
- Storm-rule fix: branch `collector-storm-count-20260923` is at 2cd7d87. The swap is ordered but blocked because the ramp lane was denied creating the immutable checkout; it polls every 2 min for that checkout, then binds beside, drains via target 4 then 0, cold-starts with explicit set-workers, and resumes the ramp.

## 3. What the user must do

1. Run the three checkout/seal/verify commands for epoch 2cd7d87 in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z/STEP_18.md`: `git worktree add --detach /home/jjyeung/agent_project_distill_epochs/2cd7d87 2cd7d87…`, seal, verify.
2. Release the stale lease `student_eval__distilled_onethinker_vsi500__s17__07753f75__worker_0` with `coord.py fail` from `/home/jjyeung/agent_project` with `AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord` (dead pid 117085).
3. Obtain a flame QoS for account mt01.

Completed by the user today: index.lock removal (21:30Z), six dead student_eval leases released, BLOCKED.json rename (21:36Z).

## 4. Lane map with lane directories

| Lane directory | Description |
| --- | --- |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_results_landing_20260923` | `luna_run.sh` restarted the collector package guard after the fast-forward. |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_guard_restart_20260923T0620Z` | `cmd_6d85afb.txt` holds the restart command. |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_fullset_evals_20260923T1944Z` | Evaluation lane: STEP_1-5, with run roots under `runs/`. |
| `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z` | The inbox has all four tables; watcher pid 601049 watches the inbox and eval_cells. |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_setup_20260922T0700Z` | Orchard lane: STEP_65-68, `logs/train_watch_148295.log`, and `logs/babysit_events.log`. |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z` | STEP_1-18, `out/health.jsonl` meter, `out/PIDS.md`, and `out/ERROR_ENDED_TERMINALS.jsonl`. |
| `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collector_storm_fix_20260923T2140Z` | Storm-rule-fix lane for branch `collector-storm-count-20260923` at 2cd7d87. |

## 5. Rulings today

- Never wait on the user for anything but deletions and permission-denied gates.
- No hard-coded hosts, paths or worker counts.
- Storage never blocks experiments.
- Results only under `/data2` or `/data3`, home is code only.
- Codex Luna only for ssh/ops lanes.
- Devin Astra max for building.
- Astra for reviews.
- Terra for drafting.
- No arbitrary cross-student dependencies.
- Lenient primary, strict secondary.
- Use every GPU on the cluster and maximise Orchard.

## 6. Incidents and lessons

- Streamed 503s ended episodes as finalized traces (fixed d1b52e4).
- A stray file was written into the epoch collector/ by teacher code (fixed by the cwd fix and the guard).
- worker_failure_storm at target 0 (fixed 2cd7d87, swap pending).
- The auto-mode classifier denies BLOCKED.json renames, epoch checkouts under home and direct score calls on other lanes' roots to lanes (route to the user; the evaluation lane scored the trace VSIBench rerun through Luna after a denial and reported it).
- Cross-host evaluation runs can lose a worker to the NFS negative-lookup cache (fail-safe).
- Worker coordination ids ignore the run root and collide with retained history.
- Admission on trinity-2-8 reads base weights at 25 MB/s (180 s timeout).
- Other users take cards (jihop2 trinity-0-23:0-3, zixinguo trinity-0-8:0,1,2,4 at 21:25Z), so probe occupancy before every launch.

## 7. Successor first actions

1. Read this doc, then check for a live successor (lane dir mtimes, process start times) before acting.
2. Verify the collector meter (`health.jsonl`) and the 2cd7d87 swap state.
3. Confirm 148295 publication and the batched cells.
4. Confirm 148380 started.
5. Land the Qwen results through the rescore lane at `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z`, with Terra drafting on branches off main and the orchestrator fast-forwarding.
6. Keep the lane map in this format.
7. Paper-ready numbers are due 2026-09-24Z.
