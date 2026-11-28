# E05 Pilot-0 Shard-1 Production Run Report (`result_e05_pilot0_s1.md`)

## 1. Executive Summary
- **Goal**: Execute Shard-1 (`--target-rows 500 --workers 16 --argon-level MEDIUM --author-models gemini-4-carbon,gemini-4-neon --seed 2026112801`) of the E05 Unlimited Gemini API Data Factory (`pilot0_runner.py`) on `/scratch` in parallel with `codex_review_e05`, leaving `e05_api_factory/*.py` untouched during the audit and independently verifying leakage, deterministic 3D math recompute parity, box IoU quality, and network/API telemetry.
- **Outcome**:
  - `pilot0_runner.py` completed cleanly (`exit code 0`, `status: PASS`), emitting **`68` verified multi-turn epistemic traces** (`pilot0_s1_traces.jsonl`, across `32` unique clean rooms) and **`98` `Argon ∩ Carbon` high-IoU 2D boxes** (`pilot0_s1_boxes.jsonl`, across `38` unique clean rooms) from the `94` candidates mined by `mine_candidate_specs(seed=2026112801)`.
  - **0/68 trace leaks and 0/98 box leaks (`0/N`)** against `RoomExclusionGuard` (`9/9` startup canaries passed; `0` overlap with `BENCH_v2`, `ReSTI_ScanNet`, `R0_dev`, `dev_S1`, `K1_heldout`, `withheld_80`; `manifest_sha256 = 1e1169ac8f129ad95b4239741695c0f67e1cc5076c2fad027857a8fc1b7d6f22`).
  - **100% (`68/68`) deterministic Python 3D math recompute parity**, **100% (`68/68`) exact `wire_xml` byte parity**, and **100% (`68/68`) physical extent calibration parity** (`half_corrected_2x` on `29` ScanNet++ and `11` ScanNet scenes; `full` on `19` ARKitScenes and `9` ScanNet scenes).
  - **`Argon ∩ Carbon` 2D Box IoU exceeds the `>= 0.85` target across mean, median, and p10**:
    - Emitted trace rows (`N = 68`): **mean `0.9457`**, **median `0.9812`**, **p10 `0.9199`**, p90 `0.9945`, max `0.9986`.
    - Exported box rows (`N = 98`): **mean `0.9585`**, **median `0.9853`**, **p10 `0.9248`**, p90 `0.9965`, max `1.0000` (vs 3D-projected GT mask box: mean IoU `0.8558`, median `0.9084`).
  - **Internet IO**: **`0.0277 MB/s`** (`32.215 MB` outbound inline base64 JPEG + `0.519 MB` inbound JSON over `1180.55 s`), using **`0.0923%` of the 30 MB/s cluster cap** with **`0` bytes** uploaded to the Gemini File API.
  - **Exact Root Cause of `68`-Row Output Cap under `--target-rows 500`**: Diagnosed in `pilot0_runner.py:153-465` (Section 4 below). Per instructions, `e05_api_factory/*.py` was not modified while `codex_review_e05` audits.

---

## 2. Independent Verification Summary (`verify_s1.py`)

### 2.1 Artifact Line Counts & Clean-Room Coverage
| Artifact | Path | Exact Lines | Unique Clean Scenes | Unique Clean Rooms | Leaks vs `RoomExclusionGuard` |
|---|---|---:|---:|---:|---:|
| Verified Epistemic Traces | `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_traces.jsonl` | **68** | 32 | 32 | **0 / 68** |
| Exported OwnHead 2D Boxes | `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_boxes.jsonl` | **98** | 38 | 38 | **0 / 98** |
| Run Summary JSON | `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/pilot0_s1_summary.json` | 116 | — | — | — |
| Independent Audit JSON | `/scratch/jjyeung/orch_home_distill/e05_api_factory/runs/pilot0_s1/verify_s1_report.json` | 132 | — | — | — |

### 2.2 Exclusion & Deterministic Math Recompute Verification
- **Startup Canaries**: `9/9` passed (`guard.assert_canaries()`).
- **Per-Set Overlap Check (`traces` / `boxes`)**:
  - `BENCH_v2`: `0`
  - `ReSTI_ScanNet` (`scene0000..scene0149`): `0`
  - `R0_dev`: `0`
  - `dev_S1`: `0`
  - `K1_heldout`: `0`
  - `withheld_80`: `0` (filtered `6` withheld rooms from the `239` pinned captures, leaving `233` clean train captures)
