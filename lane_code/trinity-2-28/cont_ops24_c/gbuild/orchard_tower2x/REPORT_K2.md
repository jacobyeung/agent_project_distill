The kit is built for ten arm-A controls. **All ten captures lack arm B in the existing dense manifest; arm C is unavailable.** No frames were substituted. The requested coverage comparison cannot yield confirm/refute evidence with these assets.

| Captures | Served / available frames | B / C |
| --- | --- | --- |
| Failing: 41069054, 41291643, 42899535, 45663051, 47332598 | 32 / 32 each | unavailable / skipped |
| Reference: 41159782, 45261332, 43828368, 43649603, 44358634 | 32 / 32 each | unavailable / skipped |

`AVAILABILITY.json` inventories the local mirrors of `/project/community/jjyeung/a52c1dcfae7bb`, `ac85ad201020f`, and `a883c5c365aee`. All three carry the same DENSE_MANIFEST SHA256, `4fef3415587c918f422515c0cf74565b77a1f90f4ef63d77c73718364e7fbc10`, with only the 32 anchors for each requested capture. Live remote inventories and PNG decodability were not checked here. The runtime checks each PNG's SHA256, decodability and native size before inference.

The optional existing `work/payload/inputs/r0dev/FRAMES_MANIFEST.json` covers ScanNet++ only. Its independent 32/64 selections do not supply these ARKit captures or a nested 96-frame arm. C requires B plus 32 more frames; B itself is absent. No claim is made about unregistered files elsewhere on Orchard.

The served reader takes its extra frames from [parity.bind_item](../work/payload/b/e2e_reader/parity.py:57), which loads [DENSE_MANIFEST.json](../work/payload/b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json), resolves the recorded PNG paths under the existing `d/f` directory, and decodes PNGs with PIL. It never decodes a source video or synthesizes missing frames. [FRAMES.json](../work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json) labels these ARKit inputs `g3s32`; ScanNet/ScanNet++ dense inputs are `g3s64`. ARKit's reported source lengths are lower bounds, not proof that additional rasters are packaged.

The manifest cites producer `/scratch/jjyeung/orch_cd/devs1_tower/out/r2/kit/PLAN.json`, SHA256 `2a2e99ff80083d1d39f1a189e49f2c82596ba76fbe228f97bba98b80547d5d48`. That producer and its original decode receipt are not supplied here. The serving/package reason for 32 versus 64 is established; the upstream reason those ARKit frames were omitted is not. A 64-frame served ARKit read would require a verified nested manifest and corresponding PNG bytes in the existing frame root, neither of which is present in these registered inputs.

`0.py` authenticates and reuses the dense package payload, input archives and existing environment snapshot through its pinned staging/namespace helpers. `2.py` invokes the unchanged [FrozenG3TTower](../work/payload/tree/student_pilot/tower_read.py:144), matching [TowerG3T._fresh](../work/payload/b/e2e_reader/real.py:41): BF16 backbone, FP32 cameras, depth chunks of eight, and `native_square_pad_bicubic_1024_bilinear_518_v1`. Only the tower is loaded for inference. The inherited staging helper unpacks existing archives into allocation-local `/tmp`; it installs no environment and adds no frames or weights to `/project`.

Metric conversion holds each capture's authenticated T1 scale and gravity fixed. Gravity is recovered as `R0.T @ [0,0,1]` from T1's first c2w rotation; the contract's stored `[0,0,1]` is world-up. The frozen conversion reproduces T1 coordinates in CPU tests. Scale/gravity are not new predictions. The scorer's arm-A control requires all ten relative-rotation RMS differences to be ≤0.5°; any failure makes the result void.

`../cap/score_tower2x/score.py` scores only the 32 bound GT anchors. It preserves the round-5 center-fit rigid transform, center-rank ≥2 pass guard, no fitted scale, translation RMS ≤0.10 m and every rotation ≤5°; gross means rotation max >60°. Relative errors cover all 496 anchor pairs. JSON includes per-anchor and per-pair residuals; Markdown lists classes and errors for A/B/C.

