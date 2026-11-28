# E05 v2 Remediated Data Factory & Live 500-Row Production Report (`result_e05_v2_remediated.md`)

## 1. Executive Summary
- **Remediation Status**: All **10** checklist items from `audit_e05_neon.md` (3 `[BLOCKER]`s, 5 `[WARNING]`s) and `result_e05_pilot0_s1.md` (2 operational hygiene items) are implemented in `/scratch/jjyeung/orch_home_distill/e05_api_factory/` and verified by **`12/12` passing unit & regression tests** (`pytest -v e05_api_factory/tests/test_factory.py`, `41.64 s`).
- **Live `E05 v2` Shard-1 Production Run (`target_rows=500`, detached)**:
  - **Host / PID**: `trinity-2-28`, **`PID=3664094`** (launched `2026-11-28T16:27:06Z` / `08:27:06 PT`, alive and streaming cleanly).
  - **Verified Live Progress (`16:36:15Z`)**: **`91 / 500` verified multi-turn traces** (`v2_s1_traces.jsonl`, surpassing the old `68`-row cap from `1,282` mined candidates across all `233` clean captures) and **`81` ownhead 2D boxes** (`v2_s1_boxes.jsonl`).
  - **Independent Audit (`verify_v2.py` on `91` live streamed traces + `81` boxes)**:
    - **0 / 91 trace leaks, 0 / 81 box leaks** (`11/11` startup canaries; `manifest_sha256 = a86f177cc34fa9eea0eab2de80a4b80dea719fa55d8c79ef2f1da8dea71e111b`).
    - **0** oracle GT leaks in `inspect(view="rgb")` `<tool_obs>`, **0** `best_cand_f` leaks, **0** unqueried `UNSEEN` fabrications, **0** `wide_cand_f` leaks, **0** `AND` parallax gate failures, **0** `vis_f` missing `best_t`, **0** redundant BEV calls, **0** counting slot truncations, and **0** robotic Carbon boilerplate hits (`17` boilerplate drafts caught and rejected live by the recompute gate).
    - **`91 / 91` (`100.0%`) deterministic 3D math recompute parity**, **`91 / 91` (`100.0%`) exact `wire_xml` parity**, and **`91 / 91` (`100.0%`) extent calibration parity**.
    - **`Argon ∩ Carbon` 2D Box IoU**: traces mean **`0.9424`**, median **`0.9678`**, p10 **`0.8852`**; exported boxes mean **`0.9395`**, median **`0.9764`**, p10 **`0.8852`** (`80` `argon_carbon_avg`, `1` `carbon_gt_selected`, `0` disjoint box averages).
    - **Throughput & API Hygiene (at 75-row interim checkpoint, `431.18 s`, `C=24`, `--timeout 120`)**: **`10.44 rows/min`** (`15,029 rows/24h` at `C=24`, `20,038 rows/24h` at `C=32`; ETA ~37 min remaining for 500 rows), timeout rate **`3.90%`** (`13/333`, down from `21.1%` smoke / `36.5%` S1), `http_429 = 0`, `internet_mb_per_s = 0.0498 MB/s` (`0.166%` of 30 MB/s cap), `file_api_bytes_uploaded = 0`, and **zero per-call NFS writes** (`usage.trinity-2-28.jsonl` writes strictly to local `/scratch`).

---

## 2. Exact Remediation Matrix (All 10 Checklist Items Verified)

