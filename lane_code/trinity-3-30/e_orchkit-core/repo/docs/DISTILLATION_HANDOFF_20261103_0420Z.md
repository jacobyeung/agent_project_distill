# Distillation handoff, 2026-11-02 20:20 PT (04:20Z, 11-03)

Orchestrator agent-project-distill-b5 (Claude session eeef9471) on trinity-0-13. L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`. Peer: main's orchestrator, reached only through durable `distillation_orchestrator_20260918/INBOX_TO_MAIN_ORCH_<UTC>.md` files. Data locations: `/data2/jjyeung/agent_project_data/DATA_MAP.md` (read it before looking for any data; update it when data moves).

## 0. First actions for the next orchestrator
1. **Adopt the live lanes.** On trinity-0-13: `for l in night1102 cp4_build cp4t_build orchard_qwen genvqa evac_finals hc_cpdm obtain_audit roomsize_scale; do lanemsg adopt distill/$l; done`. Then run `lanemsg inbox distill/<lane>` per lane. Never use a bare `inbox` or `tell`.
2. **Re-create the hourly heartbeat cron** (it dies with this session): Gemini use (`L/gemini_subagents/USAGE.json`), one batched AWS squeue, `L/aws_pull_20261029/PULLER_STATUS.json`, and per-lane inboxes. Re-arm `agent/scripts/queue_watcher.sh` in the background.
3. **Before 06:15 PT:** check that night1102 stops all training with USR1 at 06:15 and holds 0 AWS GPUs from 07:00. Main and distillation share one budget. Daytime is 0 GPUs unless the user allows.
4. **Read** `L/fullft_watch/NIGHT1102_PLAN.md` (current plan, admission order, config hashes) and the memory index.

## 1. Goal (user)
Distill SPLIT's perceptual primitives into Qwen3.5-9B so that a trace-trained student scores at least 70 on VSI-500, beats its matched direct-answer control on two seeds, and holds or improves on VSTI-450 and one other spatial benchmark. The student predicts the primitives itself: train on GT SPLIT traces, and add Cambrian-P-style pose and point-depth heads that it calls mid-trace as its own tools. Keep every granted GPU busy, score every run by morning, and finish copying irreplaceable artifacts off AWS (access ends 11-19).

## 2. User rulings today (verbatim where quoted; all in memory)
- **GPUs:**
  - "Can use 200 GPUs now", then "Oh you can use 350 then". This is a shared AWS budget with main, held at 350 until the 06:15 stop because main holds 0.
  - Don't waste GPU-hours; fill spare room with 1-GPU trace-collection jobs; "more orchard gpus and aws gpus if there's space".
- **HC v1 defect:** "Please fix the defect and retrain. In general much better to catch defects early and retrain then. Good call to first train though - better to be doing something than endlessly checking."
- **CP4:** "Yes can run the stage 4 on our base." CP4 is a faithful answer-only Cambrian-P Stage-4 replica on Qwen3.5-9B; CP4T is its trace twin on identical rows. The ScanNet pose walk: "Yes can run the walk."
- **Uniqueness:** "replicating their model is not really a good win ... it's always about uniqueness. You can't just get SOTA ... with like a stronger base model." FT-X is "the least important experiment"; answer-only arms are controls only.
- **G3T:** the user prefers no G3T in the model input (it muddies the trace claim) and will put more GPUs into the no-G3T model. The user doubts G3T is useless and suspects our fusion setup is wrong. The gates stayed at 0.0008–0.037, plausibly limited by learning rate and training length.
- **Frames:** train on variable 32/64/128 frames, not always 128 (cost). Best score first: no separate variable-frame ablation.
- **Traces and data:**
  - Generate canonical traces for every GT-solvable type, even without a SPLIT canonical form, styled like base Qwen.
  - Collect model traces only for hard types.
  - Scale room size, counting and object size.
- **Formats:**
  - Centimetre resolution: cm as integers, metres with 2 decimals, m² with 1 decimal, angles as integers.
  - Frame 1 is the reference for every pose and position (as in Cambrian-P and VGGT), naming the frame where each object is seen. Never the scan's global frame.
- **Data map:** keep the structure of our data in one file, so nobody needs searches to find data. Extract once (for example, ScanNet poses from .sens).
- **Process:** "don't just naively agree with everything I say ... find evidence ... both ways"; raise data oddities yourself. Check resumes for a loss jump in the first 1/2/10 steps.

## 3. Results banked today (all in `L/awstrain_20261027/results/SUMMARY.tsv`; verified against items.json)
- **Eval-time frames (VSI-500, 32 → 64 → 128):**
  - FT-X: 60.86 → 63.71 → 67.66.
  - FT-A: 56.51 → 63.54 → 63.46. The trace gap to FT-X closes at 64 frames (−0.17).
  - CPDM m2800: 61.42 → 63.04 → 63.94.
- **VSTI v3 at 32 / 64 / 128 frames:**
  - FT-X: 68.41 / 64.95 / 61.61.
  - FT-A: 67.11 / 64.93 / 64.69.
  - CPDM: 70.41 / 68.01 / 71.87.

  With pose heads, more frames help camera-motion questions: CPDM leads FT-A by +7.2 at 128 frames, while models without heads degrade.
- **Official 5,130 at 64 and 128 frames, FT-A + FT-X pairs:** 78 shards were running at 20:10 PT. night1102 scores them.
- **Trainer loss** (`L/fullft_review/LOSS_MEASUREMENT.md`): the full-FT loss is segment-normalized, 1.0 × answer mean + 0.5 × trace mean per row, so the answer is not diluted. FT-A-AW was cancelled.
- **HC v1** (r1hc3c_25c98bc9) defect: 45% of head-call rows trained an answer contradicting the trace, and its abs-distance programs were in cm. HC v2 (a)/(b)/(c) and HC v1F were rebuilt on commit 22074194a1b7 with 0 mismatches. The old HC v1 never resumes.
- **Trace frames:**
  - FT-A's main trace part has no coordinates.
  - CP4T traced rows: 40% first-camera frame, 13% image camera, 38% no numbers, 8% the scan's global frame. That 8% is being converted.
- **Resume checks:** clean for HX, PDG-C, FT-A-NTL and FT-X-E2 (step r within ±1.1 sd, lr continuous). FT-X-E2 finished at step 1550.
- **Trace collection (hard types only):**
  - SPLIT-Gemini: about 47.2k attempts, 81% strict.
  - Orchard plus AWS Qwen3.6-27B + GT tools: 5,072 / 5,386 strict (94.2%); blind audits k1–k4 are all clean or minor.
- **Cambrian gap audit and CP4 recipe:** `L/fullft_review/CAMBRIAN_GAP_AUDIT.md`, `CP4_RECIPE_AND_DEVIATIONS.md` and `CP4_FULL_REC_AVAILABILITY.md`.

## 4. Active runs and lanes (Argon lanes are detached processes and survive this session)
| Run / lane | Where | Check | On completion |
|---|---|---|---|
| **night1102**: all AWS submits, watching, step-50/milestone reads, resume checks, official cells, 06:15 stop | 3-30 | `lanemsg inbox distill/night1102`; one squeue | Morning: scored milestones; 0 GPUs from 07:00 |
| HC v1F (r1hc3c1f_3d84e510, 32 GPUs); HC v2 a/b/c (64 GPUs each, mb4; W64 configs); HX (63d5ec88); PDG-C (7d94a1c3); CPDM-E2 (b83e47c1). LGX/LGN 27B paused to make room | code-aws | squeue `a15_cot_ap*`; LAUNCH_LOG "Night 11-02" | Compare HC with HX at matched steps; read derived-step arithmetic |
| **cp4_build**: CP4 replica (VSI-590K, variable frames 32/64/128 at 50/30/20, cut3r pose sampler port, batch token balancing) | 3-30 | inbox; `L/fullft_review/CP4_*.md` | Writes `CP4_BINDING.json`, then `CP4_LAUNCH.sh` (64 GPUs) for Tue 21:30 |
| ScanNet .sens pose walk (in cp4_build): 44 scenes done, one resume at 23:30 PT at 20 reads/s with a 50 ms guard, no loop | 3-30 | cp4_build inbox | If the guard trips, stop for good and use dense poses |
| **cp4t_build**: CP4T-N (current traces; convert the global-frame 8%; name seen-frames), CP4T-Q (Qwen style) second, fold in Gemini/Qwen traces for hard types | 0-13 | inbox; `CP4T_GATES.md` | Binds to `CP4_BINDING.json`, then `CP4T_LAUNCH.sh` |
| **hc_cpdm**: head-call pair on CPDM with no G3T (HC-C1F, HC-C2A, HX-C) | 0-13 | inbox; `HCCPDM_GATES.md` | Launch-ready for Tue night; b5 picks HC-C1F vs HC-C2A from tonight's HC results |
| **roomsize_scale**: correct-convention room size, counting and object size from GT, canonical Qwen-style traces, new datasets | 0-13 | inbox; `ROOMSIZE_SCALE.md` | Row file for the next build |
| **obtain_audit**: share of trace facts unobtainable from the student's frames, per type | 0-13 | inbox; `OBTAINABILITY_AUDIT.md` | Recommendation per type |
| **orchard_qwen**: Qwen trace collection on Orchard (8 GPUs) and AWS 1-GPU fill (stops 05:55 PT); watches the Gemini collector | 0-13 | inbox; `/scratch/jjyeung/argon_lanes/distill_orchard_qwen/STATUS.md` | Daily yield; audits every 1,000 |
| **evac_finals**: puller (n3 to /data3, then k03, t1, e6) | 3-30, PID 3506940 | `L/aws_pull_20261029/PULLER_STATUS.json` | Optional user cleanup command in its 13:00 PT note |
| genvqa: general-VQA forgetting cells | 3-30 | inbox | Scores with tonight's evals |
| SPLIT-Gemini collector (tmux sgv2_collector, sg_offload_loop, sg_cache_evict) | 0-13 | tail `scale_v2_bank.log` | The cache evictor's frontier fix was applied at 16:02 PT |

## 5. Open items for the user
- None blocking. Offered but not decided: test GX-P and QP (about 350 GPU-h) before shelving G3T. Answer-RL stage after SFT (the Video-R1 pattern), not started.

## 6. Do not redo
- Never resume HC v1 (25c98bc9) or launch the 05:43 HC v2 configs.
- FT-A-AW is cancelled: the loss is already segment-normalized. Neither FT-X64 nor FT-X-LFP launches.
- Don't train from released Cambrian checkpoints. Don't tar or rsync onto `ap/59845bf9/d`, which is a symlink.

## 7. Footguns learned today
- An Argon lane that has sent its final report never receives later messages (pending forever). Check `run/meta.json` and launch a successor.
- The memory probe stacks 8 copies of the longest row. Balance tokens within the global batch instead of adding GPUs.
- Pending jobs count toward the cap. The 1-GPU trace fill keeps utilization up.
- Lane reports overclaim: a nonexistent /fsx path, "419/419" audits, uncentred CIs. Verify against files before relaying. Don't generalize from 2 sampled rows.

## 8. Survives vs dies
- **Survives:** all Argon lanes above, AWS jobs, the puller, the Gemini collector and its loops, Orchard jobs.
- **Dies with this session:** the hourly heartbeat cron (f1c4d56a), the 21:37 PT check (041c3df2), the queue watcher (btb35i2jj). Re-create them as in §0.