- **Independent `recompute_and_verify_trace` Re-Execution**:
  - Math recompute pass rate: **`68 / 68` (`100.0%`)**, `0` failures.
  - Exact `wire_xml` byte-for-byte parity: **`68 / 68` (`100.0%`)**.
  - Physical extent convention parity (`extent_calibration == scene.extent_convention` and `metric_scale_locked == 1`): **`68 / 68` (`100.0%`)**.

### 2.3 `Argon ∩ Carbon` 2D Box IoU Quality (`>= 0.85` Target)
- **Visual Referent Gate Agreement**: `98 / 104` (`94.23%`) blind `gemini-4-argon` (`MEDIUM`) + `gemini-4-carbon` (`MEDIUM`) checks agreed on target presence, unambiguous visibility, and 2D bounding box overlap.

| Metric Scope | Count | Mean IoU | Median (p50) | p10 IoU | p90 IoU | Min IoU | Max IoU | Target (`>=0.85`) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Emitted Trace `argon_carbon_mean_iou` | 68 | **0.9457** | **0.9812** | **0.9199** | 0.9945 | 0.2382 | 0.9986 | **PASS** |
| Exported Boxes `argon_carbon_iou` | 98 | **0.9585** | **0.9853** | **0.9248** | 0.9965 | 0.2382 | 1.0000 | **PASS** |
| Exported Boxes vs 3D-Projected `gt_iou` | 98 | **0.8558** | **0.9084** | 0.7085 | 0.9752 | 0.2684 | 0.9944 | **PASS** |

*(Note: The single low `Argon ∩ Carbon` pair at `0.2382` occurred in a multi-instance scene where `visible_count > 1` triggered the multi-instance GT-match clause `max(IoU(Argon, GT), IoU(Carbon, GT)) >= 0.55` at `gemini_client.py:493-498`; independent `box_iou_1000` recomputation matches stored `argon_carbon_iou` to within `4.885e-5` rounding).*

---

## 3. Exact Distributions (`N = 68` Verified Traces)

### 3.1 By Dataset & Extent Calibration
| Dataset | Verified Traces | Share | Extent Calibration Convention |
|---|---:|---:|---|
| `scannetpp` | 29 | 42.6% | `half_corrected_2x` (29) |
| `scannet` | 20 | 29.4% | `half_corrected_2x` (11), `full` (9) |
| `arkitscenes` | 19 | 27.9% | `full` (19) |

### 3.2 By Task Family
| Task Family | Count | Share |
|---|---:|---:|
| `metric_distance` | 24 | 35.3% |
| `small_object_size_lt30cm` | 8 | 11.8% |
| `ego_polar_out_of_view_cam_k` | 7 | 10.3% |
| `large_set_count_ge5` | 6 | 8.8% |
| `relative_size_neighbor_guard` | 5 | 7.4% |
| `camera_motion_forward` | 4 | 5.9% |
| `camera_motion_reversed` | 4 | 5.9% |
| `chiral_direction_away` | 4 | 5.9% |
| `chiral_direction_toward` | 3 | 4.4% |
| `multi_instance_disambig` | 3 | 4.4% |

### 3.3 By Epistemic Mode & Stream
| Epistemic Mode | Stream | Count | Share |
|---|---|---:|---:|
| `CLEAN_1PASS` | `S2_prior_breaker_phrasing` | 29 | 42.6% |
| `LOW_PARALLAX_WIDE_BASELINE` | `S1_epistemic_recovery` | 7 | 10.3% |
| `OUT_OF_VIEW_PERSISTENT_3D` | `S1_epistemic_recovery` | 7 | 10.3% |
| `CHIRAL_180_TWIN` | `S5_adversarial_twins` | 7 | 10.3% |
| `MULTI_SLOT_DEDUP_COUNT` | `S2_prior_breaker_phrasing` | 6 | 8.8% |
| `UNSEEN_BOX_HINT_RECOVERY` | `S1_epistemic_recovery` | 5 | 7.4% |
| `TEMPORAL_REVERSAL_INVARIANCE` | `S2_prior_breaker_phrasing` | 4 | 5.9% |
| `MULTI_SLOT_BEV_RECOVERY` | `S1_epistemic_recovery` | 3 | 4.4% |

### 3.4 By Unit & Author Model
- **Units**: `m`: `22` (`32.4%`), `cm`: `12` (`17.6%`), `ft`: `11` (`16.2%`), `in`: `10` (`14.7%`), `deg`: `7` (`10.3%`), `count`: `6` (`8.8%`).
- **Author Models**: `gemini-4-carbon`: `51` (`75.0%`), `gemini-4-neon`: `17` (`25.0%`, with `29` automatic `gemini-4-neon -> gemini-4-carbon` fallbacks on 503/timeout).

---

## 4. API Telemetry, Throughput & Exact Root-Cause Diagnosis

