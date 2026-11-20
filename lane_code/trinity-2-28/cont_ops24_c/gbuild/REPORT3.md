# 64-frame ground-call package

The package is built and CPU-tested. No GPU run or score improvement is claimed. Nothing was submitted, and T2 job 173625's package was not changed. No SSH, Git, GPU, network, or deletion command ran.

The primary population contains **104 items on 31 captures**, spanning 28 physical rooms. The control population contains **46 items on 29 captures** with only 32 frames. The scorer resamples the original 46-room population for every contrast, including subgroup contrasts.

| Artifact | Value |
|---|---|
| Delivery | [out3/dense/delivery.tgz](out3/dense/delivery.tgz) |
| Token | `a883c5c365aee` |
| Delivery SHA256 | `36a9fdb55564a3a7cfd21dee297607a60776c58991e2ebfd8272c2beaef35d7e` |
| Payload SHA256 | `e94006f6f7fc7830ffadf6ca38a33f37aa586a7570db1b162f0ff2dfc32e4de0` |
| Plan SHA256 | `e2ca1948a16a88d8f9b49cba67164f0c58f3ec704e2d4eccda918368b1add91f` |
| Delivery / installed bytes | 5,321,304 / 5,356,276 |
| Allocation | One GPU on general, `05:00:00`, inherited 16 CPUs and 200 GiB host memory |

The package retains `--gres=gpu:1`; the worker checks that the assigned device is an H100 before loading the VLM. The input archives, export pins, step 544, answering frames, call order, serving cap, text detector, selector weights, lift rule, box fit, and gap program remain the deployed ones.

## Geometry and runtime

[`FrozenG3TTower.run`](work/payload/tree/student_pilot/tower_read.py) aggregates all native frames and computes all pose rows. It retains backbone layers 4, 11, 17, and 23. Its depth/point loop selects only the 32 anchor slots. **The non-anchor depth and point grids were never computed; they were not discarded.**

[`g/d.py`](gpkg/dense_runtime/d.py) preserves the original four batches of eight anchors, then runs four additional depth-head batches and four additional point-head batches for a 64-frame capture. These batches use the same retained backbone tensors. They require no second backbone or camera forward. The sampled grids are reordered into native-frame order; the anchor grids remain separately available for the original scale calculation.

The answering prefill and scale calculation still use 32 anchors. The checkpoint's gravity output is unchanged. Camera-call services retain the anchor geometry because their `OwnGeometry` contract requires 32 rows. Only the ground/gap session receives the extended geometry and SAM frames.

Each captured 64-frame geometry includes `anchor_geometry_deltas`: byte equality and maximum absolute difference for K, canvas transform, metric poses, and scaled depth, comparing the anchor projection with the corresponding rows of the full projection. These are comparisons within the same forward, not against an archived GPU run. The scorer lists changed and unmeasured items. The CPU tower test separately compares the original and extended tower runs and finds identical anchor poses, depths, confidence, and points with deterministic tensor heads.

All changes live in the derived `g/` overlay. Runtime authentication checks 17 original source files before installing extensions. The sealed `GeometryContract.validate` remains unchanged and passes its original source-hash check. A separate reader subclass changes only its frame-count shape checks; its other geometry guards remain active.

The overlay extends FrameMap, ProfileGeometry construction and `has()`, candidate lifting and visibility, `routed_features.Geometry`, selector normalization, and box serialization/parsing. StageOneSocket already accepts a frame count and mask shape; its existing producer now receives N=64. The extra formatter checks matter: both printing and box ingestion otherwise reject support beyond frame 32.

Displayed indices are **1–N in bound native-frame order**. `source_indices` remains the original 32-anchor identity; `ground_source_indices` and `anchor_slots` supply the extended mapping. Responses intentionally differ from a 32-frame read. No baseline frame-parity gate applies.

The worker performs 150 original prefills and replays recorded calls without answer decoding. It then repeats the first ten calling items in the same arm, disabling perception memo reuse. The repeat compares against the arm's main pass. Captures retain proposals, tracks, selector inputs and complete logits, selected masks, lift summaries, boxes, geometry, timings, and memory. The 32-frame-only items are explicitly flagged.

## Selector distribution

The selector retains all 58 fields and its original weights. Its own [`selector_inputs.py`](work/payload/b/heads/selector/sl118/selector_inputs.py) defines these changes:

| Field | Extended definition | Fixed-support effect at N=64 |
|---|---|---|
| `name_frames_frac` | Frames with a proposal score ≥0.3 / N | Half its 32-frame value |
| `member_frames_frac` | Distinct track-member frames / N | Half its 32-frame value |
| `frame_span_frac` | Last minus first displayed index / (N−1) | Denominator changes from 31 to 63 |

This is a selector-input distribution change. Doubling observations at similar coverage can preserve the fractions; keeping the same observations lowers them. `name_max_score_mean` already averages over every raw frame, so additional empty frames also lower it. Support, members, visibility, detection counts, candidate counts, and ranks retain their existing log1p transforms. Extra views can change those counts, camera-center summaries, reprojection coverage, competition, and the selected identity. This arm tests the deployed pipeline with more observations; it does not isolate visibility from selection.

## Scoring and receipt fixes

[`gpkg/score_ceiling.py`](gpkg/score_ceiling.py) preserves the 93-item explicit 1–2-frame table and adds the requested 100-item `<3` served-call cohort. Null/failed ground responses contribute zero printed frames. GT visibility uses the original 32 anchors, without inventing annotations for added views.

| Cohort | Items | GT 0 | GT 1–2 | GT ≥3 | No GT |
|---|---:|---:|---:|---:|---:|
| Explicit 1–2 printed frames | 93 | 1 | 18 | 33 | 46 |
| Fewer than three printed frames | 100 | 1 | 18 | 33 | 53 |
| Primary population, fewer than three | 65 | 1 | 8 | 18 | 41 |

An item can enter multiple GT bins when its sparse objects differ, so the columns overlap. All seven additional zero-frame items lack usable GT bindings here; they enter **no GT**, not the GT-zero bin.

The exact forced-kill fallback receipt is accepted as **incomplete**. Capture bytes must still match the independent upload receipt's SHA256 and byte count. Any supplied but wrong run hash or mode still fails. Unknown incomplete receipts fail. Trailer-less gzip salvage retains complete records, reports salvage, and cannot establish a complete run. The fallback in the running point package remains byte-identical.

The dense scorer reports baseline, dense arm, and optional T1, with paired differences, per-object grounded-frame counts, primary/control tables, and sparse visibility strata within the primary population. Every table uses the same 10,000 room draws, seed `20261120`, with item weighting. Missing records/gaps score zero and completion flags expose partial populations. Repeat differences compare dense main versus fresh dense repeat.

The recorded baseline supplemental gap score is 58.6%; the primary subset's baseline is 58.3654%. The synthetic score artifacts copy baseline responses to test joins and statistics; their zero differences are **not experimental results**.

After an authenticated return:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py \
  --dense-capture DENSE.gz --dense-receipt CAPTURE.json \
  --dense-run-receipt PARITY.json --gt out2/GT.json --out SCORE_DENSE.json
