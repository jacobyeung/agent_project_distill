# b10_reserve STATUS (Devin lane, trinity-1-18; lane /scratch/jjyeung/orch_n30/b10_reserve) — successor resumes from this file alone
Updated: 20261116T1830Z (Devin successor lane).
Percent done: ~60% (list frozen+reviewed+registered; GT landed; questions generated for most scenes; videos streaming).

## Done (all paths under the lane folder)
- Inputs copied: in/kit07/pull (kit 07ca49df metadata from trinity-1-13 rows_rebuild/work/s0/pull, sha list in/kit07/pull_sha_src.txt); single-dir listings in/scannet_scans*.txt, in/scannetpp_scenes.txt, in/arkit_training_local.txt, in/arkit_metadata.csv; in/WITHHELD_ROOMS_80.json (634820b4); in/stream_scenes/{d0v5_vqa.txt 37ce92fb, legs1_mdg_rasters.txt 7a6843b1}.
- Census: code/census.py (817fb604; reproduces outputs byte-identically) -> out/CENSUS.json (a29e8e78), out/CENSUS_PER_CAPTURE.json (0694c150), out/clean_candidates.txt, out/census_stdout.txt; out/scannetpp_assets.json (9fc30a32) = per-clean-ScanNet++-scene file sizes on /data2/jjyeung/raw_datasets/scannetpp/data.
- Authorities used: division A3 f41d15aa (train+heldout), kit07 frame_map 17aa3e9e + frame_rates 36ae882f, D0 v5 VQA scenes, LEG-S1 MDG raster scenes, BENCH v2 3119aa4a (incl. ReVSI v1, VSI-Bench, VSTI), exclusions 99e6eed6/932c0c4e/dafa4a9c/600ef69d, dev-S1 969cdb56, WITHHELD_80. 0 unresolved keys in every authority.
- out/R0_SCENES.json (code/build_r0.py aaaa3d90) sha f7c45817: 374 captures / 372 rooms; R0-dev 100 ScanNet++ full-GT rooms; R0-rl 62 ScanNet++ full + 12 ScanNet full + 50/50 ScanNet++ mesh/pose + 100 ScanNet scans_test. code/test_exclusion.py 9f25653f: 3 tests OK. census.py 817fb604 reproduces CENSUS.json byte-identically. No overlap with rows_a2's 686 A2 scenes. R0_REGISTRATION_NOTE.md, R0_ROOMS.txt, R0_DEV_ROOMS.txt in out/ and events folder. RESULT r0_frozen_review_request asked ORCH for the refute review.
- Trained frame layout (kit07 frame_plan + D0 rows): ScanNet++ = VSI-590K mp4 of iphone video at 60 fps, 640x480; 32 frame indices = floor(linspace(0, total-1, 32)). R0 decodes rgb.mkv (1920x1440, 60 fps) with PyAV 15.1.0 (env /scratch/jjyeung/envs/p1cpu) resized to 640x480.
- Result: clean rooms with full GT (rgb + instances + mesh + pose) on Trinity = 162 ScanNet++ + 10 ScanNet rooms (12 captures: scene0183_00 0237_00/01 0258_00 0333_00 0339_00 0394_00/01 0485_00 0546_00 0636_00 0639_00) = 172 >= 150. Partial-GT clean pools: 50 ScanNet++ mesh+pose no instances, 50 ScanNet++ iphone-only, 100 ScanNet scans_test (pose+mesh). ARKitScenes: 0 clean local.
- IO: ScanNet++ 162 full scenes = 66.0 GB rgb.mkv + 20.9 GB GT stream (approved by ORCH 1236Z); ScanNet 12 .sens (~25 GB) only if R0-rl needs them.

## Code built (tests on CPU, env /scratch/jjyeung/envs/p1cpu)
- code/r0lib.py (PLY/segments loader, aligned_pose convention check vs colmap, layout rule, point-splat visibility 160x120, >=8 px), code/gen_questions.py (r0gen-v1: counting single/multi, size cm, abs distance m, room m2, rel distance closest/farthest, rel direction easy/medium/hard toward/away, appearance order; answers per layout answer_f32/answer_f64; D0 v5 wording), code/test_gen.py (8 OK).
- code/decode_frames.py (PyAV 15.1.0 sequential decode, swscale bicubic 640x480 PNG), code/test_decode.py (3 OK).
- code/run_scenes.py gen|decode (Pool, skip done; decode progressive by mkv size), code/aggregate.py (per-layout question files, histograms, constants table vs R0-rl median / top option).
- in/d0v5_templates.jsonl (300 D0 v5 rows per type + full answer histograms), in/validator/trace_grammar.py a41ba191 (validates traces; R0 items have no targets, so it applies to later trace rows; record this).