| # | Audit Finding / Item | Code Location | Fix Implemented | Verification Evidence |
|---|---|---|---|---|
| 1 | `[BLOCKER 1]` GT leaks in `<tool_obs>`, fake `UNSEEN`, fake `LOW_PARALLAX` | `geo_solver.py`, `pilot0_runner.py` | `inspect(view="rgb")` returns frame metadata only (`view, frame, image_ref, resolution_hw, valid_pose`). `UNSEEN` mined strictly from labels actually queried in `candidates.json` (`oof_queried=True`, score `< 0.30`) with no `best_cand_f` leak. `LOW_PARALLAX` enforces real `AND` gate ($\Delta\theta \ge 15^\circ \land \beta \ge 0.20 \land |t_2 - t_1| \ge 2$) and computes real `parallax_deg`, `baseline_ratio_beta`, `reproj_m`, `margin_top2`, and `pose_cond_deg` (from `geometry.npz` vs GT `c2w`). | `test_zero_gt_leak_rgb_inspect_and_real_oof_unseen`, `test_real_and_parallax_gate_and_non_constant_metrics`; live `91` rows: `0` RGB leaks, `0` `best_cand_f` leaks, `0` unqueried fabrications, `0` `AND` gate failures, `124` distinct `reproj_m` values, `14` distinct `pose_cond_deg` values. |
| 2 | `[BLOCKER 2]` Hardcoded `102`-candidate / `48`-scene cap | `pilot0_runner.py` | Removed `len(scenes_cache) >= 48` early break and fixed ceilings; scaled bucket caps proportionally to `max_candidates` (`BUCKET_WEIGHTS`) and enumerated multiple pairs/triplets/frames across all `233` clean captures (supporting `500` to `10,000+` rows). | `test_candidate_mining_scales_past_102_and_scaffold_hygiene` (`1,100` specs across `233` scenes); live run mined `1,282` candidates and already streamed `91` rows (exceeding old `68`-row cap). |
| 3 | `[BLOCKER 3]` `55s` timeout & cached failed futures | `gemini_client.py`, `pilot0_runner.py` | Raised default `request_timeout_s` to `120.0` with CLI `--timeout`, caught `httpx.TimeoutException` in exponential backoff retries, added `timeout_rate` to summary, scaled `httpx.Limits`, and popped `vis_cache.pop(cache_key, None)` on exception with `fut.exception()` cleanup. | Live timeout rate dropped to **`3.90%`** (`13/333`, vs `21.1%` in smoke and `36.5%` in S1) with `0` `Future exception was never retrieved` warnings. |
| 4 | `[WARNING 4]` Synchronous NFS usage writes & `OVER_CAP` stampede | `gemini_client.py` | Removed `/data2` per-call usage writes completely; logs strictly to `/scratch/jjyeung/orch_home_distill/e05_api_factory/usage.<host>.jsonl` (rejects `/data*` or `/home*`). Shared `asyncio.Lock` + `>=30s` TTL + `asyncio.to_thread` caches `OVER_CAP` checks. | `test_multi_instance_box_never_averages_disjoint_and_local_usage_only` (`1` stat across `24` concurrent workers); live tail confirms `0` `e05_api_factory` lines on `/data2` and active local `/scratch` usage log (`101 KB`). |
| 5 | `[WARNING 5]` Unpinned `K1_ROWSETS` & conflated `R0_dev`/`R0_rl` | `exclusions.py` | Required and SHA256-pinned `K1_CAPTURES_HELDOUT_57.txt` (`702b0d9f...`) and `K1_EXCLUSIONS.json` (`52fdfd0a...`) fail-closed. Split `R0_dev` (`100` `scannetpp` rooms) and `R0_rl` (`272` rooms) with disjointness & union check; expanded startup canaries to `11/11` (covering both `R0_dev`, `R0_rl`, and `arkitscenes/45261532`). | `test_exclusion_canaries_r0_split_and_k1_pins` (`11/11` canaries, fail-closed on missing `K1_ROWSETS`). |
| 6 | `[WARNING 6]` Vacuous half-extent test, blanket `scannetpp` `2x`, `no_raster` fallthrough | `geo_solver.py`, `tests/test_factory.py` | Removed blanket `if ds == "scannetpp": conv = "half"` shortcut; runs real raster containment test across ALL datasets (`71/71` clean `scannetpp` captures measure median `0.961 > 0.72`); explicitly rejects `"no_raster"` or empty raster ratios with `ValueError`. | `test_half_extent_calibration_all_datasets_and_no_raster_rejection` passes across `arkitscenes:full`, `scannet:full`, `scannet:half`, and `scannetpp:half` under both `known_conventions` and `None` auto-detection, plus rejects `no_raster`. |
| 7 | `[WARNING 7]` Multi-instance disjoint box averaging | `gemini_client.py` | Averages `Argon` + `Carbon` boxes ONLY when `ac_iou >= min_ac_iou`. Under `multi_vis=True` with `ac_iou < min_ac_iou`, selects the single GT-matching model's box (`argon_gt_selected` / `carbon_gt_selected`) or rejects if ambiguous. Singletons use strictly blind verification (`spatial_hint=""`). | `test_multi_instance_box_never_averages_disjoint_and_local_usage_only`; live `81` boxes: `80` `argon_carbon_avg`, `1` `carbon_gt_selected`, `0` disjoint averages. |
| 8 | `[WARNING 8]` `yaw_deg` sign, `vis_f`, disambig shortcut, BEV echo, Carbon boilerplate | `geo_solver.py`, `pilot0_runner.py`, `gemini_client.py` | Aligned `camera_motion` `yaw_deg` to `dev-S1` (`+ = left / CCW`). Guaranteed `first_t` and `best_t` in `vis_f`. Randomized `target_slot_index` in `multi_instance_disambig` (unique `first_frame`) and removed redundant `inspect(view="bev")`. Prevented `large_set_count_ge5` slot truncation (`max_k >= count`) and set `referent_unique=False` on counts. Added anti-boilerplate rule + deterministic recompute filter. | `test_yaw_deg_sign_dev_s1_left_positive` (`+90.0°` left, `-90.0°` right); live `91` rows: `0` missing `best_t`, `0` BEV echoes, `0` slot truncations, `0` boilerplate hits (`17` caught live), `disambig_slot_index_dist = {0: 6, 1: 3, 2: 2}`. |
| 9 | Streaming JSONL flush & accurate exit status | `pilot0_runner.py` | Opens `traces.jsonl` and `boxes.jsonl` upfront, flushes every verified trace/box immediately under locks, writes interim `summary.json` every `25` rows, and sets `status = "PASS"` / exit `0` only when `verified_rows >= ceil(0.95 * target_rows)` (with explicit `shortfall`). | Confirmed live incremental streaming (`91` traces + `81` boxes on disk mid-run; interim summary written cleanly). |
| 10 | Full pytest + detached live `500`-row `E05 v2` Shard-1 | `tests/test_factory.py`, `runs/v2_s1/` | `12/12` pytest pass; detached `PID=3664094` launched with `--target-rows 500 --workers 24 --argon-level MEDIUM --timeout 120 --author-models gemini-4-neon,gemini-4-carbon`; first `91` live rows independently verified. | `verify_v2_report.json` (`91/91` recompute + wire XML exact parity, `0/91` leaks). |

