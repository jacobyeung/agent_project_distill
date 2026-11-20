# Grounding funnel: what the routed reads can establish

**Status: BLOCKED for launch and real stage attribution.** The ground-call serialization overlay, replay manifests, parity guard and synthetic GT join are CPU-tested (nine new tests plus eleven funnel tests). A launch still requires the exact step-544 source pins, an authenticated Orchard entry sequence and a record-backed numeric gap tolerance. The named reader record supplies no such tolerance. The GT inventory identifies 38 of the 60 required captures (160,652,325 bytes); 22 expected files are unlisted, and their sizes and the production NPZ adapter remain unresolved. No GPU inference ran. Missing evidence is not counted as success or failure.

## Question and answer

Where do objects disappear from the routed reader, and how many task points could more ground-call frames recover?

The logs establish sparse selected support, but not its cause. At step 400, 74 distance items have fewer than three printed frames for at least one object; their unit-normalized gap score is 63.11 against 78.00 for 35 items with at least three frames for both objects. Equalizing those groups would add **7.35 distance-task points [0.16, 13.35]**, an association. It does not establish S3 or the benefit of 64/96 frames. The sparse objects could be absent, unproposed, or wrongly selected.

The final answers reverse that comparison: 58.24 against 43.14. Grounding quality and final-answer errors must therefore be priced separately. A measured gap improvement cannot be reported as an answer improvement without replaying the answering path.

Both reads use `candidates_argmax`: **zero observed null selections with a nonempty candidate pool**. A lever that only removes the null slot has no remaining headroom here. Presence can still affect false instances or guide proposal search; those effects remain unpriced.

## Population and inputs

The comparison uses step 544, run `469ddece`, corpus `469ddece_s544_devS1_routed_b1.r1`, and step 400, run `6ed2c7aa`, corpus `6ed2c7aa_s400_devS1_routed_A10b`. Each contains the same 150 distance items, 60 captures, 46 physical rooms and 300 requested object occurrences (218 distinct capture/name pairs). Repeated objects across questions remain separate occurrences because their task weights differ. Names come from the reader's question-only parser, checked against its source on all 300 item/step pairs; names are not GT instance identities.

Step 400 is the newest dev-S1 routed distance read found. The indexed step-600 camera read (`6ed2c7aa_s600_devS1cam_c600_173348`) contains only displacement, rotation and movement direction, 150 each. The top-level corpus `INDEX.jsonl` omits newer entries; individual index files and the reads directory supply the step-400 binding.

| Read | Local input | Bytes | SHA256 |
|---|---|---:|---|
| 544 best-candidate distance | `work/step544.jsonl.gz` | 2,436,727 | `e88ee503404755810a4a5d60296261c0594445562b71fed9e185d6c33b1e5c9e` |
| 400 routed A10b | `work/step400.jsonl.gz` | 4,338,771 | `b64e382559bbfbd79afa5c3a8c05050bd4fcd277665ce492b78fc374047bbc6a` |
| 544 remaining routed types, null-rule read | `work/step544_other_types.jsonl.gz` | 5,044,383 | Corpus pin `92f4ff9469af7184ddc8059bf5586e5386b74b99fd4545d8ef3c712c5acb51ad`; used only to inventory other types |

The source is `/data2/jjyeung/agent_project_data/distill_trace_corpus/reads/`. Matching step-400 results are recorded in `orch_n30/events/cont_ops/20261119T1512Z_RESULT_r1_m400_routed_A_H3_STOP_camera_displacement.md` and `files_m400/ROUTED_A400_scores.json`.

Other types: the 450 camera items do not locate objects. At step 544, the 36 room items contain two unserved `<ground mode="box">` calls with no object name or stage diagnostics; these cannot enter an object-instance funnel. Step 400 has no ground calls on its other routed types. Relative distance, counting and direction are not object-grounding reads in this corpus population.

## Method

