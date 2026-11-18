# Pre-launch card: D0, the data-only reseal of kit 07ca49df (rows v5, sha256 4af43b40, 152,123 rows, admitted 2026-11-16T01:28Z; job B submitted as Orchard 170111)

Lane cont_ops4 (trinity-1-3). D0 is the first leg under the 2026-11-15 trace ruling, and the user sees this card before launch. The row numbers come from rows_rebuild's v1 delivery (`events/rows_rebuild/20261115T1948Z_RESULT_d0_rows.md`, `ROWS_REPORT_D0.md`) the v3 fix round, which keeps every row and changes only targets (`events/rows_rebuild/d0_v3/ROWS_REPORT_D0_v3.md`), and v5, which leaves out the 81 rows whose captures have no frame count (`events/rows_rebuild/d0_v5/D0_V5_EVIDENCE.md`). The procedure is in `D0_LAUNCH_PROCEDURE.md`, the tools in `d0_tools/`. It follows ORCH's answers of 20:15Z (inputs) and 20:18Z (dev list).

## 1. Question the leg answers

Does training the sealed LEG-S1 recipe on rows that obey the trace grammar keep or raise dev-S1 accuracy against the step-544 export? The rows carry no answer-only line, no stated measurement, and the facing fix. The leg also tests whether the toward/away defect can be fixed without tools.

The comparison is the registered test of TRACE_RULING section 2.7: A is step 544 and B is D0 at steps 100 and 200, read with the same reader on the same items, with paired differences and the 10,000-draw room bootstrap.

## 2. What D0 is

**What stays sealed.** The trainer source b01ce449, every gate, the pose and pointing stores, the legacy routing receipt r16 and the recipe (1,000 steps, seed 17, world 4).