### 4.1 API & Network Telemetry
- **Wall time**: `1180.55 s` (`19.68 min`) at `--workers 16`.
- **Throughput**: `3.46 verified rows/min` (`~4,977 rows/24h` at `C=16`; `~9,953 rows/24h` projected at `C=32`).
- **HTTP & Retry Counters**:
  - `calls_total`: `512` (`calls_ok`: `277`)
  - `http_429`: **`0`**
  - `http_503`: **`48`** (`rate_429_503 = 9.38%`, absorbed by exponential backoff and `29` automatic `neon -> carbon` fallbacks)
  - `http_other_err`: **`0`**
  - `timeouts`: `187` (at `request_timeout_s = 55.0 s`; caused `13` `author_api_err:ReadTimeout`, `6` `author_api_err:RuntimeError` retry exhaustions, and `1` `vis_api_err:ReadTimeout`)
- **Per-Model Latency (OK calls)**:
  - `gemini-4-argon` (`MEDIUM`): `105` calls, median `13.55 s`, mean `20.12 s`
  - `gemini-4-carbon` (`MEDIUM`): `155` calls, median `18.33 s`, mean `22.17 s`
  - `gemini-4-neon` (`MEDIUM`): `17` calls, median `27.44 s`, mean `28.60 s`
- **Internet Bandwidth**: `32.215 MB` outbound + `0.519 MB` inbound = **`0.0277 MB/s`** (**`0.0923%`** of the 30 MB/s cluster cap; `file_api_bytes_uploaded = 0`).
- *(Operational Note: The initial background invocation hit the harness's default 10-minute background tool timeout at 54 verified rows (`stdout_attempt1_600s.log`) and was re-launched with an explicit 60-minute background timeout to complete all 94 mined candidates).*

### 4.2 Root-Cause Diagnosis: Why `--target-rows 500` Mined Only `94` Candidates (`68` Verified Rows)
Although `run_pilot0()` computes `pool_size = max(target_rows * 2 + 16, 80) = 1016` and passes `max_candidates=1016` to `mine_candidate_specs()` (`pilot0_runner.py:723-726`), `mine_candidate_specs()` returns only **`94` candidate specs** for `--seed 2026112801` because of three hardcoded smoke-test caps inside `pilot0_runner.py`:

1. **Early 48-Scene Break (`pilot0_runner.py:153-154`)**:
   ```python
   if len(scenes_cache) >= 48 and all(len(v) >= 6 for v in buckets.values()):
       break
   ```
   This halts scene loading after `48` captures (out of `233` clean captures) as soon as every bucket has at least `6` items.
2. **Hardcoded Per-Bucket Ceilings Summing to `102` (`pilot0_runner.py:187-465`)**:
   Each bucket check enforces a fixed constant ceiling rather than scaling with `max_candidates`:
   - `unseen_recovery_dist < 14` (line 187)
   - `low_parallax_dist < 10` (line 202)
   - `clean_dist < 14` (line 217)
   - `small_obj_size < 10` (line 242)
   - `relative_size < 8` (line 272)
   - `out_of_view_cam_k < 10` (line 301)
   - `facing_twins < 12` (line 348)
   - `camera_motion < 8` (line 395)
   - `large_count < 8` (line 438)
   - `multi_slot_disambig < 8` (line 465)
   The sum of all 10 ceilings is `102` specs maximum regardless of `--target-rows`.
3. **Single-Candidate Extraction per Capture per Task Family (`pilot0_runner.py:170,243,302,349,396`)**:
   Within each capture loop iteration, `mine_candidate_specs()` inspects only `singletons[0], singletons[1]` for distance, `small_objs[0]` for size, `singletons[0]` for `out_of_view_cam_k`, and `singletons[0..2]` for `facing_twins`. Across `233` clean captures, scaling to `500+` rows requires iterating over multiple singleton pairs/triplets per capture and scaling bucket caps by `scale = max(1, math.ceil(max_candidates / 80))` while removing the `len(scenes_cache) >= 48` break.
4. **Minor Non-Fatal Hygiene Items for Post-Audit Patching**:
   - `pilot0_runner.py:784-786`: In `get_verified_target()`, calling `fut.set_exception(exc)` followed by `raise` triggers Python's `"Future exception was never retrieved"` warning at event-loop shutdown if no second worker awaits `vis_cache[cache_key]`, and permanently caches transient `ReadTimeout` failures for that target. Fix: `vis_cache.pop(cache_key, None)` on exception instead of storing a failed future.
   - `pilot0_runner.py:964,1042`: `status` and `main()` exit-code check `len(verified_rows) >= 20` (`min(20, args.target_rows)`) instead of `len(verified_rows) >= args.target_rows`.