S0–S5 follow the brief's order. A missing upstream fact yields U, not a later-stage assignment. The worse object is the one with the **earlier** failure. S3 requires correct identity in fewer than three matched frames, not merely fewer than three printed frames. S4 measures Euclidean distance of the unrounded predicted centroid outside a full-extent annotated oriented box in a common coordinate frame; the threshold is strictly greater than 0.25 m. An aligned centroid does not guarantee correct extent or closest-point distance.

For a future GT join, any raw proposal with target IoU > 0.5 establishes proposal existence. The supplied synthetic matcher binds the selected track to a target when at least half its nonempty member masks have IoU > 0.5, following the cited route-table identity convention. A correct raw proposal lost during lifting enters S2 with an early-lifting subreason if the target is then unselected. Correct support counts only matched member frames. The real join still needs reviewed instance bindings, annotation-validity flags, pose/axis conventions and a matching-rule sensitivity analysis. Any positive GT pixels define visibility for S0; a 154-pixel eligibility gate is a separate diagnostic, not invisibility.

The primary score is the stored final-answer MRA, on the reader's released-label scoring authority. The supplemental gap score converts the printed metres into the requested unit and applies the reader's exact `official_mra` floating-point thresholds against `truth.scored`. Unavailable gaps score zero in the 150-item task denominator. No model answer is changed. This is measurement scoring, not a stage-specific GT intervention.

Intervals use 10,000 bootstrap draws of the 46 physical rooms, seed 20261120, drawing each room with all its items and using item-weighted means. Every group and contrast shares each draw. Percentiles are 2.5 and 97.5. Draws lacking a group have an undefined conditional mean; `summary.json` reports their number. They are not zero-filled or silently redrawn. Intervals are marginal and exploratory.

If stages were observed, a stage's association budget would be `(n_stage / N) × (mean_S5 − mean_stage)`, recomputed within each room draw, signed rather than clipped. No S5 group is identifiable here, so **all requested stage budgets and their confidence intervals are undefined**. The same formula below uses printed-support groups solely as diagnostics.

## Requested funnel

| Stage | 544 object count | 400 object count | Item score / 95% CI | S5-level task points / 95% CI |
|---|---|---|---|---|
| S0: no GT-visible input frame | Unknown | Unknown | Not identifiable | Not identifiable |
| S1: visible, no target candidate | Unknown | Unknown | Not identifiable | Not identifiable |
| S2: target candidate, wrong/null selection | Unknown | Unknown | Not identifiable | Not identifiable |
| S3: correct selection, <3 matched frames | Unknown | Unknown | Not identifiable | Not identifiable |
| S4: correct ≥3-frame selection, >0.25 m outside GT box | Unknown | Unknown | Not identifiable | Not identifiable |
| S5: passes all stages | Unknown | Unknown | Not identifiable | Reference unavailable |
| Unresolved objects with a valid ground call | 298 | 226 | 149 / 113 calling items | — |
| Objects outside the funnel: no valid ground call | 2 | 74 | 1 / 37 non-calling items | — |

An object with no call is a routing omission, not S0 or S1. The complete per-object inventory is `work/objects{544,400}.jsonl`; `work/items{544,400}.jsonl` preserves every item and its diagnostic group. The inventory marks all 300 requested occurrences per step unresolved, with the no-call reason separate.

## What is observable

Object counts below use the first valid diagnostic call for each requested operand. Brackets are room-bootstrap count intervals; the number of items in a room draw can change.

| Observed state, not a funnel stage | 544 | 400 |
|---|---:|---:|
| No valid ground call | 2 [0, 6] | 74 [38, 122] |
| Empty linked candidate pool | 7 [0, 19] | 4 [0, 10] |
| Selected box prints 1–2 frames | 122 [87, 161] | 95 [68, 126] |
| Selected box prints ≥3 frames | 169 [112, 239] | 127 [85, 176] |
| Total requested occurrences | 300 | 300 |

