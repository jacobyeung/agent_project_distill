# Hostile Cross-Family Re-Audit: `spatial_v2/` Fixes + `KT-6 Stage-1A` Trainer

You are an independent, skeptical cross-family code reviewer (`Codex Astra`). Perform a focused verification audit of `/scratch/jjyeung/orch_home_distill/spatial_v2/` covering:
1. **Verification of all 7 BLOCKERs & 4 WARNINGs from your prior review** (`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/codex_review_spatial_v2.md`) and the fix receipt (`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/fix_spatial_v2_codex.md`). Reproduce your prior failure cases to prove whether each blocker is ACTUALLY fixed or still broken!
2. **Hostile Audit of the new `KT-6 Stage-1A` trainer** (`data_k1_local.py`, `stage1a_model.py`, `train_stage1a.py`, `eval_stage1a.py`, `tests/test_stage1a.py`):
   - Check room-level leakage & split integrity (`RoomExclusionGuard`: are any `K1-heldout`, `dev-S1`, `R0-dev`, or `BENCH v2` rooms reachable in train? Is `split_sha256` deterministic?).
   - Check whether `Arm A (epi_vit)` vs `Arm B (corresp_stem)` is a fair, unconfounded apples-to-apples comparison (same targets, same views, same loss weights, same coordinate frames, no target leakage from `DA3-Giant` into `Arm B` DINOv2-L/14!).
   - Check for silent training bugs: coordinate convention mismatch between `DA3` teacher poses/depths and K1 GT poses/depths (`c2w` vs `w2c`, OpenCV vs OpenGL axes, ScanNet++ half-extent or orientation bugs, `bf16` overflow, `DDP` unused params or gradient sync bugs).

## Hard Rules
- Read-only. Do NOT modify files, run git, or scan NFS. You may run read-only python/pytest inspections with `-B` inside `/scratch/jjyeung/orch_home_distill/spatial_v2/`.

## Deliverable
Cite exact `file:line` for every verified finding. End with `VERDICT: GO`, `VERDICT: GO_AFTER_FIXES`, or `VERDICT: BLOCKER` and list any remaining blockers first. Keep under 160 lines.
