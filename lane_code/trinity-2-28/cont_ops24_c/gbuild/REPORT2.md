C2 is blocked on SAM API source access. No point delivery, point token, or Orchard point scripts have been emitted. The builder refuses `--points` until the real constructor and coordinate convention are reviewed and pinned. The capture salvage reader, ceiling scorer, and GT adapter v2 are implemented and CPU-tested. All 45 tests pass, including all 33 round-1 tests.

The permitted SAM environments contain editable-install metadata, not `site-packages/sam3` source files. Their finder maps `sam3` to `/home/jjyeung/agent_project/agent/third_party/sam3/sam3`. That target lies outside the user-authorized read roots. An asynchronous request asks permission to read `model/geometry_encoders.py`, `model/sam3_image.py`, and directly needed point-coordinate definitions. No SAM source at that target was read. The unfinished work is the real positive-point constructor, its source-backed CPU test, runtime import/signature admission, and the resulting sealed point package and four Orchard scripts. `gpkg/point_runtime/geometric.py` explicitly refuses; it contains no guessed constructor or text fallback.

**Preserved package.** The non-points build reproduces token `a5d6f41359166` and delivery SHA256 `f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00`. The rebuilt artifact is `out2/nonpoints/delivery.tgz`; its descriptor is `out2/nonpoints/BUILD.json`. The supplied `out/` delivery, round-1 runtime files, and Orchard scripts remain untouched. The parent `--gres=gpu:1`, 16-CPU allocation, and thread settings remain unchanged. No SSH, Git, network, GPU, submission, or deletion ran.

**Capture reading.** `gpkg/capture_io.py` hashes the raw file before decoding and verifies its byte count when the receipt supplies one. It uses `zlib.decompressobj(wbits=31)`, retains newline-terminated JSON records, and discards an incomplete final line from an unfinished gzip stream. CRC/data corruption, extra gzip members, wrong hashes, and malformed complete JSON lines raise errors. Its receipt reports `salvaged`, `records`, discarded bytes, raw SHA256, and authentication status. The join, scorer, and GT converter all use this reader. The kit join CLI delegates to the same wrapper.

`gpkg/join_capture.py` accepts an optional uploaded `CAPTURE.json` through `--upload-receipt`, independently of the parity receipt. It writes `<out>.receipt.json` and prints the salvage result. A killed stream may disagree with stale record counts; that disagreement is recorded. A complete stream with a known count mismatch is rejected. Repeat records do not enter the join. Untrusted captures retain explicit flags.

**Point-mode implementation awaiting the API pin.** The added runtime shares the unchanged replay, prefill counting, call cap, geometry observer, lifter, fitted-box provider, formatter, gap program, capture location, and upload code. Its CPU-tested logic covers these operations:

- Authenticate the embedded points bytes and admit all 150 item/source-index maps. Match call names exactly, then with `stage1.name_key` only. Record unmatched or ambiguous calls without fuzzy matching.
- Compare each scene's 32 point-file RGB hashes against the staged anchor manifest, then check the binder's returned hashes before replay. Exclude every item of a mismatched capture and record the exclusion.
- Prompt each non-null frame with its point and the same `stage1.name_key` text phrase. Select the containing mask with greatest score times presence; otherwise select the greatest-scoring mask and flag the fallback. A null point produces no mask. Record every returned proposal as RLE, per-frame decisions, one track, and an explicit skipped selector.
- Perform one prompt prefill per eligible item, with recorded calls only. Run the first ten calling items again in text mode with the memo allowlist disabled. Compare those text responses against deployed responses as a noise estimate; apply no point-arm parity gate.
- Refuse an unreviewed prompt API during both CPU rehearsal and worker admission. The builder checks the API review marker before producing a package. Its point branch embeds the points and SHA pin under numeric payload names and selects `g.pw`; the non-points branch remains byte-identical.

The general-partition CPU script option is implemented in `gpkg/scripts.py`; point-mode CLI output defaults to `out_points/` and script output to `orchard_points/`. These outputs require the reviewed API and have not been generated or validated as a point delivery. `out2/POINT_BUILD_BLOCK.json` records the tested refusal. The tensor-forward tests use a prompt-constructor double, not the real SAM class. No actual point inference, staged RGB binding, Orchard entry sequence, or GCS transfer was tested.