There are 298/229 raw ground-call attempts, including retries. Step 400's three extra attempts are two malformed calls and one unserved attempt. Of the empty linked pools, 6/3 have no retained raw SAM masks; the remaining one at both steps is `vsi590k_161834`, slippers: two retained proposals both fail lifting with `no_eligible_pixels`. This is evidence of **early lifting loss before selection**, not S4. GT is still needed to know whether those masks cover the target.

The per-frame raw proposal counts match on all 226 commonly called object occurrences, while selected frame lists differ on 12. Equal counts do not prove identical masks. The logs truncate candidate detail at 30 candidates; three step-544 occurrences have a larger linked pool. Neither truncation nor high selector confidence can be used to infer proposal absence or correct identity.

### Final-answer scores

| Step | Observable item group | Items | MRA [95% CI] | Equalize to ≥3-frame group: task points [95% CI] |
|---|---|---:|---:|---:|
| 544 | No call | 1 | 0.00 [0.00, 0.00] | 0.17 [0.09, 0.70] |
| 544 | No pair of returned boxes | 7 | 25.71 [16.00, 50.00] | 0.00 [-1.34, 1.39] |
| 544 | Either object prints <3 frames | 93 | 30.11 [22.35, 39.05] | -2.72 [-12.41, 6.95] |
| 544 | Both print ≥3 frames | 49 | 25.71 [11.76, 40.76] | Reference |
| 400 | No call | 37 | 32.97 [15.85, 44.21] | 2.51 [-2.87, 7.84] |
| 400 | No pair of returned boxes | 4 | 22.50 [0.00, 45.00] | 0.55 [-0.31, 1.77] |
| 400 | Either object prints <3 frames | 74 | 58.24 [48.77, 66.92] | -7.45 [-15.42, 0.31] |
| 400 | Both print ≥3 frames | 35 | 43.14 [27.43, 58.71] | Reference |

Overall final-answer MRA is 28.27 [21.10, 36.75] at 544 and 47.53 [39.43, 55.38] at 400. These reproduce the reported point estimates. The table's equalization numbers are associations, not grounding-stage recovery estimates.

### Printed-gap scores, converted to the requested unit

| Step | Observable item group | Items | Gap MRA [95% CI] | Sparse-support association, points on all 150 items |
|---|---|---:|---:|---:|
| 544 | Either object prints <3 frames | 93 | 55.48 [48.02, 63.87] | 11.53 [-0.17, 19.79] |
| 544 | Both print ≥3 frames | 49 | 74.08 [57.88, 84.84] | Reference |
| 400 | Either object prints <3 frames | 74 | 63.11 [54.93, 70.78] | 7.35 [0.16, 13.35] |
| 400 | Both print ≥3 frames | 35 | 78.00 [63.60, 88.82] | Reference |

The unreturned/no-call gaps remain zero in the denominator. The final-answer/gap discrepancy includes unit handling and population composition; it is not a causal claim about either. The supplied R1 trace record's 544 and 200 frame-support results remain prior associations, not stage labels; small differences from its quoted numbers must not be treated as an independent replication because this table pins the released-label authority and exact reader scorer.

## Lever decisions and point limits

No L1–L5 ranking by measured stage points is identifiable. The **only unconditional numerical upper limit** for an intervention restricted to existing calling items is 71.07 final-answer task points at 544 and 35.93 at 400: give every calling item score 100 and leave every non-caller unchanged. This ceiling applies to each lever or their union, includes unrelated answer errors, and is deliberately loose. The lever ceilings cannot be summed.

