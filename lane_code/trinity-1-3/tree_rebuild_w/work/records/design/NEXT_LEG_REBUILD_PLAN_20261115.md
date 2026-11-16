# Rebuild plan for the next training leg after the trinity-2-18 loss (design record, 2026-11-15)

Lane seal_plan, trinity-3-30. Sources: the recovered briefs, orders and verdicts in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/recovered/recovered_briefs_20261115_v2.tar.gz` (INDEX_v2.tsv beside it; paths below written `rec:<lane>/<kind>/<file>`), the design records under `/data2/jjyeung/agent_project_data/distill_design/`, `ORCH_STATE_SNAPSHOT_20261115T0930Z.md`, `orch_n30/events/evalx27/ORCHARD_INVENTORY.md`, `orch_n30/events/k1_ops3/ORCH_CD_MIRROR_1_18_FILES.txt` and `RECOVERY_MAP_2_18_OUTAGE_20261115.md`. "Unverified" marks every claim that no listing made today supports.

## Question

What did the lost stacked-seal work (trainer tree `rs_tree/work/tree_r1`, rows `rs_rows/out/rows_r3`, grammar `trace_grammar.py`, contract patches `rs_contracts` R2, coverage and census outputs) contain, and what is the shortest path to rebuild it into a launchable next leg from the step-544 export?

## Answer

- Everything the lost lanes were asked to build survives as text: 7 tree briefs, 3 row briefs, 2 contract briefs, the census briefs, 3 tree-review verdict summaries, the contract review summary, and every RESULT event the orchestrator read. The code itself does not survive, except one file (`r1_contract.py`). Every change can be re-specified from text; none can be copied.
- The base most likely survives twice: trinity-1-18 `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872` (792 files), which rs_cover named as the production source of the sealed leg, and the kit 07ca49df material on Orchard. Its seal must be recomputed before any build (section 2).
- Row rebuilding depends on one unverified fact: whether the sealed leg's input stores on Orchard hold the full routing and VQA pools (including the 75,910 deferred programs from which the facing pairs came). A read-only Orchard inventory settles it in under an hour and is the first step of the critical path.
- A first configuration (A0) can launch without geometry fusion and without the K1 selector refit: the trace-ruled direct rows, GT program responses carried over through the masked event path, simulated-miss recovery rows, room size direct, 80 rooms withheld. The trace ruling (section 2.8, row "The deployed cache is late") already names this fallback; the run identity must record it. It costs about 146 GPU-h for 1,000 steps at world 4 (estimate, 131 s/step measured on the sealed leg).
- Rebuild to A0 launch: about 30 to 40 agent-hours of builds and reviews, in three parallel lanes, about 1.5 to 2 days of wall clock; then a frame-host CPU job on Orchard, then the GPU.

## 1. What the lost tree contained beyond its base

Base: `leg_s1_tree/work/tree_s1` (11 MB code; rs_tree BRIEF.md step 1). Output: `rs_tree/work/tree_r1` with `out/TREE_R1.diff`, per-file sha256, reports R1 to R5, card `out/PRELAUNCH_CARD_DRAFT.md`, dispositions R3/R4/R6. Pass 6b was still running at 09:57Z; its result was never read.

| Pass / review | Change or finding | Source | Re-derivable from text |
|---|---|---|---|
| P1 (05:08Z) | Copy tree_s1 to tree_r1; bind init to the step-544 export identity (`evalx/.../step544_e193c2a3c/PACKET.json`) and four-stream facts; a changed mixture or code identity refuses exact resume | rec:rs_tree/written/*L635_BRIEF.md; RESULT 0512Z, 0531Z | Yes. PACKET.json is lost; the identity survives as artifact sha `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef` and in the Orchard return `okit/evalx_results/e193c2a3c/result.tar.gz` (metadata/EXPORT_ARTIFACT.json, per evalx27) |
| P1 | Direct-target trace contract and validator `student_pilot/r1_contract.py`: non-empty trace; every quantity supplied by frames, a printed response or explicit computation; mutation tests (old format, missing trace, wrong unit, wrong scene, stale pin) | same | Yes; a 4,521-B copy of `r1_contract.py` (01:25Z, an early pass) is on trinity-1-18 |
| P1 | GF-1 in the stack from `gf1_fusion/out/GF1.patch`; stage 1 trains only the geometry adapter (LM frozen), stage 2 full fine-tune; geometry from dense frames, then subsample | same; review 1 verified stage 1 trains only gf1 at lr 1e-4, stage 2 trains LM, heads, connector and gf1 (gf1 at 6e-6) | Yes. GF1.patch is lost, but the base tree already holds `gf1.py`, `gf1_config.py`, `gf1_memory.py`, `dense_eval.py`, `configs/gf1_stage{1,2}.json` (1-18 listing), and `GF1_FUSION_CONNECTOR_20261111.md` specifies it |
| P1 | Pre-launch card draft (mix per step, stages, LRs, stop read, memory, eval protocol) | same | Yes, as a new card |
| Review 1 (tree_review, NOT READY, 06:21Z) | (1) per-row admission hashed frames via raw logical paths (`r1_contract.py:45-52`, `carrier_c1_run.py:1047-1051`), bypassing `STUDENT_FRAME_ROOT_MAP`; (2) no materializer from rows to the VQA/routing stores, membership manifest and `geometry_dense`; 118,753 of 222,571 rows `frames_pending`; (3) kit did not stage (`launch_s1/build.py` ignores the config, refuses `geometry_online` at :89, closure check :26-30, layout :79); (4) 36/64 routing and 44/128 direct slots had no rows; (5) a second camera connector; (6) two dense-frame rules (`r1_dense.py:33-37` vs `dense_eval.py:7-19`); (7) grammar holes: `120cm`, number words, bare "Relate: The answer is A.", Step-only filler; (8) no tower scene evidence | rec:tree_review/results/*L1692*, *L1697*; rec:rs_tree/written/*L1722_BRIEF3.md | Yes (findings are explicit) |
| P2 (05:45Z) | Contract = shared grammar validator (no call tag, no `<tool_response>`, no number outside the allowed set, no empty think); program rows only through the masked event path (`carrier_c1_routing.py:467-468`), allowlist absolute distance, room size, camera displacement, movement direction, rotation, ending in `<answer>`; intake entry for row manifests and coverage lists with per-type admitted/refused counts; apply rs_contracts R2 patches; never the `level_basis` heading switch; card with the 288-row step, census, F1-F4 reads | rec:rs_tree/written/*L1253_BRIEF2.md; RESULT 0551Z, 0608Z (98,753 R2 rows pass intake; patches integrated) | Yes |
| P3 (06:23Z) | All eight review-1 fixes: root map; materializer `r3_materialize.py` with a production caller for `r1_dense.build_training`, RGB pins joined from `p1c_build/k6/MAP.jsonl.gz`; kit builder `launch_r3/build.py` staging from empty; sealed program families carried unchanged through the event path; renormalized mix with no empty slot and about 4 repeats max (room capped); one connector (camera connector removed: GF-1 needs none); one dense-frame rule with a test; grammar holes; component classes (external frozen towers exempt and disclosed; project-trained components must pass) | rec:rs_tree/written/*L1722_BRIEF3.md; RESULT 0638Z (97,581 rows joined; 1,172 room rows without lineage), 0716Z | Yes. The k6 MAP is lost on 2-18; copies are unverified (Mind batch 4 `p1c_build_d451`, code-aws, Orchard staging) |
| Review 2 (tree_review2, NOT READY, 07:28Z) | Closed: root map, staging, one connector, dense rule, four grammar holes. Still admitted: "half a meter", "a dozen", "So the answer is A.", "Option A is correct.". N1 dense clips must be keyed by content (2,115 of 3,242 scenes carry two canonical names, 630+ scenes two clocks 30/10 fps, 1,433 scenes one hash in several stores); N2 pose `frame_prefix`, all frame roots named; N3 9,404 route-planning ids collide, select by type; N4 bounded frame-hash memo; N5 selector role binds the fitted selector, box policy role, evidence as hashed records, refuse the deployed selector for ReVSI/VSTI and for rendering training responses; N6 exclusion accounting with upstream receipts, `scene_coverage=None` refuses; mix repeats after filtering; exclude the 1,172 lineage-less room rows in the tree | rec:rs_tree/written/*L2268_BRIEF4.md; rec:tree_review2/results/*L2255* | Yes |
| P4 (07:29Z) | N1-N6, mix; real readers to the "needs the frame host" marker for every family | RESULT 0740Z (13 families reach the boundary; 47,732 programs; 9,404 filtered), 0810Z (46 tests; evidence refuses for overlap; coverage 1446/1747) | Yes |
| P5 (08:11Z) | Component policy by class and phase: frozen external towers exempt and disclosed; init and heads `overlap_outside_claim_scope` (claim scope VSI-Bench, VSTI, ReVSI, each also without ARKit venue 381879; refuse STI-Bench, ReSTI, MindCube reads of this lineage; dev-S1 paired-comparison only); evaluation-time program choices gate native evaluation until the dated freeze file, except VSTI camera routing; 27 qualification rooms do not bind (default). Room size direct; program allowlist absolute distance + three camera types. Withhold 80 room-label rooms (seed 20261115, 40 ScanNet + 40 ScanNet++, digest `bf737b729a8f9414f400a639d33e997242f1788353ccab5e0c4e1f0fdb12e09f`). Cover the 301 uncovered statements or put them in one frame-host CPU job | rec:rs_tree/written/*L2684_BRIEF5.md; RESULT 0819Z, 0855Z (coverage 2057/2085: 5 CPU-only, 6 model-loader, 17 frame-host; `out/HOLDER_CPU_JOB_R5.md`) | Yes. The 80-room list can be regenerated from the seed and checked against the digest only if the same eligible-room input exists (unverified) |
| Review 3 (tree_review3, READY AFTER FIXES, 09:09Z) | Review-2 findings closed; 16 sources reach the marker with no refusals or duplicate QIDs. F1 pose repeats (18,547 admitted pose rows at 64/step; production binds a second pose source); F2 frame-host per-file limit 1 GiB below the stores (vqa ~3.2 GB, routing ~1.7, pose ~1.5): raise to ~6 GiB; F3 registry and run identity pin node paths; carry records in the kit under opaque names compared by sha256, no project word in any job-visible path, site = the cluster of job 169097 (Orchard); F4 evaluation scope gate keyed on the bank actually read; venue 381879 read allowed with both scores; F5 dense manifest unowned; F6 frame-host job time and no-progress limits, trace only this leg's path; four further low-risk grammar holes | rec:tree_review3/results/*L3133*; rec:rs_tree/written/*L3149_BRIEF6.md | Mostly. The "further findings" list and the four grammar holes were cut off in the orchestrator's output: unverified |
| P6 (09:11Z) / P6b (09:27Z) | F1-F6 fixes; two configurations from one source selected by one bound field: (a) full stack with GF-1 (needs the dense manifest), (b) the same leg without the connector (32-frame stores only), both staging from empty and passing step-zero parity; metadata repeat check before materialization; disk guard (no full store on a local node; 200 MB temp cap; test) | rec:rs_tree/written/*L3149_BRIEF6.md, *L3227_BRIEF6B.md; RESULT 0921Z (step-zero parity both stages and both modes; `POSE_RECONCILIATION_R6.json`: production binds two pose sources, the local replica one), 0934Z (disk guard, 7 tests) | Yes. P6b's completion (F2-F4, F6, grammar, both configs from empty) was never reported |

Contracts (rs_contracts, lost): R1 (05:19Z) three patches against tree_s1 (`PATCH_geometry`, `PATCH_candidates`, `PATCH_box`); the conditioned near-nadir guard `validate_up_convention` served 12/12 refused captures and 21/21 distance items on the raw-G3T proxy; 300/300 operands agreed. Review rc_review: INTEGRATE AFTER FIXES: drop `level_basis` (frame-1 heading everywhere; degenerate heading refuses with an emitted status, metrics stay served); `audit_training_contract` (`s1_routing.py:403-406`) defers bad rows one by one with a reason instead of aborting (a ground A, "not seen", ground B row; a call without a response raising KeyError; a legacy row missing from the manifest); one phrase normalizer (bind or remove `sam3_tower` SINGULAR / `normalize_phrase` and `reader.phrase`) with an independent-input comparison instead of the tautological 300/300; `response_status` must not count bare "unavailable" or multi-line partial failures as ok; version-flag the `points_cut` fix; fix the bare `session.geometry_mode` read. R2 (05:53Z): all applied, 289/289 changed lines covered, `heading_unavailable` for degenerate headings. Source: rec:rs_contracts/written/*, events 0507Z/0519Z/0541Z/0553Z. Re-derivable: yes. Its evidence folders (`leg_s1_review/work_debug_gravity`, `legs1_routed/out2`) are lost; the record `ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md` and the GCS geometry tar `evalx_native/geometry_8c58df1547371bdb.tar` (step-544 geometry of the dev-S1 captures) remain.

Coverage and census (rs_cover, dx_census, lost): the sealed leg used 288 rows/step (no MDG), 544 steps consumed 156,672 rows; production populations 387,266 (pointing 20,239, pose 194,987); routing holds 5,785 ARKit rows (3,063 distance programs); 75,910 policy-deferred rows plus 28,144 execution-incompatible legacy rows; benchmark units (VSI distance 834 m, room 288 m², size 953 cm; ReVSI 283/37/273; VSTI numeric in metres). dx_census: 243,784 real-scan pre-balance candidates need trace repair; 170,437 DOSE rows are barred as written; tenfold target 1,217,030 rows at a guessed ~878 CPU-h. Source: events 0505Z/0509Z/0519Z/0525Z. Their outputs (`CENSUS_LEG.md`, `lists/`) are re-derivable only by rerunning the census against the sealed stores.

## 2. The base and how to verify it

Restart from the sealed leg's own source, not from any tree_r1 fragment.

1. Candidate A, trinity-1-18 `/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872` (792 files, 9.3 MB). rs_cover's census named its `student_pilot/carrier_c1_run.py` as the production source and matched it against `leg_s1_fourstream_kit/final_b/k/7.json` (rec:rs_tree/results L3028). It contains `source_seal.py`, `gf1*.py`, `dense_eval.py`, `launch_s1/`, `configs/gf1_stage{1,2}.json`.
2. Candidate B, Orchard: the deployed kit 07ca49df (job script `okit/j/07ca49df.sh`; first input tar `okit/i/eb3429c5.tar`, 162 MB; sealed kit under `okit/x/` unverified). This is the code that trained the leg.
3. Verify, in this order, before any build: (a) run the tree's own `python -I -s -B student_pilot/source_seal.py` on A and compare with 38917ea5 (the reviewed seal of the next-leg base; REVIEW_VERDICT_NF.md) and 37845077 (kit 9ca55db0); (b) on Orchard, read kit 07ca49df's `k/7.json` (or equivalent source-hash manifest) and compare per-file sha256 with A; (c) if (a) and (b) agree, A is the base; if not, extract the source from candidate B on the lane's node and use it. Record the seal in the lane's STATUS.md. Unverified until run: which seal A carries (RECOVERY_MAP warns it may be an earlier pass).
4. GF-1 base code is inside the base (record LEG_S1_TREE_20261111.md: "The same source contains the fusion connector and dense-64 builders"). The GF-1 build base `integ_v3/work/tree` survives on 1-18 (20,931 files) only as a fallback reference.

## 3. Row families of rows_r3

rows_r2 had 13 families and 223,061 rows (rec: event 0642Z, L1835/L1849); rows_r3 had 208,318 rows after the withheld rooms, the lineage gate, room size as direct (465 rows) and the unit family reduced to its 22,280 distance program rows (event 0910Z). The r3 per-family split was never printed: unverified. Grammar for every row: the superset validator (section 2.1 of TRACE_RULING_20261115.md plus the review holes) and the ruled form of section 2.2.

| Family | r2 rows (r3 where known) | Source rows | Builder (lost) | Form and grammar rules | Built from (where it lives today) | K1-dependent? |
|---|---:|---|---|---|---|---|
| direction easy / medium / hard (sealed, re-rendered) | 13,586 / 16,527 / 22,607 | sealed VQA rows (weak canonical trace pack) | rs_rows r2 renderer | Direct; Locate lines (none when the source has no frame), relation in sector words, facing-clause Step; no angle stated | Sealed VQA store of kit 07ca49df on Orchard (unverified which tar); trinity-0-13 `orch_cd/weak_data` (11-07, unverified match) | No |
| relative distance (sealed) | 22,082 | sealed VQA | same | Direct; Locate anchor, order in words, restate closest/farthest; no metres | same | No |
| object size (sealed) | 10,492 | sealed VQA | same | Direct; Locate + Step "longest of its three dimensions"; number only as answer | same | No |
| counting (sealed) | 10,000 | sealed VQA | same | Direct; one Locate per instance (first-seen frame), count from the list | same | No |
| appearance order (sealed) | 15,302 | sealed VQA | same | Direct, unchanged form (first-seen frame per object, then order) | same | No |
| 3D box (sealed) | 4,308 | sealed VQA | same | One Locate line then the JSON (default of TRACE_RULING 2.9 point 2) | same | No |
| route planning (sealed) | 9,404 | sealed routing (direct route rows) | same | Direct; one Step per waypoint (position, heading, next waypoint, turn), then turn list; select by type (N3) | sealed routing store on Orchard (unverified) | No |
| facing toward/away pairs | 67,970 (33,985 pairs) | POOL_S1 direction programs and their forward twins (FACING_AWAY_DIRECTION_ROWS_20261112.md) | rs_rows r2 per TRACE_RULING 2.3 | Direct pairs, both-or-neither; labels recomputed from GT centres; no coordinates, no cross/dot/atan2, no tool | `back_dir/out/r2` lost; POOL_S1 lost (only its exclusion TSVs on 1-18). Rebuild needs the direction program rows with printed centres: in the 75,910 deferred rows of the sealed routing input on Orchard (unverified) | No |
| totals | 2,335 | pool annotations (POOL_R2_MIXTURE_CONTRACT_TOTALCOUNT_20261112.md) | rs_rows r2 | Direct; per-category instance list with first-seen frame, explicit sum, one scalar | `pool_r2/out/r2/TOTALCOUNT` lost; source pool lost. Needs the instance annotations of the same captures (unverified where) | No |
| units | 24,628 (r3: 22,280 distance) | distance/room program rows asked in a second unit | rs_rows r2 | Program, ground-form event rows (masked responses, `<answer>` ending), metric response plus one conversion Step; metric twin per row | sealed routing absolute-distance programs (Orchard) | GT responses: No. Deployed re-render (TRACE_RULING 2.4 units b): Yes |
| recovery | 3,820 (14.0% of distance rows) | distance programs with a simulated miss | rs_rows r2 | Program up to the failed call, the runtime's own status text, then a direct answer with Locate lines; no refusal, no operator-fault status, no call after a failed ground | same plus the runtime's response formatter (in the base tree) | Simulated misses: No. Real statuses from the deployed pipeline: Yes |
| room size direct | r3: 465 | sealed room program rows (581) + room unit rows, minus withheld and lineage-less | rs_rows r3 | Direct; Locate/Step lines, no stated area; estimate only as answer, unit converted in building the answer | sealed routing (Orchard) | No (route decision D2 defaults direct) |
| camera displacement / movement / rotation; absolute distance programs (carried, not re-rendered) | 14,020 / 12,260 / 9,143; 11,728 | sealed routing programs (47,732 incl. room 581) | tree materializer (event conversion) | Program with GT printed responses through the masked event path | sealed routing (Orchard) | GT responses: No. Absolute distance with deployed trust + fallback responses (TRACE_RULING 2.2, B6-A renderer): Yes |
| pose, pointing (not trace rows) | production 194,987 / 20,239 | sealed pose (two sources) and pointing streams | none | Outside the trace rule | Orchard (second pose source a3v2 unverified); pointing material also on 1-18 `mixdata/work/pointing` (205 files) | No |

Families that cannot be built until K1 lands (K1 GPU pass, selector refit under its kill rules, then the B6-A renderer): absolute-distance trust and fallback rows with deployed responses, units re-rendered from deployed responses, recovery rows with real statuses, and any room program rows (also gated on route decision D2/P7). Everything else in rows_r3 is K1-independent.

Inputs on other stores: GCS q8 holds no row store (listing 16:55Z); Mind batch 4 holds streams2, mixdata, mdg_build, gx_build, derivgen, p1c_build_d451, p2_build (contents vs these families unverified); code-aws holds `data2root/k6tk`, `s4_media`, pose frames `ap/f02f16ad/f/k.tar` (DENSE_FRAMES_PLAN; access recorded to end 2026-11-19; any AWS use goes through the main orchestrator). /data2 holds exclusion records only (BENCH_SCENE_EXCLUSIONS v2 copy on 1-18 `revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json`).

## 4. First configuration (A0) and the full stack

Earliest of all (ORCH 1800Z): D0, a data-only reseal on the unchanged kit 07ca49df, about one day away; specified in `FIRST_CONFIG_20261115.md` beside this record. D0 replaces only the VQA and routing row files, keeps the room, camera and absolute-distance programs with GT responses, and defers units, recovery and room direct to A0 because the sealed tree cannot consume them. A0 below is the next leg after D0 (or instead of it, if the Orchard inventory rules D0 out).


A0: config (b) of pass 6 — no geometry connector, 32-frame stores, GT program responses, simulated-miss recovery, room direct, 80 rooms withheld, claim scope as pass 5. Per 288-row step at world 4 (72 per rank), no MDG stream, 1,000 registered steps:

| Stream | Cell | Rows/step | Population | Repeats over 1,000 steps |
|---|---|---:|---:|---:|
| VQA 128 | direction toward (sealed, re-rendered) | 29.3 | 52,720 | 0.56 |
| | facing pairs (toward twin + away, same step) | 29.4 | 67,970 | 0.43 |
| | relative distance | 24.6 | 22,082 | 1.11 |
| | object size | 11.7 | 10,492 | 1.12 |
| | counting | 9.6 | 10,000 | 0.96 |
| | totals | 1.5 | 2,335 | 0.64 |
| | appearance order | 15.6 | 15,302 | 1.02 |
| | 3D box | 4.8 | 4,308 | 1.11 |
| | room size direct | 1.5 | 465 | 3.23 |
| routing 64 | camera displacement (GT program) | 14.5 | 14,020 | 1.03 |
| | camera movement direction | 12.7 | 12,260 | 1.04 |
| | camera rotation | 9.5 | 9,143 | 1.04 |
| | absolute distance (GT program) | 12.4 | 11,728 | 1.06 |
| | recovery, distance (simulated miss) | 2.0 | 3,820 | 0.52 |
| | units, distance (program) | 2.4 | 22,280 | 0.11 |
| | route planning (direct, re-rendered) | 10.5 | 9,404 | 1.12 |
| pose 64 | both sealed pose sources | 64 | 194,987 | 0.33 |
| pointing 32 | sealed pointing | 32 | 20,239 | 1.58 |

Populations are r2 counts before the withheld rooms and lineage gate; the tree must print the after-filter repeats from metadata before materialization (review-3 F1). The quotas are my proposal (the R5 card's table was never printed); the lane may adjust them under the same constraints (no empty cell, at most about 4 repeats, sealed stream quotas). If the second pose source is not on Orchard, the review-3 fallback applies: pose 60, pointing 36.

A0 gives up: deployed-response trust/fallback rows (the train-to-inference gap on absolute distance stays; the trace ruling's F3 read then tests GT-trained calls against deployed tools), real failure statuses, camera and room recovery, GF-1, larger traced direct data (DX), direct rows for VSTI camera-object types (none exist yet), own-encoder grounding. It keeps: every repair of the trace ruling on 121.5 of 192 language rows per step, the facing fix, totals, units, the contract patches, the withheld rooms, the claim-scope gates. The DENSE_FRAMES_PLAN notes that the GF-1 card needs a no-fusion control on the same checkpoint and mix, so A0 is also that control.

Full stack (A2), staged at epoch boundaries from the same source by the one bound field: A0 + deployed responses after K1 (switch at an epoch boundary, recorded in the run identity) + GF-1 (dense manifest built on Orchard from the k6 replica plus Apple range reads for 1,409 ARKitScenes clips, pose clip windows, optionally the cached pooled bank; ~190 GPU-h cached or ~345 online for 1,000 steps, estimates) + admitted DX direct traces (DOSE pool re-rendered to the grammar) + VSTI camera-object direct rows from a coverage build.

## 5. Critical path, effort and rulings

| Step | Owner | Agent-h | GPU-h | Depends on | Parallel with |
|---|---|---:|---:|---|---|
| S0 read-only inventory: Orchard kit 07ca49df (k/*.json, input tars eb3429c5 and `okit/u/4d66fc2a` t1-t3, routing/VQA stores incl. deferred rows, second pose source, k6 replica completeness at `cp4tk_fr/k6tk` — evalx27 saw only 1.33 GB there), Mind batch 4 p1c_build_d451 (k6 MAP?) | rows lane operator via `ossh.sh` | 1 | 0 | — | S1 |
| S1 base seal verification (section 2) | tree lane | 0.5-1 | 0 | — | S0 |
| S2 one throttled pull of the row text inputs (expected well under 1 GB) from Orchard to the rows node (hand stream under OUTAGE_20261115T1000Z.md) | rows lane | 0.5 | 0 | S0, IO ruling | S3 |
| S3 contracts rebuild (three patches + tests) | contracts lane, 1-2 Codex builds | 3-4 | 0 | S1 | S4, S5 |
| S4 rows rebuild: grammar validator first (publish it), then families | rows lane, 2-3 Codex builds | 8-10 | 0 | S1 (schema), S2 | S3, S5 |
| S5 tree rebuild: contract, intake, materializer, kit builder, policy, withholding, two configs, F1-F6 | tree lane, 3 Codex builds | 10-14 | 0 | S1; consumes S3 patches and S4 grammar/rows as they land | S3, S4 |
| S6 reviews: contracts (1), rows (1), tree (2 rounds), each Devin Opus high | review lanes | 6-8 | 0 | S3/S4/S5 | each other |
| S7 frame-host CPU job on Orchard: full stores, every rank's first batch on real frames, the frame-host statements | tree lane via the Orchard operator | 2-4 (plus job time) | 0 (CPU job; 0-0.5 if it must run on a GPU node) | S5, S6, Orchard ruling | GF-1 dense build |
| S8 first GPU admission: one step at world 4, true memory peak and step time | orchestrator's GO | 1 | ~1 | S7 | — |
| S9 A0 leg, 1,000 steps | — | babysit | ~146 (estimate) | S8, user's go | K1, GF-1 builds |
| GF-1 track: dense manifest + ARKit fetch on Orchard, cached bank, calibration | separate lane | 8-12 | 1-3 | S1 | S3-S8 |
| K1 track (k1_ops3, existing) | existing | — | 3-6 | — | all |

Wall clock to S8: about 1.5 to 2 days, set by S5 plus two tree reviews. Total agent-hours: about 30 to 40.

Rulings the orchestrator must make: (1) the base: candidate A or the Orchard kit source, after S1; (2) S2, a hand stream of Orchard row text to Trinity, or building rows on Orchard; (3) the A0 mix and leg length (1,000 steps registered as above, or a shorter first allocation); (4) A0 without deployed responses and without GF-1, recorded in the run identity, against waiting for K1 and the dense build (user decision; the 2026-11-15 question "no-fusion leg first or wait for fusion?" is open with default no-fusion first); (5) the claim-scope default for the init overlap (open user question of 2026-11-13; default launch and report only VSI-Bench, VSTI, ReVSI); (6) the 27 qualification rooms (default: do not bind); (7) the 3D-box family kept with one Locate line (default) or dropped; (8) whether the lanes may read the Devin CLI logs on NFS for the review lanes' heredoc writes (tree_review 1-3, scene_evidence, dense_plan) — low value, since the builds were Codex runs whose transcripts were on 2-18; my default is no; (9) the continuation question stays the user's (held).

## Options considered and rejected

- Waiting for trinity-2-18: no date, and the plan must not depend on it.
- Rebuilding tree_r1 pass by pass in the original order: the passes fixed findings that a single consolidated spec avoids (two dense rules, extra connector, path pins). The rebuild briefs state the end state of pass 6b plus review 3 directly.
- Restarting from the 1-18 `r1_contract.py` fragment: it predates the review-1 root-map fix (`r1_contract.py:45-52` is the bug site).
- Building rows on Trinity from /data2 or /data3 sources: the 3dod PNGs do not reproduce the k6 pins, and the weak packs on 0-13 are not shown to match the sealed stores; the sealed stores themselves are the authority.
- Launching A2 first: it waits on K1 and the dense build, and the GF-1 card needs A0 as its control anyway.

## What might not work, and how we would notice

- The Orchard kit lacks the deferred routing rows, so facing pairs cannot be rebuilt: S0 shows it; then facing waits on a pool rebuild (POOL_S1 from the VSI-590K sources, DOSE_POOL_KIT_20261111.md), and A0 launches with the facing cell's slots given to sealed direction toward rows (no facing fix in A0).
- The base on 1-18 is an earlier pass: S1 shows it; use the Orchard kit source.
- The second pose source is not on Orchard: S0 shows it; pose 60 / pointing 36.
- The frame-host job finds missing frames for the joined rows (the k6 map is lost): S7 shows it; rows without pins are refused per row with a reason (contract rule), and the denominator is reported.
- The four late grammar holes of review 3 are unknown: the rows review is asked to probe for new holes, not only the listed ones.

## Tests that would settle it

S0 listing; S1 seal; the three briefs' acceptance tests; S7 first batch on real frames; S8 step time and memory.

## Status

Plan written 2026-11-15 by lane seal_plan. Nothing built. Briefs: `BRIEF_tree_rebuild.md`, `BRIEF_rows_rebuild.md`, `BRIEF_contracts_rebuild.md` in `orch_n30/events/seal_plan/`.