Both supplied point files pass structural admission: 150 items, 60 captures, 298 exact call-name matches, and no unmapped calls. `out2/POINT_ADMISSION.json` records their hashes. Astra SHA256 is `fb6246cf9674c1fc40479beccaddf2dc5776927c4d280a1e6bccf8fee0ec303d`; Gemini SHA256 is `379a3b9f9570afd0b36b072dba9aa539c6ce25c39eed2c0ceeb20a7e254cfe94`. These checks do not claim that the staged RGB files match; that check belongs to runtime admission.

**Ceiling scoring.** `gpkg/score_ceiling.py` executes the hash-pinned reader's exact `official_mra` and `unit_factor` functions. It uses recorded baseline responses from `items544.json`. All 150 pinned tasks are primary and have identical `released_answer` and `ground_truth` labels; the default uses that released-label authority. `--truth` accepts explicit `{item_id: {truth: {scored: ...}}}` data. No model answer is changed.

The scorer converts printed metres to the requested unit. Missing gaps and missing capture records score zero. It compares baseline, points, and optional T1 on the same manifest population. Explicit RGB-mismatch exclusions are removed from every arm and counted. `--point-run-receipt` admits exclusions from the returned point receipt even if the capture ended before writing those items; its capture SHA must match the raw-byte receipt.

Means and paired differences share 10,000 draws of the original 46 physical rooms, seed 20261120, using Python's `random.Random` room sampling and item-weighted means. All items of a room travel together. Intervals use the 2.5th and 97.5th percentiles. Undefined subgroup draws are counted and not zero-filled or redrawn. The output includes per-object grounded-frame counts for each arm, point-minus-baseline and point-minus-T1 intervals, and text-noise records.

Object-size groups use the point-arm selected-mask fraction averaged across nonempty frames. They are prediction-derived size proxies, not GT sizes. The item-level group uses the smaller operand. A separate occurrence table and bootstrap report each question operand's own size and baseline support below three frames. Proposal masks are discarded after each record so the scorer does not retain an entire uncompressed capture.

Example after a verified return, with filenames replaced by the returned artifacts:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py \
  --point-capture POINT.gz --point-receipt POINT_CAPTURE.json \
  --point-run-receipt POINT_PARITY.json \
  --t1-capture T1.gz --t1-receipt T1_CAPTURE.json --out SCORE.json
```

Omit both T1 arguments when that capture is unavailable. No real ceiling score has been produced.

**GT adapter v2 rulings.** `gt/adapter.py convert` dispatches to `gt/v2.py`. The existing inspection API remains available for round-1 compatibility; its refusal is not the v2 conversion result. `out2/GT.json` contains all 38 available captures. `out2/GT_AUDIT.json` contains every instance's 32 visible-pixel counts, applied extent rule, binding table, cameras, and alignment status. There are 22 missing captures, nine portrait captures with unknown orientation, and 142 unique occurrence bindings among the available files.

1. Predictions are compared at the GT's 240×320 grid. The join loads the hash-pinned `routed_features.resize` function and downsamples raw proposal masks with it. Selected masks already at that grid remain unchanged. GT is never upsampled. The reader's selected-mask producer itself uses `[::2, ::2]`; the join follows the explicit ruling to resize raw proposals with the reader's resize function. Tests pin both the function and its SciPy endpoint sampling.
2. The permitted frame binder opens pinned RGB images and the mask code resizes their arrays; neither establishes a rotation/transpose mapping from portrait GT to those images. All nine `(32,320,240)` ARKit captures therefore remain U. Their native visibility counts and metadata are retained. No rotation direction was guessed, and no real captured-mask centroid comparison is available.
3. ScanNet++ (`scannetppv2`, 11 available files) lengths are doubled. ARKit (23 files) uses full extents. ScanNet (four files) carries full and half readings. The join reports both stage/evidence results and flags ambiguity; when the readings disagree, its single stage is U. Stored OBB axes are treated as rows, consistent with the supplied reader's `normalizedAxes` reshape and `ground_handcheck.py` projection.
4. Alignment fits one rigid SE(3) per capture using paired camera centers at the exact anchors, without scale. When multiple items supply cameras for a capture, one fit includes their paired anchor observations. The report retains per-anchor translation/rotation residuals, translation RMS, rotation RMS/max, and center rank. Translation RMS above 0.10 m, any rotation residual above 5 degrees, or center rank below two prevents S4/S5. Earlier S0–S3 evidence remains usable. With no real capture supplied, all real alignments are explicitly unperformed.
5. Binding applies the pinned `stage1.name_key` strip/lowercase operation to names and labels. Missing and ambiguous normalized labels remain U. No synonym, plural, fuzzy, or spatial matching is used.

The converter command actually run was:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= \
/scratch/jjyeung/envs/p1cpu/bin/python -B gt/adapter.py convert \
  --out out2/GT.json --audit out2/GT_AUDIT.json
```

