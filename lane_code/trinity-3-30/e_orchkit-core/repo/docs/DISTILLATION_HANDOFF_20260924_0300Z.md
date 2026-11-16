# Distillation handoff - 2026-09-24 03:00Z

## Headline results

| Result | Evidence |
| --- | --- |
| OneThinker-8B corrected full set | Room-fixed v2.5 + gtm2, 7,684 rows: base 39.19/31.47 VSIBench-500 and 45.40/40.16 VSTIBench-450; trace student 38.68/38.68 and 38.28/38.28; answer-only control 48.03/48.03 and 53.45/53.45. The answer-only control has no parse failures or cap hits, and beats base by +8.84 / +8.05 and the trace student by +9.35 / +15.17. |
| Qwen3.5-9B corrected trace student | Orchard 148295, 723 steps, mb2, final loss 0.16, 748 files verified: batched bs16 VSIBench-500 48.02 lenient = strict versus batched base 14.92 (+33.10); every type gains; room_size_estimation 0.00 -> 67.00. |
| Earlier banked Set B results | Qwen Set B pilot 39.80 versus 12.68 (VSI) and 44.57 versus 29.93 (VSTI); arm C stays ahead; the swarm found no wording beating bare answers at 1,000 rows. |
| Qwen3.6-27B | The base VSTIBench cell is 450/450, with 442 ok, 8 cut by preemptions, 184 cap hits at 4,096 tokens with pinned thinking, 198 parse failures, strict 0.307, and 143.5 s/item; it is an appendix row only. The arm C student VSTIBench evaluation is ordered on preempt. |

## What is running now and its ETA

| Work | State and ETA |
| --- | --- |
| Qwen answer-only corrected run | Orchard 148380 is at step 287/723 at 02:32Z, loss 0.38, 17.8 s/step. Training ends about 04:45Z, followed by publication. Its PUBLISHED.json triggers the feeder for batched bs16 VSIBench-500 and VSTIBench-450 cells; the feeder checks every 5 min. |
| Collector root B / bind swap | The fc6b364 controller has 5,973 terminals at 02:24Z. The 2cd7d87 bind was projected to publish about 03:15Z. The bind finishes only if it completes within 30 min; otherwise it is stopped and rerun on trinity-2-8 or trinity-0-18. After publication, the specified drain, cold start, explicit 48 workers, and 2-minute 429 brake apply. |
| Answer-only full-pool rebuild | The v2 rebuild runs on trinity-0-18, pid 2155571, started 01:53Z, with verification about 03:05Z. The round-2 review brief is ready; then gates, training, and evaluation follow. |
| Answer-only seed replicates s18/s19 | Prepare-training has run on trinity-2-8 since 02:11Z. Picker pid 1484237 launches on the first host with enough empty 48 GB cards among trinity-0-8, trinity-0-23:4-7, and trinity-0-13:0-5. Evaluation needs the launcher branch worktree, patch, and commit. |
| 27B evaluation | The 27B smoke 148201 finished. The flame partition is closed because it is QoS-gated; an admin must attach a flame QoS. |

## What the user must do

- The user or an authorized executor must stop the 2cd7d87 bind and rerun it on trinity-2-8 or trinity-0-18. The command is in `$L/work/bind_elsewhere.sh` in the collector lane.
- If `BLOCKED.json` appears in `collection_gt_r1316/pool_b16384`, only the user may rename it: `mv BLOCKED.json BLOCKED.json.acked_<ts>_<reason>`.
- Create a worktree/branch from `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_launcher_20260923T0745Z/work/launcher` at 91d47a0, apply `L/out/launcher_seed.patch`, and commit. The expansion lane must not run evaluation, including a dry run, until the orchestrator confirms this branch exists.
- An admin must attach a flame QoS; the flame partition is closed and mt01 holds none.
- Deletions and coordination-store writes are user-only. The auto-mode classifier also denied BLOCKED.json renames, worktree adds under home, file edits and git commits in lane worktrees, direct scoring on another lane's root, and a Devin launch; builds use Codex/Devin dispatch with a writable lane root.

## Rulings today

- 21:26Z: "Overrule 1.5m, you can always change just discuss w the other agent." Key split negotiated with aorch (session name aorch); aorch reserves nothing; 429 bursts are the brake.
- 22:50Z: "Please remember to use all the GPUs as possible to do as much training in eval." Idle GPUs are a defect.
- 02:26Z (09-24): "why aren't you using the gemini key?" -> key draw comes first; never let a bind or maintenance step starve the workers; binds run on a fast idle node or are deferred.
- 02:40Z: the final handoff carries a section per worker lane; over 1,500 words is fine.
- Standing: lenient primary, strict secondary; no hard-coded hosts/paths/worker counts; storage never blocks; results under /data2 or /data3 only; Codex Luna only for ssh/ops; Devin Astra max for building; Astra reviews; Terra drafting; no arbitrary cross-student dependencies; never touch aorch's state or collector/ on main; deletions and coordination-store writes are user-only.

## Incidents and lessons