---

## 3. Live `E05 v2` Shard-1 Verified Metrics (`N = 91` Streamed Traces, `PID = 3664094`)

### 3.1 Live Run Artifacts & Process State
- **Process**: `PID=3664094` on `trinity-2-28` (`STATUS: RUNNING`, launched `2026-11-28T16:27:06Z`, verified alive at `16:36:15Z`).
- **Command**:
  ```bash
  /scratch/jjyeung/envs/p1cpu/bin/python -u /scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_runner.py \
    --target-rows 500 --workers 24 --argon-level MEDIUM --timeout 120 \
    --author-models gemini-4-neon,gemini-4-carbon --seed 2026112802 \
    --out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/v2_s1/v2_s1_traces.jsonl \
    --boxes-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/v2_s1/v2_s1_boxes.jsonl \
    --summary-out /scratch/jjyeung/orch_home_distill/e05_api_factory/runs/v2_s1/v2_s1_summary.json
  ```
- **Output Directory**: `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/v2_s1/`
  - Traces (streaming): `v2_s1_traces.jsonl` (`91` verified rows so far)
  - Boxes (streaming): `v2_s1_boxes.jsonl` (`81` agreed boxes so far)
  - Interim Summary: `v2_s1_summary.json` (updates every 25 rows + on completion)
  - Verifier & Report: `verify_v2.py`, `verify_v2_report.json`
  - PID & Log: `pid.txt` (`3664094`), `stdout.log`