After a capture arrives, use new output paths and add `--capture CAPTURE.gz --receipt CAPTURE.json` to fit the camera alignment. Then run `gpkg/join_capture.py --capture CAPTURE.gz --receipt PARITY.json --upload-receipt CAPTURE.json --gt GT.json --out JOIN.jsonl`.

**Synthetic plumbing.** `gpkg/synthetic_v2.py` reads and authenticates the supplied round-1 synthetic capture, creates explicitly synthetic NPZ annotations, converts them, and runs the join. Its output is in `out2/synthetic/`. The join observes visibility, a matching proposal, and three correctly selected frames. Its S4/S5 stage is U because the supplied synthetic cameras are stationary and cannot determine a center-fitted rotation. Separate tests recover a known rigid transform, reject a scale change and rotation inconsistency, and distinguish ScanNet S4 versus S5 under the two extent readings. No synthetic result is presented as real GT evidence.

**Validation.** `out2/CHECKS.json` records 25 package/runtime/round-2 tests, nine kit tests, and eleven funnel tests, all passing. `gpkg/check_round2.py` sets a 15 GiB address-space limit; all numerical libraries use one thread and GPU visibility is empty. Peak child RSS was 376,172 KiB. Logs are `out2/TESTS_FINAL.txt`, `out2/TESTS_KIT_FINAL.txt`, and `out2/TESTS_FUNNEL_FINAL.txt`. All 26 checked Python source files parsed. The non-points CLI rebuild after the output-path change also passed the exact delivery hash assertion (`out2/NONPOINT_BUILD.txt`).

Tests cover gzip trailer loss, incomplete final lines, CRC rejection, SHA rejection, join/scorer salvage receipts, full-denominator scoring for a partial capture, exact official thresholds and units, shared room draws, undefined subgroup draws, all 38 GT files, normalized binding ambiguity, extents, rigid alignment without scale, synthetic joining, point containment/fallback/nulls, selector bypass through the production lifter, all point-name admissions, the 150-plus-ten worker lifecycle, capture-wide exclusions, and refusal of the unreviewed API.

**Files and SHA256.** `out2/FILES.json` and `SHA256SUMS2` inventory the authored/changed source files, generated evidence, this report, and retained test fixtures from this work. The inventory does not hash itself; `SHA256SUMS2` includes the inventory hash. Test fixture copies are retained because deletion is prohibited. The source table below covers the files a reviewer should inspect; the inventory covers generated outputs and retained copies individually.