The registered verdict is unchanged: confirm requires ≥4/5 gross exits, ≥50% reduction in the failing captures' median relative-rotation RMS, and ≤2° rise for every reference. Refute requires ≤1/5 exits and <20% median reduction; other complete outcomes are partial. Missing A/B comparisons are incomplete, and stub outputs are synthetic. GT conclusions remain conditional on REPORT9's recorded binding.

Placement adds **55,304 logical bytes** of code and input metadata. No payload, environment, frames or weights are copied into the new `/project` directory. The JSON return is capped at 500,000 bytes (below 5 MB); its receipt binds the input SHA256, return SHA256/length, token, job, completion and stub status. Each completed arm records all input c2w poses, anchor slots, IDs, PNG hashes, frozen scale/gravity, elapsed time, peak allocated/reserved memory and RSS.

The forecast is **17.79 minutes**: 600 s staging allowance + 78.21 s load allowance + 1.5 × 10 × 17.93 s measured dense-job tower time + 120 s IO/return allowance. The dense return also measured 22.28 s for 64 frames. `FORECAST.json` retains those receipts and assumptions. Staging is not measured here and aborts after 600 s. The entry refuses forecasts >25 min, checks the remaining forecast after staging, and requests one H100 GPU for 30 min including load. Cold remote staging and real GPU memory/runtime remain unverified.

**14 CPU tests passed**, including the actual 1024→518 preprocessing and served camera decoder with a stub backbone/heads, one-capture job schema/binding, nested 64/96 synthetic bindings, parent admission, no-scale scoring, controls, both verdicts and reference regression. All ten T1 rigid/relative residuals reproduce the prior artifacts within 1e-5. `TESTS_RELEASE.log` records the suite. `DRY_FINAL.json` and `../cap/score_tower2x/dry_final/TOWER2X.{json,md}` are explicitly synthetic.

`SCAN.json` covers all ten Orchard-bound files, decoded placement members, shell syntax and Python compilation. New names, paths, arguments, comments and logs are opaque. Only the input JSON values carry capture IDs, existing dependency paths and existing API symbols; reused payload internals retain their authenticated names. Runtime stdout/stderr is suppressed. `BUILD.json` identifies the exact installed files. `SHA256SUMS_K2` covers the new kit/scorer artifacts, excluding itself.

Run from `gbuild` on the authorized lane; wait for the CPU job to finish before submitting and for the GPU job to finish before fetching:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
ssh orchard 'bash -s' < orchard_tower2x/o_place.sh
ssh orchard 'bash -s' < orchard_tower2x/o_cpu.sh
ssh orchard 'bash -s' < orchard_tower2x/o_check_sub.sh
ssh orchard 'bash -s' < orchard_tower2x/o_fetch.sh > ../cap/score_tower2x/return.tgz
tar -xzf ../cap/score_tower2x/return.tgz -C ../cap/score_tower2x 5.json 5.1.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' /scratch/jjyeung/envs/p1cpu/bin/python -B ../cap/score_tower2x/score.py --return ../cap/score_tower2x/5.json --receipt ../cap/score_tower2x/5.1.json
sha256sum --check orchard_tower2x/SHA256SUMS_K2
```

The CPU entry verifies parent payload/input pins and archive sizes, then runs one synthetic capture without a GPU. It does not load weights or validate actual PNG bytes. The submit script requires its matching receipt and an empty general queue. Scripts refuse existing run markers; they contain no relaunch loop. The fetch script authenticates job identity and return bytes before streaming the two small files.

No SSH, Git, GPU, network, deletion, placement or submission ran during this build. All writes stayed under `orchard_tower2x/` and `cap/score_tower2x/`. The report applies the no-archaeology skill; no borderline history statements were retained.
