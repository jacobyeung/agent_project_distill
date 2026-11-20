| Dataset | Camera rule | Captures | T1 visible same / best alt IoU | Points visible same / best alt IoU | Changed T1 / points |
| --- | --- | --- | --- | --- | --- |
| ARKit | all | 23 | 0.618 / 0.083 | 0.626 / 0.205 | 0 / 0 |
| ARKit | pass | 2 | 0.628 / 0.056 | 0.672 / 0.192 | 0 / 0 |
| ARKit | fail | 21 | 0.618 / 0.087 | 0.626 / 0.218 | 0 / 0 |
| ScanNet | all | 4 | 0.797 / 0.078 | 0.800 / 0.089 | 0 / 0 |
| ScanNet | pass | 1 | 0.785 / 0.121 | 0.786 / 0.279 | 0 / 0 |
| ScanNet | fail | 3 | 0.810 / 0.070 | 0.813 / 0.065 | 0 / 0 |
| ScanNet++ | all | 11 | 0.519 / 0.000 | 0.666 / 0.011 | 0 / 0 |
| ScanNet++ | pass | 3 | 0.519 / 0.000 | 0.543 / 0.009 | 0 / 0 |
| ScanNet++ | fail | 8 | 0.518 / 0.000 | 0.680 / 0.022 | 0 / 0 |


Entries are medians of capture medians. Each capture pools bound object-call/anchor rows with nonempty same-frame GT; missing proposals score zero. “Best alt” selects one shift or transform per capture. A change requires >0.2 median-IoU gain on the same eligible anchors; shifts omit only out-of-range edges. All 32 anchors, alternative medians, paired baselines, and conditional-on-proposal medians are in JSON. No alternative is applied to the GT or funnel.

The literal all-32-anchor median is **0.000 for every capture, arm and hypothesis**, with 0/38 class changes in both raw arms: most queried instances are invisible in most anchors, and empty/empty IoU is zero. The visible-GT table avoids that floor. It contains 398 ARKit, 117 ScanNet and 407 ScanNet++ object-call/anchor rows per arm; ARKit captures contribute 5–45 such rows each. The paired-edge and literal full-baseline definitions both give zero changed captures. Point-selected masks also give zero changes; their ARKit same-frame median is 0.621.

**Image content supports ARKit’s same-frame, same-orientation mask binding:** all 23 captures prefer the same frame in both raw-proposal arms, including all 21 camera-rule failures. ARKit’s same-frame medians are 0.618 (T1) and 0.626 (points), versus 0.083 and 0.205 for the best alternatives. No tested shift or transform improves a capture by >0.2; the lower-overlap captures do not recover either. These results do not support the tested frame/orientation-fault explanation or establish that the camera/S1 failures are binding artefacts. They support the masks’ association with RGB content, but do not independently authenticate every native pose/RGB pair. ARKit’s eight S1 candidates remain in their own row.

| Source file | Identity fields and comparison | Can hash-bind GT rows to RGB? |
| --- | --- | --- |
| `../gt/arkit_gt/gt/<video>.npz` | All 23 contain `frame_indices`, `c2w`, `inst`, `valid`, instance labels/boxes and intrinsics. All 736 anchor indices agree; filenames agree with capture IDs. No sensor timestamps, native RGB names or RGB hashes exist. | No |
| `kit2/kit/rerun2/gt_staging.json` | `capture`, source `path`, `relative_path`, `host`, and byte count locate the NPZ; `matched_frames_and_instances_verified=false`. No per-frame identity receipt exists. | No |
| `gt/adapter.py`, `gt/v2.py`, `out2/GT.json` | Adapter inputs are staged NPZs plus `items544.json`. `source_indices` and `c2w` copy NPZ rows; target bindings map query names to unique instance IDs. Capture IDs/anchor order agree. | No; copied identifiers are not independent evidence |
| `kit2/kit/rerun2/items544.json` | `capture`, `task.native`, `source_indices`, and `task.source_frame_indices` agree with each recorded reader call and the RGB manifest. | No GT RGB hash |
| Reader `FRAMES.json`¹ and `DENSE_MANIFEST.json`² | `scene`, `native`, anchor/frame `index`, PNG `path` and `sha256` agree at all anchors. ARKit `timestamps=index/10` are synthetic; frame counts are lower bounds. Every anchor is listed in the JSON identity section. | Binds reader manifests to the same PNG identities only |
| `../cap/t1.gz`, `../cap/t1ret/PARITY.json` | Record `capture`/`source_indices`, geometry indices and proposal `frame`/`source_index` agree. T1 has no per-anchor RGB hash field; its parity receipt authenticates deployed answers/capture bytes. | No |
| `../cap/t2.gz`, `../cap/t2ret/PARITY.json` | Point records’ `binding.expected_anchor_sha256` and `bound_anchor_sha256` equal every manifest PNG hash; `frame_hashes_match=true`. Source/proposal indices agree. | Yes for reader inputs; no for GT poses |
| Payload `tree/generator/derivgen_v7/derivgen/native.py` | A compatible builder accepts calibration, RGB, selection and visibility provenance. No matching preparation/registry/config sidecars for these NPZs are supplied. Both staged GT directories contain only NPZs. | Not with the supplied files |