| Lever | Stages it can plausibly move | Measured recoverable points here | Decision |
|---|---|---|---|
| L1: 64/96 ground frames | S0; S1 if another view yields a proposal; S3 if correct support grows. Other changes are incidental geometry/selection effects. | Unknown; at most the shared 71.07 / 35.93 ceiling | First measure GT visibility on nested frame sets. Sparse-gap association is 11.53 / 7.35 points, not an L1 ceiling. |
| L2: presence before boxes | S2 false-instance/null choices; S1 only if presence triggers a broader search | Unknown; null-slot-removal component is exactly zero on these deployed nonempty pools | Do not repeat a null-only fix. Price false-presence control with identity GT. A hard gate can lose recall. |
| L3: proposals from own tokens | S1; S2 can change when better or distracting candidates enter | Unknown; shared ceiling only | Strongest prior proposal-coverage evidence, but it comes from a different route-table backend. Preserve baseline proposals and price selection harm. |
| L4: association and coverage | S2 identity/linking, S3 matched support; S4 indirectly via mask fusion | Unknown; shared ceiling only | Measure jointly with L1 first: more images cannot repair association by themselves. |
| L5: depth shape and pose | S4 directly; S2 through early lift rejection/linking and S3 through valid lifted support | Unknown; shared ceiling only | Retain as a separate arm. The slippers example proves the pipeline has an early geometry rejection, not its task cost. |

The practical measurement order is visibility and identity instrumentation, then L1/L4 coverage, with L3 proposal augmentation as the next comparison. This is an order for resolving uncertainty, not a claim that L1 has the most recoverable points.

Prior evidence, cited rather than rerun: `B6_GROUNDING_DESIGN_20261115.md` records base presence AUROC .962 and boxes on 92% of absent frames; the user brief supplies 90–93% visible-frame pointing and 83% best fusion on 260 objects. `MASK_PROPOSAL_RECALL_DEVS1_20261112.md` reports +28.29 distance / +23.19 counting for its never-proposed GT intervention on 76/91 GT-covered pairs, and the brief reports 55/224 recovered by dense aliases. These are not the 150-item routed-reader funnel. `R1_M200_TRACE_ANALYSIS_20261119.md` sections 8 and 10.1 report the 544/200 sparse-frame associations; `R1_DISTANCE_NO_CALL_DIAGNOSIS_20261119.md` separates omitted calls and unit errors. `READER_R1_20261117.md` documents the candidate-only selector.

`E3_BACKEND_GEOMETRY_PRICING_20261116.md` provides the requested 62.9 tower / 77.9 GT-geometry reference with GT masks. Its K1 label authority is affected by the extent defect documented in `EVAL_GT_HALF_EXTENT_AUDIT_20261117.md`; that audit reports corrected deployed/GT values 75.1/92.0. Neither comparison identifies S4 or prices L5 on these dev-S1 reads.

## Missing inputs and known copies

| Missing evidence | Known location and size | Consequence |
|---|---|---|
| dev-S1 GT instance rasters, full boxes and poses on exact read anchors | Recovery inventory lists 93 rasters on `trinity-1-18:/scratch/jjyeung/orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt/` (34 mesh, 59 ARKit). `W/kit/rerun2/gt_staging.json` matches 38 of the 60 distance captures, 160,652,325 bytes; 22 expected filenames are unlisted. Current availability and anchor compatibility remain unverified. | Cannot decide S0 or bind targets; 59 captures lacked GT in the original route-table population. Do not infer visibility from returned predictions. |
| Per-call raw and linked masks, chosen masks, unrounded lifts and world transform | No surviving copy identified. A10b `b/e2e_reader/stage1.py:proposal_diagnostics` emits counts, candidate frame lists, feature vectors and logits, not masks. | GT alone cannot identify S1–S5. A logged candidate ID denotes a track, not an annotated identity. Instrumented ground rerun is required unless another journal is supplied. |
| GT/RGB at added 64/96 source indices | No bound dense copy identified for the same 60 distance captures. Existing task rows bind 32 anchors. | Cannot estimate visibility gain or execute the added-frame arms. |
| K1 rasters, if used for a separate synthetic-to-real rehearsal | `K1_GT_RASTER_REBUILD_20261115.md`: 300 pinned outputs total 1,367,513,161 bytes; 296 reproduced. Copies on 1-18 and tar mirrors on 1-3 named in that record. | They are not substituted for dev-S1 frames or labels. |
| Real inference runtime and variable-frame adapter | Local A10b source archive: `/scratch/jjyeung/orch_n30/reads228/kit/A10b/package/0.tgz`, 5,252,970 bytes. This is code, not a ready runtime or dense adapter. | The delivered kit remains blocked. |

