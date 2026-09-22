# Distillation lane handoff, written 2026-09-22 23:30Z

## Command

This checkpoint supersedes `docs/DISTILLATION_HANDOFF_20260922_2100Z.md` (commit `573c08d`) for everything since 2026-09-22 21:00Z. The 2100Z document remains the source for the full incident narrative through 21:00Z, including the `/home` and `/data2` quota exhaustions, the authentication outage, the Orchard capacity table, and the decode-diagnosis report. This checkpoint covers the storage census and relocations, the GT-measurement gate reviews and split correction, the recovered trainer and collector state, the Orchard both-sides fix and its production blockers, and the completed VSTIBench and VSIBench results through 23:15Z.

`P` denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918`.

## 1. Incident and recovery state

The 27B and 9B rep2 trainers remain in different recovery states. Qwen3.6-27B arm C died at step 78/96 when `/data2` filled at 2026-09-22T19:31:22Z; all three ranks reported stale or future-dated coordination heartbeats after the renewer's write failed under `>/dev/null 2>&1 || true`. The failure was not a vnice-terminator kill, lease expiry, NCCL/CUDA/OOM, trainer-internal ENOSPC, or node loss. Its `step_75` checkpoint, taken at 19:06Z, was already synced to `/data3/jjyeung/ddp_qwen36_27b_armc_27b_trinity_20260922T1110Z_snapshots` (8.4 GiB on an export with 6.4 TB free). The resume relaunched at 20:47:11Z, began training at 20:47:34Z on trinity-0-13 cards 0, 2, and 3 with world 3 FSDP, and retained its config, seed, and microbatch cap. Its leases run through `2026-09-23T04:47:12Z`; the recorded PIDs are resume script 916636, torchrun 916796, and ranks 916828/916829/916830. No source read for this checkpoint confirms its actual resumed step progress. A still-live day-log note says step 96 was reached at 23:01Z with finalization pending, but a successor must directly re-verify it.

Qwen3.5-9B arm C rep2 remains blocked on a user-only lease host-pin move. Its trinity-0-18 launch was stood down because another user occupied all eight cards, and its 16.01 GB run directory (4,988 files, excluding `ABORT_RESUME1`) plus 19.33 GB node-local HF cache were copied at 116 MB/s to trinity-1-18, where `step_250/checkpoint.json` is present. trinity-0-18 was re-armed at 21:05:04Z with launcher pid 337586 and abort lever `ABORT_RESUME2`. The staged `relocate_leases_1_18.sh` must move the six rank leases with the documented `coord.py fail` then `coord.py claim` recipe before trinity-1-18 can bind; the permission system denies that shared `.coord` write. The documented order remains: stand down trinity-0-18 through `ABORT_RESUME2`, run `relocate_leases_1_18.sh` on trinity-1-18, then launch `qwen_rep2_resume_run_1_18.sh`.

## 2. Storage and relocation state

The 20:52Z census at `/data3/jjyeung/claude_data2_census_20260922T2055Z/CENSUS.md` measured 1,519.42 GiB across 101 distinct paths at 22:35Z, while `/data2/jjyeung` reported 9.9 TB used and 153 GiB free. Its central finding is a long tail of about 1,147 `agent_project_data` run roots rather than one visible giant: a uniform sample of 35 children found 31 completed directories totaling 64.31 GiB and 4 timeouts, which establishes a 2,107 GiB lower bound outside the distillation root. `/data2/jjyeung` is its own ZFS dataset with no nested dataset; NFS4 snapshot enumeration is unreliable, so it cannot rule snapshots out completely.

The later sweep found `/data2/jjyeung/agent_project_data/dense_backbones` at 558.30 GiB and `req209_point4d_20260910` at 149.40 GiB. Neither has a live lease match, and both should move, not delete, to `/data3/jjyeung/TO_DELETE_20260922/...` while mirroring the original absolute path. `r935_gt_dense_20260815` (45.83 GiB) and `r1298_req229_common_gt` (about 93 GiB estimated) remain on hold because their names appear in live lease names. The census also flags the 61.01 GiB Qwen3.5-27B hub entry for verify-first-then-move: it has no repository reference but was touched at `2026-09-21T19:21Z`, so the run must first be confirmed to use Qwen3.6-27B.

The relocation lane `/data3/jjyeung/claude_data2_free_20260922T2015Z/STEP_1.md` moved a 1.19 GiB audit-batch fixture to the deletion mirror and about 33.5 GiB of smaller `video_hallucination_data` children behind symlinks. `phyground`, `videophy2`, `physion-eval`, `sources`, and the small `models` and `manifests` trees are present at the destination and readable through their original symlinked paths from trinity-3-8. `/data2/jjyeung` rose from 47 MiB free at 20:20Z to 154 GiB at 22:02Z, mostly through the user's parallel `gt_masks` relocation. `datasets/mmbench2` (107G) and `datasets/worldbench` (82G) remain on `/data2`; their stopped partial copies, 9.9G and 0.9G respectively, remain under `/data3/jjyeung/video_hallucination_data/...` for a resumed subdirectory-at-a-time mover. About 189 GB remains there.

The 2026-09-22 22:45Z ruling permits unused dense-prediction banks to move from trinity to `/lab_data/tarrlab/jacoby/agent_project/dense_backbones` on `mind.cs.cmu.edu`, bank by bank with rsync without `--delete`, a checksum dry run, and then a move of the trinity source into the `/data3` mirror. Mind and trinity do not share a filesystem. The first lane, `/data3/jjyeung/claude_mind_backbones_20260922T2245Z/`, has no confirmed-complete report.

## 3. Results — OneThinker-8B arm C variants

The answer-only control matches or exceeds published arm C on both completed benchmarks. Both evaluation drivers hit the same Bash 4.4 `local`-declaration bug in `lib_evalprep.sh:66` after VSTIBench generation finished; each driver fixed its own copy by splitting the declaration, left `lib/` untouched, and scored the original generations unchanged. The protocol used an instructed prompt, a 4,096-token budget, 32 frames, greedy decoding, seed 17, RGB-only input, tool-free evaluation, harness `58794b8`, and lenient scoring as primary with strict scoring secondary.

**VSTIBench (450 items), all four cells complete:**

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict->lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 45.40 | 40.16 | 55 -> 14 | 1 | 1 | 133 | 450/450 |
| arm C (published) | 43.59 | 43.59 | 1 -> 1 | 1 | 1 | 306 | 450/450 |
| replicate 3 | 38.27 | 38.27 | 1 -> 1 | 1 | 1 | 284 | 450/450 |
| answer-only | 43.35 | 43.35 | 0 -> 0 | 0 | 0 | 2 | 450/450 |

Per-type strict macro is 53.42 for base, 50.29 for published arm C, 46.44 for replicate 3, and 52.82 for answer-only. No student beats base under lenient parsing, but answer-only is the best student and nearly ties published arm C with a median of 2 tokens rather than 306; replicate 3 falls below both. Every student sharply improves format reliability over base.

**VSIBench (500 items): base, arm C published, and answer-only complete; replicate 3 blocked at 315/500 (not scored, excluded from the table):**

| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict->lenient) | cap-hit | cap w/o answer | median gen tokens | terminal |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 39.19 | 31.47 | 93 -> 9 | 0 | 0 | 217 | 500/500 |
| arm C (published) | 42.35 | 42.35 | 4 -> 4 | 4 | 4 | 364 | 500/500 |
| replicate 3 | - | - | - | - | - | - | 315/500 (blocked) |
| answer-only | 48.76 | 48.76 | 0 -> 0 | 0 | 0 | 2 | 500/500 |

Per-type strict macro is 31.44 for base, 41.48 for published arm C, and 48.34 for answer-only. Answer-only is the best completed cell at 48.76 lenient, 6.41 above published arm C and 9.57 above base. Across the two benchmarks, it is 0.24 lenient below published arm C on VSTIBench and 6.41 above it on VSIBench, whereas replicate 3 misses arm C's VSTIBench result by 5.32 points. These results do not support the compact reasoning trace as the source of arm C's gains; future paper claims must carry the answer-only column and a replicate.

Replicate 3's VSIBench block is not a space failure. Two stale `.coord/LEASES/student_eval__distilled_onethinker_vsi500__s17__2d6cb205__shard_{0,1}_of_4.lock` directories record dead pids 2012001 and 2012002 with heartbeats frozen at 20:53:25Z. The required two scoped `coord.py fail <work_id> --error "<reason>"` calls are denied as shared-resource writes; once an authorized executor clears them, `direct_shards_pass2_inner.sh` can complete the remaining 185 items and `driver_rep3_fixed.sh` can score the cell.

## 4. Training, datasets, and pending mixes

GT-measurement v2 completed after an ENOSPC resume. The five-scene resume and `assemble_v2_full.py` in `claude_gtmeasure_mix2_20260922T1855Z/` produced `student_diagnostic_pilot_20260918/gtmeasure_v2_20260922_full` with 8,790 rows: 7,770 train, 1,020 held-out, and 13 deferred scenes with zero rows. Set A, `mix_armc_gtm2_r025_20260922`, contains 4,069 train rows and 1,399 held-out at ratio 0.25. Set B, `mix_v25_gtm2_r050_20260922`, contains 4,260 train rows and 1,746 held-out at ratio 0.50 exactly. Both passed ten self-checks.

The first Astra gate review passed the v2 rows, all 306-checkpoint assembly fidelity, and Set B, but failed Set A on the unsupported derivations for `vsi590k_094600` and `vsi590k_080725`. The pilot therefore trains on Set B only, with the Orchard OneThinker-8B arm C recipe for 402 steps. Set B's materialized trainer layout has 6,006 rows, candidate index sha `c3c3d6df...`, and targets tree sha `64dee442...`; Set A's corresponding layout has 5,468 rows but does not train.

The second Astra review blocked that Set B layout as built because the trainer's own split derivation disagrees with published `split.json` on 1,480 rows, including 870 GT-measurement and 610 compact rows that would move from published held-out to trainer train, while 425 published-train qids would move to trainer held-out. Row-to-file mapping, field mapping, and benchmark/scene identity passed. The existing `prepare-protocol --inherit-split` accepts `provisional-whole-scene-split-v1`, not the mixer's `gtmeasure-inherited-scene-split-v1`; the mixer re-emitted accepted-schema `split_trainer.json` files for Set B (sha `99d6a82b...`) and Set A (sha `9e41230d...`). Replay reproduces the published train/held-out sides exactly with `hashed_group_count 0`, but no independent gate review has checked this corrected path. The recorded plan is the full Set B index with `--inherit-split split_trainer.json`; `_trainonly` remains the 4,260-row fallback.

The type-cap remediation `ff61272` failed Astra review on a missing per-extension-slice cap check and an inherited default-artifact byte-identity defect in `dataset_builder.py`. Its independent test rerun found 516 tests, 0 failures, 1 pre-existing environmental error, 5 skipped, and zero `output_outside_data2` deferrals. The round-3 remediation at `claude_typecap_round3_20260922T2130Z/` has not received independent review.

## 5. Orchard and review state

Commit `12e477b` on `orchard-eval-containment-bothsides-20260922` resolves the production mismatch between containment's staged `PREPARED` path and media attestation's recorded `/data2` path. It resolves `path.parent` once for the package-pin loop and each `frame_receipt` check without rewriting pin strings or changing reads. Its new test uses production's recorded `/data2` manifest shape, and reverting `contracts.py` alone recreates the failure. The commit passed 81 tests with no failures and received two independent Astra PASS reviews with no blocking findings; `12e477b` is the deploy target for every Orchard evaluation.

STEP_14 deployed `12e477b` as `orchard_trainer_12e477b` and `deployment_12e477b` with 33 files. Both the 9B-replicate and 27B-base evaluation cells reached `CPU_READY / 0 failures`; the 27B base control produced 96 scored items at about 113 items/h per shard, with first items at 22:11Z. Four blockers remain. First, `orchard_admission.py:46` is not array-safe: two final-wave shards, `147630_3` and `147636_3`, died when its `scontrol` regex selected a sibling record, and the 27B wave stalled at 3 of 16 shards. This admission defect is neither fixed nor independently reviewed. Second, the 9B replicate needs a completed Qwen3.5-9B base evaluation cell; its training id is not a valid `--base-run` path, and none exists. Third, job 147599 failed at 21:56Z during preparation, before any step, with the FSDP probe OOM at `max_microbatch_size: 8` on world 4; Orchard has no live 27B training run and needs a smaller frozen microbatch cap. Fourth, GT-measurement preparation blocked on the rejected split schema and produced no `training.json`; it awaits `_trainonly` or the accepted `split_trainer.json` path.

Set B's staged layout passed per-row verification on Orchard: all 6,006 rows and 12,012 targets re-hashed with zero bad row or target hashes, and no new frames were required. The recorded `targets_tree_sha256` `64dee442...` did not reproduce under four natural tree-hash encodings because the mixer method is undocumented; the reproduced per-row digests are the stronger check. The 27B base used `--thinking off`, whereas the distilled-cell launcher defaults to `--thinking pinned`; this pairing remains a decoding-template asymmetry warning.

## 6. Collector and package-guard state

Both collectors were relaunched from `/data3/jjyeung/claude_collector_recover_20260922T2050Z/` at 16 workers. For r1313 on trinity-3-8, lease keeper pid 213556 remained alive and expires about `2026-09-23T04:05Z`; supervisor pid 767417 began its terminals rescan at 20:54:33Z. Its stale `WATCHDOG_HEALTH.json` remains at 19:57:55Z by design until the first post-validation tick. No source read confirms whether its controller launched or produced a first finalization after 22:35Z.

For r1317 on trinity-1-13, external keeper pid 1809062 renewed the lease at 20:55:18Z through about `2026-09-23T16:55Z`, and controller pid 1811177 relaunched at 20:59:43Z from epoch checkout `5245587fbf56942b1759b5db1d34f3b589f9bbd7` with `--workers 16`. The gate passed at 21:18:24Z: workers reached 16/16 by 21:09:18Z and three finalizations moved terminals from 3,157 to 3,160 and attempts from 3,176 to 3,179. This is the last confirmed r1317 read.

The package guard exited as designed when `main` fast-forwarded to `573c08d`; `claude_guard_restart_20260922T2115Z/` was dispatched. No source read confirms a replacement pid or that the guard is alive. A successor must verify it before another commit or fast-forward on `main`, and restart it after every such change.

## 7. Rulings and executor corrections in force

Codex Luna is not the default for coding or gate reviews. The 21:10Z correction requires `gpt-6-astra` at xhigh for gate reviews and design, `gpt-5.6-terra` for mechanical drafting, and `gpt-5.6-sol` for hard self-contained work; Devin remains on Astra max, with Opus 5.5 only as fallback after a Codex or Devin failure. The 21:12Z clarification permits `gpt-5.6-luna` only for ssh and cluster-operations lanes. The two Luna containment reviews are informational-only; the accepted Astra reviews govern.

The standing no-deletion rule remains in force. Cold banks move by verified copy and `mv` to a `/data3` mirror, not agent deletion. The `flame` partition is closed to `mt01` without a QoS grant; `preempt_qos` is approved for the GT pilot as `PARTITION=preempt QOS=preempt_qos WORLD_SIZE=8` if the advanced cards are needed elsewhere.

## 8. Watchers a successor must re-arm or check

First confirm whether r1313 supervisor pid 767417 completed its rescan, launched a controller, and produced a post-22:35Z finalization. Then check r1317 directly beyond its last confirmed 3,160 terminals and 3,179 attempts; its controller and external keeper are pids 1811177 and 1809062. Check the 27B resume's actual steps before its `2026-09-23T04:47:12Z` lease expiry, and keep the 9B rep2 blocked until an authorized actor performs the host-pin move in the documented order.

Confirm the restarted collector package guard is alive. Confirm whether Set B has been submitted with `--inherit-split split_trainer.json` and whether an independent gate review has approved that path. The array-wave admission bug, the absent 9B base evaluation cell, and the smaller-cap 27B relaunch remain open. Replicate 3 remains at 315/500 until an authorized actor clears its two stale `.coord` locks. Check the round-3 type-cap remediation's independent review, the paused `mmbench2` and `worldbench` moves, and the incomplete Mind transfer lane.

## 9. Must not touch / user-only deletion queue

Never edit `collector/` on `main` while the collector runs from it. Never touch another experimenter's GPU processes or cards; trinity-0-13 cards 4, 5, and 6 remain off-limits, as do other users' processes encountered during node sharing. Agents must not attempt `.coord` lease-fail, claim, or reap writes: the 9B rep2 host-pin move and replicate 3's two lock-clear calls require the user or an explicitly authorized executor. Nothing was deleted by an agent in this window.

The new user-only deletion entries are recursive removal of `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/media_archives` (160.74 GiB), `/data2/jjyeung/agent_project_clones` (3.22 GiB), and `/data2/jjyeung/transfers` (3.74 GiB), plus eventual `rm -rf /data3/jjyeung/TO_DELETE_20260922` once the user has finished with all mirrored data. The latter currently contains only the 1.19 GiB audit-batch fixture and will grow as `dense_backbones` and `req209_point4d_20260910` move. A ruling remains required before moving `r935_gt_dense_20260815` or `r1298_req229_common_gt`.

## 10. Not verified when this was written

No source read confirms the r1313 controller outcome or first finalization after 22:35Z, the actual 27B resume step progress, or the restarted collector-guard pid and liveness. The corrected Set B split-inherit path has replay confirmation but no independent gate review or confirmed Orchard submission. The array-safe admission fix, Qwen3.5-9B base evaluation cell, 27B smaller-cap relaunch, type-cap round-3 review, Mind transfer completion, and the paused `mmbench2` and `worldbench` moves remain unverified or open. Replicate 3's final VSIBench result remains unavailable because its cell is blocked at 315/500.
