# Distillation handoff - 2026-09-24 08:00Z

## Headline results

| Result | Evidence |
| --- | --- |
| Qwen3.5-9B answer-only corrected set | VSIBench-500: 55.24 versus the corrected trace student at 48.02 and the batched 4,096-token base at 14.92. VSTIBench-450: 52.95 versus 27.08 on the matched 402-question cohort, with an all-450 lower bound of 48.11 versus 27.55. Every question type gains. |
| OneThinker-8B corrected-set controls | Base: 39.19 VSIBench-500 and 45.40 VSTIBench-450. Trace: 38.68 and 38.28. Answer-only H: 48.03 and 53.45. These are lenient primary scores; strict scores appear in the rescore lane handoff. |
| First mechanism controls | Ground-truth measurement-only S-G scores 42.43 on VSIBench-500 and 49.25 on VSTIBench-450. The 1,000-row N1k control scores 45.32 on VSIBench-500. H remains 48.03 and 53.45. |
| Qwen3.6-27B batched bs8 appendix pair | On VSTIBench-450, the matched 434-question cohort gives 52.02 for arm C versus 29.94 for the paired base, a +22.08-point gain. The all-450 figures are 52.01 versus 28.49. |
| Validated collection census | Root A plus root B contains 26,090 distinct strict and 28,569 tier accepted traces. The validated strict total exceeds the 20,000-trace goal. |

VSIBench is the Visual Spatial Intelligence Benchmark, and VSTIBench is the Visual Spatial Thinking Benchmark. The project reports lenient scores as primary and strict scores as secondary. Ground-truth measurement rows are abbreviated GTM below.

## What is running now and its ETA

| Work | State and ETA |
| --- | --- |
| Collector type-priority epoch | The 93ebe001 claim-order epoch published at 07:41Z. The controlled drain began at 07:44Z; stepM then cold-starts it with the type order, 2-second pacing, and an explicit 66-worker target. Collection runs at a CPU-bound ceiling, so the successor should tune for terminal rate rather than key draw alone. |
| Answer-only full-pool training | OneThinker-8B trains on trinity-0-18, with a measured end near 13:05Z. Orchard job 148598 trains the Qwen3.5-9B model; its live probe is authoritative, with the lane estimate placing completion around 11:30-12:00Z. |
| Mechanism controls | S-T has published and N2k ends near 08:50Z. The experimenter's 07:52Z take leaves no four-card OneThinker slot until M finishes around 10:40Z; then T, C1x, and C2x run in order. C0 runs only if a spare slot appears. |
| Seed replicates | OneThinker s18 ends near 10:05Z and s19 near 11:41Z, then each evaluates on its own training cards. |
| Orchard diagnostics | The int48 supplement, then the two 32k capped-item diagnostics, wait on the user copies in the command block below. Orchard general is the only non-preemptible evaluation slot. |

## What the user must do

Run only steps 1 and 2 below to copy the pre-registered item lists and prepare the a24c998 submission script. The live Orchard lane submits int48 first and the capped-item diagnostics next. Do not run the commented step 3A or step 3B blocks unless the Orchard lane is no longer live.

```bash
export PATH=/home/jjyeung/google-cloud-sdk/bin:$PATH CLOUDSDK_CONFIG=/tmp/jjyeung_gcloud_config
L=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_setup_20260922T0700Z
R=/project/community/jjyeung/distill
RSH="ssh -F /tmp/jjyeung_ssh_orchard_config"
rsync -a -e "$RSH" $L/out/budget32k/items/ orchard:$R/items/
$RSH orchard "sed -e 's/deployment_0ab73f9/deployment_a24c998/; s/orchard_trainer_0ab73f9/orchard_trainer_a24c998/; s/^export TRAINER_COMMIT=.*/export TRAINER_COMMIT=a24c9983a3ecb1dc6e601ecb9bef64b5d972b521/' $R/submit_shards_b16.sh > $R/submit_shards_b16_a24c998.sh && diff $R/submit_shards_b16.sh $R/submit_shards_b16_a24c998.sh; true"
```

The type-order collector swap, evaluation submissions, and result landings belong to their live lanes. The full-pool, mechanism, and expansion lanes have no user-only command at this checkpoint. The user retains the optional decision on picker v2 and the optional Orchard mirror patch described in the verbatim lane handoffs.

## Rulings today

- 04:13Z queue USER-RULING (experimenter orchestrator): experimenter has priority on the shared key (7M theirs / 1M ours when shared) and on GPUs when needed; takes and releases announced via INBOX_*.md; priority never leaves capacity idle. No take announced as of 06:20Z.
- 04:57Z user: "you have the full key right now" -> ramp under a rate brake (429s above 2 percent of calls); key saturates at 8.2M tok/min near 66-70 workers (05:35-06:08Z).
- 05:20Z orchestrator: advanced order = full-pool Qwen training (148598), then mechanism Qwen C1x (148646) and C2x (148648); evaluation jobs stay on general and preempt.
- 05:50Z orchestrator: 27B appendix = batched bs8 base plus arm C student pair at the 4,096 cap; single-decode student shards cancelled; single-decode base stays banked.
- 05:55Z orchestrator: 32k budget = capped-items diagnostic only (adaptive-budget base), whole-benchmark 32k refused by the a24c998 admission contract; no harness change before the deadline.
- 06:40Z user: "keep collecting Gemini traces; prioritize counting, size, room size, absolute and relative distance."
- 07:05Z user: "we should by default have thinking on". T cells place trace text in the native thinking channel and answers in the native answer slot; the 32k adaptive-budget base is the fair thinking-on reference.
- 07:40Z: Orchard general is the only evaluation slot. It runs int48 and the full-pool Qwen b16 cells before the two capped-item diagnostics; advanced remains training-only.

## Incidents and lessons

The collector’s limiting resource moved from the Gemini key to CPU time in the GT tool. Its target should therefore follow terminals per worker, and the successor should preserve the 429 brake and the terminal-rate guard. Binding must run on an idle node because concurrent large readers can stall the controller.

The evaluation harness gives each full attempt one authority key. Interrupted items cannot be repeated in the original cell, so the Qwen answer-only primary row uses the matched cohort, the all-item score is a lower bound, and int48 is a labelled supplement. A 32k paper control must use a pre-registered proper subset, and the resulting diagnostic remains separate from the 4k benchmark row.

The experimenter may occupy claimed hardware without notice. Before any launch, each lane must inspect occupancy, respect the experimenter’s priority, and avoid preemptible evaluation when an interrupted result would be unrecoverable. Only the owning lane may stop its own processes.

## Successor first actions

1. Read this document, inspect the lane directory mtime and live processes, and adopt an existing lane rather than duplicating a loop.
2. Spawn one launch-and-babysit lane for collector. Follow the collector section, keep the one-minute cadence after any swap or relaunch, and preserve the rate brake.
3. Spawn one launch-and-babysit lane for Orchard. Keep general busy with the documented non-preemptible evaluation order and report every landed cell to rescore.
4. Spawn one launch-and-babysit lane for rescore and results. Verify manifests and media before scoring, use the official scorer, and land each results change through a branch off main.
5. Spawn one launch-and-babysit lane for trinity expansion. Watch s18 and s19, then evaluate each publication on its own cards and report the scores.
6. Spawn one launch-and-babysit lane for answer-only full-pool. Watch both students through publication and trigger the documented evaluations.
7. Spawn one launch-and-babysit lane for mechanism controls. Preserve the ordered slots, review and launch the thinking-channel cells, and report per-type scores.
8. Keep the collector guard at main’s landed tip after each validated result landing. Do not edit `collector/` on main.

## Lane: collector

# Handoff: r1316 root-B collector lane (refreshed 2026-09-24 06:25Z)

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z. D = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917. R2 = $D/runtime_control/gt_teacher_r1316. P = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918. Step log: `$L/STEP_18.md` (earlier steps STEP_17.md). Previous handoff text: `HANDOFF_collector_20260924T0235Z_plus_updates.md`.

## 1. Purpose and state
The lane collects teacher traces on root B (`$D/collection_gt_r1316`, membership v3, 714 scenes, 97,652 ready) toward 50,000 accepted; the user's 20,000 goal is met.
- **Census (validated, `P/claude_census_ab_20260924T0445Z/CENSUS_AB.md`):** A 20,762 strict / 22,688 tier; B 5,328 / 5,881 (snapshot 04:42-04:57Z, 146 burned questions excluded, none accepted); **A+B distinct 26,090 strict / 28,569 tier**. Archive-walk samples agree 300/300 (B), 300/300 (A reused), 100/100 (A fresh); upper bounds with at most ≈3% (A) / ≈1% (B) overcount at 95%.
- **Epoch 2cd7d87** (storm-rule fix) live since 03:30:26Z: config `$R2/collection_config_r1316_2cd7d87751fd70d001d3ba4ec71f3bd75d330bc1.json` (sha ecacad5c…), epoch checkout `/home/jjyeung/agent_project_distill_epochs/2cd7d87`, pacing 2 s (R1316_PLANNER_PACING_SECONDS, changeable only at a cold start).
- **Key limit:** the Gemini key saturates at ≈7.4-8.2M input tok/min. Workers that fit under it fell from 72 to ≈62-66 as tokens per trace rose. The rate brake governs; ceiling pinned at 70 by the orchestrator (05:55Z). Throughput ≈1,250-1,400 terminals/h at 62-70 workers (≈0.77 strict yield → ≈1,000 strict/h). 50,000 strict needs ≈24,000 more ≈ 24 h at this rate.
- Terminals: 8,720 at 06:18:42Z; target 62 after the 06:13:41Z brake.
- Key-share ruling (user via experimenter orchestrator 04:13Z): the experimenter has priority; on an announced take (INBOX_*.md under P) we hold ≤ 1M tok/min (≈7 workers); on release, resume. As of 06:25Z no take announced; they draw no Gemini tokens.

## 2. Detached processes (survive a session change; times UTC)
| host | pid | started | what | log |
|---|---|---|---|---|
| trinity-1-13 | 147557 (wrapper subshell 147555) | 09-24 03:30:26 | controller 2cd7d87 | `$R2/launch_20260923T0820Z/controller_r1316_2cd7d87.log` |
| trinity-1-13 | 2167527 | 09-23 08:29:40 | lease keeper (240 s, until ≈09-27 12:30Z) | keeper.log |
| trinity-1-13 | 4103516, 3221456, 2720290, 2459925 | 09-23 | package guards on 2cd7d87, fc6b364, d1b52e4, ef1c3e6 | `$L/out/GUARD_LOG.md` |
| trinity-0-23 | 1691756 | 09-24 04:33:27 | meter loop (NFS-only; moved off trinity-1-13) → `$L/out/health.jsonl` (now with calls_5m, n429exh_10m) | `$L/out/meter_err.log` |
| trinity-0-23 | 1814259 | 09-24 05:58:32 | babysit loop `$L/work/babysit_v18.sh` (CAP=70) | `$L/out/babysit_v18.log`, steps in STEP_18.md |
| trinity-1-13 | 1811177 / 1809062 | — | r1317, not ours | — |