| File | SHA256 |
|---|---|
| `gpkg/build.py` | `fea6b2a28043b6e3e2485c09c96c46b626f0e065a7753396aa29f104b3ae6b06` |
| `gpkg/capture_io.py` | `faebcaada191d7a691fd8bd0a226d296b599845c1b6d7eee812e0169a7667d3e` |
| `gpkg/check_round2.py` | `65ee53a3481498c98cd83f2790a3770b06bb98f484c405756fde975f3ee85d15` |
| `gpkg/grid.py` | `2ad924ba43cfeb3abe9d2ae870bc6b1c67457d0d57ddce83d62179f1d1d45fd5` |
| `gpkg/join_capture.py` | `d492191df031da8f9087bec500e9481f77677db364be91ce77c1c91dc822b1d7` |
| `gpkg/join_v2.py` | `82ca24b9f048da603cfaea7d1d050923800705340f7d2eaf2f746fc8f604a0ff` |
| `gpkg/READER_PINS.json` | `e35ca6a6614a258a4488c81cb4bda8a9e0476b1efd4cab548c3f3c747f667dd2` |
| `gpkg/score_ceiling.py` | `ec9a5cdd4300121d741b86a8a9863226503ad2947460a50de49988d11ce334c7` |
| `gpkg/scripts.py` | `14f00b7f62e752660d2c8b8354869715d2631580026474dcfc4ecb8960e7319f` |
| `gpkg/source_pins.py` | `1ac84929a1d463a9b37cb18a7dee79ab22380e5791fdf56d21dbbc12b0f035df` |
| `gpkg/synthetic_v2.py` | `0211a9fcb5e6020978cc2cf3c5e7b1cdd38a8f60af07cc5a560f4e4572afb887` |
| `gpkg/test_points.py` | `061ea11d587b3775c0a2132df50bd47ce2fe6bbee2fb54af822c2b1cf3589bf4` |
| `gpkg/test_round2.py` | `114cc9c7ada255f3223da79609e249397bed880f8d8bcfdd7cc0fc188e02e7ca` |
| `gt/adapter.py` | `40e0e820b3911e4e620fa5f6711d1ab5aacf0335dd4aaeb0f24d36fbc4d0673c` |
| `gt/v2.py` | `42066b8b45c5bc4ead1149858100358003d83f7077ba3a3d2b713905ca8c9ff7` |
| `kit2/kit/rerun2/join.py` | `6dfbd1d0e75b4ac1862bb7a07893d09f0ad76feb9652d7baaddb2d086eca8ed7` |
| `gpkg/point_runtime/PROMPT_API.json` | `5cb3472756c6054674bc331d8fa1095b54ecab9c3b6981edceaf0c23a67dbbc7` |
| `gpkg/point_runtime/geometric.py` | `29397f4941d2b1204bd00b1a82962be1ee9e98fbebe77ce2153811b95b7a7e6b` |
| `gpkg/point_runtime/point_socket.py` | `bc8af60e8579c3941386f7417fcd15cdf2a1fb4b0c84b1aeb79a82ef699baaa8` |
| `gpkg/point_runtime/points.py` | `dd8502af1eb6a2a09fb33ff0bd90f57d41a70fcf10ffbebb3545d3bcbbb84341` |
| `gpkg/point_runtime/pw.py` | `9507debcb0d81caff64d88bb41df8bdf4c87599efb071907ebb9eb48549594e9` |


## Round 2b: current deliverables

Both packages are built and CPU-tested. All 52 tests pass: the original 45 plus seven new tests. The T1 import fix passes against the extracted delivery. C2 includes the point arm, restricted-selector arm, and ten text repeats. No live scores or GPU validation are claimed. No SSH, Git, GPU, network, deletion, submission, or `/home` read ran.

| Package | Token | Delivery | SHA256 |
|---|---|---|---|
| Fixed T1 | `a52c1dcfae7bb` | [out2/t1/delivery.tgz](out2/t1/delivery.tgz) | `ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e` |
| C2, Astra | `ab704caf7807e` | [out_points/delivery.tgz](out_points/delivery.tgz) | `0d547179098249f9d4e34e87b99ab015d69fbed6fb5904852d8d5232be19cc58` |

Each package preserves the parent's `--gres=gpu:1`, 16-CPU GPU allocation, thread settings, input pins, and five-hour walltime. The four scripts in `orchard_t1/` and four in `orchard_points/` target their respective tokens. Both CPU checks request `--partition=general`, with no GPU request. `out/`, `out2/nonpoints/`, `orchard/`, and `orchard_r1/` remain earlier artifacts; use the paths above for this round.

### Import correction and evidence

`g.w.bind_reader_root` imports `h1eval`, rejects every already-loaded foreign `e2e_reader*` module, inserts the full `p/b` reader first, and invalidates import caches. T1 and C2 call it before `settings_for`, `prepare_runtime`, and reader imports. Replay asserts that every loaded reader module's file lies under `p/b`. The dispatch process also binds the reader before importing its memo settings.