**What changes.**
- **VQA store:** 152,123 rows over 2,186 scenes, v5 (rows.sqlite 4af43b40): v4 (v3 with one phrase corrected in 1,227 size rows) without the 81 rows of 31 ARKitScenes captures at 10 fps whose total frame count no source holds (route planning 38, facing 42 = 21 whole pairs, totals 1). The 152,123 kept rows are byte-identical to v4 in row and target. The kit pins a job receipt with the database at an opaque job path.
- **Pool selection:** the sealed selection with ROUTE_direct DEFERRED in the sealed SCENE_room_sppK form, selected rows 92,607 -> 83,184 (rows_rebuild's `pool_selection_d0_v2.json`, bb5483e7, staged under an opaque name). Deleting the entry instead makes relocation and materialization raise KeyError.
- **Warm start:** the step-544 export (artifact 1d6eeb28, `lm: full`, `heads: [pose, depth]`) under a new run identity. Its bytes are only on GCS; the CPU job reads the four parts with the Orchard gcloud configuration and repacks them.
- **Dev withheld list:** sealed (969cdb56). A new list cannot be pinned in a data-only reseal, because the pool manifest, the pool selection, upstream scene reports and the scene reference all bind the old list (see confound 6).
- **Kit:** derived from the sealed kit only by `derive_kit.py` (closure walk of every new document; additions only in fresh directories; staging edits limited to changed inputs); a job-side check (`vt.py`) verifies every new archive's actual members before staging. The job A kit is PREPARATION_ONLY (mode p); job B's kit is derived again with the final rows, new tokens and READY records bound to its identity.

## 3. Confounds (each will be stated in the run identity and the read reports)

1. **Routing-opener reset** (accepted, ORCH ruling 19:15Z). Final mode re-initializes the routing-opener embedding rows after the LM load (`carrier_c1_run.py:781-783`), so their 544 trained steps are discarded. Routed calls are relearned in the first steps: LEG-S1 from m200 had routing loss 1.18 at step 1 and 0.08 at step 18. The step-100 read reports the call rate. The fix goes into the A0 tree.
2. **Warm start with a new run identity.** The optimizer state is fresh, warmup and the LR schedule restart at step 0, and the sampler starts its plan at step 0. D0 at step N differs from LEG-S1 at step 544+N in data, optimizer state and LR position.
3. **Route planning moves to the VQA stream.** Rule S1-RD1 would empty a route-planning think in the routing stream, so 8,894 route-planning rows become direct VQA rows (7.5 rows per step, against 10.5 routed rows per step in the sealed leg). The 38 route rows of the 10 fps captures without a frame count are left out (the sealed routing stream carried them with a lower-bound frame count, a rule the VQA stream does not apply).
4. **Room programs kept.** The 581 sealed room programs, with ground-truth responses, stay in routing. Direct room rows wait for A0.
5. **Ground-truth program responses.** Every program row prints the ground-truth tool response. F3 is therefore reported, not used as a stop rule.
6. **Scope limit: the 80 withheld rooms are held out for the direct-question families only** (ORCH ruling 20:18Z). D0 keeps the sealed dev list 969cdb56. The 80 rooms of `WITHHELD_ROOMS_80.json` are out of D0's VQA store, but their routing programs (783 absolute-distance and 105 room rows) and their camera, pose and pointing rows remain in D0's training. No room-size or absolute-distance route decision, and no claim of held-out rooms for a routed type, may therefore be made on those 80 rooms with a D0 checkpoint. A0 excludes them from every stream.
7. **Trace forms change for every VQA row**, so a change in any type's score mixes the effect of the form with the effect of the warm start.
8. **Counting and size carry no evidence in most rows** (ORCH 21:58Z, stated weakness). The fix round found their cited frames contradicted by ground truth, so 9,169 of 9,253 counting rows give the procedure with no quantity or frame, and 9,622 of 9,778 size rows name the object with no frame. With the 355 appearance-order rows that drop their frames, 19,146 rows (12.6% of the 152,123-row direct-question store, about 16 of 128 direct rows per step) are procedure-only, which the rows reviewer judges answer-only in substance (`events/review_rows2/REVIEW_VERDICT_D0_ROWS_V3.md`). A0 repairs this with verified first-seen frames.
9. **Source frames kept where ground truth is silent.** Appearance order and relative distance cite ground-truth first-seen frames where ground truth covers the object (68% and 61% of citations are uncovered and keep the source frame); on the checkable citations 6.9% and 6.6% are not ground-truth-visible, nearly all two pins before ground truth's first frame. The reviewer expects a frame error of about 7.3% (appearance order) and 10.1% (relative distance) on the uncovered source citations. 355 appearance rows drop their frames because the corrected frames would contradict the order. The per-step mix below is unchanged from v1.

## 3a. Known weaknesses of the rows
- 19,146 rows (9,169 counting, 9,622 size, 355 appearance order; 12.6 percent of the store, about 16 of 128 direct rows per step) carry a procedure sentence with no frame and no number. They meet the trace ruling's letter and are answer-only in substance (the confirmation reviewer's judgement). Their source frame citations disagreed with ground truth on about a third of the checkable cases and were dropped.
- Appearance-order and relative-distance rows keep source first-seen frames where ground truth does not cover the object; expected frame error there about 7.3 and 10.1 percent.
- The re-rendered direction rows (about 50,000) cite no frame; ground truth covers all three objects in too few of them.
- The 80 withheld rooms are out of this store only; D0 keeps the sealed exclusion list, so no routed-type decision may be made on those rooms with a D0 checkpoint.

The procedure-only rows are kept: that is the default, and the user has not answered the question.

## 4. Row mix per step (288 rows: pose 64, VQA 128, routing 64, pointing 32)

**VQA (128 per step) at natural share; 152,123 rows give 0.84 passes over 1,000 steps for every family.**