The named 1-18 inventory is `B/events/k1_ops3/ORCH_CD_MIRROR_1_18_FILES.txt`, 25,016,605 bytes. A bounded 4,000,000-byte prefix contains all 93 entries in the two named GT directories; that prefix supplies the staging manifest. Three 1,200-byte spot samples also inspected the file's layout. The complete inventory was not read. No SSH, download, heavy IO, stream registration or GPU work was attempted. Sizes for the 22 unlisted files remain unknown. Listed locations and sizes are inventory-backed, not fresh remote verification.

## Phase 2 handoff and tests

`W/kit/tasks.json` plans the 149 and 113 actual calling items, adding frames by midpoint insertion into the largest temporal gap. The 32-frame set is a subset of 64, which is a subset of 96; the answering path keeps its original frames. Non-callers are not forced to route. A 32-frame parity arm is required.

`bash W/kit/run_funnel.sh GPU_INDEX --dry-run` validates the first real capture's metadata and replays its logged selector argmax. `work/first_capture_dry.json` records `scannet/scene0515_00`, `vsi590k_042574`: microwave and lamp selections match the logs; all nested frame plans pass. It stops **before RGB decoding and proposal inference**. No real images or masks were available to the dry run. Without `--dry-run`, the launcher exits 2 and explains the blockers; it cannot launch a GPU.

This is a partial analysis kit, not the requested completed GPU rerun kit. `kit/ADAPTER_REQUIREMENTS.md` specifies the missing adapter. The current reader fixes the frame map, geometry shapes and validity, lifting loops and visibility loops to 32, and selector fractions to 32/31. A naive input-count edit silently ignores extra frames or fails shape/authentication checks. The variable-frame implementation needs review and exact 32-frame parity before GO. No unreviewed rewrite is presented as launch-ready.

Eleven unit tests pass, including all six stages on a synthetic capture, first-failure precedence, unknown visibility, null selection, early-lifting loss, wrong-frame exclusion, the 0.25 m OBB boundary, rotated boxes, nested sampling, room weighting and undefined S5 budgets. Independent comparison to the local reader passes on 300 operand pairs, 513 logged selector choices and 295 official-MRA score pairs including boundary tests. Corpus hashes match the supplied pins (`work/verification.json`). No GPU or real-mask integration test is claimed.

GPU budget: the existing distance reads took 77.30 and 57.96 H100 wall-minutes, including 16.78/5.97 minutes recorded as G3T. Scaling total time by `(64+96)/32 = 5` gives 676.3 minutes. Reserve **680–1,000 H100-minutes** for both steps and both added-frame arms, provisionally, before first-capture timing. This is a planning extrapolation, not a measured bound: ground-only execution omits decoding, while dense tower cost, 96-frame memory and the new adapter can increase time. No claim about a 49 GB card is supported.

## Options rejected, failure checks, and status

- Assigning S3 from the printed frame count would conflate wrong identities with coverage. GT-matched masks settle it.
- Assigning S1 from an empty pool would conflate invisibility, raw proposal failure and early lift rejection. Raw masks plus visibility settle it.
- Using the null diagnostic as an actual rejection would contradict `candidates_argmax`; it would have preferred null on 53/33 returned objects, but did not select it.
- Reusing the old route-table oracle gains as current-reader stage costs would mix populations and backends. An exact item/instance join and stage-isolated rescoring settle it.
- Changing the answering frames, forcing non-callers to call, replacing all anchors with uniform 64/96 samples, or fitting GT scale would change the experiment. The nested manifest and a pinned answer-input hash detect those confounds.
- A correct centroid can coexist with a poor box extent; S5 is not guaranteed to score 100. Report box and gap residuals within S5 after the join.
- Annotation gaps and same-name ambiguity can masquerade as grounding errors. Reject ambiguous bindings, retain unannotated objects as unknown, and disclose coverage by dataset.