- Storm rule tripped at target 0 during a planned drain (one 503 retry exhaustion) and wrote a durable BLOCKED.json; user renamed it; fix 2cd7d87 (exhaustions excluded, threshold max(desired,4)/2) reviewed PASS; swap pending on the bind.
- Binding beside the live controller at 48 workers overloaded trinity-1-13 (load 103-113, 120 threads in I/O wait) and starved collection for about two hours; lesson: bind on a fast idle node or defer.
- The auto-mode classifier denied lanes: BLOCKED.json rename, worktree add under home, file edits and git commit in lane worktrees, direct scoring on another lane's root, a Devin launch; builds go through Codex/Devin dispatch with a writable lane root; user-only items go to the user with exact commands (all done today except the launcher branch).
- Other users take cards without notice (jihop2 trinity-0-23:0-3, zixinguo trinity-0-8:0,1,2,4, mgaur trinity-0-8 all 48 GB cards); probe occupancy and load before every launch; a lane may kill only its own stuck processes.
- Orchard ssh through IAP takes about 40 s to connect; watches need 240 s timeouts.
- Cross-host evaluation runs can lose a worker to the NFS negative-lookup cache; worker coordination ids ignore the run root; admission on trinity-2-8 reads base weights at 25 MB/s.

Additional collector-lane pitfalls:

- The meter stalls under load, so count terminals directly. A negative lease age is a scan-timing artifact.
- `start --workers N` does not reset a persisted target; always run set-workers after start.

## Successor first actions

1. Read this doc, then check for a live successor (lane dir mtimes, process start times) before acting.
2. Spawn the five lanes from their HANDOFF sections below (collector, Orchard, rescore, expansion, full-pool), each as a launch-and-babysit Claude lane on Opus with the mandatory 1-minute cadence after any launch.
3. Collector first: confirm the worker target (48) and the key draw on the meter; finish the 2cd7d87 swap; keep the 2-minute 429 brake.
4. Land results through the rescore lane (Terra drafts on branches off main; orchestrator fast-forwards and restarts the guard).
5. Keep the lane map in the fixed table format every tick; paper-ready numbers were due 2026-09-24Z, ICLR about 09-26.

| Lane | Per-lane first-actions heading in the verbatim section |
| --- | --- |
| collector | `## 4. Successor's first actions` |
| Orchard | `## First actions` |
| rescore and results | The watcher, scoring rule, results doc, working files, and pending sections |
| trinity expansion (seed replicates) | `## Successor first actions` |
| answer-only full-pool | `## Successor first actions` |

## Lane: collector

```text
# Handoff: r1316 root-B collector lane (written 2026-09-24 02:35Z)

L = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_collection_ramp_20260923T0820Z. D = /data2/jjyeung/agent_project_data/vsi_distill_training_20260917. R2 = $D/runtime_control/gt_teacher_r1316.

## 1. Purpose and state
The lane collects teacher traces toward 50,000 accepted: 20,139 strict came from root A, and root B (membership v3, union registry of 714 scenes, 97,652 ready) runs in `$D/collection_gt_r1316`. At 02:35Z there were 5,980 terminals. 146 questions are burned and must be excluded from the census (`$L/out/ERROR_ENDED_TERMINALS.jsonl`, plus the 16 stray-file failures of 10:07Z).
- Live epoch **fc6b364**. Controller **pid 3444735 on trinity-1-13**, config `$R2/collection_config_r1316_fc6b364….json`. Target **48** (readback 02:33:36Z).
- **2cd7d87 bind** (storm-rule fix): pid 4103520 on trinity-1-13 since 00:44:17Z, contract `$R2/CONTRACT_r1316_2cd7d87751fd70d001d3ba4ec71f3bd75d330bc1.json` sha256 `8a36534120562d40dd070dc52aa83f12bc076cc88540a2d36d016cadd848acc4`, output `$R2/collection_config_r1316_2cd7d87….json`, log `launch_20260923T0820Z/bind_2cd7d87.log`. **It is crawling: scene 334 of 714 at 02:33Z, 63.8 GB read, only +9 scenes in 40 min**, and it starves the workers on the same host (load about 100-110). The user-ordered move (stop it, rerun on trinity-2-8 or trinity-0-18) was **denied to this lane by the auto-mode classifier ("Shared Cluster Mutation")**. The user or an authorized executor must run it; the command is in `$L/work/bind_elsewhere.sh`. The bind is host-independent: collect.py has no hostname checks; the lease check reads age and agent only.

## 2. Detached processes (survive a session change)
| host | pid | what | log |
|---|---|---|---|
| trinity-1-13 | 3444735 (wrapper 3444733) | controller fc6b364 | `$R2/launch_20260923T0820Z/controller_r1316_fc6b364.log` |
| trinity-1-13 | 2167527 | lease keeper (240 s, until about 09-27 12:30Z) | `.../keeper.log` |
| trinity-1-13 | 2459924 | meter loop → `$L/out/health.jsonl` (stalls under load) | `$L/out/meter_err.log` |
| trinity-1-13 | 4103520 | 2cd7d87 bind | `bind_2cd7d87.log` |
| trinity-1-13 | 3221456, 4103516, 2720290, 2459925 | package guards on fc6b364, 2cd7d87, d1b52e4, ef1c3e6 | `$L/out/GUARD_LOG.md` |
| trinity-1-13 | 2865478, 2815721 | auto-stop watchdogs (expired) | `$L/out/autostop.log` |
| trinity-1-13 | 1811177 / 1809062 | r1317, not ours to touch | — |

## 3. Loops that die with this session
The 2-minute 429 brake and starvation watch (`starve_watch.log`), the bind-publish polls. No swap script is running.

## 4. Successor's first actions
- Set workers: `$L/work/setw_via_luna.sh N` (Luna → trinity-1-13 → `collect.py set-workers`, 0-96), then read back `cat $D/collection_gt_r1316/pool_b16384/WORKER_TARGET.json`. `$L/work/step_via_luna.sh N` adds a load15 < 40 gate.
- Swap once `bind_2cd7d87*.log` shows `{"config": ...}`:
  1. `setw_via_luna.sh 4`, wait for in-flight ≤ 4, then `setw_via_luna.sh 0`.
  2. Wait for attempts == terminals.
  3. Run `$L/work/stepK_swap_2cd7d87_remote.sh` on trinity-1-13 via Luna. It checks zero in-flight, sends SIGTERM to 3444735, heartbeats, starts at `--workers 0` with R1316_PKG=R1315_PACKAGE_PATH=`/home/jjyeung/agent_project_distill_epochs/2cd7d87/collector` and R1316_PLANNER_PACING_SECONDS=2, then **explicit set-workers 48**.
  4. Afterwards, point `setw_remote.sh` at the 2cd7d87 config.
- 429 brake, checked every 2 min: 44 is sustainable (≈5M, ≈900/h); 48 was clean overnight (≈1,000/h); 52+ gives 429 bursts. On n429_5m ≥ 5, step back to 44.
- `BLOCKED.json` in `pool_b16384/`: **only the user renames it** (`mv BLOCKED.json BLOCKED.json.acked_<ts>_<reason>`).

## 5. Pitfalls
Never bind on the collector host with many workers running; bind on an idle node. The meter stalls under load, so count terminals directly. A negative lease age is a scan-timing artifact. The key draw comes first (user ruling 02:26Z). `start --workers N` does not reset a persisted target; always run set-workers after start. A drain to 0 tripped the old storm rule; 2cd7d87 fixes it.
```

