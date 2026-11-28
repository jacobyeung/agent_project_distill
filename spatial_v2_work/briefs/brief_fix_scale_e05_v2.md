# Brief: Remediate All `audit_e05_neon.md` Findings & Scale `E05 v2` (`500` Verified Rows Live)

## Context
The independent hostile Neon audit (`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/audit_e05_neon.md`) returned **`VERDICT: GO_AFTER_FIXES`** with 3 `[BLOCKER]`s and 5 `[WARNING]`s, plus `result_e05_pilot0_s1.md` identified 2 hygiene items (`vis_cache.pop()` on error, incremental streaming JSONL flush).

## Exact Remediation Checklist (Fix ALL 10 Items Cleanly in `e05_api_factory/`)
Read `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/audit_e05_neon.md` first, then fix every single item:
1. **`[BLOCKER 1]` Zero Oracle GT Leaks in `<tool_obs>` + Real OOF `UNSEEN` + Real `AND` Parallax Gate (`geo_solver.py`):**
   - Strip ALL GT `visible_targets` / `box_1000` / `slot_id` from `inspect(view="rgb")` `<tool_obs>` (return frame metadata/image reference only, so the student genuinely predicts `box_hint` visually!).
   - Mine `UNSEEN` recovery strictly from labels *actually queried* in `candidates.json` (`lab in oof_scores_by_phrase`) without leaking GT `best_cand_f`.
   - Enforce the real geometric `AND` parallax gate ($\Delta\theta \ge 15^\circ \land \beta \ge 0.20 \land |t_2 - t_1| \ge 2$) on `locate(frames=...)`, computing real parallax angle, baseline ratio, and `reproj` / `pose_cond` from the actual camera poses instead of hardcoded constants!
2. **`[BLOCKER 2]` Remove Hardcoded `102`-Candidate Cap (`pilot0_runner.py`):**
   - Remove the `len(scenes_cache) >= 48` early break and fixed per-bucket ceilings; scale bucket targets proportionally to `max_candidates` and enumerate multiple clean singleton pairs/triplets/frames across ALL `233` clean captures (supporting `--target-rows 500` up to `10,000+`!).
3. **`[BLOCKER 3]` Raise HTTP Request Timeout & Retry Hygiene (`gemini_client.py` / `pilot0_runner.py`):**
   - Raise `request_timeout_s` to `120.0` (configurable via `--timeout`), catch `httpx.ReadTimeout` cleanly inside backoff retries, and in `get_verified_target()` do `vis_cache.pop(cache_key, None)` on exception instead of caching failed futures.
4. **`[WARNING 4]` Zero Per-Call NFS Writes (`gemini_client.py`):**
   - Log per-call API usage strictly to local `/scratch/jjyeung/orch_home_distill/e05_api_factory/usage.<host>.jsonl` (NEVER `/data2` per call — avoids `2×` NFS write amplification and asyncio blocking!); cache `/data2/.../OVER_CAP` checks via a shared timestamp TTL (`>=30s`) so 32 workers never stampede NFS.
5. **`[WARNING 5]` Pin `K1_ROWSETS` SHA256 & Split `R0_dev` (`100`) vs `R0_rl` (`272`) (`exclusions.py`):**
   - Require and SHA256-pin `K1_CAPTURES_HELDOUT_57.txt` + `K1_EXCLUSIONS.json` (fail closed if missing!).
   - Separate `R0_dev` (`100` scannetpp rooms) and `R0_rl` (`272` rooms) in `RoomExclusionGuard` and add canaries for BOTH!
6. **`[WARNING 6]` Real Half-Extent Tests & ScanNet++ Raster Check (`geo_solver.py`, `tests/test_factory.py`):**
   - Run the raster containment check on `scannetpp` too (no blanket `2x` shortcut), explicitly reject `"no_raster"`, and test half-extent captures across ALL datasets (`arkitscenes`, `scannet`, `scannetpp`) in `test_factory.py`.
7. **`[WARNING 7]` Fix Multi-Instance Box Averaging (`gemini_client.py`):**
   - When `ac_iou < min_ac_iou` under `multi_vis=True`, select the single GT-matching model's box (or reject if ambiguous) — NEVER average two disjoint boxes!
8. **`[WARNING 8]` `yaw_deg` Sign & Trace Hygiene (`geo_solver.py`, `pilot0_runner.py`):**
   - Match `dev-S1` convention (`+ = left`), always include `best_t` in `vis_f`, randomize target slot index in `multi_instance_disambig`, remove redundant BEV echoes and robotic Carbon boilerplate.
9. **Streaming Incremental JSONL Flush + Accurate Exit Status (`pilot0_runner.py`):**
   - Stream/flush each verified trace & box to JSONL as it completes (so partial progress is never lost on interrupt!), and set `status = "PASS"` / exit `0` only when `len(verified_rows) >= target_rows` (or `>= 0.95 * target_rows` with explicit shortfall logged).
10. **Unit Tests + Live `E05 v2` `500`-Row Production Run:**
    - Run `pytest -v /scratch/jjyeung/orch_home_distill/e05_api_factory/tests/test_factory.py` (add explicit regression tests for ALL 8 audit items above — confirm `100%` PASS!).
    - Launch detached `E05 v2` Shard-1 (`--target-rows 500 --workers 24 --argon-level MEDIUM --timeout 120 --author-models gemini-4-neon,gemini-4-carbon`, outputs in `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/v2_s1/`), verify the first `50+` streaming rows immediately (and wait for all `500` if <25 min, or report verified live progress + PID if still streaming cleanly!), and write `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_e05_v2_remediated.md`.

## Hard Rules
- Zero deletions, zero `git`, zero NFS writes during API calls, zero File API uploads.