- Design record distill_design/R0_RESERVE_SCENES_20261116.md + INDEX line written; lists copied to distill_design/R0_RESERVE_20261116/ (R0_SCENES.json f7c45817, R0_ROOMS.txt, R0_DEV_ROOMS.txt, R0_REGISTRATION_NOTE.md). Update its Status/Files when frames and questions land.

- ORCH 1325Z: R0 stands as registered. ORCH 1349Z: archive and mirror everything (one governed tar to /data3/jjyeung/ via copy_archive.py --writes-nfs; IB mirror to trinity-1-13:/scratch/jjyeung/n30_mirror/b10_reserve/, or trinity-3-30 if 1-13 would have <150 GB free after).
- ORCH 1450Z: keep priority 15; if the R0-dev video stream has not finished by 20:00Z, write a QUESTION to ORCH, who asks main for a slot. R0-dev is needed for mid-leg ranking from D0 m400 on.
- Refute review done (Codex receipt agent/scratch/codex_runs/20261116T131657Z_b10_review_r0/final_message.md): UNPROVEN, no collision; open limits T0/CP1 lists, 134 unmapped MMSI-Video clips, ScanNet++ recaptures. RESULT r0_review_verdict sent; record and note corrected (374 captures / 372 rooms).

- Pilot on real scene 01ce24e652 (work/pilot/): z-up confirmed (floor 0.06 m, ceiling 3.62 m); aligned_pose is OpenCV c2w (median 8.6 mm from colmap); 22 items, all types; ~50 s/scene. room_area fixed (3-cell pad so closing does not erode the border; 7.29 m2 vs 7.6 m2 scan bbox). code/overlay_check.py SCENE writes frame|id-raster overlays to work/overlay/ once frames exist: look at 2-3 to confirm visibility.

- First gen pass done 17:59Z (144 of 162 scenes ok; 18 in retry) and first aggregate (work/aggregate.log; out/qsets/R0_QUESTIONS_{dev,rl}_f{32,64}.jsonl, R0_QUESTIONS_SUMMARY.json; interim, rerun after retries): dev 1,837 items (counting 341, size 260, abs distance 257, rel distance 246, direction easy 170 / medium 172 / hard 170, appearance 134, room size 87); rl 2,812. Interim constants on dev: counting median 2 -> MRA 61.2 (f32) / 58.9 (f64); abs distance 1.745 m -> MRA 27.9; direction easy/hard top-option 51.8/30.6 vs chance 50/25; letters balanced. Room size is one item per room (<=100 on dev by construction); appearance order short of 150 -> raise its dev cap.

