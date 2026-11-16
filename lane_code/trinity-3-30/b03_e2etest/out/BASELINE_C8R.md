# EAT-1 baseline: kit C8r (the current routed reader) — FAIL on A1, A2, A3, A4 and A5

C8r fails EAT-1. It fails A2 dynamically on the tiny CPU model, and it fails A1, A3, A4 and A5 statically on its read path. The dynamic run also fails A3 and A4. Every expected violation the brief lists appears below with its file and line. A2 is now established: C8r enters the model once per item, and it writes every response into the cache from Python outside any registered module (530 injected tokens on 10 called items).

Code under test: code_c8r.tar (sha256 f4535bc0…, unpacked at `work/c8r_src`), and the sealed tree b01ce449 audit copy at `work/audit_copies/tree_b01ce449`. Its 792 files match RUNTIME_TREE.json. `tree:` paths below are relative to the tree, and `c8r:` paths to `native/out2/`. The allowlist is `eat1/allowlist.json`, PROPOSED and not yet reviewed. It applies USER ruling 5 (ORCH 1155Z): the fixed-math allowance covers unprojection and printing head outputs as text, so unit conversion or answer reformatting outside the model fails.

## 1. Dynamic run: tiny CPU model (`work/c8r_tiny/run6/EAT1_REPORT.md`)
The adapter `eat1/adapters/c8r_tiny.py` calls `evalpath.runtime.generate(model, processor, batch, 'routed', 16384)`, the entry C8r's routed and nomdg readers use. It runs on the tree's own tiny Qwen3.5 + CarrierC1 fixture (`tests/test_batched_routed_decode.fixture`). Items cover 6 types × 2 seeds: depth_at+dist, move, turn, pose, ground and direct. A fixed program module on `lm_head` stands in for trained LM weights. It writes no response token.

| Clause | Status | Evidence |
|---|---|---|
| A1 | PASS on this path | Only the item frames and code were opened. The tiny path binds no grounding backend, so the backend's tables never open here (they are covered in §2). |
| A2 | **FAIL** | Model entries per item: 1 (12/12), so the single-entry part holds. 530 response tokens were fed by `tree:student_pilot/carrier_c1_decode.py:65` (`consume_cache_tokens`) and written by `tree:student_pilot/carrier_c1_batch_decode.py:142` (`Row._call`), which wraps `<tool_response>` text from `respond()` (`carrier_c1_decode.py:214`). No call handler is registered on the model. |
| A3 | **FAIL** | 28 executed findings. Examples: the depth stencil-percentile estimator `tree:student_pilot/carrier_c1_routing.py:278-279` (P20/P30/P50/P80, spread); radian→degree conversion in pose and turn responses (`carrier_c1_routing.py:264,300`; constants 180/360 in `wrap` at `:119`); hard-coded frame count 32/33 (`decoupled_v.py:111-116`, `ground_context.py:44`, `p3_printed_calculator.py:159`). |
| A4 | **FAIL** | Typed error responses replace head output: `carrier_c1_decode.py:244,248` (except → `'error: …'`, which produced `error: bad_frame` for `<pose frame=40>` and `error: head_readout` for `<ground>`). The ground fallback is at `carrier_c1_decode.py:516,526` (`context.fallback`). |
| A5 | PASS on this path | (i) The sandboxed rerun is identical. (ii) Perturbing pose_head changed 6/6 naming responses and 0/4 others; depth_head changed 2/2 and 0/8. (iii) No tower is cited. The cache and tower violations sit in the backend (§2). |

Per type (A6): call rate 1.0 for every call type and 0 for direct. Seconds per item on CPU: 0.08 (direct) to 0.80 (depth_at+dist). Six findings inside head classes (camera_head, point_depth_head activations) are listed apart as model code.

## 2. Static audit of the read path (`out/BASELINE_C8R_FINDINGS.md`, 965 findings in 45 files)
The scope is `work/c8r_static/SCOPE_TIER1.txt`: the out2 reader (routed, nomdg, perception, reader_policy, geometry, gravity_guard, geometry_refusals, r1, frozen_kit), mask_kit, and the tree modules the read imports at decode time (grounding, lifting, selection, box, room, tower, decode, calculator, evalpath runtime and run). The full import closure has 231 files (`work/c8r_static/CLOSURE_C8R.json`) and includes trainer modules that the read loads only for validation. Counts by rule: constant 371, guard 137, status 107, threshold 91, table_load 87, data_file 84, unit_conversion 39, cache 21, response_outside_model 18, except_substitute 10.