The next necessary actions are a small authoritative manifest for the dev-S1 GT/video inputs, governed staging if approved, and an instrumented variable-frame adapter. The orchestrator must review that adapter and assign a card before GPU GO. This lane made no training rows, changed no reader or job, and stopped no other worker. No deletion is needed. The reader-first writing check retained no project-history passage; comparisons in this report are experimental conditions or evidence limitations.

The sealed bundle contains this report, `kit/`, CPU outputs and the compressed input reads. Its path and SHA256 are in the final event and adjacent seal receipt. It has a durable small-archive copy in `B/events/grd_funnel/`; no SSH mirror was attempted under the brief's no-SSH limit.

## Sealed delivery

CPU bundle: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/grd_funnel/20261120T0253Z_grd_funnel1_cpu_bundle.tar.gz` (11657710 bytes). SHA256 computed on scratch: `5c7f30826330f078f3b68ba03d796d02839a95ed69273469ceebfde97fc2401a`. The shared copy completed with rsync exit 0 and matching size; no shared-filesystem checksum read was performed.

## Ground-call rerun kit (grd_funnel2)

The partial kit is `W/kit/rerun2/`. Its first arm replays the step-544 read's 150 distance items: 149 callers, 298 ground calls and 149 gap calls. It preserves the one routing omission, the 32 grounding/LM anchors and the original 64 native G3T frames. One original prompt prefill supplies the own gravity/depth heads; recorded calls then run through the reader's capped hook without generating an answering pass.

The observer serializes every retained raw proposal as RLE with score, presence, prompt and source index; raw-to-linked membership; all accepted candidate masks; full selector inputs/logits/null slot and choice; selected masks; early lift summaries/rejections; final lift support/centroid/extent; the unrounded fitted box; and camera/intrinsic/canvas/scale metadata. It changes no sealed file. The exact local production feature/selection/lifting bodies pass CPU tests with synthetic inputs and producer/weight doubles; the original step-544 package still needs source verification and independent review.

The reader source is record-backed at Orchard `/project/community/jjyeung/b9ef552934627`, job 171253, script `BATCH.sh`, payload prefix `8be887e3`; checkpoint, G3T, SAM and frame inputs stay on Orchard. Step 400 uses A10b `/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164`, job 173060. The inner wrapper `0.sh` specifies general, one H100 and 12 hours. `README.md` supplies the resource submission skeleton and required variables. It is not an executable launch handoff: the authenticated namespace/staging/return integration has not been built or exercised. No existing answer-generating job may be substituted.

Every item must pass frame-list, best-frame, call/status and printed-gap parity before a trusted receipt is written. The named R1 record and its memo smoke event acknowledge GPU nondeterminism but state no numeric gap tolerance. `policy.json` therefore leaves the tolerance unset and live mode fails before runtime imports or weights. The fixture uses 0 m; no fixture tolerance is presented as an approved GPU bound. The output writer refuses above 1,900,000,000 compressed bytes, leaving no trusted receipt on failure.

Nine new tests and eleven existing tests pass. The new tests cover lossless RLE, complete null slots, unchanged production-function returns, parity failures, a hard size cap, exact source frames, unknown annotations, rigid alignment and S0–S5. The four dry runs cover step 544/400 and flags 32/64/96. They reach parsing, 150-item manifests, fabricated all-item parity, synthetic serialization/readback and the synthetic GT join. They stop before reader-runtime imports, RGB decoding, weights, prefill or GPU work. The synthetic one-object/three-frame/one-candidate capture measures 1,344 compressed bytes/item at step 544 and 1,343 at step 400. Real size/item is unmeasured. Full logs are in `W/work/rerun2/`.

`gt_staging.json` and `GT_FILES.md` name all 60 required capture files on trinity-1-18. The recovery inventory lists 38 matching files (4 ScanNet, 11 ScanNet++, 23 ARKit), totaling 160,652,325 bytes; 22 expected files (7/8/7 respectively) are unlisted with unknown sizes. The manifest records exact paths beneath `/scratch/jjyeung/orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt/`. These are inventory sizes, not a fresh remote availability check. `gt_stage_on_1_18.sh`, run on 1-18 after transfer authorization, streams the explicit available-file list directly through `ssh trinity-2-28.ib` into scratch; it never uses `/data*` or a head-node relay. No transfer was run.

The join accepts explicit, reviewed item/name-to-instance bindings; complete per-source-frame masks at raw and selected resolutions; full-extent OBBs; and a reviewed rigid reader-world-to-GT transform. It refuses inferred resizing or GT scale fitting. Its real NPZ adapter remains blocked on inspection of the annotations and poses. The closed-model visibility lane cannot supply the missing instance masks or geometric alignment by itself.

Optional `--frames 64/96` flags parse but refuse live execution until a variable-frame adapter and nested RGB/geometry bindings exist. The baseline's 64 tower images do not establish the requested nested 64-anchor set; no matching 96-frame manifest was found. Step 400's checkpoint and baseline frames are Orchard record-backed. Provisional H100 reservations are 80–120 GPU-min for 544×32, 160–240 for 544×64, 240–360 for 544×96, and 60–90/120–180/180–270 for 400×32/64/96. These extrapolate the 77.30/57.96-minute full reads and require real timing/memory confirmation.

Launch remains blocked on source pins, a record-backed numeric gap tolerance, authenticated Orchard integration and independent review. Full stage attribution also needs the missing GT files, reviewed bindings and NPZ conversion. No GPU, Slurm, SSH, Git, download, closed-model call, training row or worker stop occurred. One initial test helper automatically cleaned its own `/tmp` fixtures; the delivered tests retain them and contain no cleanup. The writing check keeps no revision-history passage; source-package comparisons remain because they bound the evidence.

Partial-kit archive: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/grd_funnel/20261120T0307Z_grd_funnel2_partial_kit.tar.gz` (196541 bytes), SHA256 `17a910f10e3aa18c053954a990c091776331f70c16b3d24e081789b0a0b8cc16`. The durable copy matches the scratch checksum. Final handoff: `20261120T0308Z_BLOCKER_grd_funnel2_parity_policy_and_launch_binding.md`.

