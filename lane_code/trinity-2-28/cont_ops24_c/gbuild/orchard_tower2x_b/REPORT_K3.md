K3 is blocked at recipe verification. **All 320 served-anchor PNGs are absent from the supplied `/scratch/jjyeung/devs1_frames/<prefix>/<sha256>.png` paths.** Pixel equality, maximum pixel differences and PNG-byte equality are unknown. No production recipe or runnable package has been selected.

`arkit_lowres/out/MISSING_ANCHORS_K3.json` lists all 320 missing hashes and paths, with comparison fields set to null. The first missing hash is `c5a2ecade08a368929d9ca1e02db03e3f23a90d1fffcdbe510e033b36cc12e09`. Initial encodings of that anchor with five Pillow and five OpenCV filters did not recover its manifest hash. This does not measure pixel differences.

`recipe.py` compares every available served anchor against all filters and both sideways turns, then records per-anchor pixel equality, maximum difference, raw RGB hashes and default-Pillow PNG byte hashes. It supports `K3_SERVED_ROOT` for an alternate local content-addressed store. OpenCV 4.10.0 is available through the existing local environment; no package was installed. The script refuses to select a recipe while references are missing.

All **1,250 supplied lowres PNGs** decode as 256×192. `INPUTS_K3.json` binds their original PNG/raw hashes and source indices. SELECTION's `n_frames` and 32 anchors agree with FRAMES.json for all ten captures. Local directories contain only the 125 selected frames, so their local ranks must never replace the original source indices.

| Arm | Frames per capture | Selection |
| --- | --- | --- |
| A | 32 | Original served anchors |
| B | 63 | Anchors plus the 3/6 point of each gap |
| C | 94 | Anchors plus the 2/6 and 4/6 points of each gap |
| A′ | 32, conditional | Recipe-decoded anchors if the recipe is not pixel-exact |

B and C each contain A's indices; C does not contain B's midpoint indices. The worker checks these exact selections and all 32 anchor slots. It returns all input c2w poses, IDs, input PNG hashes, decoded raw RGB hashes, binding, frozen scale/gravity, decode/inference/load times, GPU memory and RSS. Only anchor cameras enter scoring.

The original lowres PNGs for B+C extras total **65,235,995 bytes**, exceeding the 50 MB placement cap before code. B extras alone total 21,748,378 bytes. A′+B uses 44,270,777 bytes; all lowres inputs use 87,758,394 bytes. The builder automatically drops C in the nonexact fallback when necessary. For an exact recipe, dropping C or raising the cap requires the user's unresolved choice. No bytes were placed in `/project`; final package size is unavailable.

The draft builder reuses K2's parent package, environment, weights and FrozenG3TTower path. Five count guards are adapted in memory after authenticating three source files: four enumerated-count checks admit 63/94, and the camera encoder's even-count check admits 63. `ADAPTATION.json` records original/adapted hashes and exact replacements. Original payload files, camera math and preprocessing remain intact.

Conditional forecast: **24.36 min for all ten A+B pairs**, including 600 s staging, 78.21 s load, 1.5× measured 32/64 inference, 3 s decode per capture/arm and 120 s return reserve. A+B+C forecasts **37.39 min**. If A′ is required and C is dropped, all A+A′+B forecast 29.34 min; the admitted prefix is all A/A′ plus two B captures at 24.48 min. `FORECAST_PENDING.json` retains every task and assumption.

The entry refuses an admitted-prefix forecast over 25 min or an unverified recipe. It requests one GPU, verifies H100 at runtime, and caps the job at 30 min with eight CPUs/20 GB RAM. Arms run across all captures in A/B/C order; A′, when required, runs immediately after A. Later tasks require their conservative cost plus the return reserve to fit the remaining allocation. Budget stops retain completed results. Real staging, 94-frame GPU runtime/memory and remote admission remain untested.

`cap/score_tower2x_b/score.py` retains the round-5 rigid fit with frozen T1 metric scale, adds Umeyama similarity scale and scale/A, and reports all 496 REPORT6 relative pairs. Pass requires center rank ≥2, translation RMS ≤0.10 m and rotation max ≤5°; gross requires rotation max >60°. Similarity determines class, with rigid results also reported. Gravity uses `R_i.T @ R_0 @ g_T1` against `R_GT_i.T @ [0,0,1]`, with mean/max and all anchor residuals.

Every A control must have relative-rotation RMS ≤0.5° against T1, else both verdicts are void. B and C receive separate verdicts: confirm requires ≥4/5 gross exits, ≥50% reduction in the failing captures' median relative-rotation RMS and no reference rise >2°; refute requires ≤1 exit and <20% reduction; otherwise partial. Missing comparisons remain incomplete. GT conclusions retain REPORT9's unresolved native pose/RGB-binding caveat.

