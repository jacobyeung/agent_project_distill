# b10_reserve STATUS (Devin lane, trinity-1-18; lane /scratch/jjyeung/orch_n30/b10_reserve) — successor resumes from this file alone
Updated: 20261116T1500Z.
Percent done: ~45% (list frozen, code+tests ready; data streams queued).

## Done (all paths under the lane folder)
- Inputs copied: in/kit07/pull (kit 07ca49df metadata from trinity-1-13 rows_rebuild/work/s0/pull, sha list in/kit07/pull_sha_src.txt); single-dir listings in/scannet_scans*.txt, in/scannetpp_scenes.txt, in/arkit_training_local.txt, in/arkit_metadata.csv; in/WITHHELD_ROOMS_80.json (634820b4); in/stream_scenes/{d0v5_vqa.txt 37ce92fb, legs1_mdg_rasters.txt 7a6843b1}.
- Census: code/census.py (aff620b6) -> out/CENSUS.json (a29e8e78), out/CENSUS_PER_CAPTURE.json (0694c150), out/clean_candidates.txt, out/census_stdout.txt; out/scannetpp_assets.json (9fc30a32) = per-clean-ScanNet++-scene file sizes on /data2/jjyeung/raw_datasets/scannetpp/data.
- Authorities used: division A3 f41d15aa (train+heldout), kit07 frame_map 17aa3e9e + frame_rates 36ae882f, D0 v5 VQA scenes, LEG-S1 MDG raster scenes, BENCH v2 3119aa4a (incl. ReVSI v1, VSI-Bench, VSTI), exclusions 99e6eed6/932c0c4e/dafa4a9c/600ef69d, dev-S1 969cdb56, WITHHELD_80. 0 unresolved keys in every authority.
- out/R0_SCENES.json (code/build_r0.py aaaa3d90) sha f7c45817: 374 captures / 372 rooms; R0-dev 100 ScanNet++ full-GT rooms; R0-rl 62 ScanNet++ full + 12 ScanNet full + 50/50 ScanNet++ mesh/pose + 100 ScanNet scans_test. code/test_exclusion.py 9f25653f: 3 tests OK. census.py 817fb604 reproduces CENSUS.json byte-identically. No overlap with rows_a2's 686 A2 scenes. R0_REGISTRATION_NOTE.md, R0_ROOMS.txt, R0_DEV_ROOMS.txt in out/ and events folder. RESULT r0_frozen_review_request asked ORCH for the refute review.
- Trained frame layout (kit07 frame_plan + D0 rows): ScanNet++ = VSI-590K mp4 of iphone video at 60 fps, 640x480; 32 frame indices = floor(linspace(0, total-1, 32)). R0 decodes rgb.mkv (1920x1440, 60 fps) with PyAV 15.1.0 (env /scratch/jjyeung/envs/p1cpu) resized to 640x480.
- Result: clean rooms with full GT (rgb + instances + mesh + pose) on Trinity = 162 ScanNet++ + 10 ScanNet rooms (12 captures: scene0183_00 0237_00/01 0258_00 0333_00 0339_00 0394_00/01 0485_00 0546_00 0636_00 0639_00) = 172 >= 150. Partial-GT clean pools: 50 ScanNet++ mesh+pose no instances, 50 ScanNet++ iphone-only, 100 ScanNet scans_test (pose+mesh). ARKitScenes: 0 clean local.
- IO needed: ScanNet++ 162 full scenes = 66.0 GB rgb.mkv + ~6.5 GB GT (segments_anno, segments, mesh_aligned_0.05, colmap); ScanNet 12 .sens ~25 GB. > 30 GB, so asked ORCH (QUESTION event) before any stream.

## Code built (tests on CPU, env /scratch/jjyeung/envs/p1cpu)
- code/r0lib.py (PLY/segments loader, aligned_pose convention check vs colmap, layout rule, point-splat visibility 160x120, >=8 px), code/gen_questions.py (r0gen-v1: counting single/multi, size cm, abs distance m, room m2, rel distance closest/farthest, rel direction easy/medium/hard toward/away, appearance order; answers per layout answer_f32/answer_f64; D0 v5 wording), code/test_gen.py (8 OK).
- code/decode_frames.py (PyAV 15.1.0 sequential decode, swscale bicubic 640x480 PNG), code/test_decode.py (3 OK).
- code/run_scenes.py gen|decode (Pool, skip done; decode progressive by mkv size), code/aggregate.py (per-layout question files, histograms, constants table vs R0-rl median / top option).
- in/d0v5_templates.jsonl (300 D0 v5 rows per type + full answer histograms), in/validator/trace_grammar.py a41ba191 (validates traces; R0 items have no targets, so it applies to later trace rows; record this).