## Lane: Orchard

```text
# Orchard lane handoff — 2026-09-24 02:45Z

A successor lane spawns from this file. The lane directory is `L=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_orchard_setup_20260922T0700Z`. The Orchard root is `R=/project/community/jjyeung/distill`. STEP_16 through STEP_71 hold the full history.

## Jobs
| job | partition | what | state and ETA |
|---|---|---|---|
| 148380 | advanced | Qwen answer-only corrected run `gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2` (433d8a1, microbatch 2) | step 287/723 at 02:32Z, ~19.5 s/step wall; training ends ~04:55Z, then PUBLISHED.json |
| 148484 | preempt | 27B arm C student, VSTIBench-450 pack (0ab73f9, 4 workers), cell `qwen36_27b_distilled_armc_27b_orchard_d_vsti_c3` | pending; ~4.5 h once running; preempted runs requeue |
| roomfix VSTI b16 | general/preempt | `qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2_vsti_b16` | 450/450 scored; the landing loop copies it |

148201 (27B base VSTIBench) is complete and landed.

## Detached processes (survive a session change; on trinity-0-23)
- `work/feed/feed_loop.sh`: runs `$R/feed/feed.py` every 5 min for 12 h from 23:54Z. It submits the queue in `$R/feed/queue.jsonl`, and each item's `wait_file` is its trigger. Its next trigger is `$R/runs/gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2/publication/PUBLISHED.json`, which submits the answer-only `_vsi_b16` and `_vsti_b16` cells. Log: `logs/feed_loop.log`. Ledger: `$R/feed/ledger.tsv`.
- `work/feed/mirror_loop_b16.sh`: adds general copies of pending preempt b16 shards. Log: `logs/mirror_loop.log`.
- `work/feed/land_loop.sh`: lands every scored cell every 5 min for 24 h from 02:40Z, and appends `CELLS_LANDED.tsv`. Log: `logs/land_loop.log`.
- Watches: `work/train_watch_slow.sh 148380` (writes `logs/train_watch_148380.log`), `work/smoke_watch_148484.sh`, `work/landing_events.sh` and `work/babysit_148380_events.sh` (both write to `logs/babysit_events.log`).

## Dies with the session
In-session background waiters only. None of them resubmit anything.

## First actions
- ssh: `export PATH=/home/jjyeung/google-cloud-sdk/bin:$PATH CLOUDSDK_CONFIG=/tmp/jjyeung_gcloud_config; timeout 240 ssh -F /tmp/jjyeung_ssh_orchard_config -o ConnectTimeout=120 orchard '<cmd>'`. IAP connects take ~40 s, so use a 240 s timeout.
- Job checks: `squeue -u jjyeung -o "%i %P %j %T %M %R"`; `sacct -j <id> -D -X -o JobID,State,Start,End`. Run `bash $R/train_probe.sh 148380 gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2` for step, loss and checkpoint.
- Feeder pass by hand: `python3 -B $R/feed/feed.py`.
- Manual b16 shards: `SHARDS="0 1" PART=preempt MODEL=qwen35 VARIANT=distilled BENCH=vstibench_repr450_v2 CELL=<cell> EXTRAS="<adapter> <PUBLISHED.json> $R/runs/eval/qwen35_base_vsti_b16/run" bash $R/submit_shards_b16.sh`.
- Progress: `python3 -B $R/cell_progress.py`.
- Landing check: `python3 /tmp/jjyeung_orchard_lane/verify_publication.py /data3/jjyeung/orchard_publications/eval_cells/<cell>`.
- Resubmission rule: if 148380 fails before publishing, rerun `DEPENDENCY= ROOMFIX_GATE=$R/stage_ao_roomfix/ROOMFIX_GATE STUDENT=qwen35 bash $R/stage_ao_roomfix/launch_ao_mb2.sh`. The same run name resumes from checkpoints. Never resubmit a run that already has a PUBLISHED.json.

## Publications on /data3
- Training publications go to `/data3/jjyeung/orchard_publications/<run>/`.
- Evaluation cells go to `/data3/jjyeung/orchard_publications/eval_cells/<cell>/`, each with `SHA256_MANIFEST.json` checked on both ends and a row in `CELLS_LANDED.tsv`.
- Equivalence evidence is in `equivalence_12e477b_r10` and `equivalence_12e477b_r13`.
```

