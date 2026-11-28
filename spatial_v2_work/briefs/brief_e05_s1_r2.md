# Brief: E05 Pilot-0 Shard-1 (`500` Verified Traces + Boxes, Detached No-Timeout Run)

Attempt 1 ran `pilot0_runner.py` in a foreground Bash call and was killed at the 600s Bash timeout (`54/500` verified rows, 0 429s). Re-launch cleanly in the background so it completes all `500/500` rows!

## Exact Steps
1. Source `/home/jjyeung/agent_project/.env` if `GOOGLE_API_KEY` is unset. Ensure `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/` exists (do NOT delete `stdout_attempt1_600s.log`).
2. Launch `pilot0_runner.py` detached with `nohup` and `setsid` (`--workers 24 --target-rows 500 --argon-level MEDIUM`), writing to `stdout_s1_v2.log` and saving PID to `runner.pid`:
   ```bash
   setsid /scratch/jjyeung/envs/p1cpu/bin/python -I -u /scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_runner.py \
     --target-rows 500 \
     --workers 24 \
     --argon-level MEDIUM \
     --author-models gemini-4-carbon,gemini-4-neon \
     --seed 2026112802 \
     --out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_traces.jsonl \
     --boxes-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_boxes.jsonl \
     --summary-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_summary.json \
     > /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/stdout_s1_v2.log 2>&1 < /dev/null &
   echo $! > /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/runner.pid
   ```
3. Monitor cleanly (`sleep 180` inside bounded checks, up to completion — expect ~15–25 min at `workers=24`, NEVER kill it early!).
4. Once `runner.pid` finishes and `pilot0_s1_summary.json` exists, run independent verification:
   - Exact line counts of `pilot0_s1_traces.jsonl` and `pilot0_s1_boxes.jsonl`.
   - Zero overlap with `RoomExclusionGuard` (`0/N`).
   - Exact distribution across datasets, task families, epistemic modes, units, and author models.
   - Mean/median/p10 `Argon ∩ Carbon` box IoU, `429`/`503` counts, throughput (`rows/min`), and internet MB/s.
5. Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_e05_pilot0_s1.md`.
