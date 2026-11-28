# Brief: E05 Pilot-0 Shard-1 Production Run (`500` Verified Epistemic Traces + High-IoU Boxes)

## Objective
Run Shard-1 (`500` verified multi-turn epistemic traces + `Argon ∩ Carbon` high-IoU 2D boxes) of our `E05` Unlimited Gemini API Data Factory (`/scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_runner.py`), running **in parallel** with `codex_review_e05` ("launch while cross-check runs").

## Hard Rules
- Working dir: `/scratch/jjyeung/orch_home_distill`. All outputs stay on `/scratch` (ZERO writes to `/home` or `/data*`, ZERO deletions, ZERO `git`).
- Use `GOOGLE_API_KEY` from `/home/jjyeung/agent_project/.env` (or existing env).
- Respect the shared 30 MB/s internet cap (our inline base64 factory used `0.046 MB/s` at `C=16`, ~`0.15%` of cap; keep `--workers 16`, NEVER use Gemini File API).
- Verify 0 leaks against `RoomExclusionGuard`, 100% deterministic math recompute parity, and box IoU quality.

## Exact Steps
1. Source `/home/jjyeung/agent_project/.env` if `GOOGLE_API_KEY` is unset. Create `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/`.
2. Run:
   ```bash
   /scratch/jjyeung/envs/p1cpu/bin/python -I /scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_runner.py \
     --target-rows 500 \
     --workers 16 \
     --argon-level MEDIUM \
     --author-models gemini-4-carbon,gemini-4-neon \
     --seed 2026112801 \
     --out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_traces.jsonl \
     --boxes-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_boxes.jsonl \
     --summary-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_summary.json \
     > /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/stdout.log 2>&1
   ```
   (Run it in background or foreground and check progress every 2–3 min if backgrounded; if a transient bug or cap occurs, diagnose and report exact root cause—do NOT edit `e05_api_factory/` while `codex_review_e05` is auditing unless there is a fatal crash bug, in which case log the exact error cleanly.)
3. After completion, run an independent verification script checking:
   - Exact line counts of `pilot0_s1_traces.jsonl` and `pilot0_s1_boxes.jsonl`.
   - Zero overlap of `canonical_scene` / `canonical_room` with `RoomExclusionGuard` (`0/N`).
   - Exact distribution across datasets (`arkitscenes`/`scannet`/`scannetpp`), task families, epistemic modes, units, and author models.
   - Mean/median/p10 `Argon ∩ Carbon` box IoU (`>=0.85` target), `429`/`503` counts, total wall time, rows/min, and internet MB/s.
4. Write a concise report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_e05_pilot0_s1.md`.