¹ `work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json`. ² `work/payload/b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json`. The audit compares recorded PNG hashes; it does not reread PNG bytes. **No available check independently hash-binds an ARKit GT pose/mask row to the reader’s RGB.**

| Dataset group | Stage | Objects | Items | Mean score [95% CI] |
| --- | --- | --- | --- | --- |
| ScanNet + ScanNet++ | S0 | 1 | 1 | 90.00 [90.00, 90.00] |
| ScanNet + ScanNet++ | S1 | 19 | 17 | 66.47 [43.00, 90.00] |
| ScanNet + ScanNet++ | S2 | 18 | 13 | 70.77 [22.50, 95.00] |
| ScanNet + ScanNet++ | S3 | 12 | 4 | 85.00 [80.00, 90.00] |
| ScanNet + ScanNet++ | S4 | 0 | 0 | undefined |
| ScanNet + ScanNet++ | S5 | 4 | 0 | undefined |
| ScanNet + ScanNet++ | no-GT | 130 | 64 | 48.91 [36.79, 61.67] |
| ScanNet + ScanNet++ | censored | 22 | 4 | 90.00 [70.00, 100.00] |
| ARKit (binding unresolved) | S0 | 0 | 0 | undefined |
| ARKit (binding unresolved) | ARKit: unresolved S1 candidates | 8 | 7 | 64.29 [50.00, 100.00] |
| ARKit (binding unresolved) | S2 | 9 | 7 | 42.86 [0.00, 100.00] |
| ARKit (binding unresolved) | S3 | 17 | 6 | 56.67 [10.00, 100.00] |
| ARKit (binding unresolved) | S4 | 0 | 0 | undefined |
| ARKit (binding unresolved) | S5 | 1 | 0 | undefined |
| ARKit (binding unresolved) | no-GT | 28 | 14 | 56.43 [30.00, 79.69] |
| ARKit (binding unresolved) | censored | 31 | 13 | 72.31 [61.17, 85.00] |


ARKit rows reproduce the diagnostic labels under the recorded binding; they are not established grounding-failure counts. The ARKit S1-candidate row is excluded from the accepted S1 count. Counts cover all 300 object occurrences and 150 items, including no-GT captures. Scores and intervals use the REPORT7 item rules and 10,000 shared room-bootstrap draws (46 rooms, seed 20261120). No item reaches S5; repair budgets remain undefined.

| Dataset group | GT captures | Pass | Moderate | Gross |
| --- | --- | --- | --- | --- |
| ScanNet + ScanNet++ | 15 | 4 | 9 | 2 |
| ARKit (binding unresolved) | 23 | 2 | 13 | 8 |


These are the 38 distance-reader capture fits. Pass requires centre rank ≥2, rigid translation RMS ≤0.10 m and every rotation ≤5°; gross means rotation max >60°, and other failures are moderate. ARKit classes remain conditional on the unverified binding. The REPORT8 camera-question corpus contains only ScanNet and ScanNet++; its score table is therefore already the non-ARKit result, and an ARKit camera-question score is undefined.