## Successor progress (from 18:09Z)
- First retry (b10retry) finished: 16 of 18 ok. The first-pass failure list was incomplete: 13 more scenes (R0-rl) had failed; b10retry2 (work/gen_retry2.sh, list work/gen_retry2.list, log work/gen_retry2.log, ends RETRY_DONE) runs them.
- Pose-gate failures, all inspected with work/pose_diag.py (aligned_pose vs colmap, translation/rotation error and aligned translation span): 7dab70c8c8 (dev, span 15 km), c29b5e479c (dev, drift p50 6.5 cm / p90 19.5 cm), 120acffd90 (rl, span ~400 m), 46001f434d (rl, span ~240 m), ab4f373966 (rl, rotation ok but translation span 46 m). All deferred with reasons in out/DEFERRED.json (gate kept at 0.05 m as preregistered; deferred scenes stay in the denominator). cc0aa81452 pending in retry2.
- Overlay check done on 04d0dc245b, 0a5c013435, 193672f661 (work/overlay/*.png): raster lines up with frames (jacket, chairs, door, cabinets, floor boundaries).
- Hand/automatic item audit on all f32 items: rel distance gap >= 0.20 m and answer = true extreme (0 errors); direction answers match angle sign rules (0 errors), every angle >= 15 deg from a boundary; appearance answers match first positions (0 errors, distinct positions); abs distance >= 0.37 m p5. Labels are raw ScanNet++ vocab, same as the D0 v5 (VSI-590K) rows; a few odd labels ("structure", "ceilng lamp bar") left as they are.
- gen_questions.py -> r0gen-v2 (backup work/gen_questions_v1.py.bak): RNG/qid seed kept as 'r0gen-v1' so v1 items reproduce; R0-dev appearance cap 3 (was 2) and 30 tries per cap unit. test_gen OK. Plan: after retry2, move out/questions -> work/questions_v1 and regenerate all scenes with v2 (run_scenes.py gen), then aggregate.

## In flight (as of rotation)
- Streams: b10r0_gt DONE (EXIT 0 17:28Z; record renamed .done). b10r0_vid_dev RUNNING since 17:30Z (39.3 GB, ~85 min at 8 MB/s -> ~19:00Z). b10r0_vid_rl waiting (26.7 GB, ~1 h after vid_dev). Logs work/streams/<n>.log; check STATE.md rows b10r0_*.
- tmux b10pipe (code/pipeline.sh, log work/pipeline.log): ran gen once (run_scenes.py gen; log work/run_gen.log), then aggregate.py -> out/qsets/ (that first aggregate misses the retried scenes), then decode every 5 min (progressive; frames/scannetpp/<scene>/, out/frame_manifests/; log work/run_decode.log), renames video stream records on clean EXIT, writes work/STREAM_FAILED_<n> on failure, runs check_redecode.py at the end and logs 'pipeline finished'.
- tmux b10retry (work/gen_retry.sh, log work/gen_retry.log ends with RETRY_DONE): re-runs gen for the 18 scenes in work/gen_retry.list that failed in the first pass, with the fixed colmap-name parser (names like 'iphone/frame_000010.jpg'). Two of them failed for a different reason: aligned_pose disagrees with colmap (7dab70c8c8: 615 m median, likely a different frame naming or unaligned poses; one other at 0.054 m, just above the 0.05 m gate). Read gen_retry.log for which still fail.
- If b10r0_vid_dev/rl have not finished by tomorrow, nothing else is needed: b10pipe carries on. If b10pipe died, rerun its steps by hand (skip-done built in).

## Next steps
1. When RETRY_DONE: for scenes still failing on the colmap gate, inspect (compare aligned_pose vs colmap for a few frames; check camera ids in cameras.txt). Either fix the convention rule with evidence or defer the scene with the reason (strict gate: deferred scenes stay in the denominator; record them in out/DEFERRED.json). Then rerun `cd LANE && /scratch/jjyeung/envs/p1cpu/bin/python -W ignore code/aggregate.py out/questions out/qsets` and check out/qsets/R0_QUESTIONS_SUMMARY.json: dev ~150 items per type? (dev caps x1 over 100 scenes; if a type falls short, raise its CAPS for R0-dev in gen_questions.py, bump GEN_VERSION, regenerate dev only), histograms vs D0 reference, constants table.
2. Hand-inspect ~20 items across types; once frames exist run `code/overlay_check.py <scene>` for 2-3 dev scenes and view work/overlay/*.png to confirm the visibility raster lines up with the frames.
3. After both video streams and the final decode: check work/run_decode.log for BAD/ERROR, out/REDECODE_CHECK.json equal=true; write out/FRAMES_MANIFEST.json (all per-scene manifests + sha256) .
4. Archive (ORCH 1349Z): tar of out/R0_SCENES.json, out/qsets/, out/frame_manifests/, frames/, code/ into one file on /scratch, then copy_archive.py to /data3/jjyeung/ (governed, --writes-nfs; README step 4); IB mirror to trinity-1-13:/scratch/jjyeung/n30_mirror/b10_reserve/ (check df first; trinity-3-30 if 1-13 would keep <150 GB free); sha256 both; record paths in STATUS and the design record.
5. Update distill_design/R0_RESERVE_SCENES_20261116.md (Files, Status: questions + frames hashes, constants table, deferred scenes) and its INDEX line; final RESULT event (questions per type, constants, archive and mirror paths).
6. If b10r0_vid_dev has not finished by 20:00Z, tell ORCH (QUESTION) so it can ask main for a slot.

## Open questions (answered by ORCH 1236Z; in force)
- Streams approved: tier 3, priority 15, one at a time; ScanNet .sens (~25 GB) only if R0-rl needs those 12 captures. Keep 150 GB free on /scratch.
- Wording/answer formats from D0 v5 templates; validate with a41ba191 where traces exist.
- T0/CP1 covered by kit07 frame_map + division A3 (refute review checks).
- ORCH 1306Z: R0 registered (every leg excludes R0 rooms). I order the review myself: Codex review gpt-6-astra high (both census and build_r0 were written by Claude models).

## Must read
LANE_RULES.md; briefs/qs/10_reserve_scenes_r0.md; this file; out/CENSUS.json; events *_ORCH_* in the events folder.