`gpkg/import_smoke.py` extracts each real delivery's outer archive and its `0.tgz` into a fresh directory under `work/`. A fresh isolated interpreter starts with exactly `[p/b, p/tree, p]` prepended, matching entry action 3. It runs the worker/replay imports, `settings_for`, `prepare_runtime`, dispatch preparation, and the runner/operator/job module imports. A separate `-I -S` process loads the actual operator helpers and validates job inputs using only the standard library.

The interpreter is `/scratch/jjyeung/envs/p1cpu/bin/python`, with torch `2.11.0+cpu`. The original delivery, SHA256 `f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00`, fails with the reported `cannot import name 'parity'` error from `h1eval/reader_core`. Fixed T1 and C2 pass; their receipts enumerate all loaded reader paths under `p/b`. The standard-library operator/job checks pass for all three deliveries. See `out2/IMPORT_{LEGACY,T1,POINTS}_R2B.json`.

### Point and control behavior

The five supplied SAM reference files are SHA-pinned in `gpkg/point_runtime/PROMPT_API.json`. The real `Prompt` constructor has nine optional parameters, all defaulting to `None`. A positive point uses float32 embeddings `[1,1,2]`, a Boolean padding mask `[1,1]` containing `False`, and int64 labels `[1,1]` containing `1`, all on the tower's device.

The encoder documents normalized coordinates in `[0,1]`, converts them to `[-1,1]` for `grid_sample`, and unbinds them as `x,y`. Its default positive labels are ones. The supplied builder enables direct projection, pooling, and positional encoding for points. CPU tests execute the complete unchanged `Prompt` class and `_encode_points` method extracted from the reference AST. A nonsymmetric 2×2 grid verifies that `(0.75,0.25)` samples the top-right pixel. This avoids importing missing relative dependencies from outside the supplied reference directory.

Before replay, both the staged CPU rehearsal and worker verify the source hashes, import `Prompt` from the staged SAM tree, reject foreign SAM modules, and compare the exact constructor signature. The detector also checks the loaded geometry encoder. The deployed `Sam3Tower` has no `predict_inst` and builds with `enable_inst_interactivity=False`; a disabled detector point encoder therefore refuses.

The point detector preserves the text phrase, stable score ordering, K1 joint floor `0.05`, cap `30`, bilinear logit resize, reader canvas resize, and selected-mask downsampling. It selects the highest score×presence among retained masks containing the point. If none contains it, it selects the best retained mask and records the fallback; if K1 retains none, it returns no mask. Null points skip detection for that frame. Selected frames form one track. The selector is explicitly skipped; the deployed lift, fitted box, formatter, and gap program remain in use.

The restricted-selector arm runs the deployed text detector, early lift, linking, candidate features, and head on the full original pool. It checks points against the raw member masks at their own frame indices. Only candidate tracks with at least one containing member are eligible. It chooses the largest original candidate logit among eligible indices, preserving candidate order and ties. No eligible track returns null. The capture records original logits, eligible indices, exact/normalized name mapping, and the chosen original index.

The worker performs 150 point replays, 150 restricted-selector replays, and ten fresh text replays of the first calling items. Each replay has one prefill and no answer decode. Pass indices are 0, 2, and 1 respectively; arm labels disambiguate them. Main/control passes share only the admitted G3T memo. Text repeats disable memo reuse. The same observer records masks, tracks, lifts, boxes, responses, timings, and memory. C2 applies no baseline parity gate because its ground responses intentionally differ.

Both intervention arms use exact call names, then the reader's `name_key`; unmatched/ambiguous names remain explicit. Both use the embedded points SHA and compare all 32 anchor RGB hashes before replay, then check the binder's returned hashes. A mismatched capture is excluded from every scored arm and counted.