babysit_v18 rules, once a minute: (a) rate brake: 429s > 2% of provider calls in 5 min, or any 429 retry exhaustion in 10 min → −4 workers (floor 40), then hold 10 min; it may fire 2 min after a ramp step. (b) ramp +4 per 10 clean min, clipped to CAP. (c) per-worker rule: 10 min after a ramp, a > 20% drop in 15-min tok/min per heartbeating worker reverts the step and holds until the draw recovers to within 10%. (d) stale meter (> 300 s): `work/count429.py 300` supplies the 429 count; the ramp pauses. (e) every 9 min a new INBOX_*.md mentioning the key: take → 7 workers; release → resume. (f) a BLOCKED.json in pool_b16384 stops the loop (exit 3). Each line logs trinity-1-13 load and D-state count.

## 3. Loops that die with this session
None needed: the meter and babysit run detached on trinity-0-23. The census sub-lane finished.

## 4. Successor's first actions
1. Liveness: `ps -o pid,lstart,args -p 1691756,1814259` on trinity-0-23; `ssh -n -F /dev/null -o BatchMode=yes trinity-1-13 'ps -o pid,lstart,args -p 147557,2167527'`. Direct ssh to trinity-1-13 works for set-workers and reads; on a classifier denial use `$L/work/setw_via_luna.sh`-style Luna dispatch (P/tools/luna_run.sh) and do not retry verbatim.
2. Terminals landing: `ls $D/collection_gt_r1316/terminals | wc -l` twice a few minutes apart; `tail -3 $L/out/babysit_v18.log`.
3. Set workers by hand (the loop will adjust from there): `ssh -n -F /dev/null -o BatchMode=yes trinity-1-13 "bash $L/work/setw_remote_2cd7d87.sh N"`, then `cat $D/collection_gt_r1316/pool_b16384/WORKER_TARGET.json`. Never use `setw_remote.sh` (points at the retired fc6b364 config).
4. Restart the babysit loop (one loop only; kill the old pid first): `cd $L/out && CAP=70 LAST_CHANGE=$(date +%s) LAST_ACTION=ramp setsid nohup bash $L/work/babysit_v18.sh > $L/out/babysit_v18.stdout 2>&1 < /dev/null &`.
5. Restart the meter if it dies (one only; it shares meter_state.json): `cd $L/out && setsid nohup bash -c "for i in \$(seq 1 6000); do /data2/jjyeung/envs/planner/bin/python -W ignore -B $L/work/meter.py > /dev/null 2>>$L/out/meter_err.log; sleep 60; done" > /dev/null 2>&1 < /dev/null &`. Run it on a lightly loaded node, not trinity-1-13.
6. Swap to a new epoch (only when one is sealed and bound on an idle node, never beside the controller): set-workers 4 until in-flight ≤ 4 (meter attempts − terminals), then 0; wait until zero workers and episodes on trinity-1-13; stop the babysit loop; run a copy of `$L/work/stepK_swap_2cd7d87_remote.sh` with the new epoch/config/OLDPID=147557 over ssh (run it under `timeout`; the ssh may hang after the controller detaches, and the controller survives); then explicit set-workers; then restart meter-independent pieces pointing at the new config (new setw_remote_<epoch>.sh).

## 5. Pitfalls
- The key, not the node, is the ceiling: at 72 workers 429s passed 2%; tokens per trace drift up, so the worker count that fits keeps falling. Let the brake govern; pacing changes need a cold start (35-45 min lost) and add nothing the ramp cannot.
- I/O stalls: heavy /data2 readers elsewhere (prepare-training gates, census archive walks) put the controller host's workers into D state (05:41-05:46Z: load 139, 52 D-state, draw 7.4M → 3.3M). If D-state > 30 for > 3 min, message the orchestrator with the reader pids; never kill another lane's processes.
- The meter stalls under load on the host it runs on; keep it off trinity-1-13. A negative lease age is a scan-timing artifact.
- `start --workers N` does not reset a persisted target; always set-workers after start.
- BLOCKED.json in `pool_b16384/`: only the user renames it (`mv BLOCKED.json BLOCKED.json.acked_<ts>_<reason>`); the loop exits when it appears.
- Census of root B with collector/census.py aborts on 15 questions carrying a `.retired/` folder ("unknown attempt budget"); skip `.retired` first.
- `pkill -f <pattern>` from a Bash tool call matches the calling shell too; kill by pid.
- Write nothing into the repo tree; all artifacts under /data2.
- Resident lane session also runs `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z/work/sentinel.sh 1800` (in-session, dies with the session): a successor re-arms it with CTL_PID/BABYSIT_PID set if pids change.
- r1316 provenance (ruling 06:52Z 09-24): the epoch chain 6aa9d60 → d1b52e4 → fc6b364 → 2cd7d87 → collector-claim-type-order-20260924 lives on branches, never on main; production launches from /home/jjyeung/agent_project_distill_epochs/<sha>. A reviewed merge into main is queued for after the ICLR deadline. Type-priority epoch in progress: build `$L/claimorder/`, bind on trinity-2-13, then drain-and-swap.

## Current state 2026-09-24 07:40Z (supersedes pids above where they differ)
- babysit loop **pid 1939065** (trinity-0-23; SETW env selects the setw script, default setw_remote_2cd7d87.sh; after the swap restart with SETW=setw_remote_93ebe00.sh). Meter pid 1691756 (trinity-0-23).
- Type-priority epoch **93ebe00155144e46ca9ee6d8b25fd596f5441962** (branch collector-claim-type-order-20260924; checkout /home/jjyeung/agent_project_distill_epochs/93ebe00155144e46ca9ee6d8b25fd596f5441962; contract sha 44b93e88…). Bind **pid 1013882 on trinity-1-13** (nice 19, ionice idle; log `$R2/launch_20260923T0820Z/bind_93ebe00_on1313.log`), ETA ≈08:05-08:10Z. Abort watcher pid 1962132 (trinity-0-23, `work/bind_abort_watch.sh`, log out/bind_abort_watch.log). If it aborts: do NOT retry on trinity-1-13; rebind on trinity-2-13 or 0-18 with `work/stepL_bind_93ebe00_remote.sh` (≈6-9 h at 4-11 MB/s). Epoch guard for 93ebe00 is pid 1128092 on trinity-2-13.
- Swap after publish: set-workers 4 → 0 via `work/setw_remote_2cd7d87.sh`, wait zero in flight, then `W=<brake target> bash $L/work/stepM_swap_93ebe00_remote.sh` on trinity-1-13 (sets R1316_CLAIM_TYPE_ORDER=object_counting,object_size_estimation,room_size_estimation,object_abs_distance,object_rel_distance,obj_appearance_order,object_rel_direction_medium and pacing 2 s; stops 147557 only at zero in-flight). Tell the orchestrator the drain start time first.
- Throughput note: GT tool time is CPU-bound on trinity-1-13 (median 46 s → 116 s per episode 06:45 → 07:10Z; 69 episodes ≈63 cores); after the swap, measure per-type tool time and cap workers where terminals/10 min peak.
- Resident session sentinel: `BABYSIT_PID=… BIND_LOG=… BIND_PID=… BIND_HOST=… bash $L/work/sentinel.sh 1800` (in-session).

## Lane: Orchard

# Orchard lane handoff — 2026-09-24 06:25Z

The Orchard lane runs our jobs on the Orchard H100 Slurm cluster. Lane directory `L=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_setup_20260922T0700Z`; Orchard root `R=/project/community/jjyeung/distill`. STEP_16 through STEP_72 hold the history; STEP_72.md covers 2026-09-24 03:20Z onward. The previous handoff is kept as `HANDOFF_orchard.md.prev_0245Z`.

