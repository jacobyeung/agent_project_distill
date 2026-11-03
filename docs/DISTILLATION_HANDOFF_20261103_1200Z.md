# Distillation handoff, 2026-11-03 04:00 PT (12:00Z)

Orchestrator agent-project-distill-0e (Claude session 9dfa7b58) on trinity-0-13. L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`. Data map: `/data2/jjyeung/agent_project_data/DATA_MAP.md`. Memory index: `~/.claude/projects/-home-jjyeung-agent-project-distill/memory/MEMORY.md` (read the READ FIRST entries).

## 0. First actions for the next orchestrator
1. Adopt the live lanes: `lanemsg adopt distill/evac_finals distill/genvqa`. night1102 ends tonight. cp4_build and cp4t_build are retired.
2. The Claude subagents of session 0e (cp4_build2, cp4t_build2, pseudogt, aws_inodes) end with that session. Continue their work from their files: `/scratch/jjyeung/cp4_build2/HANDOFF_2000.md` (CP4T build), `/scratch/jjyeung/cp4t_build2/out/` (final rows), `/scratch/jjyeung/pseudogt/PLAN.md`, `/scratch/jjyeung/aws_inodes/INVENTORY.md` with `L/aws_inodes_20261103/`.
3. Re-create the crons, which die with the session: an hourly heartbeat, and the 11-04 11:07 PT CP4T launch check after the cot window ends.
4. Before any training launch, show the user the pre-launch check (memory `prelaunch-thinking-checklist`).
5. **AWS is down until the user says it is back (USER 11-03 ~14:30 PT; both tunnels died ~13:18 PT).** Take no AWS action until then. Afterwards, in order (memory `aws-down-until-user-says`):
   1. Run cp4_build4 from `/scratch/jjyeung/cp4_build3/HANDOFF.md`. The 11-03 Slurm migration emptied the queue, which had held 7 running CPU jobs, 13 BeginTime jobs and 8663875. So check every job in `L/aws_reserve/AWS_JOB_LEDGER.jsonl` against its outputs, resubmit the unfinished ones under new opaque names, and run the CP4T CPU prep. Launch CP4T once cot-faithfulness has released.
   2. Submit the m06 and e7c packs (`/scratch/jjyeung/aws_pull_triage/pack/u_submit.py`, plan in `PULL_PLAN.md` there) ahead of aws_inodes wave 2.
   3. Submit the ARKit mesh job.
   - The gcs_stage watcher (tmux `gcsstage` on 0-13) uploads e7a and k06 to GCS by itself when port 42224 returns.

## 1. Goal and standing rules (user, 11-02/03; details in memory)
- SOTA spatial VQA with traces, plus a spatial foundation model for VLA distillation. Standing loop: per-category diagnosis, fix data or traces, train, read.
- No control runs. No answer-only rows (CP4T is traced-only). Think before every launch, with the written check shown to the user.
- Trace format (memory `centroid-named-frame-convention`):
  - one-sentence plan;
  - views named by the processor's `<t seconds>` pair label, from ground-truth fps (ScanNet 30, ScanNet++ 60, ARKit 10, ADT 30; fps 1 with frame ordinals when real timing is unknown);
  - gravity-aligned camera-centred frame;
  - pose step phrased as the other camera seen from the reference view, with right/forward/clockwise positive;
  - written-out math (dot/cross, gaps and norm, shoelace);
  - metres internally plus one conversion line;
  - distance questions get a box variant and a centroid variant;
  - one camera per pair label;
  - no pixel counts;
  - 100% reproducibility and GT-match gates.
- GPUs:
  - the user's 18 MB/s weighted IO cap;
  - weekdays by day distillation holds at most 32 AWS GPUs, plus 16 for data jobs;
  - spare GPUs go to data generation;
  - pack 1-GPU jobs one job per node;
  - eval output cap 8,192 with one 16,384 retry; paper rows keep 16,384 with a 32,768 retry.
- **cot-faithfulness has 100% AWS GPU priority through 11-04 11:00 PT** (user ruling relayed in code-aws `peer_inbox/TO_AGENT_PROJECT.md`). Distillation submits NO AWS GPU jobs until a release; this was acknowledged in FROM_AGENT_PROJECT.md. AWS maintenance is 07:00-20:00 PT 11-03 and takes the CPU nodes too.
- AWS inodes: below 20M is the target. Clean up regularly. The one vetted prune command is allowlisted in rm_guard (agent_project commits 753b0276f, d36bc47d6, 5024353b8):
  `bash L/aws_inodes_20261103/aws_prune_run.sh MANIFEST_<date>[a-z].tsv [--dry-run]`
  The user still has to run `python3 mkman.py install` in that lane dir to upload the fixed px.sh; until then the wrapper refuses on a hash mismatch.
- Agent context: rotate near ~300K tokens with a written handoff.

## 2. Results banked 11-02/03 (L/awstrain_20261027/results/SUMMARY.tsv)
- Official VSI 5,130 at 32/64/128 frames:
  - FT-X 64.14 / 65.93 / 65.48;
  - FT-A 61.38 / 62.46 / 62.81;
  - CPDM 63.79 / 63.36 / 63.19.
- VSTI at 128 frames: CPDM 71.87 vs FT-X 61.61. The pose heads help camera motion only; traces didn't help with frames.
- Per-category diagnosis: `L/fullft_review/CATEGORY_DIAGNOSIS_20261103.md`.
  - Gaps to Cambrian-P: rel distance -16.6, room size -15.9, rel direction -8.6, appearance order -7.9.
  - Causes: starved categories, answer-restating traces, no ARKitScenes, cm/m units.
- 3D-box probe (1,000 scenes): base Qwen centre error 0.37 m, size 26%. FT-X lost box output entirely. FT-A and CPDM got worse in x/y.
- Weight-space pilot W1-W4: no-go. HC v2 a/b/c at m400: VSI 52-54, VSTI 55-62, below CPDM.

## 3. CP4T (the flagship next run)
- Qwen3.5-9B full fine-tune from base on Cambrian-P Stage-4 recipe: 32/64/128 frames, pose/depth heads with pose-only rows at beta = 1, token-budget batching on 32 GPUs (trainer b2c2f8a0).
- Data, all traced:
  - cp4t_build2 final files in `/scratch/jjyeung/cp4t_build2/out/*_final.jsonl.gz`, 416,752 rows (ScanNet/ScanNet++ + VSTI + route 181,750; ARKit 42,814; ADT 37,909; appearance order 38,369; T_base benchmark types 115,910);
  - roomsize_scale2 215,057 rows (room size 27,232; counting 103,285; size 84,540);
  - pseudo-GT left/right single images 20,469 (2-frame clips, a trainer change in progress).
- Caps: rel_direction ≤50K; abs_distance ≤35K; counting ≤40K; size ≤35K; rel_distance, appearance order, room size and route all; non-benchmark ≤15%.
- Estimate: ~2,500-3,000 steps, ~520-700 GPU-h on 32 GPUs, milestones every 100 steps.
- Status: CPU prep in progress. **USER pre-approved the CP4T launch (11-03 ~04:15 PT: "You can launch the CP4T training. Don't wait for me").** Launch on 32 GPUs as soon as the final arm passes its dry run AND cot-faithfulness releases GPUs (a release post, or 11-04 11:00 PT). Post the filled pre-launch check in the chat at launch.
- **CURRENT: /scratch/jjyeung/cp4_build3/HANDOFF.md** (cp4_build3, 05:00 PT) supersedes cp4_build2's. The launch arm is T4B2C7N1 = F1 + G2 + F4 + F5 + R3 (spec 4496c028, run r1n1_b2c2f8a0, caps_n1.json); submit with /scratch/jjyeung/cp4_build3/SUBMIT_CP4T.sh. Mix: about 365K question rows + about 346K head-only rows ≈ 2,780 steps, ≈ 580-640 GPU-h on 32 GPUs. ADT and pgt are out of this launch. Steps from 20:00 PT are in HANDOFF.md §successor steps.
- cp4_build2 finished (04:15 PT). State: /scratch/jjyeung/cp4_build2/STATUS.md and HANDOFF_2000.md. SUBMIT script: L/fullft_review/SUBMIT_CP4T.sh.
  - Trainer b2c2f8a077c5 is installed on AWS; the 2-frame image-clip commit 3b55cfbd is NOT installed yet.
  - The rehearsal arm T4B2C7E1 passed admission.
  - A successor (cp4_build3) builds the capped final arm after 20:00 PT.
- Evaluator: commit 174a50d5 is BLOCKED by review. Its VSTI v3 media-attestation port skips the frame-receipt and media-pin checks. A Codex fix is running (brief and result in /scratch/jjyeung/cp4_build2/codex/EVAL_FIX_*); it needs one independent review before use. The retry, the fps override and VSI-500 scoring passed review.

## 4. Lanes and agents
| Owner | What | Next |
|---|---|---|
| roomsize_scale3 (Argon, finished) | Hypersim adapter (v3 rows), ARKit mesh AWS spec | submit the ARKit job when AWS is back |
| orchard_qwen5 (Claude Opus subagent of session 0e) | estimated-tool SPLIT left/right production drain on 0-13 (tmux -L oq3; disk guard at 115 GB). Only LR is admitted; AD, CC, CR, Count and RC failed the E3 gates (`/scratch/jjyeung/orchard_qwen4/HANDOFF.md`) | convert rows, DATA_MAP counts, stop the 0-13 SAM 3 servers |
| SPLIT-Gemini v2 collector (unattended; tmux -L v3 `sgv2_collector`, evictor and offload loops) | refilled pool of 67,739 questions (~85 h of key; tiers in `bank_v2/data/non_canonical_priority_qids.json`); archive fix references /data2 media in place, CONTRACT 14efdf3e | check it in the heartbeat; `/scratch/jjyeung/sgv2_refill/HANDOFF.md` |
| procthor_trace (Claude Opus subagent of session 0e) | ProcTHOR/SIMS-V canonical traces: phase 1 traced 5,808 VSI-590K turns, phase 2 adds new questions and renders for room size, counting and appearance order, balanced to VSI-Bench | final rows plus review by 11-05 morning PT, for CP4T v2 |
| gcs_stage watcher (tmux `gcsstage`, 0-13) | e7a and k06 AWS→GCS upload | fires when the AWS tunnel returns |
| evac_finals (Argon, 3-30; not running) | the Trinity puller is stopped: everything queued is already in GCS (`/scratch/jjyeung/aws_pull_triage/PULL_PLAN.md`) | re-enable for new packs only |
| hc_cpdm (Argon; stopped) | HC-NEW on CP4T rows; gates in `L/fullft_review/HCNEW_GATES.md`; state in /scratch/jjyeung/argon_lanes/distill_hc_cpdm/work/. HC v1F m1000 trails CPDM m2800 (VSI-500 57.72 vs 61.42, VSTI-450 64.52 vs 70.41; `/scratch/jjyeung/orchard_qwen3/hc_eval/RESULT.md`) | decide on a successor after CP4T launches, given HC v1F's deficit |
| genvqa | general-VQA forgetting cells (method models only) | CPDM, then CP4T |

## 5. Open user questions
- None. USER 11-03: the main project is done and its orchestrator is gone, so distillation is the only orchestrator and manages main's leftover AWS trees, under the same safety rules.
- The AWS inode cleanup is handled by successor aws_inodes2, a Claude subagent of session 0e. If that session ends, continue from /scratch/jjyeung/aws_inodes/INVENTORY.md and L/aws_inodes_20261103/.
- The evaluator fix is being finished by a Claude subagent; its result and review land in /scratch/jjyeung/cp4_build2/codex/EVAL_FIX_RESULT.md.

## 5b. Open data issues for the next round
- **ADT frame alignment.** The release mp4 frame count does not equal the aria_trajectory row count (e.g. 3,526 mp4 frames at 30 fps vs 2,880 traj rows), so "video frame i = traj row i" is false. The new ADT rows (37,909) are out of CP4T v1 and need a per-sequence timestamp alignment. Checked 11-03 (/tmp scratch adt_align_check; Argon run /scratch/jjyeung/argon_runs/adt_align_20261103/result.md): the old RG2DS_T rows use only the trajectory's row-0 camera pose ("camera at the first frame (0.0 s)") and object poses picked by index, with no per-frame poses. So the drift (10-28 s by the end of a video) does not affect them. The residual risk is an unverified start offset between video frame 0 and trajectory row 0. Any per-frame-pose ADT rows need timestamp alignment.
- **General-VQA forgetting.** CPDM vs base is -4.6 on MMStar and -7.9 on Video-MME non-capped items (L/fullft_review/GENVQA_CELL.md). Add about 10% general video/image QA replay in CP4T v2.
- **Hypersim rows for CP4T v2.** 37,721 strict single-image rows are ready, in `/scratch/jjyeung/argon_lanes/distill_roomsize_scale3/work/HYPERSIM_ROWS_v3.jsonl.gz`. They have floor-plane directions (VSI-590K's released Hypersim direction labels use the image plane), real-scan prior band [p1/1.5, 1.5×p99], and pass the Claude review fixes D1–D5. The converter must write `media_path` twice per row for trainer 3b55cfbd. CP4T v1 holds no Hypersim rows; its direction rows were audited as floor-plane (`/scratch/jjyeung/cp4_build3/DIRECTION_PLANE_AUDIT.md`).
- **ARKit mesh rows for CP4T v2.** The roomsize_scale3 spec (`work/ARKIT_AWS_JOB_SPEC.md`, `work/ARKIT_LAUNCH_AFTER_MAINT.md`) fetches 4,107 ARKit meshes on AWS cpu-big and generates ~150K rows, including room size. The 20:05 PT cron submits it after maintenance.
- **SPLIT-Gemini collector disk on 0-13.** The staging floor and evictor target are read from override files (`distill_split_gemini_v2/SCRATCH_FLOOR_GB` = 125, `distill_split_gemini_fix/EVICT_TARGET_GB` = 126). The audit blob store (`argon_work/split_gemini_pilot/archive_blobs`) now grows more slowly, because /data2 media is referenced in place and blobs are written sparse. Two cleanup commands wait for the user to run them: `dedup_retired_staging.py --apply` (26 GB of approved duplicates) and `apply_unreferenced_blobs.py --apply` (71 GB, needs approval), both in `distill_split_gemini_fix/` under Python 3.12 (`/scratch/jjyeung/envs/argon_proxy_v1/bin/python3`). On trinity-3-3, `bash /scratch/jjyeung/free_space/FREE_3_3.sh` (approved, 112 GB) also waits for the user.
- **ProcTHOR rows for CP4T v2.** Lane procthor_trace (`/scratch/jjyeung/procthor_trace/`): exact simulator GT, no AWS, balanced to VSI-Bench.
- **Estimated-tool LR rows** (`/scratch/jjyeung/orchard_qwen3/prod/lr_v*/rows_e2v1_*.jsonl.gz`): admitted single-image left/right traces; DATA_MAP gets the final counts.
- **Pseudo-GT left/right rows** (20,469) need trainer 3b55cfbd (2-frame clips), which forces rebuilding the arms. Next round.
- **No CPU nodes outside the AWS reservation exist** (cpu-035/038 and cpu-big-044 are not in sinfo).

## 6. Footguns found tonight
- Lane reports misquote numbers; read SUMMARY.tsv.
- A Claude lane can thrash its context and die silently (cp4_build died 20:39 PT).
- Generators had defects only real examples revealed: 0.02 m placeholder boxes, height on the wrong axis, yaw-blind distances, window indices past the recording end, label synonyms, counterclockwise angles, missing option lists, mixed cameras within one pair label.
- Jobs whose time limit crosses a reservation sit in BadConstraints.
- rm_guard matches text, so avoid naming archive or prune tools inside Bash commands; use Read/Write.