The default CLI is:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/build.py --points
```

To select the supplied Argon file, pass its path to `--points` and a distinct `--out`. Both files pass admission tests. The emitted package above embeds Astra, SHA256 `fb6246cf9674c1fc40479beccaddf2dc5776927c4d280a1e6bccf8fee0ec303d`.

### Scoring and sparse-item definition

`gpkg/score_ceiling.py` reports recorded baseline, points, restricted selector, and optional T1 on the same manifest. It checks capture hashes, identities, anchor indices, call order, and served flags. It converts printed metres to the requested unit and executes the pinned reader's exact `official_mra`. Missing gaps/records score zero. Every arm has paired differences against baseline; points also retain the optional comparison against T1.

All means and contrasts use the same 10,000 draws of the original 46 physical rooms, seed `20261120`, with item weighting. Explicit RGB exclusions reduce every arm's denominator together. Output records missing-arm counts, the paired-population completion flag, run failure, exclusions, text-repeat differences, and per-object frame counts.

The requested 93-item subset consists of items with at least one served ground response that explicitly prints one or two frames. Counting null statuses as zero would produce 100 items. The scorer uses 93 and reports the seven additional null-only cases separately. The clarification received no answer before this build finished.

Sparse visibility comes from `gt/` v2's bound instance pixel counts at the same 32 valid anchors. Bins are 0, 1–2, ≥3, and no GT. Missing captures, incomplete anchors, and missing/ambiguous labels enter no GT. Portrait orientation uncertainty does not change visible-pixel counts. An item with two sparse objects can enter multiple visibility bins, but only once per bin; these bins are not disjoint. Current bin counts are 1, 18, 33, and 46 respectively, covering the 93-item union.

The synthetic scoring test supplies all 310 records with copied baseline responses, so all paired differences and their intervals are exactly zero. It also supplies optional T1, validates all visibility categories, and checks the 150/93 denominators. `out2/SYNTHETIC_SCORE_R2B.json` is plumbing evidence, not a point-arm measurement. The recorded baseline's supplemental gap score is 58.6 percent; no real point/control score exists yet.

Example after a return:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py \
  --point-capture C2.gz --point-receipt C2_CAPTURE.json \
  --point-run-receipt C2_PARITY.json --gt out2/GT.json --out SCORE_C2.json
```

Add `--t1-capture T1.gz --t1-receipt T1_CAPTURE.json` when available. `join_capture.py` skips the control and noise passes when producing a point-arm GT join. All capture readers retain raw-byte SHA verification and trailer-less gzip salvage.

### Runtime forecast and comparison limits

`out2/FORECAST_R2B.json` estimates about **167 GPU-minutes**, with an unmeasured planning range of **84–250 GPU-minutes** on one GPU, including CPU waits. The package reserves at most 300 GPU-minutes. Its worker deadline is 215 minutes from job start, reduced by staging time; the slow end can exceed it. Job 173618 loaded no models, so it provides no throughput calibration.

The workload has 310 prefills, 2,031 positive-point detector forwards, 9,536 restricted text forwards, 640 noise text forwards, and 9,856 SAM image encodings. The forecast lists every assumed rate. Its G3T estimate allows up to 130 fresh computations while caching works; verification failures could force more. The unchanged 1.9 GB capture cap allows about 6.13 MB compressed per record across 310 records. Neither runtime nor capture size has been measured with weights.

The following conditions limit or invalidate a purchase comparison:

- An incomplete arm, deadline stop, output-cap failure, or salvaged partial capture creates missing-record zeros. A score can still be produced, but it cannot establish a complete paired result.
- RGB exclusions change the target population. Missing or ambiguous GT limits visibility strata; overlapping visibility bins must not be summed as disjoint groups.
- The point arm changes proposals, track construction, and selection together. It is a ceiling for the specified point-guided pipeline. The restricted arm isolates selection eligibility conditional on deployed text proposals and links.
- Points can miss an object, and the highest retained mask can fall back to one that misses its point. Fallback and no-mask rates must accompany scores. The closed model's source/null errors remain part of the intervention.
- The detector API, weights, checkpoint step, reader source, text, frame bindings, serving rules, and unit/truth authority must match. The runtime refuses pinned-source/API differences, but no staged Orchard SAM import, model load, forward pass, or final RGB admission ran here.
- Ten text repeats estimate only a small sample of execution noise. Large differences from recorded baseline, nondeterminism, or G3T memo verification failures need review before attributing changes to grounding.

