# Distillation lane handoff, written 2026-09-23 02:30Z

## Command

This checkpoint covers 2026-09-22 23:15Z through 2026-09-23 02:30Z. It supersedes `docs/DISTILLATION_HANDOFF_20260922_2330Z.md` (commit `7adf4ba`) for everything after 2026-09-22 23:15Z. The 23:30Z and `docs/DISTILLATION_HANDOFF_20260922_2100Z.md` (commit `573c08d`) documents remain the sources for the earlier narrative; this checkpoint cites them rather than repeating the `/home` and `/data2` quota exhaustions, authentication outage, storage census detail, answer-only result and tables, Orchard capacity table, decode diagnosis, and earlier rulings.

`P` denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`. `S` denotes `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918`.

## 1. Session restart and surviving work

The user wants the orchestrator session restarted on Opus 5.5 at this handoff, after the in-flight jobs have launched. The successor must re-arm every item identified below as dying with the session.

Slurm jobs on Orchard, the detached v2.5 render driver, collectors r1313 and r1317, the `/data3` mover lane, and the Mind backbone-transfer driver survive a session restart. The rest of this checkpoint records their state and the successor actions that the restart leaves behind.

## 2. Rulings and executor tiering

Codex Luna (`gpt-5.6-luna`) serves ssh and cluster-operations lanes only and is never the default coding tier. Devin builders use `gpt-6-astra-max-priority`; Codex gate reviews use `gpt-6-astra` at `xhigh`; mechanical drafting uses `gpt-5.6-terra`; Opus 5.5 or Astra follows a Codex or Devin failure. `DEVIN_PERMISSION_MODE=dangerous` is exported in the user's `~/.bashrc`.

Account `mt01` cannot access Orchard's `flame` partition without a QoS grant, while `preempt_qos` is approved. At 00:55Z, the other experimenter session reported that the user gave the Gemini key priority, so the collectors hold reduced worker counts and never ramp; the trace goal already stands at 20,139 strict.

The r1313 controller on trinity-3-8 runs supervisor-less at about one terminal per hour, with controller pid 826571 and lease-keeper pid 213556 expiring about 04:05Z. The r1317 collector on trinity-1-13 runs at 16 workers and drains its last roughly 100 of 3,357 terminals, with controller pid 1811177 and keeper pid 1809062.

The Mind cluster is approved for cold backbones at `/lab_data/tarrlab/jacoby/agent_project/dense_backbones`. Its lane, `/data3/jjyeung/claude_mind_backbones_20260922T2245Z/`, moves at about 16 GiB/h.

## 3. Storage and relocation

At 01:00Z, `/data2/jjyeung` had 1,042 GB free and was 91 percent used. An independent 02:07Z check reported an 11T filesystem, 9.6T used, 1.2T available, and 90 percent used.

The `/data3` mover lane at `/data3/jjyeung/claude_data2_moves_20260922T2240Z/` is at HuggingFace entry 4 of 17 and moves data by `mv` plus symlink. Its deletion mirror is `/data3/jjyeung/TO_DELETE_20260922/`; relocated masks at `/data3/jjyeung/relocated_from_data2_20260922/` include 383 complete and 729 partial entries.

The user-only deletion queue remains as the 23:30Z document records it. The only addition is that untracked `.devin/agents/` and `.devin/skills/` appeared at the repository root at 2026-09-22 20:34Z with unknown origin and entered `.git/info/exclude` at 01:45Z so provenance gates read the tree as clean.

## 4. Set B materialization

The train-only trainer layout is `S/mix_v25_gtm2_r050_20260922_trainer_trainonly`, with 4,260 rows: 2,130 compact and 2,130 gtmeasure. Its `candidate_index.jsonl` has 4,260 lines and sha256 `b2878130847582dcc5fb15d555a8664bbb689a5df09d53d9551fcaacd32191f6`; its targets sha256 is `19c8c26e14ca542462d6cd9a326ae4f0d416a645bb990853a8d8ffdb53ffcf9c`. Zero of the 1,746 held-out qids appear in the train-only layout.

`split_trainer.json` sits at `S/mix_v25_gtm2_r050_20260922/split_trainer.json`, not inside `_trainonly`, and uses schema `provisional-whole-scene-split-v1`. Set A has sha256 `9e41230d286cb63fa2178e31383bfd1abc806f214f66989fa8fbe46d6ac342e9`; Set B has sha256 `99d6a82b827509baab88aa85c2a4e74f18d5569383507dfa5186151558c423b6`.

The trainer's `make_inherited_split` reproduces published sides exactly with `hashed_group_count 0`. The mixer records scenes in `new_train_scenes`, which the trainer ignores, so the scene lists were rebuilt from rows.

## 5. Orchard training and evaluation

The Orchard lane is `P/claude_orchard_setup_20260922T0700Z/`, the root is `/project/community/jjyeung/distill/`, and the trainer branch is `orchard-eval-containment-bothsides-20260922` at `12e477b`.

`preempt_qos` limits the account to four nodes and 32 GPUs. Ten scattered one-GPU shards held that cap; `scontrol top` is denied, so the lane used `scontrol hold` on pending shards 147701-147705, which remain held. Evaluation uses `eval_node_pack.slurm` with eight workers per node and sequential cohorts.

Job 147670 completed 27B Orchard training on `advanced`: four H100s, microbatch 4, 49.6 seconds per step, 96 steps, 1:54 wall time, no OOM, and no KeyError. Its publication is `runs/armc_27b_orchard_d/publication`, copied and two-ended verified to `/data3/jjyeung/orchard_publications/qwen36_27b_armc_orchard_d/` with 121 files and 993.6 MiB.

The OneThinker Set B pilot is job 147711 on `advanced`, world 4, run `gtm2_v25_onethinker_orchard_a`, with 402 steps at 9.9 seconds per step. It launched through `afterany:147670`; its ETA was about 02:37Z, and loss fell from 2.19 to 0.37 by step 28. `runs/gtm2_v25_onethinker_orchard_a/` has `GTM_GATE_PASS`; `training.json` pins protocol sha `606eeb39...`, which pins `split.inherited_from` sha `99d6a82b...`.

The Qwen3.5-9B pilot races preparation job 147716 on `general`, world 4, run `gtm2_v25_qwen35_orchard_w4`, against pending preempt job 147717 at world 8. The first starter wins and the other is cancelled; job 147706, the world-8 OneThinker preparation, was cancelled. OneThinker base job 147718 is packed for VSIBench-500 and then VSTIBench with the instructed prompt and harness `12e477b`.

`generate.py` requires identical core key sets for pairing. The thinking-off 27B base cell `qwen36_27b_base_vsi_thinkoff` therefore remains a standalone row, with lenient and strict both 24.75 and 207 content parse failures, while 27B base cells pinned to VSI and VSTI queue ahead of every 27B distilled cell.

After 147711 completes, the preempt order is OneThinker pilot cells, held packed 9B base shards, 9B base VSTIBench, pinned 27B base, and then 27B distilled cells for both publications. Evaluation copies land at `/data3/jjyeung/orchard_publications/eval_cells/<cell>/` with two-ended manifests. Single-quoted ssh heredocs mangled quotes in two preparations, so scripts must be written locally and sent with rsync. At 02:05Z, `advanced` had 4 GPUs, `preempt` 4, rising to 12 when 147718 starts, and `general` 1.

## 6. Lenient rescore lane

The lenient rescore lane is `/data3/jjyeung/claude_orchard_rescore_20260923T0050Z/`. Its scripts are `orchard_lenient_rescore.py`, `orchard_results_table.py`, `verify_manifest.py`, and `watch_eval_cells.sh`; its verified combined draft is `out/RESULTS_qwen_orchard_cells.md`.

The wrappers resolve the Orchard-native `run` pin locally when an Orchard path is unreachable from trinity, while still checking the recorded sha256. Work resumes per evaluation-cell copy.

## 7. Qwen3.6-27B trinity publication

The publication branch is `trainer-27b-model-pin-20260922`, at `ac73f1e`: `16a64ac` pins the model, `096617d` completes publication diagnostics, `dcdb7aa` fixes a regression, and `ac73f1e` records refusals. Astra returned two PASS verdicts and 82 tests OK.

`PUBLISHED.json` has sha256 `dceeefa0fde7419d426a9d1f5f5ace4624015c34dba36c75c407236879d91958`. The accepted run is `ddp_qwen36_27b_armc_27b_trinity_20260922T1110Z`, with 1,212 tensors; its copy is `/data3/jjyeung/orchard_publications/qwen36_27b_armc_trinity/` with 123 files.

`finalize` cannot rerun from a fixed checkout because the protocol pins the runtime closure by path and sha and includes `contracts.py`. Trinity-side 27B evaluation remains blocked because harness branch `d65bd2b` changes the token limit, omits the answer-format instruction, and has no sharding, so all 27B cells run on Orchard. `STEP_1.md` and `STEP_2.md` under `/data3/jjyeung/claude_q27b_finalize_fix_20260922T2355Z/out/` are verified present; the branch is not landed.

## 8. Results and pending repeats

Qwen3.5-9B run r6 reaches 26.41 on VSIBench against base 15.47 and arm C 49.25; it reaches 25.67 on VSTIBench against base 28.59 and arm C 46.56. Lenient equals strict for r6. The VSIBench control records 197 parse failures and 194 cap hits without answers, while VSTIBench records 212 parse failures and 211 cap hits without answers; the source characterizes the controls as 40 to 45 percent parse failures.

The 27B thinking-off base reaches 24.75 with lenient equal to strict, 207 parse failures, and no compatible distilled cell. It is a standalone reference row. `docs/RESULTS_PER_TYPE_20260922.md` carries the full per-type tables for both r6 and this base row.

The r6 recovery stalled on a false `.done` marker and stale per-inode NFS ENOSPC on trinity-0-23. The lane-copy relaunch from trinity-1-3 used `/data3/jjyeung/claude_qwen_r6_eval_resume_20260922T2047Z/`.

For OneThinker replicate 3 on VSIBench, the user cleared the two stale locks at 02:20Z with `coord.py fail` on `shard_0_of_4` and `shard_1_of_4` of `student_eval__distilled_onethinker_vsi500__s17__2d6cb205`. `P/claude_eval_recover_20260922T1853Z/` is finishing the final 185 items and will write `RESULTS_armc_rep3.md`.

The Qwen 9B trinity resume is parked at checkpoint step 250 of 288 in `P/claude_qwen9b_rep2_resume_20260922T1950Z/`. Another user took trinity-0-18, and every trinity-1-18 card was in use at 22 GB each at 02:20Z; `out/relocate_leases_1_18.sh` remains unused.

## 9. Uncapped v2.5 render

The uncapped render lane is `P/claude_v25_uncapped_render_20260923T0030Z/`, writing `S/diagnostic_set_compact_v25_uncapped_20260923/` with renderer `07ea703` and `--type-share-cap` off. Its denominator is 20,139 across rounds 3 and 4, and its pid file, log, and heartbeat are `out/render.pid`, `out/render.log`, and `out/HEARTBEAT.log`.

At 00:54Z the render had processed 2,900 items, passed 883 Tier I items, ran at about 90 per minute, and estimated completion about 04:05Z. At 02:07Z, `out/render.log` ended with `{"processed": 9000, "denominator": 20139, "tier_i_passed": 2509}`, the heartbeat was live at `2026-09-23T02:06:20Z`, and `out/render.pid` held 232293.

After rendering, run `verify`, then `BUILD_RECORD`, then an Astra gate review at `gpt-6-astra` `xhigh`; the lane dispatches that review itself. If the lane dies with the session, the successor dispatches the gate review. A PASS launches full-scale OneThinker and Qwen 9B runs on Orchard from the uncapped set, materialized with the published-split `split_trainer.json` and the pilot recipe.

## 10. Watchers that die with the session

The background loops that die with the session are the collector package guard, render completion and heartbeat watcher, `eval_cells` new-manifest watcher, queue watcher at `agent/scripts/queue_watcher.sh`, and home-low watcher. Re-arm each after the restart.

The collector package guard is pid 854242 on trinity-3-8 and must restart after any landing on `main`. The inventory also marks the collector controllers and keepers listed in section 2 for re-arming with the session.

## 11. Must not touch / user-only queue

Never edit `collector/` on `main` while a collector runs from it. Agents must not write `.coord` leases through fail, claim, or reap; those calls remain with the user or an explicitly authorized executor. Never touch another experimenter's GPU processes or cards.

The user-only deletion queue remains the 23:30Z document's queue. The only addition in this window is the `.git/info/exclude` entry for `.devin/agents/` and `.devin/skills/`; it is an exclusion, not a deletion. No agent deleted anything in this window.

## 12. Paper timeline

The OneThinker pilot's per-type results are expected about 03:45Z, with Qwen later. Full-scale runs follow the render gate. Paper-ready numbers are due 2026-09-24Z, leaving one day to write.

## 13. Not verified when this was written

The Orchard states for jobs 147670, 147711, 147716, 147717, 147718, and held shards 147701-147705 come from dictated facts. This drafting lane did not run a Slurm query because it has no Orchard access.

The collector pids, lease expiries, and terminal counts in section 2 come from dictated facts and were not re-probed. The Mind-transfer lane, the `/data3` mover's entry 4 of 17, and the relocated-mask counts were not re-probed either.

Replicate 3 has no final VSIBench number when this checkpoint was written. The results document records that its lane is completing the final 185 items after the user cleared the stale leases.