**13 scorer/scheduling tests pass.** They cover scale recovery and scale/A, gravity transport/gauge, all 496 pairs, K2 residual reproduction, controls, confirm/refute/reference regression, binding rejection, independent C incompleteness, arm order and clean budget stops. See `TEST_SCORER_FINAL.log`.

**The synthetic CPU pipeline passes at 32/63/94/32 frames**, using the real 1024→518 preprocessing, camera composition and pose decoder with stub backbone/heads. All anchor raw hashes agree across the synthetic arms. It took 12.74 s and peaked at 1,545,908 KiB RSS. `CPU_PIPELINE.json` explicitly marks it synthetic. The required real-capture decode/anchor comparison is blocked and has not passed. `SCAN_SOURCE.json` passes the two remote Python sources; the complete placement scan awaits a build.

Run locally only after the missing served PNGs are restored and the exact-recipe placement choice is resolved:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
ulimit -v 20971520
/scratch/jjyeung/envs/p1cpu/bin/python -B orchard_tower2x_b/recipe.py
/scratch/jjyeung/envs/p1cpu/bin/python -B orchard_tower2x_b/build.py
# For an exact recipe over budget, build requires an approved --drop-c or --project-cap value.
/scratch/jjyeung/envs/p1cpu/bin/python -B orchard_tower2x_b/dry_run.py
/scratch/jjyeung/envs/p1cpu/bin/python -B orchard_tower2x_b/scan.py
/scratch/jjyeung/envs/p1cpu/bin/python -B ../cap/score_tower2x_b/score.py --return orchard_tower2x_b/DRY.json --receipt orchard_tower2x_b/DRY.1.json --out ../cap/score_tower2x_b/dry
```

The builder generates the following lane scripts after those prerequisites. They do not exist in the blocked build and must not be run now. On the authorized lane, wait for each CPU/GPU job to finish before the next dependent command:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
ssh orchard 'bash -s' < orchard_tower2x_b/o_place.sh
ssh orchard 'bash -s' < orchard_tower2x_b/o_cpu.sh
ssh orchard 'bash -s' < orchard_tower2x_b/o_check_sub.sh
ssh orchard 'bash -s' < orchard_tower2x_b/o_fetch.sh > ../cap/score_tower2x_b/return.tgz
tar -xzf ../cap/score_tower2x_b/return.tgz -C ../cap/score_tower2x_b 5.json 5.1.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' /scratch/jjyeung/envs/p1cpu/bin/python -B ../cap/score_tower2x_b/score.py --return ../cap/score_tower2x_b/5.json --receipt ../cap/score_tower2x_b/5.1.json
sha256sum --check orchard_tower2x_b/SHA256SUMS_K3
```

No SSH, Git, GPU, network, deletion, placement or submission ran. All writes stayed in the three authorized new-output locations. `SHA256SUMS_K3` covers the present source, tests and evidence; a completed build will require a new report and checksum manifest.

## K3b — stopped before packaging

**No recipe is selected.** All 320 supplied served PNGs were found and authenticated at `K3_SERVED_ROOT=/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames`. Every tested sky-direction recipe matches **0/320 pixels-exact anchors and 0/320 PNG byte streams**. [Per-anchor evidence](/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/out/RECIPE_K3.json) records all 20 candidates.

| Filter | Pixel-exact anchors CW / CCW | Max difference CW / CCW | PNG-byte matches CW / CCW | Mean absolute error CW / CCW |
| --- | --- | --- | --- | --- |
| PIL/nearest | 0 / 0 | 255 / 255 | 0 / 0 | 8.2190 / 39.0011 |
| PIL/bilinear | 0 / 0 | 255 / 255 | 0 / 0 | 7.2797 / 38.4545 |
| PIL/bicubic | 0 / 0 | 255 / 255 | 0 / 0 | 6.9660 / 38.4134 |
| PIL/lanczos | 0 / 0 | 255 / 255 | 0 / 0 | 6.9585 / 38.4412 |
| PIL/box | 0 / 0 | 255 / 255 | 0 / 0 | 8.2199 / 38.9978 |
| OpenCV/nearest | 0 / 0 | 255 / 255 | 0 / 0 | 8.2229 / 39.0073 |
| OpenCV/bilinear | 0 / 0 | 255 / 255 | 0 / 0 | 7.2072 / 38.4253 |
| OpenCV/bicubic | 0 / 0 | 255 / 255 | 0 / 0 | 6.8637 / 38.4017 |
| OpenCV/lanczos | 0 / 0 | 255 / 255 | 0 / 0 | 6.9910 / 38.4490 |
| OpenCV/area | 0 / 0 | 255 / 255 | 0 / 0 | 7.7849 / 38.7709 |

