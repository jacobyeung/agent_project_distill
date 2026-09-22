# Distillation lane handoff, written 2026-09-22 21:00Z

## Command

This checkpoint supersedes `docs/DISTILLATION_HANDOFF_20260922_1130Z.md` (commit `5e17f02`) for everything since 11:30Z. The 1130Z document still holds the full narrative behind items not repeated here, including the v1 full-set gate FAIL detail, the Orchard capacity table, and the decode-diagnosis detail. This checkpoint records the `/home` quota exhaustion at 10:02Z, the more damaging `/data2` quota exhaustion from about 19:30Z to 20:00Z, the separate authentication outage from 15:15Z to 18:50Z, the recovery state for both trainers, the `/data2` relief lane, the collector throttle attempts, the package-guard state, and the first VSTIBench results.

`P` denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`.

## 1. Incident and recovery state

The `/home/jjyeung` quota reached 251G/251G with 0 free at 10:02Z. Re-pointing logs to `/data2` mostly recovered that incident, but `/data2` later became full. At 19:31Z, `nebby.ib:/exports/data2` had 90 MiB available and 183,614 of 51,933,051 inodes free at 20:00Z; it had 64G free at 19:00Z and fell at 66-78 GiB/h through the hour. The `/data2` failure killed the two live trainers, every evaluation shard on trinity-0-18, the package guard, r1317's and the v2-generator's watchers, and both collectors' health/control writers. It also broke the Orchard `gcloud`/IAP ssh control path until its config moved to node-local `/tmp`.

The authentication outage from 15:15Z to 18:50Z killed every live non-detached subagent. Detached `setsid` processes survived. The Orchard control path now uses `/tmp/jjyeung_gcloud_config`, `/tmp/jjyeung_gcloud_wrapper.sh`, and `/tmp/jjyeung_ssh_orchard_config`; this relocation does not survive a reboot. Nothing was deleted.

The current recovery state is:

| item | confirmed state |
|---|---|
| Qwen 9B arm C rep2 | The trainer died at step 266/288. Its last complete checkpoint is `step_250`, with 38 steps remaining. A resume launched with pid 263511 on trinity-0-18 was stood down at 20:55:59Z because another user's process occupied GPU 0. Relocation to trinity-1-18 started at 20:56:22Z and is not confirmed complete. |
| Qwen 3.6-27B arm C | The trainer died at step 78/96. Its last complete checkpoint is `step_75`, which is fully synced to `/data3`; 21 steps remain. Resume leases were issued on trinity-0-13 at 20:47:12Z through `2026-09-23T04:47:12Z`, and weights loading was confirmed for all three ranks. Actual resumed training steps are not confirmed. |
| Orchard arm C chain | Job 147597 was RUNNING from 19:08:19Z on orchard-community-2, and job 147599 was PENDING on `afterany:147597` at the last read. The `/data2` failure did not directly affect these jobs. |
| Orchard 27B base VSIBench control | Job 147601 had all four shards fail on the `PREPARED`/`STUDENT_FRAME_ROOT_MAP` path-containment mismatch. Neither identified fix option had been applied. |
| Package guard | The guard restarted with pid 755985 at 19:18:48Z and died silently within minutes. The restart is not confirmed running. |

## 2. Relocation and collector state

The no-deletion `/data2` remedy moves finalized questions' `gt_masks` caches from `/data2` to `/data3` and leaves an absolute symlink in place. The relocation lane `claude_data2_relocate_20260922T2010Z` runs on trinity-0-23, and its STEP_1 and STEP_2 files stay on `/data3` because `/data2` had no room. The pilot question `vsi590k_000507` was relocated and its symlink was verified over ssh from trinity-3-8.

Three movers, S0/S1/S2, cover 25,103 combined ids in disjoint round-robin thirds of 8,368, 8,368, and 8,367 ids. The set contains 20,541 ids from the audited `CANDIDATES.txt` and 4,562 additional tolerance-25 census ids. The movers run with `ionice -c3 nice -n 19` at about 25-30 questions per minute combined. The script uses only `mv` and `ln -s`; it does not delete anything. The movers are children of the current session shell rather than `setsid`-detached, so they die if that session dies. STEP_2 at 20:40Z was explicitly interim, and its totals were not finalized when read. The measured `gt_masks` size was about 6.3 MB mean across a 10-question sample, with a 3.6-12 MB range, so the estimated relief from relocating every accepted question is 130-155 GiB. The remaining roughly 11 TB of `/data2` is in `archive_blobs`, `episode_inputs`, and `terminals`, whose sizes were not measured.

Neither collector throttle attempt took effect. For r1313, `setw.sh 4` wrote `workers=4` to `watchdog_control_v5.json` on all 40 tries from 20:33:34Z to 20:46:40Z, but the supervisor did not adopt it. `WATCHDOG_HEALTH.json` still reads `target=28`, `finalized=26878`, and `utc=2026-09-22T19:57:55Z`, although watchdog pid 212703 reports `R`. For r1317, all 5 `setw_r1317_ramp.sh 4` attempts raised `RuntimeError: stale or foreign collection lease` in `collector/collect.py:coord_guard`; `WORKER_TARGET.json` remains `storm_workers=32, total_workers=32`. The pre-check state was 3,157 terminals, 3,176 attempts, and a 3,357 pool, or 94.1% terminaled. Neither attempt was retried.

## 3. Results — VSTIBench, OneThinker arm C variants

The first results cover 450 items with lenient scoring primary and strict scoring secondary. Both drivers hit the same `bash local` bug in `claude_eval_prep_20260922T1122Z/lib/lib_evalprep.sh:66` immediately after VSTIBench generation finished. The local driver copies were fixed by splitting the `local` declaration, the shared `lib/` was left untouched, and the original generations were scored unchanged after relaunch at 18:57-18:58Z. The protocol used an instructed prompt, a 4,096-token budget, 32 frames, greedy decoding, seed 17, RGB-only input, tool-free evaluation, and harness `58794b8`.

**Rep3** (trinity-1-3 cards 0,6; adapter `/data3/jjyeung/ddp_onethinker_v1cxl2_onethinker_20260922T0335Z_armc_rep3`; source `RESULTS_armc_rep3.md`):

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict->lenient) | median gen tokens |
|---|---:|---:|---:|---:|
| base | 45.40 | 40.16 | 55 -> 14 | 133 |
| arm C (published) | 43.59 | 43.59 | 1 -> 1 | 306 |
| this run (rep3) | 38.27 | 38.27 | 1 -> 1 | 284 |

Per-type strict macro: base 53.42, arm C published 50.29, rep3 46.44. The VSIBench 500-item run was in flight at 19:31Z with driver pid 1982259 on trinity-1-3; its attempt-2 relaunch used `--resume` and preserved 65 items, but completion was not confirmed.

**Answer-only control** (trinity-1-13 cards 2,3; source `RESULTS_armc_answeronly.md`):

| cell | lenient (primary, %) | strict (secondary, %) | parse failures | median gen tokens |
|---|---:|---:|---:|---:|
| base | 45.40 | 40.16 | 55 -> 14 | 133 |
| arm C (published) | 43.59 | 43.59 | 1 -> 1 | 306 |
| this run (answer-only) | 43.35 | 43.35 | 0 -> 0 | **2** |

Per-type strict macro: base 53.42, arm C published 50.29, answer-only 52.82. The VSIBench 500-item run used driver pid 1768489 on trinity-1-13, measured about 2,540 items/h across two cards before two shards stalled in the 19:31Z event, and resumed on their own by 19:49:01Z. Completion was not confirmed.

## 4. Training, datasets, and pending mixes

OneThinker arm C answer-only training finished at 14:21Z with last logged loss 0.222 on trinity-1-13 cards 2,3. The arm C matched subset contains 3,431 rows, with 3,052 train rows and 379 held-out rows. Its `candidate_index.jsonl` is at `/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl` with sha256 `530663315143fa6202983cdad82c8bc4375c1c6f9b111f230ceebe09410ea80c`. Its split is `/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z/split.json` with sha256 `4dd7467fd3b63b6a124bebf7c9a7be1749e3ac7696f6c7acaaaa49755efe4083`.

The v2.5 corrected full build rendered 18,692 round-3 strict sources, admitted 2,856 rows, split them into 2,130 train and 726 held-out rows, and deferred 15,836. Its config sha256 is `d6ca6ef4beb4d4b8bd4ead9cac6b0f62622d6f77558a6476f1475e1b05bd7e86`. Its internal verification passed, but its independent review remains pending, so `training_eligible: false` remains in force. The compact-target type-cap review also failed for commit `69eee15d3de0efd2b6e5a27ccf4436810d1925e2` against parent `5411443`. The fix lane `/data3/jjyeung/claude_typecap_fix_20260922T2040Z/` is in progress, has no `DEVIN_LANE_DONE` marker, and has no recorded commit sha.

The gtmeasure v1 resume generated 137/137 remaining scenes and 3,810 rows in `S/gtmeasure_v1_20260922_resume/`, but it is not yet merged with the original 169-scene `gtmeasure_v1_20260922/` directory. The gtmeasure v2 full generation finished at 20:04:17Z; its marker is `FULL_GENERATION_V2_DONE` under `P/claude_gtmeasure_v2_verify_20260922T0758Z/`, and its generator pid was 3602895. The two prepared mix commands, with ratios 0.25 for the pilot and 0.50 for the corrected set, have not been confirmed run.

## 5. Orchard and review state

Orchard deployed `dc80ae1` and the 27B base VSIBench control used array job 147601. All four shards failed within a minute at `orchard_trainer_dc80ae1/student_pilot/orchard_eval/contracts.py:331` with `ValueError('Generation package reference escapes its directory')`. The recorded root cause is a launcher wiring mismatch: `submit_eval_27b_base.sh` passes `PREPARED` from the project-filesystem copy while `eval_job.py:76` sets `STUDENT_FRAME_ROOT_MAP` to a node-local staged tree. The two identified options were to pass `PREPARED` as the staged path or resolve both sides of the comparison at `contracts.py:330`/`:352`; neither was applied, and option 2 needs an independent review.

The Orchard admission bind fix (`7b691ad` plus `386702e`) received PASS reviews at 13:45Z and 19:49:31Z. The eval-contracts fix (`237b451` plus `dc80ae1`) received an Opus 5.5 PASS at 19:05Z. Astra's re-review of the eval-contracts fix failed twice at 19:58Z and 20:07Z while writing its receipt/cache because of `No space left on device`; the Opus 5.5 PASS remains the only recorded review of that change.

## 6. Rulings in force this window

1. The 08:50Z ruling requires training on the 3,431-row arm C subset while the failed full set is re-rendered until its independent gate passes: “Make sure that it passes.” The v2.5 rebuild satisfies the re-render half, but the condition remains open because its type-cap fix failed independent review.
2. Lenient scoring is primary, and strict parsing is secondary. Never penalize a correct answer given in the wrong format.
3. Every GPU on the cluster is usable. Never ask for allocation, and leave every other experimenter's running process untouched.
4. `vnice` is required only above 16 large GPUs held in total on trinity; below that threshold it is optional. Orchard has no `vnice`; Slurm allocation, QoS, and preemption govern there.
5. Maximize Orchard's use. Preemption is acceptable, and partial results plus resume are preferred over holding out for an uninterrupted run.
6. The shared Gemini key cap is “You can go up to six million” tokens per minute across every collector drawing on it.
7. Opus 5.5 is permitted for subagent gate reviews when Codex cannot run. Codex Astra re-reviews use `gpt-6-astra --effort xhigh`, and Devin builders use Astra max priority.

## 7. Watchers a successor must re-arm or check

The successor must confirm the r1313 health state directly rather than trust its stale health file. The last recorded values are `target=28`, `finalized=26878`, and `utc=2026-09-22T19:57:55Z`; watchdog pid 212703, controller pid 215319, guard pid 120283, and lease keeper pid 213556 were the last known pids.

The successor must check r1317 directly. Its last recorded state was 3,157 terminals, 3,176 attempts, and a 3,357 pool, and its worker-count change failed on the stale or foreign collection lease guard.

The successor must check the Qwen 9B relocation `RELOCATE.log`, complete the host-pin move if the relocation succeeds, and re-arm the resume on trinity-1-18. The successor must also check whether the Qwen 3.6-27B resume has reached actual training steps. Neither resume's own WATCH log path was confirmed.

The successor must confirm whether the package guard restart lane `claude_guard_restart_20260922T1945Z` is running, whether the three non-detached movers S0/S1/S2 are still alive, whether the two gtmeasure mix commands have run, whether the gtmeasure v1 directories have been merged, whether the type-cap lane has committed, and whether Orchard job 147599 has started. The Orchard admission review waiter was pid 3744262 and its condition fired with the Astra PASS at 19:49:31Z; its exit still needs confirmation.

## 8. Must not touch / not this session's to do

Never edit `collector/` on `main` while the collector runs from it. Never touch another experimenter's GPU processes or cards. In particular, trinity-0-13 cards 4,5 and 6 remain off-limits, and the eight `eval_gpu.run` processes started by `jihop2` on trinity-0-18 at 20:43:43Z were left untouched. The `/data2` relief lane uses only `mv` and `ln -s`; dead-run marker files such as `STOP_RENEWERS_q27b`, `STOP_RENEWERS_qwen`, and `LANE_COMPLETE_qwen` remain in place. Nothing was deleted.

## 9. User-only deletion queue

Nothing in this queue has been acted on. The relocated `gt_masks` mirror at `/data3/jjyeung/relocated_from_data2_20260922/gt_masks/` is a relief copy, not a deletion candidate. Permanent removal of the `/data2` originals requires the user's decision, as does any decision to remove the `/data3` mirror; the estimated total once movers finish is 130-155 GiB.

The following items remain queued for the user's decision: `agent_project_distill/agent/scratch/devin_lanes/claude_compact_v25_typecap_20260922T1015Z/out/devin_xdg/data/devin/credentials.toml` (331 bytes); `/project/community/jjyeung/probe_256m.bin`; `probe2_256m.bin` on Orchard; the stale index-lock-class file renamed aside at 2026-09-21 05:26Z; the link-latency probe directory; one stray `.nfs_probe` file; and one stray placeholder file. The last four items must be re-located before they are queued for deletion.

The confirmed-safe items remain untouched: `agent_project_distill/agent/scratch/devin_lanes/answer_line_unit_fix_20260921T2355Z` (12M, `DEVIN_LANE_DONE`, content landed as commit `d9e3d57`) and `agent_project_distill/agent/scratch/devin_lanes/qwen27b_student_20260922T0545Z/out/devin_test_tmp` (678K, smoke-test scratch only). The latter lane's live orchestration files must stay because the 27B job still reads them.

## 10. Not verified when this was written

The package guard restart was not confirmed; the only observed output was an empty `guard_stdout.log`. Neither arm-C resume was confirmed to have reached actual training steps. The final r1313 and r1317 states were not confirmed beyond `target=28`/`finalized=26878` and 3,157/3,176/3,357 respectively. The two gtmeasure mix commands were not confirmed run. The three relocation movers were not confirmed alive, and their final totals were not confirmed because STEP_2 was interim. The type-cap Devin fix was not confirmed committed. Orchard job 147599 was not confirmed started; it was PENDING on `afterany:147597` at the last read. The Qwen arm A r6 VSIBench evaluation was not updated by any source read in this window and remains unconfirmed.
