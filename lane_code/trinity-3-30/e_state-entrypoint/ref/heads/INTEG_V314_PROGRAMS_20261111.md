# v3.14 programs in the student decoder (integ_v314): review record

Status: USE AFTER FIXES (Claude Opus cross-family review, 2026-11-11, CPU only). The Codex lane integ_v314 built the patch and claimed PASS.

## Where
- Patched tree: /scratch/jjyeung/orch_cd/integ_v314/work/tree_v314. The base it was copied from is /scratch/jjyeung/orch_cd/integ_v3/work/tree.
- Patch: /scratch/jjyeung/orch_cd/integ_v314/out/INTEG_V314.patch (1,318 lines, 9 files). The lane's record is out/RECORD.md.
- Verdict: /scratch/jjyeung/orch_cd/integ_v314/REVIEW_VERDICT.md. Checks: review_work/parity_check.py, with results in review_work/PARITY_RESULTS.json.
- Reference: gt_ceiling/work/tp/prog_v2.py; generator derivgen_v7 (gt_ceiling/work/v314/derivgen_v7); design record GT_CEILING_DECOMPOSITION_20261111.md.

## Question
Does the student's integrated generate() parse and execute v3.14 programs exactly as the v3.14 trace generator writes them and as prog_v2 computes them, without changing how a v3.13-trained model behaves?

## Answer
For the arithmetic and the text, yes. The box_grid_5cm rule, the minimum over instance pairs, the camera-gap distance, the tilted-box envelope, the fused full-height box and the 3D merge all equal prog_v2 on the same inputs. The runtime also re-produces the generator's responses byte for byte. Three problems remain before a v3.14 GPU leg:
1. Nothing binds a checkpoint to its program version. The GPU adapter builds v3.13 sessions, and v3.13 sessions accept the v3.14 grid and camera forms, so a v3.14 model would run the old rules silently.
2. On own-head masks, one box-less or fragmentary instance hides the whole category. prog_v2 skips such an instance.
3. The exact-frame gate keys on a `frame_of` attribute that no production geometry class defines, so it never filters a frame.

## Evidence
- Grid: 281 real smoke distance rows, 779 gap values, maximum difference 0.0 m against prog_v2 `C.box_box_dist`; the relative winner matches on 196/196 rows.
- Camera-gap function: exact on 300 boxes. Tilted envelope: encloses every corner on 15 real and 100 synthetic boxes, and the measurement uses the private box.
- Fused box: equals `gbox_full` on the same points. The 20,000-point cap against prog_v2's 4,000 changes box lengths by at most 2.5 cm.
- Merge: 40/40 equal counts against `merge_count` on identical sightings.
- Version leak: a 3.13 session answers `rule="box_grid_5cm"` and `<gap camera=...>` with distances.
- Whole-name failure: one instance without a box returns `chair: box unavailable`; 9 instances return `unresolved`.
- Camera rule: the runtime and the generator take the nearest instance supported in the asked frame; prog_v2 takes the largest-mask instance. A two-instance case gives 1.25 m against 5.00 m.
- Training data: no training row contains `<gap camera=`, because render_full never calls render_camera.
- Round trip: the 516 rows are rel_distance 196, direction medium 131, direction hard 104 and abs 85, with no counting, size or camera rows. Its box provider returns the generator's own boxes, so it proves interoperability, not perception-path parity.
- tests.test_integ_v314 passes 16/16 on my rerun.
