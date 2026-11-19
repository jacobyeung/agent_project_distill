The tower-frames section-8 CPU dry run is PASS. No GPU time was used.
The accepted specification has SHA256 133e8cfdbb149401767c76fc5908154b9dd106d2a4b580bcca81d207615169aa.

Run these commands from `/scratch/jjyeung/orch_n30/sb_ktow3`:
- `sha256sum inputs/KIT_SPEC_tower_frames_v2.md` verifies the accepted spec.
- `bash scripts/cpu.sh scripts/bind_camera.py > out/bind_camera.log 2>&1` produces the camera joins and byte-hash audit.
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v3.log 2>&1` produces every section-8 count and timing below.
- `bash scripts/cpu.sh code/test_kit.py > out/tests_v3.log 2>&1` produces the regression result.
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh` checks launcher syntax.
- `bash scripts/cpu.sh scripts/finalize_v3.py` produces the report, GPU request, code hashes, edited-line audit, and archive.

Section 8a: PASS; five train captures have zero stored-C64 self-comparison differences for pose, depth and distance. All five median_ratio scales agree with stored convert scales within 1e-4 relative.
Section 8b: PASS; 10 A0 rows on five train captures match sb_kbox4 exactly in prediction, response, member frames and box values.
The N=32 comparison rebuilds geometry through the same function used by Part B: own-depth median_ratio, float32 exp(log(scale)), checkpoint gravity and the serving guard.
Section 8c: PASS; all 450 staged records and calls parse; synthetic formatting uses a staged scale and gravity. Real 440/450 text parity remains a GPU check.
Section 8d: PASS; all 296 captures pass numbering and 9472 anchor/model-row hash assertions.
N=32 lifting matches the original tree on all five train captures; the N=64 fixture visits all 64 slots.
The dry run took 65.244 seconds and peaked at 1099040 KiB RSS. The launcher uses nice 10 and eight numerical threads.
Regression tests: 18 PASS. The validation receipt records Python parsing and shell syntax checks.

Part C binds all 450 items by exact scene and ordered source-frame indices in existing local A_MANIFEST records, with every PNG byte hash verified.
The audit verified 3264 unique PNGs (822710679 bytes); 431 items also bind to 64-frame DENSE records whose anchors match those PNG hashes.
The request supplies the frame root and bundle identity; the local manifests supply the explicit scene/index/hash mapping. No filename-to-scene mapping was inferred.
The remaining 19 items have 32-frame parity inputs but MISSING dense inputs for scannet/scene0475_00 and scannet/scene0475_01. They are skipped only in dense camera arms.
Exact missing dense manifests:
- `/scratch/jjyeung/devs1_r2/anchors/g3s64/scannet__scene0475_00/DENSE.json`.
- `/scratch/jjyeung/devs1_r2/anchors/g3s64/scannet__scene0475_01/DENSE.json`.
`inputs/CAMERA_FRAME_JOINS.json` records every item, source and hash; `out/CAMERA_BINDING.json` and `out/BLOCKERS.json` list the dense skips.

The box kit freezes no object variant: replace_box part 1 FAIL; fused_path PASS applies to GT masks only. This kit uses today arms and one added-frame-gain comparison.
Part B runs independently of Part A's bars. K1 train decides the bars; held-out scores remain report-only after DECISION.json. No held-out values were evaluated here.
The scripts retain vnice, scratch-only assets/writes, hash-validated DONE resume, shared-ledger admission and an explicit GPU GO bound to code hashes.
Prepared commands are `bash scripts/run_A.sh`, `bash scripts/run_B.sh`, and `bash scripts/run_C.sh`, each with one explicitly assigned CUDA_VISIBLE_DEVICES.
GPU_NEED.json requests one 48-GB card: A 0.5 expected/0.75 hard-stop GPU-h; B 2.5/3.0; C 0.6/0.75. It stops allocations above 40 GB; actual GPU memory remains unmeasured.
Ruling 0749Z permits this kit's 3.6 expected GPU-h and the room kit's 0.2 to share one card. Schedule them sequentially under the shared 16 GPU-hour ledger.
CPU interpreter: `/scratch/jjyeung/envs/p1cpu/bin/python`; prepared GPU interpreter: `/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python`.
`out/EDITED_LINES.json` and its patch list every copied-source edit; `out/CODE_SHA256.json` pins the delivered code. All generated JSON receipts record input SHA256 values.
GPU performance and decision outputs are MISSING/NOT_RUN. No GPU, network, SSH, Git, tmux or process-control action ran; the archive was not mirrored.
Archive: `out/sb_ktow3.tar`; verify with `sha256sum -c out/sb_ktow3.tar.sha256`.
Writing skills: no-archaeology and summary. No revision-history sentences were retained.