```

Add `--t1-capture T1.gz --t1-receipt T1_CAPTURE.json` when available. The point CLI remains available with `--point-capture`, `--point-receipt`, and `--point-run-receipt`.

## Memory and timing forecast

[`out3/FORECAST.json`](out3/FORECAST.json) records the code counts and all assumed rates. The workload has 160 prefills, 8,704 SAM image encodings, and 17,408 text-grounding forwards. With working memo verification, the manifest implies 88 fresh G3T computations and 1,888 extra depth/point frame pairs. Disabling memo reuse can increase these to 159 and 3,616.

Scaling the observed 77 H100-min full read by the mixed workload's frame exposure gives 140.65 minutes. Adding the extra head batches gives approximately 141–144 minutes. This scaling includes answer-decode work that replay omits, while underrepresenting potentially quadratic linking costs. A separate component model gives **78–238 H100-minutes**. Plan for **about 150 H100-minutes**, not a measured bound.

The inherited worker deadline is 215 minutes after job start, reduced by staging. The 238-minute high estimate can exceed it. The five-hour allocation reserves time for capture upload/readback and normal return. Capture compression has a 1.9 GB cap, averaging 11.875 MB per record across 160 records.

Memory should fit an 80 GB H100 under the deployed precision and efficient-attention path, but no GPU admission was measured:

| Component | Planning GiB |
|---|---:|
| VLM and auxiliary weights | 18–24 |
| G3T FP32 weights | 5.2–6.5 |
| SAM weights | 2–4 |
| Prefill cache, heads, private encoder workspace | 6–18 |
| Active tower workspace, including retained layers | 4–12 |
| Allocator headroom | 4–8 |
| Total | **39.2–72.5** |

G3T's four retained tensors occupy about 1.342 GiB at 64×1,374×2,048 BF16 elements per layer; baseline already incurs that allocation on these captures. Both heads retain their batch size of eight. SAM encodes and detects one image at a time and stores pyramids on the CPU. A conservative four-level FP32 pyramid estimate is 13.45 GiB host memory at 64 frames. The operator's host-memory admission includes both dense and anchor G3T grids and retains the 200 GiB allocation.

Efficient attention is essential: one explicit 16-head global attention matrix at this sequence length would occupy about 230 GiB even at two bytes per element. Precision changes, kernel fallback, unexpected auxiliary copies, or allocator pressure can invalidate the fit estimate.

`metadata/8_64.json` and `8_32.json` record the first calling item at each count: seconds, allocated/reserved peaks, GPU free/total memory, initial VLM load time, and remaining worker budget. A failed first replay records its error and available peaks. Optional configuration limits `first_item_max_seconds` and `first_item_max_reserved_bytes` stop after that record. STOP and deadline behavior remain active. No first-item GPU measurement exists yet.

## Validation and package use

The final bounded run passed **37 package/runtime tests, nine kit tests, and eleven funnel tests**, including all earlier tests. Five additional producer checks run inside the round-three suite. Peak child RSS was 836,512 KiB; the address-space limit was 15 GiB, numerical libraries used one thread, and GPU visibility was empty.

Evidence: [CHECKS_R3_FINAL.json](out2/CHECKS_R3_FINAL.json), [full tests](out2/TESTS_FINAL_R3_FINAL.txt), [producer tests](out3/PRODUCERS_FINAL.txt), [rebuild/import checks](out3/REBUILD_AND_IMPORT.json), and [script checks](out3/STATIC_CHECKS.json). Tests exercise exact 32-frame arrays/features/responses, every active producer through frame 64, preserved anchor head batches, scale inputs, camera-service separation, geometry guards, source authentication, capture validation, fresh repeats, and first-item failure records. Package checks use the parent's own input-pin helpers and fresh-process imports.

| Preserved delivery | Rebuilt SHA256 |
|---|---|
| Original T1 `a5d6f41359166` | `f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00` |
| Fixed T1 `a52c1dcfae7bb` | `ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e` |
| Point package `ab704caf7807e` | `0d547179098249f9d4e34e87b99ab015d69fbed6fb5904852d8d5232be19cc58` |

`gpkg/build.py --dense` builds this arm. `--legacy-t1` deterministically repacks the authenticated frozen original T1 members; it preserves that historical package, including its known import limitation. The ordinary builder retains the fixed T1, and `--points` retains the point package. Rebuild tests write to fresh temporary destinations.

The four scripts in [`orchard_dense/`](orchard_dense/) place, run the CPU entry check, check/submit, and fetch. CPU admission also authenticates and compiles the overlay and exercises 32/64 geometry/socket shapes. The normal job-finally path uploads even a partial capture to GCS, authenticates readback, and returns CAPTURE/PARITY metadata. The capture stays outside the small returned archive.

These are operator commands, **not commands run here**; wait for each job/check to finish before its dependent step:

```bash
ssh orchard 'bash -s' < orchard_dense/o_place.sh
ssh orchard 'bash -s' < orchard_dense/o_cpu.sh
ssh orchard 'bash -s' < orchard_dense/o_check_sub.sh
ssh orchard 'bash -s' < orchard_dense/o_fetch.sh
```

The submit guard refuses while another general job is running. Retrieve the large capture separately through the governed transfer workflow using its returned generation and SHA256; the existing pull script refuses to overwrite its fixed `cap/0.gz` destination.

The comparison cannot establish a gain if the primary population is incomplete, binding/pins differ, the wrong GPU/precision is used, or resource limits stop the run. Nonzero anchor deltas make geometry part of the intervention. Selector distribution changes, newly exposed same-name instances, memo verification failures, and execution noise must accompany interpretation. GT strata remain limited by missing/ambiguous annotations and describe only anchor visibility. Ten repeats provide a small noise sample. Real model loading, GPU execution, runtime, memory, and score improvement remain unverified.

[`out3/FILES.json`](out3/FILES.json) and [`SHA256SUMS3`](SHA256SUMS3) inventory the changed sources and deliverables. [BUILD.json](out3/dense/BUILD.json) inventories every package member. Failed-check logs and temporary fixtures under `work/tests/` and `work/imports_*` were retained; no cleanup ran.