Each violation the brief expects, located:

| Clause | Expected violation | Located at |
|---|---|---|
| A1 | selector tables | `tree:student_pilot/candidate_policy.py:78` loads the logistic selector weights (`predict` at :13). `s1_grounding.py:16` loads `s1_version.json` |
| A1 | `tower_scale_rule.json` | `tree:student_pilot/tower_scale.py:11` (estimator `tower_scale_rule.py`) |
| A1 | alias table | `c8r:mask_kit/variantlib.py:19` (`ALIASES`, used at :22). `c8r:mask_kit/vendor/phrase.py:3` (`SINGULAR`) |
| A1 | box policy | `tree:trace_format/box_v313.py:279,460-467` (`fit_gbox_policy_voteb5_best1_v1`). Pinned at `c8r:nomdg.py:19,148` |
| A1 | mask cache | `c8r:perception.py:68-116` (`Masks`, `kit.load_cache` of SAM 3 `.npz`). `c8r:nomdg.py:190,267,414`. `tree:student_pilot/ground_sources.py:93` (`CachedSAM3`) |
| A1 | towers outside the export | `c8r:geometry.py:66-80`: G3T runs in a separate stage with its own weight pins. Its manifest is loaded at read time (`tree:student_pilot/s1_grounding.py:43,49`, `c8r:nomdg.py:414`) |
| A3 | selector | `tree:student_pilot/candidate_policy.py:13,79-80,103` (count 0.15, merge 0.2). `native_selection.py:1-12` (0.5 m one-vote selector) |
| A3 | depth cut | `tree:student_pilot/candidate_policy.py:25-36` (P10/P90 ± 0.15 m, erosion 3). `ground_lifting.py:96` |
| A3 | box policy | `tree:trace_format/box_v313.py:460-467` (5 cm voxels, ≥2 frames, voteb5/best1, 4,000 points) |
| A3 | room rule | `tree:trace_format/room_v314.py:149-184` (`votes >= threshold`, floor cells by distinct-frame votes) |
| A3 | proposal settings | `c8r:perception.py:14` (`SETTING` joint_floor .05, cap 100, dense_aliases, mask .5). `c8r:mask_kit/variantlib.py:12-25`. `tree:student_pilot/ground_sources.py:10-31` (floor .3, joint gate). `ground_v3.py:83` |
| A3 | phrase normalizer | `c8r:mask_kit/vendor/phrase.py:11-13`. `c8r:reader_policy.py:11-17` (cached-phrase universe) |
| A3 | heading rule | `tree:student_pilot/carrier_c1_routing.py:264,300` (yaw and turn printed in degrees, `wrap` :119) |
| A4 | gravity guard | `c8r:gravity_guard.py` (wraps `GeometryContract.validate`, :37-39). Installed at `c8r:geometry.py:143`. Refusals at `c8r:geometry_refusals.py` |
| A4 | reader's fallback arm | `c8r:nomdg.py:129-131` (`refusal_decode`: a rule writes the item's record and the model never runs). `tree:student_pilot/carrier_c1_decode.py:516,526` (ground fallback) |
| A4 | threshold statuses | `tree:student_pilot/carrier_c1_decode.py:118-121` (`ground_text`: frames with p ≥ tau, else `'not seen'`, where tau comes from `grounding_meta`). Gap `'not seen'` at :218 |
| A5 | cache | `c8r:nomdg.py:190,248,267-268` (`mask_cache`), `c8r:perception.py:52`. Towers do not run inside the call (A1 row above) |

## 3. Limits
- The tiny model cannot exercise the SAM 3 backend. A1 and A5 for the backend therefore rest on the static audit, and a GPU EAT-1 run on the real artifact (`out/RUN.md`) must confirm them dynamically.
- Static mode counts admission-time loads, such as the request JSON in `routed.py` and `nomdg.py`, which run before `generate()`. Dynamic A1 counts only opens after `generate()` starts.
- The allowlist and the model-code exemption (methods of declared head classes) are PROPOSED and need the cross-family refute review.
