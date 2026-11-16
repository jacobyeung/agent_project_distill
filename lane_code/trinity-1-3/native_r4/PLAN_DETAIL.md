# native_r4 plan detail: VSTI native read of step 544, camera calls served (2026-11-16)

## 1. What exists where (checked 06:10-06:25Z: Orchard listings work/inv/inv1.out, inv2.out; one ssh to trinity-1-13, work/inv/n113.out)
| Thing | Where | Size / count | Status |
|---|---|---|---|
| VSTI-450 v3 items | Orchard `okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs/` (450-item json, 203,124 B); same file in main repo `agent/` | 9 types x 50, all ScanNet val, 311 scenes | exists |
| VSTI full test + erratum | same Orchard dir: test 5,736 items (2.0 MB, 312 scenes), erratum list 306 dropped items, FULL_SCENES (sampler, shard plan), release-video manifest (312 shas) | 5,736 | exists |
| Release videos | Trinity `/data2/jjyeung/raw_datasets/vstibench_hf/` (ScanNet.tar.gz 5.53 GB; extracted 312 mp4; sha list); Orchard `cp4tk_eval/inputs/data2root/.../` video root (content and shas: listing inv3 running) | 312 | Trinity verified; Orchard unverified |
| 32 LM frames for VSTI in the kit's PNG/sha format | nowhere (GCS evalx_native holds only dev-S1 frames/masks/geometry) | 311 x 32 = 9,952 PNG, ~4-5 GB est. | must build |
| Pose-tower raw cache (frozen G3T at 32 frames, `g3s32/g3t/<ds>__<scene>.npz`) | dev-S1 only (geometry_8c58df..., 157 captures, 3.8 s/capture, ~10 GB peak). Old June `dense_backbones/g3t_scaled_con_dense_outputs` for 312 VSTI scenes on /data2: different producer, not admissible | 311 captures | must build (G3T on a card) |
| G3T weights (tree `student_pilot/tower_read.py`: weights d460957b..., config 5aeb2acd..., revision c55e91a0) | on Orchard: unverified (inv3 running) | ~ | verify |
| Step-544 export, base, runtime, numpy, trainer tree, bwrap | Orchard (C8r FAMILY assets; nr2tmp/direct544) | base 19.3 GB, runtime 8.1 GB | exists |
| VSTI scorer | main repo `agent/evaluation/_score_index_vstibench_mechanical.py` (official five-subtask collapse: rel_dist v1-3 and obj_obj lr/nf/ud each collapse); Orchard `official_reads/tree/official/score_and_aggregate.py` (produced the 450-set primaries below) | ~ | exists; port one, check equal on old predictions |
| Same-item comparators | Orchard `official_reads/scores/o_f17_vsti`, `o_p1w4m200_vsti` (per-question scores, 450 items each): f17 primary 66.95, P1 m200 68.71; camera displacement 36.6 / 39.6, movement direction 50.0 / 66.0 | 450 each | exists (other models; item-paired) |
| Step-544 direct VSTI read | none found | ~ | absent |

## 2. Camera categories
VSTI has no rotation type. Camera questions: `camera_displacement` (50 in VSTI-450, 50 scenes; 833 in full) and `camera_movement_direction` (50, 50 scenes; 913 in full); 86 scenes carry one. Wording names the frame pair "between frame 8 and frame 20 of 32", so the 32 LM frames must be VSTI's own 32 sampled frames. Not camera calls: `camera_obj_abs_dist`, `camera_obj_rel_dist_v1/v2/v3` (camera-to-object; need object grounding) and `obj_obj_relative_pos_lr/nf/ud`: every call on them except a camera call is refused.

## 3. What must be built (smallest change to C8r, code f4535bc0)
1. Item adapter: VSTI-450 v3 -> kit TASKS (all nine types; ids, GT, options, scene); frame-pair parse for "frame A and frame B of 32".
2. Frames: VSTI's 32 frames per scene from the release videos with the benchmark's sampler (same as the comparator reads' `prepared_32`, to be matched by sha), PNG + inventory; staged to Orchard through the governor (or decoded on Orchard if its videos match the release shas).
3. Pose tower in the job: `geometry.tower` on the 311 scenes (dense_frames 32, slots 0..31) before decoding, then the existing `prepare` with step-544's own depth (scale) and gravity heads; existing gravity guard unchanged.
4. Serving policy "camera only": serve `move`, `turn`, `pose`; refuse `ground`, `depth_at`, `box_3d`, `gap`, `surface_pair` and all others with a fixed refusal response, record each refusal, let the student finish; score its final answer. No mask cache, no selector bound.
5. Arms: native only (default; see question). Scripted camera program on the 100 camera items (CPU, same tower) kept as the program reference.
6. Scorer port + report: per type and per the five official subtasks: items, call rate, served and refused calls, score with a scene-clustered bootstrap interval; camera types beside f17 and P1 m200 on the same items (labelled other models); headline marks every category with refused calls.
7. Canary: first 10 items (2 displacement, 2 direction, 6 spread over the others) decoded, checked (calls parsed, served, refused, answers scored), projection written; the job continues only if the canary passes. Order after the canary: camera items first, so a time-out still returns both camera categories.
8. Return path unchanged (pool `okh7/n2r/<token>` + GCS q8/n2r/<token>).

## 4. GPU time (one Orchard H100; rates from events/native_r2/20261116T0515Z_RESULT_decode_times.md)
- Staging and load: ~0.5 h (dev-S1 job: 2,929 s outside items for 84 captures, incl. geometry prepare).
- Pose tower: 311 x 3.8 s = 20 min + load; prepare ~10-20 min.
- Camera items: 50 x 6.0 s + 50 x 7.3 s = 11 min.
- Other 350 items: no measured VSTI rate for step 544. If it answers directly (~150-300 sampled tokens at ~21 tok/s) ~10-15 s each = 1.0-1.5 h; if it calls the refused tools and runs to the 2,048 budget, up to ~100 s each = 9.7 h.
- Total: central ~2.5-3 h; worst ~11 h, above the 6 h full limit. The canary measures the call rate on camera-object items and the job projects before continuing.
- Full 5,736: camera 1,746 x 6.6 s = 3.2 h; others 3,990 x 10-100 s = 11-110 h. Not one job.