| Family | Trace form | Rows | Rows/step | Sealed rows/step |
|---|---|---:|---:|---:|
| Direction easy (re-rendered) | find the three objects (no frame), the relation, the heading, the answer | 12,969 | 10.9 | 15.1 |
| Direction medium (re-rendered) | same | 15,547 | 13.1 | 18.4 |
| Direction hard (re-rendered) | same | 21,385 | 18.0 | 25.2 |
| Facing easy / medium / hard (twins) | one Seen line naming each object's first-seen frame, the relation, the heading, the answer | 15,024 / 10,912 / 9,022 | 12.6 / 9.2 / 7.6 | 0 |
| Relative distance | locate the anchor at its first frame (ground truth's where it covers the object), candidates ordered by distance with no metres, the answer | 20,665 | 17.4 | 24.6 |
| Object size | the object named (ground-truth first-seen frame in 156 rows, no frame in 9,622), the number as answer only | 9,778 | 8.2 | 11.7 |
| Counting (re-rendered) | the category and the counting procedure, no quantity or frame (84 rows keep ground-truth first-seen lists), the total without a noun | 9,253 | 7.8 | 11.1 |
| Totals | instances per category by first frame, the sum written out | 1,239 | 1.0 | 0 |
| Appearance order | sealed passing traces, frames corrected to ground truth where covered; 355 rows without frames | 13,622 | 11.5 | 17.0 |
| 3D box | one line with the object's frame, then the box JSON | 3,813 | 3.2 | 4.8 |
| Route planning | one Step line per waypoint with its turn, the turn list | 8,894 | 7.5 | 0 (10.5 routed) |
| **Total** | | **152,123** | **128** | 128 |

Every v3 row passes trace_grammar a41ba191 (sentences written without number agreement, e.g. "I find the shower walls behind me: turn back."), all scenes are in VQA division 4c230a7e, every cited frame is in `k/frame_map.jsonl.gz`, and qids are unique. Sealed abs-distance (26,876) and room (387) VQA rows are left out, as the kit drops routed types from VQA anyway. Trace forms are read from `events/rows_rebuild/SAMPLES_<family>.md` (first sample of each).

**Routing (64 per step), at natural share; 47,732 program rows give 1.34 passes.**

| Type | Rows | Rows/step | Sealed rows/step |
|---|---:|---:|---:|
| Camera displacement | 14,020 | 18.8 | 15.7 |
| Camera movement direction | 12,260 | 16.4 | 13.7 |
| Camera rotation | 9,143 | 12.3 | 10.2 |
| Object absolute distance | 11,728 | 15.7 | 13.1 |
| Room size | 581 | 0.8 | 0.65 |
| Route planning | 0 | 0 | 10.5 |

**Pose (64 per step) and pointing (32 per step)** use the sealed stores unchanged: pose 194,987 rows (0.33 passes), pointing 20,239 rows (1.58 passes).

## 5. Gates before the first GPU step

1. **Rows.** review_rows2's confirmation of the v3 store, ORCH's admission of v5 (an independent read of the v5 evidence first), and the v5 upload verified on Orchard.
2. **Kit.** derive_kit pass 1, the confirmation review, independent review of the derived config and admission contract, a read-only staging verification, pass 2 and an ANON_OK content scan; locally `b/g.py check p` and `b/a.py`.
3. **m544 repack, inside a job on node-local `/tmp` (done by job 170050: `okh7/i_bb09a77d/m.tar`, 42457dbd, and its GCS copy).** Members `m544/…` become `ap/8865619b/runs/469ddece/m544/…` (staged into the union, which `tk_stage_init` reads), plus the artifact.json copy at `ap/d0i<run>/m544/artifact.json` outside the per-job kit root. The repacked archive goes to GCS under a new name with its sha256. The kit lists the artifact, heads and manifest by sha256 and the shards by name; `tk_stage_init` verifies every shard against the sha-pinned manifest.
4. **CPU job A2 on `general`** (job 170109, running since 2026-11-16T03:28Z; job 170050 failed in preparation on the 81 rows v5 leaves out). Stage 1: `vt.py`, `r.sh p 0` (native full-population admission, which settles whether VQA admission takes route-planning rows) and a read-only family census (admitted and refused rows per family); its status goes to project and GCS before stage 2. Stage 2: the sealed CPU first batch, four rank processes at once (16 threads each), within a 3 h cap; a rank the cap ends is reported as not measured. Job B is cancelled before it starts if stage 1 fails or if any rank stage 2 measures raises or gives a non-finite loss.
5. **Advanced job:** mode t with in-job admission and the GPU first-step gate `all_rank_native_v1`.

## 6. Stop rule and reads

- **At steps 100 and 200 the leg reports TRACE_RULING 2.7 F1 to F4 against step 544.**
  - F1: no tested direct type (route planning, counting, direction easy/medium/hard, relative distance, object size) has B minus A wholly below zero.
  - F2: on the 150 facing twins, away accuracy clears 54/40/36, at most 20% of pairs give the same answer to both twins, and toward accuracy does not fall.
  - F3 (deployed responses and fallback) is reported only. The step-100 read prints the call rate for the opener-reset recovery.
  - F4: any routed-versus-direct win is reported for the next seal.
- **Registered stop rule** (`distill_design/D0_STOP_RULE_20261116.md`): stop at step 200 if F1 fails. If F2 fails while F1 passes, stop unless away accuracy beats step 100's on at least two difficulty levels and beats step 544's on all three; in that case, read once more at step 400. The reads decide, and the leg stops only on ORCH's word after a read.
- **Operational gates:** admission refusal; the native step-1 gate; a step-1 loss check of pose, VQA and pointing against m544's steps 530 to 544 (routing exempt because of the reset); the wall-clock budget stop; scancel on alarm.
- **Exports:** steps 100 and 200 need upload sessions minted for D0's run name before launch.

## 7. Cost and allocation

- **Training:** 1,000 steps at about 131 s is 36.4 h: two advanced allocations of 4 GPUs for 24 h, about 146 to 190 GPU-hours with admission. The second allocation resumes exactly from D0's end slot.
- **Reads at m100 and m200:** step 200 lands about 7.5 h after the first step, inside the first allocation.
- **Advanced QOS:** 4 GPUs per user, shared with the LEG-S1 continuation, main and native_r2. D0 and the continuation cannot run at the same time.
- **Project space:** 176 GB free at 00:42Z; each allocation's end slot needs 113 GB plus 20 GB to spare, and the second allocation writes the other slot while the first stays.
  - If project lacks the slot plus 20 GB at an end slot, `jb.sh` streams the slot from node `/tmp` to one GCS object (`q8/d2d30e36/359fcc3c_s<step>.tar`, about 16 min at the measured 121 MB/s), checks its size and md5, and records it in `o/<job>.SLOT_TO_GCS`, so the exact resume survives.
  - Only if that upload also fails are the optimizer state and the exact resume lost. The weights survive in every case, because every milestone export and the stop export go from node `/tmp` straight to GCS; the next leg would then warm-start from the stop export, as D0 itself starts.
- **CPU job A2:** one `general` slot, 64 cores, 800 GB, 6 h: staging, mode p (1 h 45 min in 169097) and the census, then at most 3 h of CPU first batch with the four ranks in parallel (about 100 s per row by estimate, 72 rows per rank, so all four ranks should finish within the cap).

## 8. What D0 gives up against A0

- GF-1 geometry fusion.
- In-tree grammar refusal: D0 relies on the build receipt only.
- Per-type quotas beyond what the store composition gives.
- Room direct rows, unit rows and recovery (failed-call) rows.
- Deployed responses and fallback (K1).
- The contract fixes: near-nadir guard, one candidate universe, per-row audit deferral, `response_status`, `points_cut`.
- The routing-opener warm-start fix.
- Withholding of the 80 rooms from the routing, pose and pointing streams.
- DX direct-data scale.

D0 keeps the ruling's main change: no answer-only rows and no stated measurements in any language row.