| Step | Class | Captures | Items | Displacement % [95% CI] | Rotation % [95% CI] | Direction % [95% CI] | All % [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 544 | pass | 4 | 72 | 63.3 [42.5, 85.0] | 67.2 [53.3, 90.0] | 100.0 [100.0, 100.0] | 70.1 [60.8, 88.6] |
| 544 | moderate | 9 | 180 | 60.7 [48.5, 74.3] | 52.9 [39.5, 64.8] | 93.9 [86.4, 100.0] | 70.4 [66.5, 73.7] |
| 544 | gross | 2 | 36 | 60.0 [50.0, 62.5] | 70.0 [50.0, 76.7] | 66.7 [33.3, 83.3] | 65.6 [50.0, 78.0] |
| 544 | unclassified-GT | 19 | 288 | 74.6 [63.4, 80.7] | 59.4 [47.5, 70.0] | 98.0 [95.2, 100.0] | 78.1 [72.6, 83.1] |
| 544 | no-GT | 18 | 324 | 70.7 [58.2, 79.5] | 60.4 [47.6, 73.1] | 93.5 [83.1, 100.0] | 74.6 [64.9, 82.7] |
| 544 | all | 52 | 900 | 69.1 [62.7, 74.4] | 59.7 [53.8, 65.3] | 93.7 [88.9, 97.5] | 74.2 [70.2, 77.7] |
| 400 | pass | 4 | 72 | 67.3 [58.0, 90.0] | 55.3 [47.5, 75.0] | 80.0 [50.0, 100.0] | 63.7 [60.8, 69.3] |
| 400 | moderate | 9 | 180 | 65.9 [53.8, 77.7] | 60.0 [51.4, 67.9] | 80.3 [64.3, 93.5] | 69.3 [61.9, 75.8] |
| 400 | gross | 2 | 36 | 67.0 [50.0, 71.2] | 70.0 [60.0, 100.0] | 50.0 [33.3, 58.3] | 59.2 [58.0, 60.6] |
| 400 | unclassified-GT | 19 | 288 | 79.2 [69.3, 85.3] | 52.9 [43.2, 58.9] | 76.5 [70.0, 85.4] | 70.6 [66.5, 74.4] |
| 400 | no-GT | 18 | 324 | 73.6 [64.0, 79.9] | 58.3 [45.5, 72.7] | 75.0 [65.3, 85.3] | 68.5 [60.6, 76.5] |
| 400 | all | 52 | 900 | 73.3 [68.0, 77.7] | 57.1 [51.6, 62.8] | 75.3 [69.7, 81.2] | 68.6 [65.4, 71.8] |


Camera-question classes are approximate reconstructions on 15 overlapping captures; 19 GT captures remain unclassified and 18 lack GT. No ARKit camera-question records exist. The 10,000 room-bootstrap intervals are copied from the validated REPORT8 artifact.

Per-capture results: [BINDING_R9.md](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_bind/BINDING_R9.md). Every per-object/per-anchor value and identity comparison: [BINDING_R9.json](/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_bind/BINDING_R9.json).

No validated portrait mapping exists in the supplied adapter. Diagnostics use unchanged native 320x240 GT for identity/180/flips and exact np.rot90 GT for +/-90, giving 240x320. Proposals use the identical routed_features.resize function to each resulting GT grid. GT is never resized. For H=320,W=240: CCW maps (x,y) to (y,W-1-x); CW maps (x,y) to (H-1-y,x). Raw proposals are resized to that hypothesis grid; these are normalized-image-coordinate diagnostics, not an accepted source calibration.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
mkdir -p ../cap/score_bind
/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round9.py > ../cap/score_bind/ANALYZE_COMPLETE_R9.log 2>&1
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round9 -v > ../cap/score_bind/TEST_R9.log 2>&1
/scratch/jjyeung/envs/p1cpu/bin/python -B render_round9.py
sha256sum --check SHA256SUMS9
```

| Input | SHA256 |
| --- | --- |
| GT.json | 3e871a24d2f4b2ec5ddb723a08e90fc152d7d74ec6fe9720a5c27fb7a7fa5f1c |
| FRAMES.json | c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439 |
| DENSE_MANIFEST.json | 4fef3415587c918f422515c0cf74565b77a1f90f4ef63d77c73718364e7fbc10 |
| FUNNEL_T1.json | 23ee3456d2fdea1184547417ae542cbe26de6b612f70a456296d5c90359af199 |
| CAMERA_SPLIT.json | 453d7db15085a57f601fb88100873c9fa1faaa1f278cb5eeecad292345850c6d |
| t1.gz | fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7 |
| t2.gz | 2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08 |


`BINDING_R9.json` records exact SHA256s for every analysis input/source and six uncompressed NPY members in each of the 38 NPZs. Those member hashes bind the consumed masks/indices/poses/inventories; they are not full-archive hashes or GT-to-RGB evidence. `SHA256SUMS9` covers all new sources, logs, tests and deliverables except itself.

Completed analysis: 61.26 s; peak RSS 499.8 MiB; one numerical thread; 15 GiB address-space cap. The audit read 2,949,384 compressed bytes for the six hashed NPZ members per capture (some members were also loaded for scoring); it did not load depth or RGB pixels. Both captures authenticate by SHA256; 122 landscape calls reproduce the T1 join’s proposal-availability decision. Four CPU tests pass. No GPU, SSH, Git, network, deletion or job submission ran; earlier deliveries remain unchanged.
