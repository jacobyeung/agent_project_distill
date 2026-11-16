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

## Appendix: orchestrator facts (verbatim, 22:15Z)

# Facts for the 22:15Z handoff checkpoint (orchestrator distill_orch, session fb40b735 on trinity-0-23; clock 2026-09-23 22:15Z)
- main HEAD: 6d85afb (= e69c0ba results stack + 1bba105 answer-only VSIBench section + 6d85afb answer-only VSTIBench section and four-cell summary in docs/RESULTS_PER_TYPE_20260922.md). Landed by fast-forward at 22:12Z; collector package guard restarted on trinity-3-8 after the fast-forward (previous guard pid 2207891 exits on HEAD change; restart via P/claude_results_landing_20260923/luna_run.sh with the command in P/claude_guard_restart_20260923T0620Z/cmd_6d85afb.txt).
- Headline result (OneThinker-8B, corrected full set = room-fixed v2.5 + gtm2, 7,684 rows, trinity harness 91d47a0 launcher, paired 58794b8 base cells, lenient primary / strict secondary): base VSIBench-500 39.19/31.47, VSTIBench-450 45.40/40.16; trace student (Set B roomfix, publication /data3/jjyeung/orchard_publications/gtm2_v25full_onethinker_trinity_roomfix, PUBLISHED sha 45427e94…) 38.68/38.68 and 38.28/38.28; answer-only control on the same data (publication …_roomfix_answeronly, sha 9ab1c09b…) 48.03/48.03 and 53.45/53.45, no parse failures, no cap hits. Answer-only beats base by +8.84 VSI and +8.05 VSTI and beats the trace student by +9.35 and +15.17; the trace student is at or below base (VSTI -7.12: camera_obj_rel_dist_v2 -28, rel_dist_v1 -20, obj_obj_lr -16, camera_movement_direction -14; VSI route_planning 26 to 16 from 26 cap-hit loops at 4,096 tokens). Evaluation lane dir: P/claude_trinity_fullset_evals_20260923T1944Z (STEP_1-5, run roots under runs/). Inbox with all four tables: /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md.
- Earlier banked results stay valid: Qwen Set B pilot beats base on both benchmarks (VSI 39.80 vs 12.68; VSTI 44.57 vs 29.93; batched bs16 +26.94/+18.88); arm C stays ahead; swarm (about 30 cells) found no wording beating bare answers at 1,000 rows; the room-size label fix (18b7f3a) is the largest positive effect.
- Qwen corrected trace run: Orchard job 148295 (gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2, advanced partition, orchard-community-3, microbatch 2, 3 epochs, 723 steps) at step 452/723 at 22:00Z, loss 0.18, 23 s/step, publication about 23:45Z; feeder on deployment 0ab73f9 submits batched bs16 VSIBench-500 and VSTIBench-450 cells paired with the batched base cells when its PUBLISHED.json appears (trigger /project/community/jjyeung/distill/runs/gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2/publication/PUBLISHED.json, checked every 5 min). Orchard lane dir P/claude_orchard_setup_20260922T0700Z (STEP_65-68, logs/train_watch_148295.log, logs/babysit_events.log).
- Qwen answer-only corrected run: Orchard job 148380 (gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2) queued on advanced with afterany:148295; identical recipe (trainer 433d8a1, mb2, world 4, batch 32, seed 17, LoRA r32/a64, lr 1e-4, 3 epochs, split record eec29d98…); inputs staged and verified (MANIFEST fd7d5619…, candidate_index 5797eac2…, 9,232 rows); expected 15-20 s/step, publication about 04:00-05:00Z 09-24; its PUBLISHED.json also triggers batched cells. Record STEP_68.md.
- 27B smoke 148201 on Orchard preempt: 68/450 items after five preemptions, 121.9 s/item (about 118 items/h on 4 workers); a full cell needs about 4 h on a non-preempt slot; requeues itself.
- Flame partition: closed to us. It is gated by QoS (flame-t1a_qos, flame-t1b_qos, flame-t2_qos, flame-t3_qos); account mt01 holds only advanced, general and preempt; sbatch --test-only refuses ("No QoS specified for 'flame' partition …" / "Invalid account or account/partition combination specified"). The user expects 8 H100s there; an admin must attach a flame QoS to mt01 for user jjyeung. Probe record: Orchard lane STEP_67.md.
- Collector r1316 root B: controller on epoch fc6b364 (scene-verification cache, pacing 2 s) started 21:37:46Z after the user renamed a spurious BLOCKED.json aside (storm rule tripped on one 503 retry exhaustion at target 0 during the planned drain); first trace 21:41Z; 44 workers 4.7M tok/min, load 19; stepped to 60 at 22:01Z; 429 burst (42 in 15 min) at 22:10Z, brake ordered: back to 44, hold 15 clean minutes, retry 52. Terminals about 3,100 at 22:00Z (plus 130 questions burned by streamed 503s and 16 by the stray file, both excluded by the census). Lane dir P/claude_collection_ramp_20260923T0820Z (STEP_1-18, out/health.jsonl meter, out/PIDS.md, out/ERROR_ENDED_TERMINALS.jsonl). Lease keeper 2167527 and meter 2459924 on trinity-1-13.
- Storm-rule fix: branch collector-storm-count-20260923 head 2cd7d87 (fc6b364 + c551e88 + 2cd7d87; pool.py _check_failures ignores "provider retries exhausted" and "stream retries exhausted" retirements and uses len(recent) > max(desired, 4)/2; tests in collector/test_tolerant_pool.py; Astra review PASS round 2; receipts /data2/jjyeung/agent_project_data/codex_runs_distill/codex_runs/20260923T214706Z_storm_count_review_c551e88 and 20260923T215421Z_storm_count_review_r2_2cd7d87; lane dir P/claude_collector_storm_fix_20260923T2140Z). Swap ordered but blocked: the ramp lane was denied creating the immutable checkout; the user must run the three commands in P/claude_collection_ramp_20260923T0820Z/STEP_18.md (git worktree add --detach /home/jjyeung/agent_project_distill_epochs/2cd7d87 2cd7d87…, seal, verify). The ramp lane polls for that checkout every 2 min and then binds beside, drains via target 4 then 0, cold-starts with explicit set-workers, and resumes the ramp. The branch is not on main (root B lineage from ef1c3e6).
- Key sharing: user overruled the relayed 1.5M cap at 21:26Z ("you can always change, just discuss with the other agent"); split negotiated directly with aorch (session name aorch, trinity-3-13); aorch reserves nothing, its draw is zero apart from short Flash episodes (about 0.2M for 15 min); 429 bursts are the brake; measured ceiling about 7.8M tok/min at 64 workers.
- User actions still open: (1) the three checkout/seal/verify commands for epoch 2cd7d87 (STEP_18.md); (2) release the stale lease student_eval__distilled_onethinker_vsi500__s17__07753f75__worker_0 with `coord.py fail` from /home/jjyeung/agent_project with AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord (dead pid 117085); (3) obtain a flame QoS for account mt01. Completed by the user today: index.lock removal (21:30Z), six dead student_eval leases released, BLOCKED.json rename (21:36Z).
- Rulings today: never wait on the user for anything but deletions and permission-denied gates; no hard-coded hosts, paths or worker counts; storage never blocks experiments; results only under /data2 or /data3, home is code only; Codex Luna only for ssh/ops lanes; Devin Astra max for building; Astra for reviews; Terra for drafting; no arbitrary cross-student dependencies; lenient primary, strict secondary; use every GPU on the cluster and maximise Orchard.
- Incidents and lessons: streamed 503s ended episodes as finalized traces (fixed d1b52e4); a stray file written into the epoch collector/ by teacher code (fixed by the cwd fix and the guard); worker_failure_storm at target 0 (fixed 2cd7d87, swap pending); the auto-mode classifier denies BLOCKED.json renames, epoch checkouts under home and direct score calls on other lanes' roots to lanes (route to the user; the evaluation lane scored the trace VSIBench rerun through Luna after a denial and reported it); cross-host evaluation runs can lose a worker to the NFS negative-lookup cache (fail-safe); worker coordination ids ignore the run root and collide with retained history; admission on trinity-2-8 reads base weights at 25 MB/s (180 s timeout); other users take cards (jihop2 trinity-0-23:0-3, zixinguo trinity-0-8:0,1,2,4 at 21:25Z), so probe occupancy before every launch.
- Successor first actions: read this doc, then check for a live successor (lane dir mtimes, process start times) before acting; verify the collector meter (health.jsonl) and the 2cd7d87 swap state; confirm 148295 publication and the batched cells; confirm 148380 started; land the Qwen results through the rescore lane (P/claude_orchard_rescore lane at /data3/jjyeung/claude_orchard_rescore_20260923T0050Z, watcher pid 601049 on the inbox and eval_cells) with Terra drafting on branches off main and the orchestrator fast-forwarding; keep the lane map in this format; paper-ready numbers due 2026-09-24Z.