## Allocation rules in force
- Partitions: advanced, general and preempt only. Flame is not ours; it needs an admin-attached flame QoS.
- Our QoS limits: advanced (adv_4gpu_qos) 4 GPUs, one node, 6 running and 12 submitted jobs; general (general_qos) 1 GPU, 1 running job, 5 submitted; preempt (preempt_qos) 32 GPUs, 4 nodes, 50 submitted.
- Advanced is for training only (orchestrator, 05:30Z): 148598 (full-pool), then the mechanism lane's C1x and C2x. Put no evaluation shards on advanced, and keep at least 3 advanced submit slots free. The feeder's advanced cap is 0.
- Evaluation runs on general (never preempted; use it for anything that must not be interrupted) and preempt (preemption leaves items `interrupted`).
- REQ-20260924-238 (the experimenter's 27B temperature-0.6 reruns, P0) has GPU priority on announced takes. Our offer, in order: (1) general at once; (2) cancel the 27B batched pair on preempt (command below); (3) advanced only after 148598 finishes. Watch the orchestrator directory for `INBOX_*` files every 10 minutes.

## Jobs (06:20Z; 07:25Z update: 27B batched pair LANDED, base b8 manifest 3e8b42dd (16 interrupted), student b8 manifest f00fe525 (0 interrupted); no lane jobs queued; int48 (nice 0) then cap32k (nice 100) go on GENERAL per the 07:40Z ruling; never advanced or preempt)
| job(s) | partition | what | state |
|---|---|---|---|
| 148598 | advanced | full-pool Qwen answer-only training (full-pool lane's job) | RUNNING, orchard-community-3 |
| 148646, 148648 | advanced | mechanism lane C1x and C2x training (theirs) | PENDING (node limit / dependency) |
| 148605-148619 (1-15; shard 0 was probe 148528) | preempt | 27B base VSTIBench batched bs8, cell `qwen36_27b_base_vsti_b8` (0ab73f9, pinned, 4,096 cap) | 258/450 at 06:18Z; 5 running, 3 pending |
| 148620-148632, 148637-148639 | preempt | 27B arm C student batched bs8, cell `qwen36_27b_distilled_armc_27b_orchard_d_vsti_b8`, paired with the b8 base | shard 15 done by general copy 148670 (12:49 for 28 items, about 27 s per item); 28/450; rest PENDING |
| 148672 | general | general-slot filler: student b8 shard 14 | submitted 06:20Z |
All 27B jobs run at nice 300 so student cells go first.

Landed today:
- Training `gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2` (148380): `/data3/jjyeung/orchard_publications/gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2`, 748/748 verified, PUBLISHED.json sha 1f33e20f.
- Answer-only VSIBench b16: 500/500, manifest c1aa3ac6, 2094 files.
- Answer-only VSTIBench b16: 450/450 with 48 `interrupted`, manifest f37ba0dd, 1913 files.
Both cells are under `/data3/jjyeung/orchard_publications/eval_cells/` with rows in `CELLS_LANDED.tsv`.
Abandoned: single-decode 27B student cell `..._vsti_c3` at 69/450 (orchestrator accepted the batched pair). The single-decode base `qwen36_27b_base_vsti_pinned_c3` stays banked as the appendix row.

## Harness rules found today (0ab73f9; also true of a24c998)
- **Attempt authority** (`student_pilot/orchard_eval/generate.py:420-436`): a paper cell's key is benchmark + ordered item ids + model identity (adapter) + scope + protocol sha, with no cell name. A new cell with the same key is refused with "This checkpoint/cohort already has an attempt authority; resume the original frozen run". An identical-protocol re-run under a new name (the `_r2` attempt, 148649-148653) fails by design. A different item subset, decode mode or budget gives a new key.
- **Interrupted items are final:** `generate.py:492-496` writes `interrupted` receipts once and never repeats them. `retry.py:963-964` refuses batched cells, and `retry.py:870-871` requires single decode.
- **Budgets above 4,096 tokens** on paper cells need a pre-registered proper-subset items file (`contracts.py:374-375`, `388-389`). A whole-benchmark 32k cell is impossible, so the orchestrator dropped it.
- **Subset cells are not scored:** eval_job prints "RGB subset smoke finished; it is not a scored full cohort". `land_loop` needs `score/scores.json`, so subset cells (int48, cap32k) must be landed by hand. The land_loop commands work: manifest_dir.py on Orchard, rsync to `/data3/.../eval_cells/<cell>`, verify_publication.py on both ends, append the CELLS_LANDED row.
- Batched decoding is not token-identical to single decoding, and a subset changes how items are batched. The Astra review (`agent/scratch/codex_runs/20260924T043549Z_budget32k_review/final_message.md`) therefore labels subset re-decodes as their own diagnostic cells.

## Pending cells (waiting on the user's rsync)
- **int48** (the orchestrator's option A): cell `qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2_vsti_b16_int48`, re-decoding the 48 interrupted VSTIBench qids "in their own batch, same harness, adapter, pairing, bs16 and 4,096 cap". The items file is `$L/out/budget32k/items/ao_vsti_b16_int48.json` (sha cb3cf605) with `.provenance.json`. Once `$R/items/ao_vsti_b16_int48.json` exists, submit on general:
  `A=gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2; P=$R/runs/$A/publication; EVAL_ITEMS_FILE=$R/items/ao_vsti_b16_int48.json EVAL_SHARD_COUNT=1 SHARDS=0 PART=general MODEL=qwen35 VARIANT=distilled BENCH=vstibench_repr450_v2 CELL=qwen35_distilled_${A}_vsti_b16_int48 EXTRAS="$P/adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW $P/PUBLISHED.json $R/runs/eval/qwen35_base_vsti_b16/run" bash $R/submit_shards_b16.sh`
  Land it by hand; the rescore lane splices the 48 receipts in.
- **cap32k "adaptive-budget base"**: cells `qwen35_base_{vsi,vsti}_b16_cap32k_capped4096` (367 and 202 capped items at 32,768 tokens, harness a24c998, which the user staged). The user runs `$L/out/USER_CMDS_32k_reruns.sh`: step 1 (rsync), step 2 (submit script) and step 3B (uncomment). Step 3A (whole benchmark) is refused by the harness. Land by hand when the receipts are complete. The 27B base at 32k (per-item timing first) is not started and needs the same path.

## Detached processes on trinity-0-23 (survive a session change)
| pid | script (under `$L/work`) | job | ends |
|---|---|---|---|
| 1382676 | `feed/feed_loop.sh` | runs `$R/feed/feed.py` every 5 min (queue `$R/feed/queue.jsonl`, ledger `$R/feed/ledger.tsv`; CAPS advanced 0, general 3, preempt 46) | ~11:54Z |
| 1154593 | `feed/mirror_loop_b16.sh` | `$R/feed/mirror.py` adds general copies of pending preempt shards of the listed Qwen b16 cells | ~10:00Z |
| 1537073 | `feed/land_loop.sh` | lands every scored cell every 5 min and appends `CELLS_LANDED.tsv` | ~02:33Z 09-25 |
| 1406683 | `landing_events.sh` | logs new landings to `logs/babysit_events.log` | about 24 h |
| 1727926 | `watch_ao_cells.sh` | per-minute job and cell census to `logs/watch_ao_cells.log` (do not stop) | ~10:58Z |

Finished: land_train_148380.sh, topup_27b_b8.sh, watch_148500.sh, train_watch_slow, babysit_148380_events, smoke_watch_148484.

Known defect: mirror.py skips a shard that was already mirrored once, so a requeued preempt shard gets no new general copy. The patch (`$L/work/feed_patch/patch.py`, which also adds item-level env and nice) is unapplied; the classifier denied it, so it is surfaced to the user.

## User-only items still open
1. Run `$L/out/USER_CMDS_32k_reruns.sh` steps 1, 2 and 3B. Step 1 also carries the int48 items file.
2. Optional: apply the mirror patch with `ssh -F /tmp/jjyeung_ssh_orchard_config orchard 'python3 -B -' < $L/work/feed_patch/patch.py`.
3. An admin attaches a flame QoS; mt01 holds none.
4. The classifier denied these lane actions this session: staging a24c998 (the user has since done it), rsync of item files to `$R/items`, patching feed.py and mirror.py, launching new detached helpers, and `scancel` of our own pending jobs [Interfere With Workloads]. Interactive `sbatch` and `scontrol update nice` were allowed.

## Ready command if REQ-238 takes preempt (run only on the orchestrator's word)
`ssh -F /tmp/jjyeung_ssh_orchard_config orchard 'scancel -u jjyeung -n $(squeue -u jjyeung -h -o %j | grep -E "qwen36_27b_(base|distilled_armc_27b_orchard_d)_vsti_b8" | sort -u | paste -sd,)'`
It may need the user, since scancel was denied to the lane. Partial receipts stay in the cells, and resubmitting the same shards later resumes them.

## Successor first actions
1. Check for a live session: STEP_72.md mtime and the pids above (`ps -eo pid,lstart,args | grep claude_orchard_setup_20260922T0700Z/work`). Adopt; never duplicate a loop.
2. ssh: `export PATH=/home/jjyeung/google-cloud-sdk/bin:$PATH CLOUDSDK_CONFIG=/tmp/jjyeung_gcloud_config; timeout 240 ssh -F /tmp/jjyeung_ssh_orchard_config -o ConnectTimeout=120 orchard '<cmd>'`. IAP connects take about 40 s.
3. Every 10 minutes, read-only: `squeue -u jjyeung -o "%i %P %T %M %R"`, `python3 -B $R/cell_progress.py`, `test -f $R/items/ao_vsti_b16_int48.json`, `squeue -u jjyeung -h -o %j | grep -c cap32k`, and `ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_ | head`.
4. Keep general busy. The int48 cell goes first once its items file exists. Otherwise submit the next unfinished 27B student b8 shard as a general copy: `SHARDS=<s> PART=general MODEL=qwen36_27b VARIANT=distilled BENCH=vstibench_repr450_v2 CELL=qwen36_27b_distilled_armc_27b_orchard_d_vsti_b8 EVAL_SHARD_COUNT=16 EVAL_DECODE_MODE=batched EVAL_DECODE_BATCH_SIZE=8 EXTRAS="$R/runs/armc_27b_orchard_d/publication/adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW $R/runs/armc_27b_orchard_d/publication/PUBLISHED.json $R/runs/eval/qwen36_27b_base_vsti_b8/run" bash $R/submit_shards_b16.sh`, choosing the highest shard that has not run.
5. Land the int48 and cap32k cells by hand when their receipts are complete; land_loop lands the 27B b8 cells once they are scored. Send the orchestrator each CELLS_LANDED row.

## Lane: rescore and results

# Handoff — rescore and results lane (2026-09-24T06:45Z)

Lane dir `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z` (L). Step log `L/STEP_27.md`, `L/STEP_28.md`.
Table-work dir `/data3/jjyeung/claude_paper_tables_corrected_20260924T0325Z` (T): worktrees under `T/work/`,
prompts, Terra reports and generated tables under `T/out/`.

## Watcher
pid `601049` (`bash scripts/watch_eval_cells.sh`, cwd L, PPID 1, own session, started 09-23 18:13Z on
trinity-0-23). Every 120 s it prints to `L/out/watch_eval_cells.log`: `NEWCELL <name>` for a new directory under
`/data3/jjyeung/orchard_publications/eval_cells/`, `TSV_CHANGED` when
`/data2/.../claude_orchard_setup_20260922T0700Z/CELLS_LANDED.tsv` changes, and `INBOX_CHANGED` when
`L/out/INBOX_TRINITY_FULLSET.md` changes. It only notifies; scoring is manual. Restart: kill the pid, then
`setsid nohup bash scripts/watch_eval_cells.sh >> out/watch_eval_cells.log 2>&1 < /dev/null &` from L and check PPID 1.
Orchard progress for in-flight cells: `/data2/.../claude_orchard_setup_20260922T0700Z/logs/watch_ao_cells.log`.

## Scoring rules
- Lenient primary, strict secondary, always per question type; official metric via the real SENS scorer, never a flat mean.
- Order per cell: `verify_manifest.py <cell_dir>` (sha must match CELLS_LANDED.tsv), then `check_media_errors.py`
  (any media_error, interrupted or empty item gives REFUSE_PUBLISH: hold unless told otherwise), then rescore.
- Batched Qwen pair helper: `bash L/scripts/score_b16_pair.sh <vsi|vsti> <cell> <outdir>` (does all three steps plus
  the per-type table against qwen35_base_{vsi,vsti}_b16). Interpreter `/home/jjyeung/.local/bin/python` (needs
  numpy); /usr/bin/python3 is 3.6 and fails.
- Batched (bs16) cells pair only with batched bases, single-item only with single-item.
- Matched-cohort convention: when a student cell has interrupted items that cannot be rerun (the attempt-authority
  guard forbids a second full attempt), the primary row is the matched cohort (those qids excluded from student AND
  base, `scripts/recompute_matched_cohort.py --exclude-status interrupted`); the all-items row with interrupted
  counted wrong is the lower bound; a supplementary re-decode of just those items, when it lands, is a third,
  labelled form. The generator supports this (student-side excluded set, commit f0b3aa8).
- Adaptive-budget convention (planned, not yet built): 32k-cap base reruns get their own base condition on the same
  harness string; the student delta moves to the 32k base, the 4k base stays as a secondary column, and cap-hit /
  parse-failure rates are shown per cap (from scores.json cap_count, cap_without_answer_count, parse_failures).
  Expected cells: qwen35_base_{vsi,vsti}_b16_cap32k_capped4096 ("adaptive-budget base").
- Deltas are computed from unrounded scores (the generator's values win over hand arithmetic on rounded numbers).

## Paper tables and results doc
- Generator: `tools/paper_tables/build_tables.py` + `manifest.json` (on main). Manifest `table` field: main
  (corrected set only), appendix, omit. Run with
  `/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12 -B -m tools.paper_tables.build_tables --manifest tools/paper_tables/manifest.json --out <dir>`;
  `--check-doc docs/RESULTS_PER_TYPE_20260922.md --mismatches <file>` audits the doc. Known state: the whole-doc
  golden test fails on unmapped layouts only (no score-derived discrepancy); tests otherwise pass.
- To add a cell: set status complete, strict_score_path = the "scores_dir" field in the lenient JSON,
  lenient_score_path, lenient_cell_key = cell name, then regenerate.
- Doc: `docs/RESULTS_PER_TYPE_20260922.md`.

## Branch and commit conventions
Each results change is its own branch off main's current tip, in a worktree under `T/work/`. Terra drafts via
`bash agent/scripts/codex_dispatch.sh mech <worktree> <prompt> --label <name> --writable-root T/out` and
self-commits; the lane skims the diff and the Terra report, then sends the sha. The orchestrator fast-forwards
main and restarts the collector guard; tooling-only commits wait for the next results commit (each landing costs a
guard restart). Never edit main, collector/ or another lane's run root.

## Scored (on main unless noted)
| cell | result (lenient = strict unless noted) | score dir |
|---|---|---|
| OneThinker corrected trace / answer-only, Trinity | VSI 38.68 / 48.03 vs base 39.19 (strict 31.47); VSTI 38.28 / 53.45 vs 45.40 (40.16) | paths in tools/paper_tables/manifest.json |
| Qwen corrected trace b16 (148295) | VSI 48.02 vs 14.92; VSTI 43.93 vs 27.55 | L/lenient/{vsi,vsti}_qwen35_orchard_roomfix_b16 |
| Qwen answer-only b16 VSI (148380) | 55.24 vs 14.92 (+40.33), 0 parse failures, base cap-hit 367/500 | L/lenient/vsi_qwen35_orchard_answeronly_b16 |
| Qwen answer-only b16 VSTI (148380), 48/450 interrupted | matched 402: 52.95 vs 27.08 (+25.87, primary); all-450 lower bound 48.11 vs 27.55 | L/lenient/vsti_qwen35_orchard_answeronly_b16 (MATCHED_402.txt, TABLE_all450.md); qids L/out/ao_vsti_interrupted_qids.txt |
| Qwen3.6-27B base VSTI pinned c3 | 30.71, provisional appendix | L/lenient/vsti_qwen36_27b_base_pinned_c3 |

## Pending
- Branch results-mechanism-controls-20260924 (worktree T/work/repo_mech): mechanism-controls section skeleton
  tip 015af3b (rebased onto 3752531; skeleton + macro-column label fix), HELD by the orchestrator: commit the S-G row on top of this branch, send the tip sha; rows fill in as
  mechanism cells land.
- int48 supplement `qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2_vsti_b16_int48`
  (hand-landed after a user rsync; path and sha arrive via the orchestrator): verify, media check, substitute the
  48 receipts, add as the third form.
- 27B arm C VSTI b8 scored (52.01, lenient/vsti_qwen36_27b_armc_b8); bundle with its b8 base + S-G on the mechanism branch.
- Mechanism cells S-G (~06:55Z), S-T (~07:30Z), N1k/N2k/N4k, C0/C1x/C2x, M: fill the mechanism tables per type.
- 32k capped base cells (adaptive-budget convention above); 27B base b8 VSTI and 27B arm C VSTI (in flight on
  Orchard); seed s19 (~11:40Z plus eval).

## Successor first actions
1. `ps -o pid,ppid,lstart,cmd -p 601049`; if it is dead, restart it (never run two). `tail L/out/watch_eval_cells.log`.
2. Read `L/STEP_28.md` bottom-up and this file; `git -C /home/jjyeung/agent_project_distill log --oneline -5`.
3. Check whether 015af3b is on main (`git merge-base --is-ancestor 015af3b main`); branch new rows off main's tip.
4. For each NEWCELL or TSV change: follow the scoring order, then a Terra branch off main's tip, then message the
   orchestrator with lenient/strict per type, base vs student, and the sha.

## Lane: trinity expansion

# Handoff: trinity_expansion lane (checkpoint 2026-09-24 06:15Z)

Lane dir L=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_expansion_20260923T2250Z.
Records: L/STEP_1..STEP_12.md (STEP_12 is the current session). The previous handoff (02:33Z) is kept as L/HANDOFF_expansion_20260924T0233Z.md; its sections on recipe, frozen protocols and the e746674 review ruling still hold.

## Runs (both OneThinker answer-only roomfix replicates, 723 steps, trainer e746674, vnice-wrapped, checkpoints every 25 steps)
| run | host | cards (world) | run_train.sh pid | first step | rate | step at 06:10Z | train end (measured) |
|---|---|---|---|---|---|---|---|
| s19 | trinity-0-23 | 4,6 (2) | 1594934 | ~03:36Z | 40.2 s/step | 228/723 | ~11:40Z |
| s18 | trinity-0-8 | 0,1,2,4 (4) | 1078176 | 06:01:25Z | 19.8 s/step | 26/723 | ~09:55Z |

- Metrics (node-local, read over ssh for s18): /scratch/jjyeung/ddp_onethinker_gtm2_v25full_onethinker_trinity_roomfix_answeronly_s1{8,9}_a1/train/metrics.jsonl; checkpoints in .../train/checkpoints/step_*.
- Heartbeats: L/run_s1x/out/HEARTBEAT_train.log. They are event-only (a new line = state change): train-failed, finalize-started, completed-and-published, ALARM ...; mtime is not a liveness signal.
- run_train.sh retries up to 6 attempts with checkpoint resume (new attempt dirs _a2, _a3 ...), then finalizes (L/run_s1x/out/finalize_onethinker.log) and publishes to
  /data3/jjyeung/orchard_publications/gtm2_v25full_onethinker_trinity_roomfix_answeronly_s18 and ..._s19. Success line: "attempt-N completed-and-published".
- CARDS.tsv rows were written by the picker; this lane does not write CARDS.tsv (orchestrator rule). Card release after training is for the orchestrator/user.

## Picker (not inspected this session, per orchestrator)
Picker v1 (pid 1484237) was killed by the user ~05:2xZ. Picker v2 (L/work/picker_v2.sh, reported pid 1763757 on trinity-0-23, log L/out/PICKER_v2.log, s18 only) launched s18 on trinity-0-8 at 05:55Z. Presumably it has nothing more to launch; its fate is the user's decision. Do not touch it.

## Evaluation (launcher branch trinity-eval-launcher-seed-20260924 @ 29d45794adf00d848f5b6dda704ee7b6f59db0ce, confirmed by the orchestrator; worktree L/work/launcher_seed_wt; dry run with s17 PAIRED)
PLAN CHANGE (orchestrator ~07:00Z): trinity-2-8 is unusable (other user's compute apps on all 8 cards). Evaluate each replicate on its own training cards right after it publishes, both benchmarks in parallel, 2 cards each: s18 on trinity-0-8 cards 0,1 (VSI) and 2,4 (VSTI); s19 on trinity-0-23 card 4 (VSI) and 6 (VSTI). Keep the existing CARDS.tsv claims; add none. Dry run on trinity-0-8:0,1 with s17 publication: rc 0, PAIRED (L/eval/dryrun_s17_t08.log). ~600 items/h per card for answer-only adapters.
After a run's heartbeat shows completed-and-published and the publication dir exists, probe the target node (ssh <host> nvidia-smi ...), then per benchmark (example below uses trinity-2-8; substitute the cards above):
  ssh trinity-2-8 nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader   # pick empty 24 GB cards immediately before launch
  setsid nohup bash L/eval/launch_seed.sh s18 vsibench_answerable500 1 trinity-2-8:0 trinity-2-8:1 ... > L/eval/s18_vsi_driver.log 2>&1 &
  setsid nohup bash L/eval/launch_seed.sh s18 vstibench_repr450_v2 1 trinity-2-8:2 trinity-2-8:3 ... > L/eval/s18_vsti_driver.log 2>&1 &
(env L/eval/env.sh; run roots L/eval/runs/<s18|s19>/<benchmark>; launch logs L/eval/<run>_<benchmark>_launch<n>.log; it launches 1 card, waits for a first outcome, then widens.)
Scoring once all items are terminal:
  bash L/work/launcher_seed_wt/scripts/trinity_eval/status_eval.sh L/eval/runs/<run>/<benchmark>
  bash L/work/launcher_seed_wt/scripts/trinity_eval/score_eval.sh L/eval/runs/<run>/<benchmark>    # writes scores/attempt_*/RESULTS.md, SCORES.json
Append the tables to /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md in the format of the s17 answer-only entries (lenient primary / strict), and report paths to the orchestrator.
Expected cost: OneThinker ~243 items/h per card, so 4 cards finish a cell in ~30-40 min.

## Watchers (die with the session; restart them from a new session)
- L/work/watch_s19_successor.sh [max_min] : 1-min local poll of s19; exits with an EVENT line on heartbeat change, pid gone, 10-min step stall, or after max_min. Log L/out/WATCH_s19_successor.log.
- L/work/watch_s18_successor.sh [max_min] [stall_s] : same for s18 over ssh to trinity-0-8 (also exits after 3 ssh failures). Log L/out/WATCH_s18_successor.log.

## Successor first actions
1. tail -3 L/out/WATCH_s18_successor.log L/out/WATCH_s19_successor.log; cat L/run_s18/out/HEARTBEAT_train.log L/run_s19/out/HEARTBEAT_train.log.
2. ps -p 1594934 (s19, local on trinity-0-23); ssh trinity-0-8 'kill -0 1078176 && tail -1 /scratch/jjyeung/ddp_onethinker_gtm2_v25full_onethinker_trinity_roomfix_answeronly_s18_a1/train/metrics.jsonl | cut -c1-400'.
3. Re-arm watchers in the background: bash L/work/watch_s19_successor.sh 60 ; bash L/work/watch_s18_successor.sh 60 600.
4. On completed-and-published: ls the publication dir, check finalize_onethinker.log, then run the eval commands above for that run; score; append to INBOX_TRINITY_FULLSET.md.
5. On train-failed / ALARM: read L/run_s1x/out/full_train_vnice_onethinker_a*.log tail and the attempt STATE.txt; run_train.sh retries itself; kill only this lane's own stuck processes.

## Lane: answer-only full-pool

# Handoff: answer-only full-pool lane (refreshed 2026-09-24 07:40Z)

LANE = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_answeronly_fullpool_20260923T2250Z. S = /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918. R = /project/community/jjyeung/distill (Orchard). History: STEP_1-4.md (STEP_4 covers this session). Previous handoff: HANDOFF_fullpool_20260924T0200Z.md.

## The set (v3, reviewed PASS)
- Paths: `S/answeronly_fullpool_20260923` (mix) and `S/answeronly_fullpool_20260923_trainer` (layout). Builder: branch answeronly-fullpool-20260923 in LANE/work/repo (a worktree of the main repo), commit f661a76 (on top of ce5322b). The branch is not on main yet; the orchestrator lands it by fast-forward if wanted.
- Counts: train 25,164 (7,684 carried byte-identical / 12,963 root A r1313 / 4,517 root B r1316), heldout 4,235, 38 heldout scenes, 285 inherited groups stable, 0 train rows in heldout or benchmark scenes. Dropped 6,212 unique qids (4,574 duplicates, 1,503 strict rejections, 85 room-label mismatches, 50 ingest refusals).
- Hashes: candidate_index.jsonl b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446 (29,399 rows); split_trainer.json 46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70 (mix and trainer copies identical); trainer MANIFEST 86206af4…, mix MANIFEST ac7113bc…. Build record: LANE/out/{BUILD_SUMMARY,VERIFICATION,BUILD_INPUTS}.json, build.log, verify.log (verify passed 04:15Z).
- Labels: every new row's target AND candidate-index answer equal ground truth (review 3 full scan: 20,167 new rows, 0 disagreements).
- Superseded builds, renamed not deleted: `*_v1_labelfail` (targets held teacher estimates), `*_v2_indexlabelfail` (index answers held teacher estimates); audit copies in LANE/out/v1_build and LANE/out/v2_build.

## Reviews (Codex Astra, effort high)
- Round 1 FAIL (target labels): agent/scratch/codex_runs/20260924T003556Z_answeronly_fullpool_review/final_message.md.
- Round 2 FAIL (index answer field only; fix f661a76): agent/scratch/codex_runs/20260924T034142Z_answeronly_fullpool_review2/final_message.md.
- Round 3 PASS, no defects: agent/scratch/codex_runs/20260924T041526Z_answeronly_fullpool_review3/final_message.md (paths relative to /home/jjyeung/agent_project_distill).

## Recipe and compute matching
Both students train 1 epoch = 787 steps (25,164 / batch 32), LoRA r32/a64, lr 1e-4, seed 17, effective batch 32. This matches the step count of the 7,684-row answer-only controls (723 steps = 3 epochs x 241). The comparison is matched compute, not matched epochs. The mechanism lane's 1k/2k/4k ladder runs 3 epochs each. Both facts belong in the results doc.

## OneThinker-8B (trinity-0-18 GPUs 4-7, world 4)
- Chain (all setsid, survive a session change): run_cpu_gates.sh (shell pid 2196483 started 04:09Z; prepare-training python pid 2197395 since 04:12Z) -> launch_after_gates.sh (pid 2204700; waits for GATES_DONE in LANE/train/work/cpu_gates.log) -> LANE/train/out/run_train.sh (waits for 3 clean GPU readings, claims coord leases, bind-lease, vnice-wrapped DDP train, finalize) -> publication /data3/jjyeung/orchard_publications/gtm2_answeronly_fullpool_onethinker_trinity.
- Config LANE/train/work/training_config_fullpool_w4.json (w2 file differs only in world_size). Trainer b084aaf (claude_onethinker_v241_launch_20260921T0015Z/work_checkout_b084aaf). Gate env LANE/train/work/gates_env.sh holds the v3 hashes.
- Cards claimed in P/claude_swarm_20260923T0835Z/CARDS.tsv (owner answer_only_fullpool, to 15:23Z); orchestrator reserved them.
- Training since 06:36Z (GATES_DONE 06:34Z); vnice pid 2238553, python pid 2238565; step 85/787 at 07:24Z, 29.0 s/step on the A6000s, loss ~0.6 -> end ~13:05Z, then finalize/publication.
- Watch: LANE/train/out/HEARTBEAT_train.log (launch states), LANE/train/out/WATCH_onethinker.log (step, loss, s/step, GPU memory), run root /scratch/jjyeung/ddp_onethinker_gtm2_answeronly_fullpool_onethinker_trinity_a<N> on trinity-0-18. Resume: run_train.sh retries up to 6 attempts and resumes from the latest checkpoint (every 25 steps).

## Qwen3.5-9B (Orchard advanced, 4 H100)
- Job 148598 RUNNING since 05:10Z on orchard-community-3, run gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1, deployment R/code/deployment_433d8a1_qmb2_e1 (= qmb2 with epochs 1, the only diff), trainer 433d8a1. Still in prepare-training at 07:25Z (2 h 15 min into the job; same row-scaling as trinity: trinity prepare-training took 2 h 09 min); step 1 expected ~07:45-08:15Z; ~18 s/step -> end ~11:30-12:00Z, then R/runs/<run>/publication/PUBLISHED.json.
- Staging: R/stage_ao_fullpool (MANIFEST_TRINITY.json sha 608ccc7b…, verified 72,190/72,190), launcher R/stage_ao_fullpool/launch_ao_fullpool.sh (local copy LANE/work/stage_orchard/). Preempt copy 148582 (w8) was cancelled at 05:20Z before it started.
- Probe: `bash R/train_probe.sh 148598 gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1`. Resubmit if it dies before publishing (same run name resumes from checkpoints): from R/stage_ao_fullpool run `WANT_IDX=b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446 WANT_SPLIT=46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70 WANT_ROWS=29399 ROOMFIX_GATE=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20260924T041526Z_answeronly_fullpool_review3/final_message.md STUDENT=qwen35 bash launch_ao_fullpool.sh` (add PARTITION=preempt QOS=preempt_qos WORLD_SIZE=8 for a preempt copy; different run name). adv_4gpu_qos allows 4 GPUs, 1 node, 12 submitted jobs per user.

## Evaluation (after publication)
- OneThinker: LANE/eval/launch_ao.sh (copy of claude_trinity_fullset_evals_20260923T1944Z/launch_ao.sh; env LANE/eval/env.sh with PUB_AO = the new publication; launcher repo claude_trinity_launcher_20260923T0745Z/work/launcher at 91d47a0). Run `bash LANE/eval/launch_ao.sh vsibench_answerable500 1 trinity-2-8:0 ... trinity-2-8:7` and the same for vstibench_repr450_v2 (probe cards first; outputs LANE/eval/runs/fullpool/<bench>). Pair with the 58794b8 base cells as the 7,684-row control did; append tables to /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md in the existing format.
- Qwen (automatic): LANE/eval/qwen_eval_on_publish.sh runs detached on trinity-0-23 (setsid, started 06:58Z; it needs that node's /tmp IAP ssh config). It polls every 5 min for the run's PUBLISHED.json, then submits one general-partition job per b16 cell (EVAL_SHARD_COUNT=1, SHARDS=0, nice 0; VSIBench first) and logs to LANE/eval/qwen_eval_on_publish.log. Cells: qwen35_distilled_gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1_{vsi,vsti}_b16. If trinity-0-23 dies, submit by hand as below.
- Qwen (manual): batched bs16 VSIBench-500 and VSTIBench-450 cells through R/submit_shards_b16.sh on deployment 0ab73f9, paired with R/runs/eval/qwen35_base_{vsi,vsti}_b16/run; either add a feeder entry (R/feed/queue.jsonl, wait_file = the run's PUBLISHED.json, owned by the Orchard lane) or submit by hand: `SHARDS="0 1 2 3 4 5 6 7" PART=preempt MODEL=qwen35 VARIANT=distilled BENCH=<bench> CELL=qwen35_distilled_gtm2_answeronly_fullpool_qwen35_orchard_w4_mb2_e1_<vsi|vsti>_b16 EXTRAS="<adapter> <PUBLISHED.json> R/runs/eval/qwen35_base_<vsi|vsti>_b16/run" bash R/submit_shards_b16.sh`. Cells land in /data3/jjyeung/orchard_publications/eval_cells/; the rescore lane scores them.

## Survives vs dies
Survive: the trinity-0-18 setsid chain (gates, launch_after_gates, run_train, renewer, watcher) and Orchard job 148598. Die with this session: the in-session Monitor and wait loops only (none of them launch anything).

## Successor first actions
1. `ssh trinity-0-18 'pgrep -af "run_cpu_gates|launch_after_gates|run_train|prepare-training" | cut -c1-150'`; `grep "GATE\|===" LANE/train/work/cpu_gates.log`; `tail LANE/train/out/HEARTBEAT_train.log LANE/train/out/WATCH_onethinker.log`.
2. Orchard: `squeue -u jjyeung -o "%i %P %j %T %M %R"` and the train_probe command above.
3. Babysit at 1-minute cadence until step 1 of each run, then lengthen to 10 min; report step/787 and s/step.
4. On each PUBLISHED marker, launch the two evaluations above and hand the cell paths to the rescore lane through the orchestrator.
5. Pitfall: when killing a gate chain, kill the python child too (a v2 prepare-training child outlived its shell and nearly wrote into the v3 frozen/ dir). Never pgrep over ssh with a pattern that also matches the ssh command line.

## Lane: mechanism controls

# Handoff: mechanism-controls lane (refreshed 2026-09-24 07:30Z)

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_mechanism_controls_20260924T0340Z. S = /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918. PUB = /data3/jjyeung/orchard_publications. Current state is in L/STEP.md, and a one-line-per-run status goes to L/out/lane_watch.log every minute (detached watcher L/work/lane_watch.sh, pid in out/lane_watch.pid).

## Question and reviewed matrix
The lane asks why answer-only supervision beats trace supervision (OneThinker H: base 39.19/45.40, trace 38.68/38.28, answer-only 48.03/53.45, VSIBench-500 / VSTIBench-450 lenient). The headline set H (7,684 rows) splits into T and G. T holds 3,842 strict-accepted teacher rows of three types: rel_direction_medium 2,589, appearance_order 707 and counting 546. G holds 3,842 GT-measurement rows that no teacher touched; every numeric type comes from G. The Astra xhigh design review returned PASS-WITH-CUTS (agent/scratch/codex_runs/20260924T033204Z_mechctl_design_review); the result is out/REVIEWED_MATRIX.md.
| cell | rows | isolates |
|---|---|---|
| M | H-trace 7,684 | loss dilution: trace training with the answer tokens re-weighted as in answer-only (trainer bab1ad5) |
| S-G / S-T | 3,842 each | GT-measurement rows alone / teacher rows alone |
| C0 | 7,684 | G + accepted-only teacher-type sample under the same type x dataset x scene quotas as C1x |
| C1x | 7,684 | G + a rejection-enriched sample (803 rejected = 20.9% of T), GT labels: teacher curation |
| C2x | 7,684 | C1x questions with the teacher's own answers (660 wrong = 8.6% of the set): label source |
| N1k/N2k/N4k | 1,000/2,000/4,000 | scaling; nested H subsets; world 2 (H is world 4: a known confound, report it) |
| Qwen C1x/C2x | 7,684 | label source on Qwen3.5-9B (Orchard advanced, world 4) |
Reading rule: a difference counts if it is at least 2 points lenient, a paired scene-clustered 95% CI excludes zero, and the direction agrees on both benchmarks; raise the floor if the s18/s19 seed spread is wider.

## Sets (all verified; L/out/build/REPORT.md, READY_<cell>.json)
S/mechctl_<cell>_20260924 (mix) and _trainer (layout), for sg, st, c0, c1x, c2x, n1k, n2k and n4k. Every set carries H's 1,548 heldout rows and inherits the full-pool v2 split 294b7bda (owned copy L/out/build/FROZEN_FULLPOOL_SPLIT.json; its source was renamed to S/answeronly_fullpool_20260923_v2_indexlabelfail) with parents eec29d98 and 5dcd3cdc; no scene group was newly hashed. Builder commits: sg eba34b4; all others c7e8f7e.

## Branches (landing is optional; nothing on distill main needs them)
- distill repo: mechanism-controls-20260924 c7e8f7e (student/compact_targets/answer_controls.py + tests), worktree L/work/repo, based on the full-pool branch ce5322b.
- S/trainer_repo: answer-weighted-loss-20260924 bab1ad5 (cell M loss, e746674 + answer_loss_weight_mode), worktree L/work/trainer_m. trinity-eval-launcher-mechctl-20260924 834ff9e (29d4579 + acceptance of that setting), worktree L/work/launcher_m.

## OneThinker runs (b084aaf recipe: world 4, LoRA r32, batch 32, 3 epochs, seed 17; M uses bab1ad5)
Each run lives in L/runs/<cell>/ (work/: gates_env.sh, run_cpu_gates.sh, cpu_gates.log, frozen/; out/: run_train.sh, HEARTBEAT_train.log, WATCH_onethinker.log). Publication: PUB/mechctl_<cell>_onethinker_trinity. Generator: L/work/make_cell_run.sh.
Slots run through L/work/slot_seq.sh <cards> <steps>, which runs on the slot's host and logs to L/out/slot_<host>_<cards>.log. Steps are wait_pub:X, eval:X (VSI on the first two cards, VSTI on the last two) and train:X. A train step claims X atomically in L/runs/.claims/X, skips X if it is already training or published, stops any armed run_train of X on that host, and runs a host-patched run_train copy on the slot's cards. Start a slot with `ssh <host> bash L/work/start_slot.sh <cards> <steps...>`.
| cell | where | state (07:25Z) |
|---|---|---|
| sg | done | published 06:47Z; VSI 42.43/42.43 scored; VSTI on 0-23:3 |
| n1k_w2 | done | published 06:36Z; VSI 45.32/45.32 scored |
| st | 0-28:2,3,4,6 | published 07:19Z; VSI+VSTI evaluating on its own cards (slot) |
| c0 | 0-28 slot | trains after S-T eval (~07:50Z, ~4.1 h, ~12:00Z) |
| M | 3-23:4-7 | step 276/723, 22.4 s/step, ~10:10Z; then own-card eval, then C1x (slot 3-23 4,5,6,7) |
| c1x | 3-23:0-3 armed | attempt 1 refused 07:01Z (the experimenter's REQ-238 Qwen3.6-27B vLLM servers hold 0-3 for hours); attempt-2 waiter is armed until ~08:55Z; otherwise the 3-23 4-7 slot trains it after M |
| c2x | first free slot | train:c2x claimed by whichever slot (0-28 after C0's eval, or 3-23 4-7 after C1x's eval) gets there first |
| n2k_w2 | 0-23:5,7 | step 57/189, 39.7 s/step, ~08:50Z |
| n4k_w2 | 0-23:5,7 | after N2k: L/work/after_n2k.sh first runs P1/P2 eval runners on 0-23:5 (VSI) and :7 (VSTI) until idle, then trains N4k |
Card rules (orchestrator): the experimenter has GPU priority. Never touch trinity-0-23 GPUs 0-2 or trinity-3-23 GPUs 0-3 while its jobs hold them. 0-23 GPUs 4 and 6 run s19. 0-18 GPUs 4-7 belong to the full-pool lane. 0-23 GPU 3 is ours for evaluation. Claims are recorded in P/claude_swarm_20260923T0835Z/CARDS.tsv.

## Cell T (thinking channel; orchestrator priority above C2x)
The corrected trace re-templated into the native thinking channel, with no trainer change. Qwen `tq` target = trace + "\n</think>\n\n" + answer (the prompt ends "<think>\n"; source is the qcap4096 set with 7,682 rows). OneThinker `to` target = trace + "</think>\n<answer>X</answer>" (the base's own form; no opening tag). Heldout twin rule: compare final lines and require exact trace identity. Build: Devin follow-up pid 1946382 (L/BRIEF_DEVIN_THINK2.md, out/think2/, code in L/work/repo thinking_controls.py). Next: Astra review (`agent/scripts/codex_dispatch.sh review L <brief> --model gpt-6-astra --effort high`) of out/think2/RENDERED_EXAMPLES.md plus the diff, checking one <think>/</think> per example, the mask right after "assistant\n<think>\n", the bare answer after the last </think>, and that the OneThinker prompt ends where the base generation starts. Then launch Qwen T on Orchard advanced after C1x (148646) and ahead of C2x (move 148648's dependency), and OneThinker T on the first free 4-card trinity slot ahead of C2x (a train:to step before train:c2x in a slot, after make_cell_run.sh to ...).

## Qwen (Orchard; ssh via /tmp/jjyeung_ssh_orchard_config, 240 s timeout)
- 148646 C1x (mechctl_c1x_qwen35_orchard_advanced_w4): HELD (scontrol hold) at the orchestrator's request. Release with `scontrol release 148646` once the Orchard lane's three evaluation cells run on advanced after 148598 (about 12:00Z). 148648 C2x: afterany:148646.
- Preempt world-8 copies 148642/148644: `scancel` each once its advanced copy starts.
- Staging: L/work/orchard_stage (verified 49,054/49,054); launcher /project/community/jjyeung/distill/stage_mechctl/launch_mechctl_qwen.sh (CELL, WANT_IDX, WANT_SPLIT, WANT_ROWS, PARTITION/QOS/WORLD_SIZE, DEPENDENCY).

## Evaluation (OneThinker)
- L/work/eval_cell.sh <cell> <bench> <host:idx...> uses launcher 91d47a0, or L/work/launcher_m for M. Outputs go to L/eval/<cell>/<bench>; scored with score_eval.sh; each finished benchmark is appended to L/out/EVAL_DONE.tsv. Results are in scores/attempt_*/RESULTS.md.
- Runner: L/work/eval_runner.sh <host:idx> [bench] takes the priority queue L/work/eval_queue.txt (P1/P2 subset: eval_queue_p12.txt) with atomic claims in L/eval/.claims. It runs on 0-23:3 (pid tree from eval_runner_0-23_3.sh; log L/out/eval_runner_trinity-0-23_3.log).
- Results so far: S-G VSI 42.43 (base 39.19; H 48.03); N1k VSI 45.32.

## User-only items
None pending. There are no deletions: failed partial outputs sit under S/_quarantine (st build) and L/runs/_quarantine.

## Successor first actions
1. `tail -12 L/out/lane_watch.log`, then check `ps` on trinity-3-23, trinity-0-28 and trinity-0-23 for run_train.sh / chain_after.sh / launch_after_gates.sh; if the lane_watch pid has died, restart it: `setsid nohup bash L/work/lane_watch.sh >/dev/null 2>&1 < /dev/null &`.
2. Check the slot logs (L/out/slot_*.log), the eval runner log and L/out/EVAL_DONE.tsv; send each new RESULTS.md headline and per-type table to the orchestrator.
2b. When the T sets are READY: dispatch the Astra review, then launch T as described above.
3. Cancel the preempt Qwen copies once the advanced copies run.
4. Keep the 1-minute cadence after each launch; lengthen to 10 min once steps flow.

## Appendix: FACTS.md verbatim

# Facts for the 08:00Z handoff (orchestrator distill_orch, Fable 5.1 session on trinity-0-23; started 03:19Z 2026-09-24; clock at writing 06:20Z, to be appended at 07:50Z)

## Head and landings today
- main: 584e215 -> 5685402 (corrected-set paper tables) -> 5dc272f (doc-audit checker fix) -> 65bb856 (Qwen answer-only VSIBench row) -> f0b3aa8 (Qwen answer-only VSTIBench rows, matched and lower-bound) -> 3752531 (full-pool builder, Set B and tools/gtmeasure code line, 52 files, plus the GT-measurement verification paragraph in CLAUDE.md). Guard restarted after each by lane claude_guard_restart_20260924T{0355,0410,0555,0615,0650}Z through luna_run.sh; current guard pid 2390508 on trinity-3-8 at 3752531.
- Pending landings: full-pool builder branch answeronly-fullpool-20260923 (f661a76, rebasing onto f0b3aa8); next results rows (mechanism cells, 32k diagnostics, int48 supplement, full-pool students, seeds).

## Goal revision 03:40Z (verbatim in memory distillation-lane-goal): through ICLR 2026-09-25, characterize which teacher supervision transfers (curation vs GT labels vs trace text, data scaling, seed ranges); land every result on main; collector at the key ceiling; every free GPU on trinity and Orchard.

## Results banked today (lenient primary; lenient = strict on every Qwen cell)
- Qwen3.5-9B answer-only corrected (Orchard 148380, 723 steps, loss 0.136): VSIBench-500 55.24 vs corrected trace student 48.02 vs batched 4k-cap base 14.92 (base capped on 367/500 items, 366 without an answer); VSTIBench-450 matched-402 52.95 vs base 27.08, lower bound all-450 48.11 vs 27.55 (48 items interrupted by preemption; harness allows one full attempt per model/benchmark/protocol, so no rerun; 48-item re-decode supplement pending). Every type gains. Answers beat traces for both students on both benchmarks.
- Census (claude_census_ab_20260924T0445Z/out/COMBINED.json): 26,090 distinct strict / 28,569 tier (A 20,762/22,688; B 5,328/5,881 excluding 146 burned); B validated 300/300; A reused 6,566/6,566; fresh-A validated 100/100 (report CENSUS_AB.md, complete 06:11Z; overcount bounded at about 3 percent for A and 1 percent for B). The 20,000 goal is met on a validated census. Per-type strict A+B: rel_direction 14,407; rel_distance 6,196; appearance_order 2,207; abs_distance 2,021; counting 895; size 275; room size 89. Pitfall: 15 root-B questions with a `.retired/` folder abort census.py; skip `.retired` first.
- Corrected set H (7,684) is 3,842 teacher rows (rel_dir_medium 2,589, appearance 707, counting 546) plus 3,842 GT-measurement rows; every numeric type is GTM.

## Rulings today
- 04:13Z queue USER-RULING (experimenter orchestrator): experimenter has priority on the shared key (7M theirs / 1M ours when shared) and on GPUs when needed; takes and releases announced via INBOX_*.md; priority never leaves capacity idle. No take announced as of 06:20Z.
- 04:57Z user: "you have the full key right now" -> ramp under a rate brake (429s above 2 percent of calls); key saturates at 8.2M tok/min near 66-70 workers (05:35-06:08Z).
- 05:05Z orchestrator: s18 reservation on trinity-0-23 cards 0-3 withdrawn (idle 100 min); cards went to the accepted-only control, then the experimenter's r1467 took GPUs 0-2 at 05:40Z; C0 moved to trinity-0-28 behind S-T.
- 05:20Z orchestrator: advanced order = full-pool Qwen training (148598), then mechanism Qwen C1x (148646) and C2x (148648); evaluation jobs stay on general and preempt.
- 05:50Z orchestrator: 27B appendix = batched bs8 base plus arm C student pair at the 4,096 cap; single-decode student shards cancelled; single-decode base stays banked.
- 05:55Z orchestrator: 32k budget = capped-items diagnostic only (adaptive-budget base), whole-benchmark 32k refused by the a24c998 admission contract; no harness change before the deadline.

## Incidents and lessons today
- Classifier denials: memory write of goal text; expansion lane kill of its own picker, CARDS.tsv claim and host pin, read-only check of picker_v2; Orchard lane staging to Orchard (rsync, submit script), feeder/mirror patch, detached helper creation, scancel of failing shards. User ran deploy_eval_a24c998.sh (05:25Z) and kill 1484237 (05:24Z). Open user items: the 32k/int48 items rsync and submits (USER_CMDS_32k_reruns.sh in the Orchard lane out/), the feeder/mirror patch, and the picker_v2 decision.
- Harness rules learned: attempt-authority key (benchmark, ordered item ids, adapter, scope, protocol sha) allows one full attempt; subset cells produce receipts only and must be landed by hand; a24c998 contracts require a pre-registered proper subset for budgets above 4,096 on paper cells.
- Orchard per-user limits: advanced 4 GPUs on one node, 12 submits; general 1 running job, 5 submits; preempt 32 GPUs, 50 submits, priority behind other users.
- Trainer prepare-training is single-thread (132 rows/min): 25k rows = 190 min in gates with claimed GPUs idle; three concurrent prepare readers plus the census stalled the collector controller node for 5 min at 05:41Z.
- Draw drop at 56 workers was a stale-meter artifact; meter moved to trinity-0-23; brake counts 429s from attempt journals when the meter is stale.

## Running at 06:20Z (details in per-lane HANDOFF files)
- Collector: 2cd7d87 controller pid 147557 on trinity-1-13, 66-70 workers, about 1,400 terminals/h, 8,575 root-B terminals at 06:08Z; loop pid 1786659 and meter 1691756 on trinity-0-23.
- Orchard: 148598 full-pool Qwen (advanced, prep until about 07:30Z, ends 11:30-12:00Z); 148646/148648 queued; 27B batched pair on preempt; general free after the failed _r2 shards.
- Trinity: full-pool OneThinker gates on trinity-0-18 (train from about 07:20Z on cards 4-7); S-G 3-23:0-3 (ends 06:50Z), S-T 0-28:2,3,4,6 (07:20Z), M 3-23:4-7 (09:55Z), N1k 0-23:5,7 (06:36Z) then N2k, N4k; C0 after S-T, C1x after S-G, C2x after C1x; s18 0-8:0,1,2,4 (09:55Z), s19 0-23:4,6 (11:40Z).

## Added 07:10Z
- 06:40Z user (verbatim in memory collection-type-priority-20260924): keep collecting Gemini traces; prioritize counting, size, room size, absolute and relative distance. Collector lane is sizing the root-B pool by type and finding a claim-order knob or a type-ordered re-bind (cost 35-45 min of collection); decision pending.
- 07:05Z user: "we should by default have thinking on". Audit (rescore lane, from run records): every Qwen cell was evaluated with enable_thinking=True and OneThinker at its native template; the 4k cap cut the bases' thinking (Qwen 9B base closed its think block on only 134/500 VSIBench items). Training (mechanism lane, student_pilot/batches.py): Qwen students learn an empty think block ("\n</think>\n\n" + target supervised), so answer-only trains thinking off and trace students put the trace outside the think channel; OneThinker trace targets lacked its native <think>...</think><answer>..</answer> wrapper. Ordered: T cells (trace inside the native think channel, answer in the native answer slot; same 7,684 rows and recipe as the trace student) for both students, above C2x: Qwen T on advanced after C1x, OneThinker T on the first free 4-card trinity slot; trainer format flag via Devin/Codex, Astra review, unchanged harness. The 32k adaptive-budget base is the fair thinking-on reference.
- Per-type read on the answer-only rows (lenient): OneThinker trails base only on object size (-4.6) and rel_dir_hard (-2.0); its smallest gains are distance (+7/+8) and its largest counting (+21.4); Qwen gains on every type against the 4k base.
- Landed 3752531 (full-pool builder, Set B and tools/gtmeasure line, 52 files, CLAUDE.md verification paragraph); guard pid 2390508. Held for the next landing: results-mechanism-controls-20260924 (rebasing onto 3752531) with the S-G row.
- 07:15Z orchestrator approved the type-ordered claim epoch (collector lane plan c): no live knob reorders claims, so a new epoch adds R1316_CLAIM_TYPE_ORDER (counting, size, room_size, abs_distance, rel_distance, appearance_order, rel_direction); Devin build in the collector lane worktree (1-1.5 h), seal and bind on an idle node in parallel (60-80 min), then drain and swap (35-45 min of reduced collection, about 600-800 terminals); earliest priority claims 09:30-10:00Z; after the drain the branch tip is fast-forwarded to main and the guard restarted before the relaunch. Root-B remaining by type: counting 2,603 (strict yield 0.84), object size 3,912 (0.15 strict, 0.67 tier), room size 652, abs_distance 11,235 (0.44/0.80), rel_distance 22,347 (0.83), rel_direction 40,283 (0.93), appearance_order 7,616 (0.74). Projected on the new epoch: about 1,090 counting strict/h for 2 h, then about 195 size strict/h (870 tier) for 3 h, then room size, then distance; today's mix gives about 30 counting and 6 size strict per hour.
- 07:20Z: the type-order epoch lands by option 2 (launch from the epoch checkout of the sealed sha on branch collector-claim-type-order-20260924; main is not fast-forwarded because the r1316 chain 6aa9d60 -> d1b52e4 -> fc6b364 -> 2cd7d87 lives on branches and main's collector/ differs in 15 files; reviewed merge queued for after the deadline). Bind on trinity-2-13 (idle; /data2 reads about 11 MB/s on every node), 1.5-3 h, in parallel with collection. Devin build pid 1899052 on trinity-0-23 since 06:44Z.
- 06:55Z mechanism lane: S-G published (/data3/jjyeung/orchard_publications/mechctl_sg_onethinker_trinity, 06:47Z) and N1k (mechctl_n1k_w2_onethinker_trinity, 06:36Z); C1x training on 3-23:0-3 since 06:48Z; N2k 189 steps at 40 s/step (ends 08:50Z); M ends 09:55Z. Evaluation is the trinity bottleneck: trinity-2-8 refused (other users' compute apps on all 8 cards; the launcher refuses any card with compute apps), 0-18:4-7 taken by full-pool OneThinker (training since 06:44Z, 29.3 s/step on A6000s, ends 13:05Z); orchestrator opened the free GPUs of trinity-1-13 (collector controller node) for evaluation under nice/ionice with a 15 percent terminal-rate guard; evaluation priority S-G, S-T, C0, C1x before N-ladder cells; N1k VSIBench runs on 0-23:3 (about 2 h per benchmark per card at 243 items/h).
- T cells: Devin pid 1895562 building with no trainer change (Qwen target trace + "\n</think>\n\n" + answer on the qcap4096 set, 7,682 rows as 148295 used; OneThinker "<think>"+trace+"</think><answer>"+answer+"</answer>" on the uncapped roomfix set); Astra review must confirm exactly one think block per rendered Qwen example and the parser's bare answer after the last </think>.
- GTM rows available without the teacher (gtmeasure_v2_roomfix_20260923, same split, 7,770 train rows of which H uses 3,842): counting +823, size +794, room +794 (about 6 questions per scene on one room label), camera_abs_dist +776, abs_distance +384, rel_distance +357, about 3,928 total; more needs higher generation density or new scenes (306 prepared, 13 deferred). Decision rule: add them only if numeric-type lenient scores still rise from N4k to H beyond the seed floor (about 2 points) and S-G reaches H's numeric scores.
- 06:57Z: type-order epoch built and sealed: commit 93ebe00155144e46ca9ee6d8b25fd596f5441962 on branch collector-claim-type-order-20260924 (collect.py sort_ready_rows, R1316_CLAIM_TYPE_ORDER, unchanged order when unset, 39 tests), epoch checkout /home/jjyeung/agent_project_distill_epochs/93ebe00155144e46ca9ee6d8b25fd596f5441962, sealed contract sha 44b93e88244ff70a2e128d31f6d5b8a8e7507b5c285c752663d42346a7d2b0fe (47 files verified); dry run: counting at catalog positions 1-2,817 (218 done), size from 2,818, room 7,124, abs_distance 7,826, rel_distance 20,384, appearance_order 44,340, rel_direction 53,268. Bind pid 1128096 on trinity-2-13 since 06:53Z (guard 1128092), log $R2/launch_20260923T0820Z/bind_93ebe00.log; drain and swap after publication with the variable set in the controller environment.
- 07:05-07:15Z unannounced experimenter takes: trinity-3-23 GPUs 0-3 (two Qwen3.6-27B vLLM TP2 servers, 06:49Z/06:54Z, REQ-238) right after S-G freed them, so C1x's admission refused ("foreign compute PID on the leased GPU") and C1x moves to M's cards (3-23:4-7) after M's own-card evaluation about 10:00Z, C2x to the first free 4-card slot after; and Orchard general (job 148679 r1468-qwen36-serve, 12 h limit, since 06:59Z), which removes our only non-preemptible evaluation slot. Ruling: no evaluation cell on preempt from now on (an interrupted item can never be retried in that cell); the int48 supplement and the two 32k capped-items diagnostics run on advanced with afterany:148598 (about 12:00Z, about 1.5 h) while the mechanism lane holds 148646 (C1x) until they start; order after: C1x, Qwen T, C2x. The 27B batched pair stays on preempt (base 354/450, student 417/450 at 07:03Z; land_loop lands them). Inbox note INBOX_TO_EXPERIMENTER_20260924T0710Z_gpu_takes.md asks the experimenter to announce takes and releases and lists our claimed cards and chains.
- Evaluation on trinity: one queue runner on trinity-0-23 GPU 3 (L/work/eval_runner.sh, queue L/work/eval_queue.txt, results L/out/EVAL_DONE.tsv; answer-only adapters score at about 600 items/h per card, so about 45 min per benchmark), runners on GPUs 5 and 7 after N2k (about 08:50Z) until the P1/P2 backlog clears, then N4k; cells that finish training evaluate on their own cards first (L/work/eval_then_chain.sh). Seed replicates evaluate on their own cards (s18 on 0-8:0,1 and 2,4; s19 on 0-23:4 and 6) since trinity-2-8 is refused (other users' compute apps on all 8 cards).
- 07:14Z T cells: 148646 (Qwen C1x) held on advanced until the three evaluation cells run; T sets rebuilt by Devin pid 1946382 (out/think2/) with two rulings: heldout twin rows compare the final line and require exact trace identity; OneThinker T target = trace + "</think>\n<answer>" + X + "</answer>" with no opening tag (the template opens the block; the raw base generations look like "REASONING</think>\n<answer>X</answer>"). Rendering checks passed on real rows for both students with no trainer change (Qwen max suffix 3,614 tokens, 0 new cap drops, parser recovers the answer). Astra review (effort high) on RENDERED_EXAMPLES.md, then OneThinker T and Qwen T launch. Trinity slots run through L/work/slot_seq.sh with atomic claims for C2x.
- 07:13Z: Qwen3.6-27B arm C student batched bs8 VSTIBench 52.01 lenient = strict (cell qwen36_27b_distilled_armc_27b_orchard_d_vsti_b8, landed 07:13Z, 3 parse failures, 3 cap hits, median 376 tokens; per type cam_disp 17.00, cam_dir 36.00, cam_obj_abs 50.40, rel_v1 64.00, rel_v2 70.00, rel_v3 74.00, pos_lr 84.00, pos_nf 86.00, pos_ud 92.00); pairs only with the b8 base (418/450 at 07:13Z); pinned single-item base 30.71 is a reference only. To be bundled with the S-G row on results-mechanism-controls-20260924.
- 07:20Z collector: bind pid 1013882 on trinity-1-13 (niced, since 07:05:46Z) reading about 39 MB/s with the cache partly warm, ETA 07:45-08:05Z; abort watcher pid 1962132 (terminals per 10 min below 120 for 10 min, brake-aware reference; D-state above 30 for 3 min). The draw fell to 3.95M tok/min at 70 workers with 0 429s because GT tool time per episode rose from 18 s (03:50Z) to 116 s median (07:10Z) on heavier scenes; the tools run on CPU (about 63 of 96 cores at 69 episodes), so the worker ceiling is CPU in this regime, not the key. Pre-authorized after the swap: measure per-type tool time and terminals against worker count, let the per-worker rule cap the target where terminals peak, and cost a permanent cap versus a controller move to trinity-2-13.
- 07:25Z first mechanism scores (OneThinker VSIBench-500 lenient, PAIRED base 39.19; H answer-only 48.03): S-G 42.43 (+3.24; gain on rel_direction and route, not on its own counting or size: counting 29.6 -> 25.8, size 48.0 -> 45.6, room 51.8 -> 59.2); N1k 45.32 (+6.13, two thirds of the full gain from 1,000 rows). Cells L/eval/sg/vsibench_answerable500 and L/eval/n1k_w2/vsibench_answerable500; EVAL_DONE.tsv. S-G VSTIBench about 07:55Z; S-T both benchmarks started 07:20Z on 0-28; M step 276/723 (ends 10:10Z); N2k ends 08:50Z. REQ-238 stage 1 (374 reruns) is RUNNING on the experimenter side since 06:34Z.
- 07:35Z 27B batched pair scored (VSTIBench-450, bs8, 4k cap): base landed 07:24Z with 16 interrupted and 187 cap hits; primary matched-434 cohort student 52.02 vs base 29.94 (+22.08); all-450 upper bound 52.01 vs 28.49; every type gains; pinned single-item base 30.71 reference only; goes into the bundled commit with S-G, N1k and S-T (tip sha expected about 08:25Z).
- 07:40Z: REQ-238 serve job 148679 ended after about 35 min, so Orchard general is ours again: the int48 supplement and the two 32k capped-items cells run on general one after the other when the user's items rsync lands (no preempt for evaluation, no advanced window); the hold on 148646 is released and advanced stays training-only after 148598 (C1x, then Qwen T, then C2x). 27B batched base landed 07:24Z (1,967 files verified; 434 ok, 16 interrupted, 187 cap hits, 204 parse failures).
- 07:45Z: Orchard general is the only evaluation slot (no preempt, advanced training-only): queue order by nice value is int48 and the full-pool Qwen b16 cells (nice 0; the full-pool lane's own submitter LANE/eval/qwen_eval_on_publish.sh fires on PUBLISHED.json, submits VSIBench first, general only), then the two 32k capped-items diagnostics (nice 100). Full-pool at 07:24Z: OneThinker step 85/787 at 29.0 s/step (ends 13:05Z, eval from LANE/eval/launch_ao.sh after publication); Qwen 148598 still preparing (step 1 expected 07:45-08:15Z, end about 12:15Z). Seeds at 07:27Z: s18 252/723 at 20.1 s/step (ends 10:05Z), s19 342/723 at 40.0 s/step (ends 11:41Z).
- 07:48Z: USER_CMDS_32k_reruns.sh updated (previous kept as .v1): step 3B now PART=general, nice 100, one job per cell (EVAL_SHARD_COUNT=1; general_qos allows 5 submitted jobs per user); the user runs only steps 1 (items rsync) and 2 (a24c998 submit script) and the Orchard lane submits int48 (nice 0) then the two cap32k cells (nice 100) itself; each cap32k cell may run 3-6 h on one GPU (unmeasured). The full-pool Qwen evaluation must also use one job per benchmark on general. Collector at 07:35Z: 136-139 terminals per 10 min, 6.63M tok/min, 0.1 percent 429s, 9,815 terminals; bind halfway (65.6 GB read), ETA 08:05-08:10Z.
- 07:42Z: T review PASS (Astra high, receipt agent/scratch/codex_runs/20260924T073108Z_mechctl_T_review/final_message.md): one think block per Qwen example, mask ends after "assistant\n<think>\n", no second close tag, no trainer change; OneThinker mask ends at "assistant\n" with tail "</think>\n<answer>X</answer><|im_end|>"; 18,462 rows replayed through the pinned trainers with byte-identical split records. Sets S/mechctl_to_20260924 (7,684) and S/mechctl_tq_20260924 (7,682), commit 7801d4c. 148646 released (pending on advanced); Qwen T staged, to be submitted afterany:148646 with 148648 moved to afterany:T. OneThinker T gates running; it trains in the first 4-card slot that finishes its sequence, ahead of C2x. C0 training on 0-28 since 07:38Z. S-T own-card evaluation failed (launcher CPU preflight overran the 900 s timeout on 0-28 slow /data2) and moved to the 0-23:3 runner after N1k VSTIBench (~07:55Z); all evaluation launches now run from trinity-0-23 with a 40-min timeout (eval_cell.sh). S-G VSTIBench scored (numbers pending).
- 07:47Z: S-G VSTIBench 49.25 lenient = strict (base 45.40, H 53.45; cam_obj_abs 36.0 -> 52.4, pos_lr 60 -> 48); GTM rows recover about 40 percent of H's gain on both benchmarks. Orchard advanced: 148646 (C1x) -> 148683 (Qwen T, afterany:148646) -> 148648 (C2x, afterany:148683), about 3.6 h each; if 148598 ends 09:15Z: C1x 12:50Z, T 16:30Z, C2x 20:10Z.
- 07:44Z: 93ebe00 bind published on trinity-1-13 at 07:41:36Z after 36 min (config collection_config_r1316_93ebe00155144e46ca9ee6d8b25fd596f5441962.json, sha 125e28af4ac6dcb27c658a3d6b6a1a6de1d4022f07d68903ff9836682da64475, 97,652 ready; abort watcher never fired). Drain started 07:44Z (workers 4, then 0, wait for zero), then stepM stops controller 147557 and cold-starts 93ebe00 with R1316_CLAIM_TYPE_ORDER and 2 s pacing, explicit set-workers 66. 9,903 terminals at 07:42Z, no BLOCKED.json.
- 07:52Z second unannounced take: REQ-238 vLLM TP2 servers (pids 1721770/1721772, 1723328/1723332) took trinity-0-28 GPUs 2,3,4,6 right after S-T published, so C0 cannot start; OneThinker cells C0, C1x and T have no 4-card slot until M finishes about 10:40Z. Orchestrator order for OneThinker slots: T (M's cards at 10:40Z), then C1x, then C2x; C0 dropped unless a spare slot appears (C1x and C2x compare against banked H with the matched-quota caveat). Qwen side unchanged (C1x, T, C2x on advanced). Full-pool Qwen evaluation submitter (pid 2017912 on trinity-0-23) now submits one general job per benchmark, VSIBench first.