## Lane: rescore and results

```text
# Handoff — orchard-rescore-results lane (2026-09-24T02:37Z, no state change)

**Watcher**: pid `601049`, command `bash scripts/watch_eval_cells.sh` (cwd
`/data3/jjyeung/claude_orchard_rescore_20260923T0050Z`, detached via `setsid nohup`, PPID 1, own
session — survives session loss), log `out/watch_eval_cells.log`. Polls every 120s: (1) lists
`/data3/jjyeung/orchard_publications/eval_cells/` and prints `NEWCELL <name>` for any new directory
(state: `scripts/known_cells.txt`); (2) hashes `P/claude_orchard_setup_20260922T0700Z/CELLS_LANDED.tsv`
and prints `TSV_CHANGED` on any change, catching corrected re-lands into an already-known directory
name (state: `scripts/known_cells_landed_tsv.sha256`); (3) hashes `out/INBOX_TRINITY_FULLSET.md` and
prints `INBOX_CHANGED` on any append (state: `scripts/known_inbox_trinity_fullset.sha256`) — note
this lane's own appends to that file also trigger the signal, harmless. Restart pattern if it ever
needs to change: kill the pid, edit `scripts/watch_eval_cells.sh`, `setsid nohup bash
scripts/watch_eval_cells.sh >> out/watch_eval_cells.log 2>&1 < /dev/null &`, disown, verify `ps -o
pid,ppid,sid` shows PPID 1.

**Scoring rule**: lenient primary / strict secondary (2026-09-22T05:30Z ruling, never penalize a
correct answer in the wrong format). Every cell: `scripts/verify_manifest.py <cell_dir>` first
(full-manifest sha check, no exceptions), then `scripts/check_media_errors.py <cell_dir>` (any
`status: media_error`/`interrupted`/empty generation makes the cell provisional — score with stated
caveats only if explicitly instructed, otherwise hold), then `scripts/orchard_lenient_rescore.py` +
`scripts/orchard_results_table.py` (official per-benchmark metric via the real SENS-harness scorer,
never a flat mean — `scripts/recompute_matched_cohort.py` for any excluded-item subset view).
**Batched (bs16) cells pair only with batched cells**, never single-item, per the standing rule; the
decode-identity table proving non-token-identity is
`claude_decode_throughput_20260923T0805Z/out/identity/IDENTITY.md`.

**Results doc**: `/home/jjyeung/agent_project_distill/docs/RESULTS_PER_TYPE_20260922.md`. Layout:
`## OneThinker-8B` (base-complete sections, Set B pilot Orchard, Known defect, pre-roomfix
full-scale, Corrected Set B full-scale trinity harness roomfix incl. answer-only + four-cell
summary) → `## Qwen3.5-9B` (base vs arm C, Set B pilot Orchard, Batched-decode protocol block,
Qwen corrected full set 148295 batched) → `## Qwen3.6-27B` → status/interpretation/appendix/
provenance. **Terra procedure**: `bash agent/scripts/codex_dispatch.sh mech <worktree> <prompt> --label
<name>`; branch every worktree off `main`'s CURRENT tip (never a stale head); Terra self-commits
(fixed since `a864821`, ~13 consecutive successes); never touch `main` — orchestrator fast-forwards.