Each table entry covers 320 anchors; CW/CCW describes Left, while Up is unrotated and Down rotates 180°. Pixel differences use RGB uint8 channel values. PNG comparisons use default Pillow PNG encoding for every resampler. Versions and hashes are in `RECIPE_K3.json`.
The lowest-error prescribed candidate is OpenCV bicubic/Left-CW: mean absolute error 6.8637, maximum 255. Capture 41069054 contributes mean error 58.8159 under Down=180°. A separate all-320 diagnostic leaves Up/Down unrotated and turns Left clockwise: **0/320 exact**, mean error **1.0761**, maximum **124** ([evidence](SERVED_IDENTITY_K3b.json)). This diagnostic is not an adopted recipe.
The served rasters are RGB, 640×480 for Up/Down and 480×640 for Left, exactly 2.5× the corresponding lowres dimensions (source W×H=256×192). They are **not reproduced by the tested lowres upscaling filters and sky rotations**; Down=180° is particularly inconsistent with the images. The original source/decode filter remains unverified; dimensions and resemblance alone do not establish provenance.
**Arms:** C is dropped. A requires the 32 served anchors; the nonexact fallback requires A′ (32 recipe-decoded anchors) and B (63 recipe-decoded frames, anchors plus 3/6 midpoints). No production arm ran. The full A+A′+B forecast is **1,760.311972 s = 29.338533 min**, versus the 25 min cap. A+B alone is 24.355742 min but omits the required decode control. `build.py --drop-c` rejects the full forecast before writing any package file; it cannot substitute an admitted prefix.
**Bytes:** `/project` bytes added = **0**; no runnable placement package exists. A′+B would ship 630 unique lowres PNGs totaling **44,270,777 bytes** before packaging; final placement bytes are therefore undefined. The time cap alone triggers the requested stop. [PREFLIGHT_K3b.json](PREFLIGHT_K3b.json) records counts, forecast, and absence of placement files.
**Existing Orchard inputs:** K2 [AVAILABILITY.json](../orchard_tower2x/AVAILABILITY.json) lists packages `a52c1dcfae7bb`, `ac85ad201020f`, `a883c5c365aee`, each registering only 32 anchors per requested capture; its optional `inputs/r0dev/FRAMES_MANIFEST.json` is ScanNet++ only. [AVAILABILITY_K3b.json](AVAILABILITY_K3b.json) inspects their 934/937/937 code-payload members and identical `a/1.json` (SHA256 `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207`): no lowres_wide PNGs, trajectory or video members and no declared ARKit source recording. Inputs name `d/f`, environment/weights/checkpoints, and shared archives `e/0..3`, `g/0`, `a2.tar`, `a4.tar`, `a3.tar` under `/project/community/jjyeung/okh7/e6fc152498/`.
The [served reader](../work/payload/b/e2e_reader/parity.py:57) opens manifest PNGs with PIL; it cannot recover the missing timestamps from these registered inputs. This kit must ship extra PNGs per capture unless a source recording is separately located and registered. The opaque external archives were not enumerated live, so absence of an unregistered recording elsewhere on Orchard is not established.
**Tests:** all 14 scorer/scheduling tests pass, including dropped-C reporting; remote source opaque-word scans and Python compilation pass. K3’s synthetic CPU evidence remains intact. The real-capture package dry run, package scan, placement and GPU inference did not run because packaging stopped. `TEST_SCORER_K3b.log`, `SCAN_K3b.json`, `BUILD_K3b.log`, and `RECIPE_K3b.log` retain the evidence.
**Lane commands:** place, CPU-check, submit and fetch scripts were not generated; the failed preflight provides no runnable lane commands. The existing scorer has no production return to score. Inspect the gate and verify this delivery locally:

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export K3_SERVED_ROOT=/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames
sed -n '1,12p' orchard_tower2x_b/BUILD_K3b.log
sha256sum --check --quiet orchard_tower2x_b/SHA256SUMS_K3b
```

`SHA256SUMS_K3b` covers current kit/scorer sources, preserved K3 evidence, and K3b evidence; the original `SHA256SUMS_K3` remains a historical snapshot. No SSH, Git, GPU, network, deletion, placement or submission ran. The requested appended section preserves the K3 record; its blocked state and commands do not describe a runnable K3b package.