- Design record distill_design/R0_RESERVE_SCENES_20261116.md + INDEX line written; lists copied to distill_design/R0_RESERVE_20261116/ (R0_SCENES.json f7c45817, R0_ROOMS.txt, R0_DEV_ROOMS.txt, R0_REGISTRATION_NOTE.md). Update its Status/Files when frames and questions land.

- ORCH 1325Z: R0 stands as registered. ORCH 1349Z: archive and mirror everything (one governed tar to /data3/jjyeung/ via copy_archive.py --writes-nfs; IB mirror to trinity-1-13:/scratch/jjyeung/n30_mirror/b10_reserve/, or trinity-3-30 if 1-13 would have <150 GB free after).
- ORCH 1450Z: keep priority 15; if b10r0_gt has not started by 20:00Z, write a QUESTION/BLOCKER to ORCH, who asks main for a slot. R0-dev is needed for mid-leg ranking from D0 m400 on.
- Refute review done (Codex receipt agent/scratch/codex_runs/20261116T131657Z_b10_review_r0/final_message.md): UNPROVEN, no collision; open limits T0/CP1 lists, 134 unmapped MMSI-Video clips, ScanNet++ recaptures. RESULT r0_review_verdict sent; record and note corrected (374 captures / 372 rooms).

## In flight

- ORCH 1236Z answered: streams approved (tier 3, priority 15, GT -> R0-dev video -> R0-rl video; ScanNet .sens last, only if needed); wording/answer formats from D0 v5 row templates (b11_presence STATUS.md names path); validate with a41ba191.
- Governed streams (launcher code/gov_stream.py, reader code/gated_tar_reader.py; dest data_cache/scannetpp/<scene>/...; logs work/streams/<n>.log; lists work/streams/<n>.list):
  - b10r0_gt (972 files, 20.9 GB: segments_anno, segments, mesh_aligned_0.05, pose_intrinsic_imu.json, colmap cameras/images for 162 scenes)
  - b10r0_vid_dev (95 rgb.mkv, 39.3 GB), b10r0_vid_rl (67 rgb.mkv, 26.7 GB)
  Check: STATE.md rows b10r0_*; log ends with 'EXIT (0, 0, 0)'. When a stream EXITs 0: mv /data3/jjyeung/orch_n13_20261026/io_governor/streams/b10r0_<n>.json ...b10r0_<n>.done.$(date +%s). Never restart a failed one (BLOCKER).

- tmux b10pipe runs code/pipeline.sh (log work/pipeline.log): renames each stream record .done.<epoch> on a clean EXIT, writes STREAM_FAILED_<n> on a failed one (never restarts); after the GT stream: run_scenes.py gen (12 workers) + aggregate.py -> out/questions/, out/qsets/; then run_scenes.py decode (8 workers, progressive) every 5 min until both video streams exit. If b10pipe is gone, run those steps by hand (skip-done is built in).

## Next steps
1. After gen (b10pipe): read work/run_gen.log for ERROR lines, inspect a few scenes' items by hand (questions_meta zup/camera convention), check out/qsets/R0_QUESTIONS_SUMMARY.json (per-type counts ~150 on dev, histograms, constants).
2. Decode (b10pipe) -> frames/scannetpp/<scene>/, out/frame_manifests/<scene>.json; check work/run_decode.log for BAD/ERROR; build one frames manifest with sha256.
3. Update the design record; archive (list, manifests, questions, frames) to /data3 via copy_archive.py (governed, --writes-nfs); mirror on a second node over IB (ask if >5 GB); final RESULT.

## Open questions (answered by ORCH 1236Z; in force)
- Streams approved: tier 3, priority 15, one at a time; ScanNet .sens (~25 GB) only if R0-rl needs those 12 captures. Keep 150 GB free on /scratch.
- Wording/answer formats from D0 v5 templates; validate with a41ba191 where traces exist.
- T0/CP1 covered by kit07 frame_map + division A3 (refute review checks).
- ORCH 1306Z: R0 registered (every leg excludes R0 rooms). I order the review myself: Codex review gpt-6-astra high (both census and build_r0 were written by Claude models).

## Must read
LANE_RULES.md; briefs/qs/10_reserve_scenes_r0.md; this file; out/CENSUS.json; events *_ORCH_* in the events folder.