**Working files** (this lane's `out/`): `RESULTS_onethinker_orchard_cells.md`,
`RESULTS_qwen_orchard_cells.md`, `RESULTS_trinity_fullscale_roomfix.md`,
`INBOX_TRINITY_FULLSET.md` (append-only, shared with the `trinity_fullset_evals` lane).

**Pending**: Qwen VSTI roomfix (scored 450/450 on Orchard, landing-loop copy in progress); 27B base
appendix row (`qwen36_27b_base_vsti_pinned_c3`, scored, HELD for bundling); Qwen answer-only twin
(run 148380, ~05:30Z); seed replicates and full-pool runs not yet started.
```

## Lane: trinity expansion (seed replicates)

```text
# Handoff: trinity_expansion lane (written 2026-09-24 02:33Z)

Lane dir L=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_expansion_20260923T2250Z. Notes: STEP_1..STEP_10.md.

## Runs
Two OneThinker answer-only roomfix replicates with the run2_answeronly recipe (set mix_v25_roomfix_answeronly_20260923_trainer, split_trainer.json,
LoRA r32/a64, eff batch 32, 3 epochs, 723 steps). Only the seed and the world size change. Trainer e746674a3280 (branch trainer-seed-configurable-20260923,
worktree L/work/trainer_seed_wt; b084aaf plus the configurable seed). Manifests: L/run_s18/RUN_MANIFEST.md, L/run_s19/RUN_MANIFEST.md.
- s18: seed 18, world 4, run gtm2_v25full_onethinker_trinity_roomfix_answeronly_s18, lane L/run_s18.
- s19: seed 19, world 2, run ..._answeronly_s19, lane L/run_s19.
Protocols frozen 02:11Z in run_s1x/work/frozen, verified: split sha 42fc4208…, 7,684 train rows, 1,548 heldout.

## Review ruling
The Astra review of e746674 returned FAIL (L/review/REVIEW_E746674.md): seed-17 protocol hashes and work ids differ from b084aaf because they bind source bytes.
The orchestrator ruled it non-substantive: settings, training digest and batch-plan bytes are identical at seed 17. Seed-17 work stays on b084aaf.

## Live processes (survive a session change)
- Gates on trinity-2-8: s18 pid 2713858, s19 pid 2713915. Logs: run_s1x/work/cpu_gates.log. prepare-training started 02:11Z; expected finish 03:10-04:00Z (slow /data2).
- Picker: L/work/picker.sh, pid 1484237 on trinity-0-23 (setsid). Log: L/out/PICKER.log.
  - After GATES_DONE it writes run_s1x/out/GATE_FINISH.log.
  - Every 10 min it probes trinity-0-8 (all cards), 0-23:4-7 and 0-13:0-5. A card counts as empty if it is a 48 GB card with used < 100 MiB and no compute apps, on a host with load1 < 96.
  - s18 needs 4 such cards and s19 needs 2. On a match it appends CARDS.tsv rows (owner trinity_expansion, status S18-TRAIN/S19-TRAIN, expiry +8 h) and seds the pinned hostname in run_s1x/out/run_train.sh.
  - It then runs: ssh <host> "ONETHINKER_GPUS=<cards> setsid nohup bash L/run_s1x/out/run_train.sh > L/run_s1x/out/run_launch.log 2>&1 &".
  - run_train.sh waits for 3 clean readings, claims coord leases, trains vnice-wrapped with checkpoint resume (6 attempts), and finalizes to /data3/jjyeung/orchard_publications/<run>.
- Dies with the session: only this orchestrating agent. No local training or eval runs.

## Evaluation (blocked)
Launcher 91d47a0 refuses seed != 17 at publication validation. The user's pending commands:
1. Create a worktree/branch from the launcher repository /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_trinity_launcher_20260923T0745Z/work/launcher at 91d47a0.
2. Apply L/out/launcher_seed.patch and commit.
Until the orchestrator confirms that branch exists, run no eval, not even a dry run.

## CARDS.tsv
/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/CARDS.tsv. The latest row per host/idx wins. Append a row per card on claim and a RELEASED row on release. Never delete rows.

## Successor first actions
1. tail L/out/PICKER.log; check run_s1x/out/GATE_FINISH.log and cpu_gates.log (GATES_DONE).
2. For a launched run: nvidia-smi on its host, run_s1x/out/HEARTBEAT_train.log and WATCH_onethinker.log, and /scratch/jjyeung/ddp_onethinker_<run>_a*/train/metrics.jsonl. Report first step and s/step. Babysit every minute for 10 min, then every 10 min.
3. On completion, check the publication (finalize_onethinker.log, publication sha) and release the cards in CARDS.tsv.
4. After the launcher branch exists: dry-run eval (launch_eval.sh --dry-run --probe-cards), then VSIBench-500 and VSTIBench-450 on 24 GB cards (trinity-2-8 first, at most 4 shards on trinity-3-8), paired with base by certificate.
5. Append the tables to /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md in the existing format.
```

## Lane: answer-only full-pool

```text
# Handoff: answer-only full-pool lane (written 2026-09-24 ~02:00Z)

LANE = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_answeronly_fullpool_20260923T2250Z. S = /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918. Notes: STEP_1-3.md.

## The set
The set is a strict superset of the 7,684-row answer-only set. It adds one bare-answer row per other strict-accepted teacher question from root A (r1313) and root B (r1316).
- **Build v1:** 23,633 train rows (7,684 carried / 12,963 A / 2,986 B) and 4,235 heldout; 739 steps per epoch at batch 32. The v1 outputs were renamed to `S/answeronly_fullpool_20260923{,_trainer}_v1_labelfail` and its audit files copied to LANE/out/v1_build.
- **Holdout:** 38 heldout scenes (the inherited 37 plus 1). Split inherits eec29d98 and 5dcd3cdc. All 285 inherited groups are stable, and 0 train rows fall in heldout scenes, heldout qids or benchmark scenes.
- **Label ruling (coordinator):** every target equals ground truth. The carried rows already do (0 of 546 numeric differ). Fix ce5322b relabels the 1,930 new numeric rows that held the teacher's estimate (within 5%) to ground truth.

## Rebuild v2 (running)
- **Process:** `LANE/out/BUILD_COMMAND.sh` on trinity-0-18 under setsid, pid 2155571, started 01:53Z, commit ce5322b. It needs about 70 min, so it should finish near 03:05Z.
- **Logs:** LANE/out/full_build_v2_nohup.log, build.log and verify.log. Results: out/BUILD_SUMMARY.json.
- **Outputs:** `S/answeronly_fullpool_20260923` and `_trainer`. MANIFEST shas are in BUILD_SUMMARY.json. Root B counts may grow slightly from the new snapshot.

## Round-2 review (not yet dispatched)
- **Brief:** LANE/BRIEF_CODEX_REVIEW2.md.
- **Command:** `cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh review LANE LANE/BRIEF_CODEX_REVIEW2.md --model gpt-6-astra --effort high --label answeronly_fullpool_review2 --writable-root LANE/out/review`.
- **Receipt:** agent/scratch/codex_runs/<ts>_answeronly_fullpool_review2/final_message.md.
- **PASS requires:** a full scan finding target == ground truth for every new row, plus no regression in holdout, carried byte-identity, accounting and the loader. This is the last allowed iteration.

## Training (after PASS)
- **Scripts:** LANE/train/work/run_cpu_gates.sh, LANE/train/work/launch_after_gates.sh and LANE/train/out/run_train.sh. They use trainer b084aaf, config training_config_fullpool_w2.json (world 2, 1 epoch, batch 32, LoRA r32/a64, lr 1e-4, seed 17) and run tag gtm2_answeronly_fullpool_onethinker_trinity.
- **Publication:** /data3/jjyeung/orchard_publications/gtm2_answeronly_fullpool_onethinker_trinity.
- **Gate env:** regenerate LANE/train/work/gates_env.sh for v2. AO_SET is `S/answeronly_fullpool_20260923_trainer`, AO_SPLIT is its split_trainer.json, AO_INDEX_SHA and AO_SPLIT_SHA are their sha256sums, and AO_ROWS is `wc -l candidate_index.jsonl`. The current gates_env.sh holds v1 values; the index sha will change.
- **Cards:** trinity-0-18 GPUs 4 and 5. Probe with nvidia-smi and claim them in P/claude_swarm_20260923T0835Z/CARDS.tsv.

## Evaluation
Copy P/claude_trinity_fullset_evals_20260923T1944Z/launch_ao.sh with PUB set to the new publication and the output under LANE. Run VSIBench-500 (vsibench_answerable500) and VSTIBench-450 (vstibench_repr450_v2) on trinity-2-8 GPUs 0-7. Append the tables to /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md in the existing format.

## Survives vs dies
The setsid build, and later the setsid training, survive a session change. The wait loops and monitors of this session die.

## Successor first actions
1. Check pid 2155571 over ssh and tail verify.log.
2. When verify passes, read BUILD_SUMMARY.json, rehash the MANIFEST, and message the orchestrator with the counts.
3. Dispatch review 2.
4. On PASS, regenerate gates_env.sh, then run run_cpu_gates.sh, then launch_after_gates.sh on trinity-0-18 via setsid after claiming the cards.
5. Babysit: every minute for 10 minutes, then every 10 minutes. Report step 1 and s/step.
6. After publication, run the evaluations and append the tables.
```

## Appendix: FACTS.md verbatim

```text
# Facts for the 03:00Z handoff (orchestrator distill_orch, session fb40b735 on trinity-0-23; clock 2026-09-24 02:35Z)

## Head and docs
- main HEAD 7499e6f (= 0c4de3b handoff 22:15Z + Qwen corrected-set VSIBench section). Landing procedure: lanes commit on branches off main's tip in worktrees under their lane dir; the orchestrator runs `git -C /home/jjyeung/agent_project_distill merge --ff-only <sha>` and then restarts the collector package guard on trinity-3-8 through P/tools/luna_run.sh with the command in P/claude_guard_restart_20260923T0620Z/cmd_7499e6f.txt (substitute the current guard pid 2336105 and the new sha). Never edit collector/ on main while a collector runs.
- Results doc: docs/RESULTS_PER_TYPE_20260922.md (OneThinker four-cell table, Qwen corrected-set VSIBench section, swarm appendix). Inbox of tables: /data3/jjyeung/claude_orchard_rescore_20260923T0050Z/out/INBOX_TRINITY_FULLSET.md.

## Headline results (lenient primary / strict secondary; per-type tables in the doc)
- OneThinker-8B, corrected full set (room-fixed v2.5 + gtm2, 7,684 rows), trinity harness 91d47a0 launcher paired with 58794b8 base cells: base 39.19/31.47 VSIBench-500, 45.40/40.16 VSTIBench-450; trace student 38.68/38.68 and 38.28/38.28; answer-only control 48.03/48.03 and 53.45/53.45 (no parse failures, no cap hits). Answer-only beats base by +8.84 / +8.05 and the trace student by +9.35 / +15.17; the trace student is at or below base (VSTI -7.12: camera_obj_rel_dist_v2 -28, rel_dist_v1 -20, obj_obj_lr -16, camera_movement_direction -14; VSI route_planning 26 -> 16 from 26 cap-hit loops). Publications: /data3/jjyeung/orchard_publications/gtm2_v25full_onethinker_trinity_roomfix (sha 45427e94…) and …_roomfix_answeronly (sha 9ab1c09b…).
- Qwen3.5-9B corrected trace student (Orchard 148295, run gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2, 723 steps, mb2, final loss 0.16, publication sha e54cb5a0…, 748 files verified): batched bs16 VSIBench-500 48.02 lenient = strict vs batched base 14.92 (+33.10); every type gains; room_size_estimation 0.00 -> 67.00. Cell: /data3/jjyeung/orchard_publications/eval_cells/qwen35_distilled_gtm2_v25full_qwen35_orchard_w4_roomfix_qcap4096_mb2_vsi_b16 (manifest ff4580cc…). VSTIBench b16 cell at 394/450 at 02:26Z, one shard at a time on the general slot (jobs 148460-148466 general copies, 148436-148438 preempt); lands in eval_cells, scored by the rescore lane, documented on a branch together with the 27B base row.
- Earlier banked results stay valid: Qwen Set B pilot 39.80 vs 12.68 (VSI) and 44.57 vs 29.93 (VSTI); arm C stays ahead; swarm (about 30 cells) found no wording beating bare answers at 1,000 rows.
- 27B: base VSTIBench cell qwen36_27b_base_vsti_pinned_c3 landed 02:29Z (450/450, 442 ok, 8 cut by preemptions, 184 cap hits at 4,096 tokens with pinned thinking, 198 parse failures, strict 0.307, 143.5 s/item); appendix row only. 27B arm C student VSTIBench evaluation ordered on preempt (runs/armc_27b_orchard_d/publication, 4-worker pack, about 18 GPU-h, preempt only).

## Running now
- Qwen answer-only corrected run: Orchard 148380 (gtm2_v25full_qwen35_orchard_w4_roomfix_answeronly_mb2, advanced, orchard-community-3), step 287/723 at 02:32Z, loss 0.38, 17.8 s/step; training ends about 04:45Z, publication after; its PUBLISHED.json triggers the feeder for batched bs16 VSIBench-500 and VSTIBench-450 cells paired with the batched base cells (submit_shards_b16.sh on deployment 0ab73f9; feeder checks every 5 min; run one pass by hand if the marker appears between passes).
- Collector r1316 root B on epoch fc6b364 (controller pid 3444735 on trinity-1-13): 5,973 terminals at 02:24Z; starved since about 01:20Z by the 2cd7d87 bind (pid 4103520, started 00:44:17Z, reads every scene asset, scene 325/714 at 01:53Z, projected publish about 03:15Z); workers stepped 48 -> 36 -> 24 -> 20; user ruling 02:26Z: key draw comes first, workers back to 48 at once (restore48_0229 through Luna), bind finished only if within 30 min, otherwise stopped and rerun on a fast idle node (trinity-2-8 or 0-18). After bind publish: drain via 4 then 0, stop at zero in-flight, cold start 2cd7d87 (checkout /home/jjyeung/agent_project_distill_epochs/2cd7d87, contract CONTRACT_r1316_2cd7d87…json sha 8a365341… under runtime_control/gt_teacher_r1316), pacing 2 s, explicit set-workers 48, 2-minute 429 brake (44 sustainable at 5-6M tok/min, 48 clean for 30 min, 52 and 60 burst 429s at 7.5-8M). Lease keeper 2167527 and meter 2459924 on trinity-1-13; meter rows stall under I/O load and a negative lease age is a scan artifact. If a BLOCKED.json appears in collection_gt_r1316/pool_b16384, only the user renames it aside (mv to BLOCKED.json.acked_<ts>_<reason>). Totals: root A 20,139 strict accepted; root B 5,973 terminals (yield about 0.76); 130 questions burned by streamed 503s and 16 by a stray file, excluded by the census. 50k strict needs about 38 h at 900/h.
- Answer-only full-pool set: 23,633 train rows (3.08x; 7,684 carried byte-identical + 12,963 root A + 2,986 root B), 4,235 held-out, 38 held-out scenes, all 285 inherited groups kept; round-1 review FAILED only on label source (1,930 new numeric rows carried the teacher estimate); carried rows verified equal to ground truth (0 of 546 numeric differ); fix ce5322b relabels to ground truth; v2 rebuild on trinity-0-18 (pid 2155571, started 01:53Z, verify about 03:05Z); round-2 review brief ready; then gates, claim trinity-0-18 GPUs 4,5, train one epoch (739 steps, world 2, batch 32, trainer b084aaf, run tag gtm2_answeronly_fullpool_onethinker_trinity), evaluate on trinity-2-8 GPUs 0-7 through launch_ao.sh, append tables to the inbox. Paths: student_diagnostic_pilot_20260918/answeronly_fullpool_20260923 (+_trainer); v1 outputs renamed *_v1_labelfail.
- Answer-only seed replicates s18 (world 4) and s19 (world 2): trainer e746674 (seed configurable; Astra FAIL ruled non-substantive: protocol hashes bind source bytes, settings and batch plan identical at seed 17); protocols frozen (train 7,684 / heldout 1,548, split 42fc4208…); prepare-training on trinity-2-8 since 02:11Z (/data2 at 1.6 MB/s), then the picker (pid 1484237 on trinity-0-23, L/out/PICKER.log) launches on the first host with enough empty 48 GB cards among trinity-0-8, 0-23:4-7, 0-13:0-5 (trinity-0-8 saturated by another user: load 421, all 48 GB cards held). Evaluation needs the launcher branch (user command pending: worktree from P/claude_trinity_launcher_20260923T0745Z/work/launcher at 91d47a0 into L/work/launcher_seed_wt, apply L/out/launcher_seed.patch, commit).
- 27B smoke 148201 finished (its cell above). Flame partition closed (QoS-gated; mt01 holds none); admin must attach a flame QoS.

## Rulings today (verbatim where short)
- 21:26Z: "Overrule 1.5m, you can always change just discuss w the other agent." Key split negotiated with aorch (session name aorch); aorch reserves nothing; 429 bursts are the brake.
- 22:50Z: "Please remember to use all the GPUs as possible to do as much training in eval." Idle GPUs are a defect.
- 02:26Z (09-24): "why aren't you using the gemini key?" -> key draw comes first; never let a bind or maintenance step starve the workers; binds run on a fast idle node or are deferred.
- 02:40Z: the final handoff carries a section per worker lane; over 1,500 words is fine.
- Standing: lenient primary, strict secondary; no hard-coded hosts/paths/worker counts; storage never blocks; results under /data2 or /data3 only; Codex Luna only for ssh/ops; Devin Astra max for building; Astra reviews; Terra drafting; no arbitrary cross-student dependencies; never touch aorch's state or collector/ on main; deletions and coordination-store writes are user-only.

## Incidents and lessons (today)
- Storm rule tripped at target 0 during a planned drain (one 503 retry exhaustion) and wrote a durable BLOCKED.json; user renamed it; fix 2cd7d87 (exhaustions excluded, threshold max(desired,4)/2) reviewed PASS; swap pending on the bind.
- Binding beside the live controller at 48 workers overloaded trinity-1-13 (load 103-113, 120 threads in I/O wait) and starved collection for about two hours; lesson: bind on a fast idle node or defer.
- The auto-mode classifier denied lanes: BLOCKED.json rename, worktree add under home, file edits and git commit in lane worktrees, direct scoring on another lane's root, a Devin launch; builds go through Codex/Devin dispatch with a writable lane root; user-only items go to the user with exact commands (all done today except the launcher branch).
- Other users take cards without notice (jihop2 trinity-0-23:0-3, zixinguo trinity-0-8:0,1,2,4, mgaur trinity-0-8 all 48 GB cards); probe occupancy and load before every launch; a lane may kill only its own stuck processes.
- Orchard ssh through IAP takes about 40 s to connect; watches need 240 s timeouts.
- Cross-host evaluation runs can lose a worker to the NFS negative-lookup cache; worker coordination ids ignore the run root; admission on trinity-2-8 reads base weights at 25 MB/s.

## Successor first actions
1. Read this doc, then check for a live successor (lane dir mtimes, process start times) before acting.
2. Spawn the five lanes from their HANDOFF sections below (collector, Orchard, rescore, expansion, full-pool), each as a launch-and-babysit Claude lane on Opus with the mandatory 1-minute cadence after any launch.
3. Collector first: confirm the worker target (48) and the key draw on the meter; finish the 2cd7d87 swap; keep the 2-minute 429 brake.
4. Land results through the rescore lane (Terra drafts on branches off main; orchestrator fast-forwards and restarts the guard).
5. Keep the lane map in the fixed table format every tick; paper-ready numbers were due 2026-09-24Z, ICLR about 09-26.
```
