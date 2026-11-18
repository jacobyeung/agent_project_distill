# EAT-1 baseline: next-leg tree, build 5 (seal ba346bd9) — GF-1 passes A1 and A5; the routed types inherit C8r's A2, A3 and A4 failures

GF-1 passes the clauses that concern the tower. Its frozen G3T tower is a registered module, and it runs inside the call, once per item, during the routed prefill. Perturbing the tower changed 4 of 4 naming responses and no others. A1 passes only when the claimed artifact lists the G3T weights by sha256, because the export leaves them out (§2). The next-leg tree leaves the read path between heads and tokens unchanged from the sealed tree b01ce449. Every routed type therefore inherits C8r's A2, A3 and A4 failures (`out/BASELINE_C8R.md`), and the distance and room types also inherit its backend failures under A1, A3, A4 and A5.

Package: `tree_rebuild_b5_ba346bd9.tar` (sha256 bc31a06d…, equal to the copy on trinity-1-3), unpacked at `work/nextleg/b5/work/tree_r1`. `b5:` paths below are relative to that tree. Build 6 was still running at 13:30Z; §4 lists what its contracts r6 add.

## 1. What changed on the read path relative to b01ce449
Of the 33 read-path tree files in the C8r tier-1 scope, the build changed only three:
- `b5:evalpath/runtime.py:55-56` and `b5:evalpath/run.py:143-144,208-209`: the legacy reader entries (`load_model`, `load_request_items`, `run_worker`) now raise `unsupported_entry`. The next leg has no admitted reader in this tree yet, so any GPU EAT-1 run needs one (`out/RUN.md`).
- `b5:student_pilot/carrier_c1_routing.py:183-185`: R2 event rows. This is training-row code.
The decode loop (`carrier_c1_decode.py`, `carrier_c1_batch_decode.py`), the calculator, the grounding backend (`s1_grounding`, `ground_v3`, `ground_sources`, `candidate_policy`, `native_selection`), lifting, the box, room and tower-scale modules all equal the base byte for byte. The static scan of the 33 files (`work/nextleg/static/SCAN_READ.json`, `out/BASELINE_A2_TREE_FINDINGS.md`) gives 571 findings: constant 290, threshold 76, status 52, guard 48, table_load 32, data_file 20, response_outside_model 17, unit_conversion 15, cache 12, except_substitute 9.

## 2. GF-1 (geometry fusion)
| Clause | Verdict | Evidence |
|---|---|---|
| A5 (iii) tower inside the call | **PASS** | `b5:student_pilot/carrier_c1.py:156` registers `G3TEncoder` as `auxiliary_heads.geometry_encoder`, and `:162` registers `Fusion` as `auxiliary_heads.gf1`. The routed prefill calls `model.geometry_features` and `model.patch_injection` (`b5:student_pilot/carrier_c1_decode.py:328,360`). Dynamic run: `module_runs tower:g3t = 1` per called item. |
| A5 (ii) perturbation | **PASS** | g3t perturbation changed 4/4 naming responses and 0 others. pose_head changed 4/4 (`work/b5_gf1_tiny/run6/EAT1_REPORT.json`). |
| A5 cache | note | `b5:student_pilot/gf1.py:223-232` is a per-row `ClipCache` that memoises the live tower output within one row, keyed by tensor versions. It is not a precomputed cache, but the scanner flags it. The reviewer decides. |
| A1 one artifact | **conditional** | The export drops `geometry_encoder.*` from `heads.pt` (`b5:student_pilot/carrier_c1_run.py:2002-2006`) and reloads the encoder from its pinned path (`carrier_c1_run.py:814`, `g3t_online.py:199-204`, which verifies the sha256). A1 passes only if the claimed artifact manifest lists that weights file by sha256 with role `tower`. The export directory alone is not one artifact. |
| A3 | model code | The 35 constants in `gf1.py`/`g3t_online.py` (image size 518, layer indices, pooling) run inside module forwards or methods of the registered tower and connector classes. `dense_frames=64` is a config parameter (`gf1.py:12`). |

The dynamic GF-1 run used the tree's own tiny GF-1 fixture (`tests/test_gf1.fixture`) and the adapter `eat1/adapters/gf1_tiny.py`. GF-1's output layer is zero-initialised, so the adapter adds seeded noise as a stand-in for trained fusion weights. It also unbinds trace version 3.14, which otherwise demands a live ground session. Result: A1 PASS, A5 PASS, and A2, A3 and A4 FAIL through the decode loop.

## 3. What the routed types inherit
| Routed type | Path | Inherited failures |
|---|---|---|
| camera displacement, movement direction, rotation | pose head → `respond()` → `OwnGeometry` text (`carrier_c1_decode.py:214`, `carrier_c1_routing.py`) | A2: Python writes the responses (`carrier_c1_batch_decode.py:142`, 154 injected tokens on 4 called tiny items). A3: radians printed as degrees (`carrier_c1_routing.py:264,300`) and 32 frames hard-coded. A4: typed `error:` responses (`carrier_c1_decode.py:244,248`) |
| object absolute distance | `s1_grounding.build_backend` → SAM 3 cache → selector → depth cut → G3T lifting × tower scale → box policy | every C8r A1/A3/A4/A5 backend row (`out/BASELINE_C8R.md` §2), unchanged |
| room size (direct for the next leg, ORCH 1227Z; a call from a warm-started student goes unserved) | b5 still has the backend and room rule (`trace_format/room_v314.py:149-184`) | as above, whenever a room call is served |
Export and frame count: `artifact.json` writes `anchors=list(range(1,33))` (`carrier_c1_run.py:2026`). The decode, calculator and pose readout refuse anything but 32 frames (`carrier_c1_decode.py:83,91,151`, `carrier_c1.py:590`, `p3_printed_calculator.py:159`). USER ruling 2 (frame count 32 or 64 as a parameter) therefore needs these sites changed; GF-1 already takes 64 dense frames. The MDG export stores a calibrated `tau` as artifact metadata (`carrier_c1_run.py:2011`), and `ground_text` thresholds on it (`carrier_c1_decode.py:118-121`). That tau is a fitted threshold outside any head (A3).

## 4. Expected from build 6 (contracts r6; `distill_design/CONTRACTS_REBUILD_20261115.md`), to verify on its final package
- `validate_up_convention` inside `GeometryContract.validate`: a guard (A4).
- `heading_plane_min` (config-bound, 0.3): a threshold outside a head (A3).
- `heading unavailable` status: an A4 status literal unless a head formats it.
- `student_pilot/phrases.normalize_phrase`: still a phrase normalizer outside the weights (A3).
- MDG `points_cut`: the depth cut stays (A3).
Rerun: `python -m eat1.scan $(sed "s#tree_r1#<b6 tree>#" work/nextleg/static/SCOPE_READ.txt) --json …` plus the two tiny adapters with `tree=<b6 tree>`.