## Parity rule for the ground-call rerun (registered 2026-11-20T03:50Z by cont_ops24, before any comparison)

The rerun compares itself with the baseline read (Orchard job 171253, package b9ef552934627, read 1, candidates_argmax) on all 150 step-544 routed-distance items. GPU inference is not bitwise deterministic, so the rule has two parts, and the job writes a trusted receipt only if both hold.
- Discrete fields. For every recorded call, the call text, the served status, the response kind, the printed frame list, the printed best frame and any status text must equal the baseline's. An item matches when all its calls match; the one non-calling item matches trivially. At least 95% of the 150 items (143) must match.
- Gaps. Inside the same job, the first ten calling items run their ground and gap calls a second time with no perception-memo reuse. The tolerance is twice the largest absolute difference between the two printed gaps over those ten items' gap calls. Every gap call of an item whose discrete fields match must lie within that tolerance of the baseline's printed gap (printed metres, as the baseline stores only the printed value).
- A failed rule never suppresses the capture: the job still returns it, the receipt says `trusted: false` with the counts, and any table built from it carries that flag.
- Evidence check: no two existing returns of the same 150 items under one selection rule were found (the step-544 null-rule read uses a different selector), so the rule above stands as ordered. The step-544 stage1.py and grounding.py in the baseline payload are byte-identical to the kit fixtures (sha256 b1a77424…, d8fe3c61…).