### Validation and file hashes

The final bounded check was:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= \
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/check_round2.py --tag R2B
```

It passed 32 package tests, nine rerun-kit tests, and 11 funnel tests: **52 total**. It imposed a 15 GiB address-space limit and one BLAS/OpenMP thread; peak child RSS was 392,624 KiB. It parsed 34 Python sources. Both final deliveries passed the CPU smoke checks, while the original delivery failed as expected. Eight shell scripts passed `bash -n`; their embedded Python compiled, and embedded delivery/BUILD bytes matched the final artifacts.

The initial local run exposed two test doubles that lacked reader provenance; those tests now isolate their mock-only import guards, while the real-payload smoke checks exercise the guards. No cluster-killed work was retried. Temporary test/extraction directories remain under `work/`; no files were deleted. Each BUILD descriptor inventories all sealed payload files. The table below covers changed deliverable sources and emitted artifacts. `out2/FILES_R2B.json` also records file sizes and this report's final hash; `out2/REPORT2_R2B.sha256` records the report digest.

| File | SHA256 |
|---|---|
| `gpkg/runtime/w.py` | `2a2894f1e1fc40c5d90c87017c5745d2c6f4d024f1358fddbab60eb60b50f857` |
| `gpkg/dispatch.py` | `5deb8e0d98a3af632274b67fedd5ea6136745d4f49178686df53001518b6706d` |
| `gpkg/build.py` | `9ff0b5b7a5db4ccb9499c0cf65b68151fd3920a79c893765515adb568fe19aed` |
| `gpkg/import_smoke.py` | `62d64d4147d5a77b340493d4affcc84ea19966aba550dbd0637383e9f7277a5e` |
| `gpkg/check_round2.py` | `b0c53684abdc62e22c32191658aaa95138058c5e35d85e4edb1a57aa3b0351bf` |
| `gpkg/point_runtime/geometric.py` | `6efc29f2faca1e2e0222dfeb219f4c4c2706c2dc93b899c8023f9cda9d742d37` |
| `gpkg/point_runtime/PROMPT_API.json` | `8ed7c5ed63d0d7e962886a1d97bd3d49899ba4a321470cc6108126a0aa13e1a1` |
| `gpkg/point_runtime/point_socket.py` | `11e614b780f2de45050efd49db65d2ac898b93b3e9467821117e875109be11c2` |
| `gpkg/point_runtime/pw.py` | `6fdf45227073751c3e7ad151d857122ed017ddd1627ae8a13e4efb4ac960cf53` |
| `gpkg/point_runtime/restricted.py` | `067ef11e7d7bbc5668ca16888993afb068581c271af04ddbd07ebebfe4b5ed75` |
| `gpkg/score_ceiling.py` | `3f51c6ac2ac9412b20a73461524ecf68c72ee4c14fd1e62c925007f6b5d638c6` |
| `gpkg/join_capture.py` | `bfc287d5ab5d8e35f0f3ada303919ce4a941b5057d11a44bf482bc6d2fa0974a` |
| `gpkg/test_package.py` | `93e10d28bbcb64c2996ed4fc1a21cafee07df0583679d3f0026bda00bfc8e626` |
| `gpkg/test_points.py` | `500f05e8855f01d06369b0be2ab62d0023970d6a9018088ffa9e7be0a34cfa0c` |
| `gpkg/test_round2.py` | `46bd316e603fb1ab6d508b626bf2077ad24712d31bf06a86281dcb7215b6d318` |
| `gpkg/test_runtime.py` | `caaedafda2aa4c9e26475f0f4d608af9bc9c5d6fc341b0baf6d0a5b709db23d7` |
| `gpkg/test_round2b.py` | `9386d1120b0fe766ccb688158fd091a75de74b93aaa7ffac20e4353c84622c46` |
| `out2/t1/delivery.tgz` | `ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e` |
| `out2/t1/BUILD.json` | `5456d17123d3d0a58944972c67ca34ce221f672108b69da2963a9002c79afa0e` |
| `out_points/delivery.tgz` | `0d547179098249f9d4e34e87b99ab015d69fbed6fb5904852d8d5232be19cc58` |
| `out_points/BUILD.json` | `55fb9a048104ca9260e7169f669a96101d69b7933b792e231c9554fd2e17d326` |
| `out2/IMPORT_LEGACY.json` | `4822d6e3584a0eab70ef89e4afbdb825127dae0dc60cd27c842f81fe055535a1` |
| `out2/IMPORT_FIXED.json` | `bde9a982ee5a9d997a47d87bfe31e64e5c34a9332b1f847bdd87b445167ae7fb` |
| `out2/IMPORT_LEGACY_R2B.json` | `e1337f5e1e85f73ff542d15c80e26c27f34c4ea90c4855c15966bbc548f0ec6f` |
| `out2/IMPORT_T1_R2B.json` | `c616d4d4008b3a7de34d04e5f016eedb74b1ee3a4e8461b0ff9901783d4b2424` |
| `out2/IMPORT_POINTS_R2B.json` | `919d655f95a1a5241c9a6107fbaac58a282228e080ad67fb977ecd068c8d34db` |
| `out2/FORECAST_R2B.json` | `4f9a110d86cef8aec6353351539e416b14a7d0c0a57ad33cec8947c35fcb982c` |
| `out2/SCRIPTS_R2B.json` | `56f26a250a47a2ed5fcc32b30d4765acd5329683162cb5fe0c5702a9db526f02` |
| `out2/SYNTHETIC_SCORE_R2B.json` | `996fbb7d7bed3d358700dc7b4a2821cfa39df8fdd798620f5ef4507018414537` |
| `out2/CHECKS_R2B.json` | `d31308212d55d4df10ae2b4451c234cbab454aa25494f22a37544c134cd6708a` |
| `out2/TESTS_R2B_INITIAL.txt` | `41955bd94acf8047b144ce4bb1cd8a02d5bb9eda76a14f17bb5ff663e7c28da5` |
| `out2/TESTS_R2B_SECOND.txt` | `38d51bc1de4e7a14bb80cf65c5ade1b0a86606775801b8c9b8a8e33eb6d59b8d` |
| `out2/TESTS_FINAL_R2B.txt` | `2a02cad922bf6c11bba04f61edcb89ed958329b506e0a5c71d569d82a36253d2` |
| `out2/TESTS_KIT_FINAL_R2B.txt` | `cab6906ba9be7ce1b658189a3fd01017a2677bc4f8c7e2406e2d83ce1b1c3be7` |
| `out2/TESTS_FUNNEL_FINAL_R2B.txt` | `a95483b11e731673b9df231736f4f4747666a1011414997e569a9dd0da4cf37a` |
| `orchard_t1/o_check_sub.sh` | `9bf644f5fa285ddd006ef0db1ea8b422c1c074edf1f7c8f385aae3bb75c09dd1` |
| `orchard_t1/o_cpu.sh` | `03cea7afaa8ef4d713e2ba0ebde1b47418e92d8958ec1cbc2c81af5c647573fc` |
| `orchard_t1/o_fetch.sh` | `65e7c7d2f4cef174b9a5751687028ddc9e3d81b2a3736a6527b790d926956619` |
| `orchard_t1/o_place.sh` | `a08dd54a02c3e90ee3950f180948fda4c1a25d86a6c00e6bb5a68fb0b7bec19d` |
| `orchard_points/o_check_sub.sh` | `eefdffd5b02d69b99fe3940c291b2016b020c8ee7f10c22c0db0de78cdaad74c` |
| `orchard_points/o_cpu.sh` | `3f76b256585994f6713a338de15f843e22407347f80cc44c294e891ff209f8a8` |
| `orchard_points/o_fetch.sh` | `7b5fe2d27575e9e9602bd20aadeb124d3f1fd25f3279e3ace9584ac157c96035` |
| `orchard_points/o_place.sh` | `2f7e01fc7ea01a3f7d1b10edbbd936f2040580be4012bfe66550d137edf6f1ca` |

Recorded at 2026-11-20T04:55:09.244750+00:00.
