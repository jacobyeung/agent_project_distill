# Lane: w1_split_breakthroughs (Read-Only Recon)

## Goal
Audit the major breakthroughs achieved in the **SPLIT project** (`/home/jjyeung/agent_project`, `/home/jjyeung/cvpr_overleaf`, and recent Nov 19–28 design records) over the past few weeks, and extract EVERY concrete architectural, representational, algorithmic, and trace/data lesson that can inspire our fine-tuned spatial student & VLA backbone!

## Hard Cluster & Safety Rules
- READ-ONLY research. Do NOT edit repo code, do NOT delete anything, do NOT run `git` commands, do NOT run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`, bare `rg` over `/home` or `/data*`). Use exact paths and bounded reads only.

## Exact Files / Places to Inspect
1. `/home/jjyeung/cvpr_overleaf/` — list top-level `.tex` files and `sections/` (`ls -1 /home/jjyeung/cvpr_overleaf /home/jjyeung/cvpr_overleaf/sections 2>/dev/null`), then read the abstract, introduction, method, key results/tables, and analysis/ablation sections from the `.tex` files!
2. `/data2/jjyeung/agent_project_data/distill_design/MASTER_SPLIT_IMPROVEMENT_PLAN_20261127.md` (read carefully — Nov 27 master plan!).
3. Recent Nov 22–28 SPLIT findings in `/data2/jjyeung/agent_project_data/distill_design/`:
   - `X1_PERC_VS_REASON_GRID_20261126.md` (GT text LOW 93.7 vs video HIGH 61.6; blind Qwen3-8B +13.2 over Pro video!)
   - `GEMINI_PAIRED_THOUGHTS_20261127.md` (Base vs SPLIT thought shift: M-share 13.5->1.8!)
   - `FLASH_SAMPLED_FRAME_GT_3BENCH_ROUND_END_20261126.md` (93.61 mean with sampled-frame GT!)
   - `PYTHON_CONTROL_AND_0FRAME_4BENCH_20261125.md`
   - `T2_FULL210_4ARM_20261127.md` & `T2_EGOEXO_V2_REPAIR_BUILD_20261127.md` (Ego-Exo4D cross-view video-only SPLIT +33.5 over base!)
   - `T1_HV_DEV20_RECON_20261127.md` & `T1_HV_V2_REPAIR_BUILD_20261127.md` (HourVideo streaming loop-closed submaps, SigLIP index, crisp floorplans, stitched view)
   - `T3_VQ3D_SUITE3A_ARMS23_20261127.md` & `T3_VQ3D_GT_POSES_20261127.md` (VQ3D 3D localization!)
   - `LONGVIDEO_SPEED_DESIGN_20261123T0036Z.md`
   - `ARGON_DYNAMIC_TRACE_ANALYSIS_20261119.md`
   - `OTHER_METHODS_TRACE_ANALYSIS_20261119.md`
   - `DESIGN_T1_LARGE_TRANSLATION_20261126.md`
4. Check `/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/long_video/SUPP_DRAFT/PILOT_ONESHOT_PROGRAM_20261125/RESULT.md` and `PILOT_REVSI_MAJ8_20261125/RESULT.md` and `X6_ARM_NL_NOSIZE_RESULT_20261126.md` (explicit paths only!).

## Deliverable
Write a high-signal report (max ~250 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
Include:
1. **What SPLIT Proved Scientifically in Nov 2026** (X1 perception vs reasoning bottleneck, paired thought shifts, Maj@8 vs perception, single-shot program vs iterative loop, Python-only control, dynamic 4D wins, long-video streaming submaps, Ego-Exo4D cross-view, VQ3D 3D queries).
2. **Exact Tools, Representations, and Interfaces That Drove Huge Gains** (e.g., metric 3D pointmaps, loop-closed submaps, cross-view registration, bearing/heading conventions, floorplans, stitched views, active re-inspection, dynamic 4D geometry).
3. **Where SPLIT Still Breaks** (grounding misses, cross-submap fragmentation, dynamic failures, latency).
4. **Top 10 Direct Inspirations for Our Fine-Tuned Spatial Student + VLA Backbone** (be bold and concrete: how do we internalize SPLIT's biggest wins directly into model weights, depth/pose/memory heads, and API-collected traces?).

Print a concise <=20-line summary to stdout when done.
