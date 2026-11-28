# Hostile Cross-Family Audit: `e05_api_factory/` + Pilot-0 Verified Smoke Rows

You are an independent, skeptical cross-family reviewer (`Codex Astra`). Audit ALL files under `/scratch/jjyeung/orch_home_distill/e05_api_factory/` (`exclusions.py`, `geo_solver.py`, `gemini_client.py`, `pilot0_runner.py`, `tests/test_factory.py`), `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_e05_api_factory.md`, AND sample rows from `/scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_smoke.jsonl` and `pilot0_ownhead_boxes.jsonl`.

## Hard Rules
- Read-only. Do NOT modify files, run git, or scan NFS. You may run read-only python inspections (`-B`) inside `/scratch/jjyeung/orch_home_distill/e05_api_factory/`.

## What to Attack (Cite exact `file:line` and row indices)
1. **Leakage & Provenance Audit:** Verify `RoomExclusionGuard` (`exclusions.py`) against `BENCH_v2`, `R0` (`R0-dev` vs `R0-rl`), `dev-S1`, `K1-heldout`, `withheld_80`, and the `75` `ReSTI` ScanNet rooms (`0000..0149`). Are any held-out rooms, venues, or `H900`/`D580` held-out lexical skins leaked into `pilot0_smoke.jsonl` or `pilot0_runner.py` templates?
2. **3D Geometry & Math Audit (`geo_solver.py`):** Independently check `box_grid_5cm` surface distance, ScanNet++ `2.0x` half-extent correction (does it double-correct any already-full boxes?), `ego_polar` (`toward`/`away` chiral `180°` sign, left/right handedness, `VSTI@k` camera transform), `SE(3)` camera motion, and `>=5` 3D counting against real emitted rows in `pilot0_smoke.jsonl`.
3. **Trace Quality & Epistemic Realism:** Read 6–8 emitted traces in `pilot0_smoke.jsonl` across task families. Are the `GeoAPI-v2` / `S3` epistemic recovery traces genuinely faithful to the geometry, concise (`<250` tokens), free of unit-conversion arithmetic bugs, and free of shortcut leakage? Are the `Argon ∩ Carbon` boxes in `pilot0_ownhead_boxes.jsonl` consistent and non-degenerate?
4. **Bandwidth & Cluster Safety:** Confirm zero Gemini File API uploads, bounded inline JPEG payloads, safe `429`/`503` backoff, and zero heavy NFS reads when scaling to `C=16..32` workers.

## Deliverable
End with `VERDICT: GO`, `VERDICT: GO_AFTER_FIXES`, or `VERDICT: BLOCKER` and a prioritized list of verified issues (`BLOCKER` vs `WARNING`) with exact `file:line`. Keep under 150 lines.