### 3.2 Independent Audit & Quality Metrics (`verify_v2_report.json`)
| Metric | Value (`N = 91` Traces / `81` Boxes) | Status |
|---|---|---|
| Exclusion Canaries & Leaks | `11/11` canaries; `0/91` trace leaks, `0/81` box leaks | **PASS** |
| Deterministic Math / Wire XML / Extent Parity | `91/91` (`100%`) / `91/91` (`100%`) / `91/91` (`100%`) | **PASS** |
| Oracle GT / `best_cand_f` / `wide_cand_f` Leaks | `0` / `0` / `0` | **PASS** |
| Real OOF `UNSEEN` & `AND` Parallax Gate Failures | `0` unqueried fabrications; `0` `AND` gate failures | **PASS** |
| `vis_f` / BEV Echo / Slot Truncation / Boilerplate | `0` / `0` / `0` / `0` | **PASS** |
| `<think>` Word Length | mean `62.2`, median `63.0`, min `23`, max `98` (`<= 220`) | **PASS** |
| Trace `Argon ∩ Carbon` IoU | mean **`0.9424`**, median **`0.9678`**, p10 **`0.8852`** | **PASS** |
| Box `Argon ∩ Carbon` IoU / GT IoU | AC mean **`0.9395`** (med `0.9764`); GT mean **`0.8237`** (med `0.8730`) | **PASS** |
| Throughput & Network (75-row checkpoint) | **`10.44 rows/min`** (`15,029/24h` @ `C=24`), `3.90%` timeout, `0` HTTP 429, `0.0498 MB/s` | **PASS** |

### 3.3 Live Distributions (`N = 91`)
- **Dataset / Calibration**: `scannetpp:half_corrected_2x` (`48`), `scannet:full` (`27`), `scannet:half_corrected_2x` (`1`), `arkitscenes:full` (`15`).
- **Task Families**: `metric_distance` (`20`), `chiral_direction_toward` (`11`), `chiral_direction_away` (`11`), `multi_instance_disambig` (`11`), `relative_size_neighbor_guard` (`10`), `ego_polar_out_of_view_cam_k` (`7`), `camera_motion_forward` (`6`), `large_set_count_ge5` (`6`), `small_object_size_lt30cm` (`5`), `camera_motion_reversed` (`4`).
- **Epistemic Modes**: `CLEAN_1PASS` (`28`), `CHIRAL_180_TWIN` (`22`), `MULTI_SLOT_DISAMBIG` (`11`), `LOW_PARALLAX_WIDE_BASELINE` (`7`), `OUT_OF_VIEW_PERSISTENT_3D` (`7`), `UNSEEN_BOX_HINT_RECOVERY` (`6`), `MULTI_SLOT_DEDUP_COUNT` (`6`), `TEMPORAL_REVERSAL_INVARIANCE` (`4`).
- **Units**: `m` (`23`), `deg` (`22`), `ft` (`14`), `cm` (`14`), `in` (`12`), `count` (`6`).
- **Author Models**: `gemini-4-carbon` (`67`), `gemini-4-neon` (`24`).

*(Note on `build_e05_api_factory.md` doc discrepancies flagged by Neon audit: the actual `6` blocked `withheld_80` captures are `scene0201_02, scene0255_01, scene0478_00, scene0478_01, scene0614_02, scene0692_03`, and `min_ac_iou` in code is `0.55`.)*
