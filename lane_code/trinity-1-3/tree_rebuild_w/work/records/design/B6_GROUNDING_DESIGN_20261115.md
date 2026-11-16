# B6: the grounding design for the repair seal (2026-11-15)

**Status:** DESIGN, read-only. Nothing was built, trained, launched or staged. Lane `b6_design`, trinity-2-18. Paths are under `/scratch/jjyeung/orch_cd/` unless absolute. `DD` = `/data2/jjyeung/agent_project_data/distill_design/`; `MEM` = `/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/`. Eligibility arithmetic: `b6_design/work/eligibility_checks.py`, output `b6_design/work/eligibility_checks.out.json`. **GUESS** marks an unmeasured effect; **DIAG** marks an oracle or benchmark-scene diagnostic that cannot select a design.

## Question

Which grounding module goes into the repair seal, what exactly is trained, frozen and supervised, how does its output reach the language model, and what does a builder build?

## Answer

1. **Put no new trainable grounding module into the seal.** The seal grounds through the deployed frozen backend: SAM 3 proposals at the frozen `dense_aliases` setting, the frozen candidate selector, G3T lifting scaled by the checkpoint's own heads, printed as `<tool_response>` text. This is option (d) of the brief on top of the existing frozen tower, which the user already approved as a frozen component.
2. **Fix the backend's eligibility before any ReVSI or VSTI routed read.** The deployed selector was fitted on 84 scans from 44 ScanNet rooms; all 44 are VSTI rooms, 18 are ReVSI rooms and 6 are STI-Bench/ReSTI rooms (`work/eligibility_checks.out.json`). It stays legal for VSI-Bench and dev-S1, but not for ReVSI or VSTI. The build refits it on eligible training captures.
3. **Train the routed rows on deployed responses** (trust rows plus real-failure fallback rows), as `trace_ruling/out/TRACE_RULING_20261115.md` section 2 proposes. B6 supplies that ruling's missing grounding inputs: an eligible training-scene cache and a renderer.
4. **Under the seal's route table, grounding is a guard, not a lever.** Only absolute distance consumes masks in the seal (room reads no masks; direction, relative distance, counting and size stay direct). On official VSI-Bench, recovering missed objects already pays nothing once a direct fallback exists: with fallback, the frozen proposal setting minus baseline proposals is −0.59 [−2.29, +1.04] (`official_reads/ROUTED_ABSDIST_ROOM_VSI5130_20261113.md:35`). The expected gain of the recommended design is about **+0.2 VSI points** (arithmetic in 4.5), and it removes a measured failure loop.
5. **The own-encoder head (branch O) does not enter this seal.** It has no trained weights, its stated bar is parity with SAM 3 rather than a gain, its inputs drift when the seal fine-tunes the shared ViT, and its teacher labels contain 5 dev-S1 captures. It proceeds as an LM-frozen side experiment (build brief part B) whose training-side test decides entry at the next seal.
6. **The planning report's B6 inputs are not training data.** `mask_recall` covers the 152 dev-S1 captures and `grd_selector/out/accept2` covers VSI-Bench scenes and the 44 VSTI rooms. Both can measure, never train.

---

## 1. Inventory

Scene-eligibility verdicts use `revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json` (VSI-Bench, VSTI 312 ScanNet val, ReVSI, STI/ReSTI, DSI, OSI, MindCube; `benchmark` key), the dev-S1 manifest `devs1_masks/out/MANIFEST.json` (152 captures) and the dev-84 split `ofs_e1/out/ROOM_SPLIT.json`.

| Piece (lane) | What it is | What was measured, on which scenes | Weights and kit | Training-scene eligibility |
|---|---|---|---|---|
| Deployed backend: SAM 3 tower + frozen selector (`sam3_tower`, `grd_selector`) | SAM 3 (0.85B, frozen) text-prompted proposals; logistic accept model `DEPLOY\|portable_np\|logistic`, top-1 for unique types; frozen pair merge for counting (`devs1_masks/out/DESIGN_RECORD.md:10-11`) | Official VSI abs distance strict 61.09, fallback 62.83, direct 53.38 (`official_reads/ROUTED_ABSDIST_ROOM_VSI5130_20261113.md:31,33`). VSI ScanNet with fusion policy on G3T: abs 66.5 vs GT masks 79.3; rel 59.1 vs 91.5; counting 54.4 vs 98.1 (DIAG; `DD/GRD_SELECTOR_KIT_20261111.md:13-17`). dev-S1 route table: only abs distance routes, +8.1 [+0.9, +16.9] (`MEM/result-devs1-route-table-predicted-masks-20261112.md`, table) | SAM 3 checkpoint SHA `9999e234…`; tower API CPU-ready, 21 + 33 CPU tests, GPU parity pending (`sam3_tower/out/RECORD.md`; `sam3_tower/events/20261110T1432Z_RESULT_sam3_tower_batch.md`). Selector code and tables `grd_selector/work/setsel/` (227 MB data) | Selector fitted on all 84 dev scans (`DD/GRD_SELECTOR_KIT_20261111.md:62`) = 44 rooms: **44 VSTI, 18 ReVSI, 6 STI/ReSTI**, 0 VSI, 0 dev-S1 (`work/eligibility_checks.out.json`). SAM 3's own training data is unaudited (`DD/GROUNDING_OWN_ENCODER_20261110.md`, section 3.5) |
| Proposal setting `dense_aliases` (`mask_recall`) | Dense text pass (joint 0.05, cap 30) plus aliases | dev-S1 abs 46.9 → 56.2, +9.3 [+4.2, +14.9]; counting −8.3; 55 of 224 never-proposed instances recovered at 10% precision (`MEM/result-devs1-route-table-predicted-masks-20261112.md`, para 2). Official: +3.06 strict, −0.59 with fallback (`ROUTED_ABSDIST…:35`) | Frozen kit_combo3 `b3fa05c6` (`DD/MASK_PROPOSAL_RECALL_DEVS1_20261112.md:37`) | Setting chosen on dev-S1 (six variants on the same 152 captures; same memory note). No weights |
| Never-proposed audit (`mask_recall`) | Cause census of 224 / 1,056 operand instances on 93 GT-covered dev-S1 captures (`mask_recall/out/NEVER_PROPOSED.md:1`) | Grants (DIAG, dev-S1): unresolved 81 → +14.34 abs / +12.31 count; few views 74 → +8.82 / +8.57; presence gate 11 → +1.84 / +1.10 (`NEVER_PROPOSED.md:19-22`). Ever recall 78.8% (`:41`). 13 "ceiling light" targets bound to "ceiling", a matcher error (`:50`) | Kit `mask_recall/out/mask_recall_kit.tar.gz` (2.6 MB) | **dev-S1 only; never trainable** |
| Point and grid prompts (`own_ground`) | Kit A: class-agnostic grid masks plus naming; kit B: CP1 m200 pointing as SAM 3 point prompts | GT-centre point recovers 15 of 81 unresolved; 16×16 grid 22 of 81 (registered build bar ≥25, stop ≤8) (`MEM/result-devs1-route-table-predicted-masks-20261112.md`, last para; `own_ground/out/STATUS.md`). Kit B's real pointing run is not reported in any file I read | `own_ground/out/kit_A.tar.gz`, `kit_B.tar.gz` (3.2 MB each) | dev-S1 measurement only |
| Frozen-feature probe E-A (`own_probe`) | Matched heads on frozen features: Qwen ViT 640×480 (A1), 1024×768 (A2), SAM 3 PE (A7) | Choosing among SAM 3 candidates by name: A1 on target 64.3% vs A7 66.5%, A1 − A7 −2.3 [−8.0, +4.5]; all arms fail the 0.90 name-consistency bar. Cross-frame identity linear top-1: A1 0.949 vs A7 0.955 (`own_probe/inbox_gpu/r5_phase1_20261110/card/P0_CARD.md:22,31,33,42,64`). Scenes: 31 tuning scans of dev-84, 37 training rooms | Small result tar `own_probe/inbox_gpu/r5_phase1_20261110/own_probe_r5_small_results.tar.gz`; no reusable head | Tuning scans are VSTI rooms: measurement only. R2 (masks), R3 (presence) never measured |
| Branch O / OGD head (`own_head`, `own_teach`, design `DD/GROUNDING_OWN_ENCODER_20261110.md`) | ~45M SAM 3-style decoder on the student's ViT taps (re-read of 4 frames per name), presence head, selector; query = frozen name embeddings; SAM 3 as teacher; LM frozen (`GROUNDING_OWN_ENCODER…:74-86`) | **Never trained.** r10 pilot died at step-0 validation on a name join (`own_head/inbox_gpu/r10_pilot_20261111/pilot10.log`); r11 fix passes the full-label CPU gate, GPU not run (`DD/PILOT_FULL_LABEL_PATH_20261111.md`, Status). Teacher label audit: POS masks 4.6% wrong, MISS rows 36.8% wrong (`GROUNDING_OWN_ENCODER…`, P7 section) | Code `own_head/out/own_head_code.tar.gz`; r11 receipt `own_head/out/BUILD_RECEIPT_r11.json`. Teacher labels `head_teacher_full.tar` (1.04 GB, SHA `189140d7…`) exist **only in `/dev/shm/jjyeung_evalx/teach_r5_full/` on trinity-2-18**, which a reboot erases | 205 scenes (67 ScanNet, 138 ScanNet++), 0 benchmark rooms, but **5 dev-S1 captures**: scene0380_01, scannetpp 37c9538a2b, 3ce6d36ab5, d6bb698875, e667e09fe6 (`work/eligibility_checks.out.json`). The gate predates dev-S1 |
| MDG-A (`mdg_build`, `mdg_next`) | 39M mask decoder prompted by LM hidden states on T0 prefill features (`DD/INDEX.md:73`) | NO-GO: held-out in-mask 65.1 (+3.8 [+0.5, +7.2] vs T0), null 65.7 in-video, 0 of 4 types CI > 0 (`DD/INDEX.md:73`) | Checkpoints `mdg_build/work/runs_backup/mdga_w8/s_0819/best/step_00000300…2100` | **Ineligible**: trained on 251 benchmark scenes and 72 dev-S1 scenes (`MEM/mdga-init-ineligible-20261113.md`) |
| Own presence and own boxes (`verify_kit`) | Student yes/no presence per frame; native boxes (V3) as selector feature | Base presence AUROC 0.962 vs SAM 3 0.927; box drawn on 92% of absent frames; V3 + MDG frame ranking 82.9% on target vs SAM 3 top 80.0%; SAM-free arm 75.4%; T0 presence shifted toward yes, AUROC 94.3 (`MEM/result-presence-pose-routing-20261110.md:14-17,39,42`). Dev-84 scans | Kit `verify_kit/out/`; no weights | Measured on VSTI rooms; diagnostic |
| Learned visual verifier (`grd_selector` accept v2) | Student PRES32 + V3 features inside the accept model | Predicted f = 0.23 fixed at h = 0.02 against the bar f ≥ 0.5, h ≤ 0.05; crop P(yes) AUC 0.58–0.69 (`grd_selector/out/RUN_CARD_PRES32_V3.md:35-37`). Wrong tops: 12/30 look-alikes, 9/30 unlabelled real objects (`DD/GRD_SELECTOR_KIT_20261111.md:30-31`). Never run | Run card ready, ~2.5 GPU-h | Its test set is VSI-Bench objects (`grd_selector/events/20261111T1820Z_RESULT_accept_v2_item5_check_bar.md`): test-set selection; cannot choose a design |
| SAM-native gate + 3D ball selector (`hrp_infer`) | Zero-training 3D vote over SAM 3 proposals | vs T0 direct on dev-84: abs +22.76, rel +6.67, 2 of 4 types (`hrp_infer/out/ORACLE.md`, last table) | Patches `hrp_infer/out/reread_generate.patch` | Dev-84 measurement |
| Own-ViT re-read (`own_reread`) | Patch that reads the shared ViT's taps (blocks 9/17/25/27) inside `generate()` without touching LM state | 37 CPU tests; CUDA latency unmeasured (`own_reread/out/RECORD.md`) | `own_reread/out/own_vit_reread.patch` | No data |
| HR pointing rows (`hrp_rows`) | High-resolution single-image pointing and keypoint rows | 15 of 30 hand-opened rows admitted; rows review-only (`hrp_rows/out/RECORD.md`, Answer) | `hrp_rows/out/sample2k` (453 MB) | Scene policy excludes eight eval sets (`hrp_rows/out/RECORD.md`, Local sources); dev-S1 not checked |
| GT ceiling decomposition (`gt_ceiling`) | Where selector masks lose against GT masks, VSI ScanNet | Accept errors 12.0 rel, 7–10 directions; never-proposed 6–8 rel/directions, 6 abs, 22 counting; counting linking 13.7 (DIAG; `gt_ceiling/out/GT_CEILING_DECOMPOSITION_20261111.md:125-127`) | Patches | Benchmark scenes; diagnostic |
| Native 3D boxes (`box3d_probe`) | Qwen3.5-9B `bbox_3d` with the object given | Centre 0.21 m, longest-edge MRA 66.7, IoU 0.21; GT mask + GT depth 84.1 / 0.61 (`box3d_probe/out/table.md`) | Raw outputs | Not a grounding module (object given) |
| Pointing stream masks | Leg pointing rows' target masks | Set b2a masks survive (37 MB at `mixdata/out/pointing_v2/data2root/p5x9`); pa3 and pa3b masks are lost (`MEM/pointing-masks-lost-on-aws-20261112.md`) | Rows pin mask SHA256 | b2a in the sealed leg (20,239 pointing rows; `leg_s1_review/CONTINUATION_FACTS_20261114.md`, section 4) |

Two framing numbers in the brief need context. The "58.7 with the model's own heads" belongs to an earlier model's head programs; in this lineage the own heads supply only scale and gravity, and masks come from the external segmenter (`trace_ruling/out/TRACE_RULING_20261115.md:100`). The 224 never-proposed instances are counted at default density; `dense_aliases` recovers 55 of them.

## 2. Where grounding can pay in the seal

The seal's route table: program rows only for absolute distance, room size and the three camera types; all other types answer directly (`trace_ruling/out/TRACE_RULING_20261115.md`, Answer item 1; `MEM/result-devs1-route-table-predicted-masks-20261112.md`). Camera types read pose, room reads geometry, so **absolute distance is the only mask consumer**.

Prices, in official VSI primary points (task weight 1/8; `next_queue/out/NEXT_QUEUE_20261115.md:31`):

| Lever on absolute distance | Measured basis | VSI points |
|---|---|---|
| Perfect masks (ceiling, DIAG) | 79.3 − 66.5 = 12.8 task points on VSI ScanNet (`DD/GRD_SELECTOR_KIT_20261111.md:13`) | 12.8 / 8 = **1.6** if it held on all three datasets |
| Perfect recall of never-proposed objects (ceiling, DIAG) | 7.6 task points with GT masks (`DD/GRD_SELECTOR_KIT_20261111.md:40`) | 7.6 / 8 = 0.95 |
| Recall once a direct fallback exists (measured, official) | Frozen setting minus baseline with fallback −0.59 [−2.29, +1.04]; recovered items score like direct on the same items (`ROUTED_ABSDIST…:35,59`) | **≈ 0** |
| Direct fallback on failed grounds (measured scripted, official) | 62.83 − 61.09 = 1.74 task points (`ROUTED_ABSDIST…:31,33`) | 1.74 / 8 = **0.22** |
| Accept fix at the verifier bar f 0.5, h 0 (simulated, VSI ScanNet) | abs +3.0 task points (`grd_selector/out/RUN_CARD_PRES32_V3.md:29`) | 3.0 / 8 = 0.375 (GUESS beyond ScanNet) |
| Accept fix at the predicted f 0.23, h 0.02 | abs about +1.2 (row f 0.25, h 0, `RUN_CARD_PRES32_V3.md:27`; h > 0 lowers it) | ≤ 0.15 (GUESS) |

The large grounding prize lies outside the seal. Relative distance on VSI ScanNet scores 59.1 routed against 61.0 direct and 91.5 with GT masks (`DD/GRD_SELECTOR_KIT_20261111.md:15`; direct from `gt_ceiling/out/GT_CEILING_DECOMPOSITION_20261111.md:104`). Fixing accept errors (12.0) and never-proposed objects (6–8) together would lift it to about 77–79, that is +16 to +18 over direct, or 2.0–2.3 VSI points (DIAG ceiling). The verifier bar alone gives rel +3.0, still a tie with direct, so no realistic accept fix flips the route. The planning report's M3 price of 0.625 points assumes routed relative distance (`next_queue/out/NEXT_QUEUE_20261115.md:246`); in this seal relative distance stays direct, so M3 buys nothing here.

## 3. Options and verdicts

### (a) Frozen SAM 3 prompted by the model's own pointing or presence — rejected for the seal
- Pointing cannot beat its own ceiling: a point at the GT centre recovers 15 of 81 unresolved misses, a class-agnostic grid 22 of 81 (`MEM/result-devs1-route-table-predicted-masks-20261112.md`, last para). SAM 3's decoder, not the prompt, fails on most of them.
- Presence triggers only reach the presence-gate group: 11 instances, grant +1.84 abs (DIAG; `mask_recall/out/NEVER_PROPOSED.md:21`).
- Whatever recall it adds is worth about zero once a fallback exists (section 2, row 3).
- The CP1 lineage's pointing is eroded (59.1 against base 67.0; `DD/GROUNDING_OWN_ENCODER_20261110.md`, section 0 row 6), and the leg trains it further.

### (b) A mask or box head on the model's own visual features — rejected for the seal; continued off-seal
- **No eligible trained weights exist.** MDG-A is ineligible and failed its read; OGD never trained (section 1).
- **Its bar is parity, not gain.** Branch O's own design says "Branch O's bar is parity with S at 50M added weights instead of 850M, not a selection win" (`DD/GROUNDING_OWN_ENCODER_20261110.md:11`). E-A agrees: own and SAM 3 features tie on selection and identity (`P0_CARD.md:64`).
- **The seal moves its inputs.** The seal trains the encoder at LR 1e-5 (`leg_s1_review/CONTINUATION_FACTS_20261114.md`, section 1). A head fitted on step-544 ViT taps reads shifted features after the seal; one trained inside the seal puts its loss on the shared ViT, an untested risk to the direct path that the stacked read cannot attribute (no ablation arm, `NEXT_QUEUE_20261115.md:250`).
- **Its supervision for the target cases is the noisiest class.** Objects SAM 3 misses are taught by raster MISS rows, 36.8% wrong (`DD/GROUNDING_OWN_ENCODER_20261110.md`, P7 section).
- **Its labels need a fix**: 5 dev-S1 captures, and the only copy sits in `/dev/shm`.
- Sub-variant (b3), an auxiliary mask loss on the shared ViT during full fine-tuning to help direct answers: no measurement in this lineage supports it, and the pointing stream (32 rows per step) already carries grounding supervision in text. Rejected for the same attribution reason.

### (c) The existing selector with a learned verifier — rejected as a seal change; keep the selector, refit it
- The student-feature verifier is predicted to fix f = 0.23 against the bar 0.5 (`RUN_CARD_PRES32_V3.md:36`), worth ≤ 0.15 points (section 2).
- 9 of 30 wrong tops are unlabelled real objects; no check can fix them (`DD/GRD_SELECTOR_KIT_20261111.md:31`). A name-only labeler reaches 82.3% against SAM 3's 80.0% (`DD/GROUNDING_OWN_ENCODER_20261110.md:11`).
- Its only test set is VSI-Bench objects, so running it would select on the benchmark.
- The existing selector stays, but refitted on eligible scenes (section 4.2), because its fit set covers 18 ReVSI and 44 VSTI rooms.

### (d) No new module; routed rows trained on deployed responses — adopted, with the backend fixes
- It addresses measured failures: after refused grounds the native model repeated one gap call 198 times (14,754 tokens), and none of 165 sampled training distance rows shows a failure (`NEXT_QUEUE_20261115.md`, section 1.6, row "Failed-ground behavior").
- Every training response today is ground truth: 73,088 pool rows with `mask_source gt`, `not_seen false` (`trace_ruling/out/TRACE_RULING_20261115.md:92`).
- Scripted fallback is worth +1.74 abs task points officially (section 2).
- It adds no parameters and no training-step cost.

## 4. The recommended design

### 4.1 Module and place in the forward pass
1. The model writes `<ground obj=NAME mode="box">` twice and `<gap …>` for absolute distance, or `<ground mode="room">` (sealed 3.14 grammar; `trace_ruling/out/TRACE_RULING_20261115.md:72`).
2. Inside `generate()`, the call goes to the frozen grounding backend: SAM 3 (checkpoint `9999e234…`, 1008 px, bf16, batch 1) at `dense_aliases` (joint 0.05, cap 30, merged cap 100, linker 0.3, mask threshold 0.5), the candidate selector, an interior depth cut, G3T depth and pose scaled by the checkpoint's own heads, and the frozen box policy `fit_gbox_policy_voteb5_best1_v1` (`legs1_routed/out/ROUTED_READ_SPEC_NOMDG.md`, "Geometry and masks").
3. The backend prints its result as text inside `<tool_response>`: the box values, or a typed status such as `ceiling lamp: not seen` (`TRACE_RULING_20261115.md:225-232`). The model continues from those tokens; after a failure it answers directly from the frames and never repeats the call.

Benchmark reads may serve proposals from a cache made by the same frozen tower on the same frames (`nomdg.py cache-bind`, same spec). The product claim needs the live path, so the build proves cache and live tower agree (4.6, proof P6).

### 4.2 Trained, frozen, initialized
| Part | State in the seal | Initialized from | Eligibility evidence |
|---|---|---|---|
| SAM 3 tower | frozen, outside the module tree and optimizer | checkpoint `9999e234…` | CPU tests show it absent from state dict, parameters and optimizer (`sam3_tower/out/RECORD.md`, Evidence). Its own training data is unaudited, a limit to state on the card |
| Candidate selector (logistic, ~20 portable features) and pair merge | frozen during training; **refitted once, offline, before the seal** | refit on eligible training captures with the unchanged `grd_selector/work/setsel/fit.py` / `fit_pairs.py` | New fit set must pass the gate in proof P1. The current fit set is 44 VSTI / 18 ReVSI rooms (`work/eligibility_checks.out.json`) |
| G3T tower, private pose/depth heads | as in the leg | step-544 export | unchanged from the leg (`init_audit/INIT_AUDIT.md` per `MEM/mdga-init-ineligible-20261113.md`) |
| LM and ViT | trained as the seal's recipe says | step-544 export | unchanged |

If the refit fails non-inferiority (4.5), the seal keeps the current selector, reports VSI-Bench and dev-S1 routed reads only, and serves no mask-based routed read on ReVSI or VSTI.

### 4.3 Supervision
- **Responses** (masked from the loss; the routing encoder masks response spans, `TRACE_RULING_20261115.md:98`): printed by the deployed backend on eligible training captures. Trust rows keep a response within 15% of GT whose accepted masks match the GT instance; fallback rows keep a real failure status followed by a direct answer; silently wrong responses are left out (`TRACE_RULING_20261115.md`, section 2.6). GT enters only that classification.
- **Answers and traces**: the row's GT answer and the trace forms of the trace ruling.
- **Selector refit labels**: GT instance rasters of eligible training captures, y = 1 when half a candidate's members match the named GT instance at IoU > 0.5 (the existing labelling rule, `DD/GRD_SELECTOR_KIT_20261111.md`, "Candidates and features").
- **What survives**: GT rasters of the dose pool's training captures (pool already excludes dev-S1 and eval rooms: `dose_pool/out/POOL_S1/EXCLUDE_DEV_S1.tsv`, `EXCLUDE_EVAL_ROOMS.tsv`); b2a pointing masks (`MEM/pointing-masks-lost-on-aws-20261112.md`); the SAM 3 teacher labels on 205 scenes (volatile, `/dev/shm`). **Lost**: pa3 and pa3b pointing masks (same note). **Unusable for training**: every dev-S1 cache (`devs1_masks`, `mask_recall`), the dev-84 caches (VSTI/ReVSI rooms) and every VSI-Bench cache (`TRACE_RULING_20261115.md`, section 2.6 table).

### 4.4 How the output reaches the LM
As text tokens only: the printed `<tool_response>` body, in the sealed 3.14 event schema with the runtime's own status strings. No embedding, mask or hidden state enters the LM. The LM never writes response tokens: response spans carry zero loss.

### 4.5 Expected gain, priced
- Fallback after failed grounds: (62.83 − 61.09) / 8 = **+0.22 VSI points** over the pre-registered strict arm, measured with scripted fallback (`ROUTED_ABSDIST…:31,33`). Whether the trained model falls back as the script does is a GUESS; F3 of the trace ruling tests it.
- Removing the repeated-call loop: unpriced (GUESS); the loop wastes the token budget on the affected items.
- Selector refit: 0 points on VSI expected (non-inferiority). It makes ReVSI and VSTI mask reads reportable.
- ReVSI distance and room: no student routed read exists; unpriced.
- Against the alternatives: (a) ≈ 0; (b) 0 in the seal (parity); (c) ≤ 0.15 (GUESS). None of them is measured either.

### 4.6 Cheapest test that kills it before a full leg (training-side scenes only)
Stage K1, CPU plus 3–6 GPU-h (cache estimate for about 300 captures, `TRACE_RULING_20261115.md`, section 2.6, stage 3). Run the deployed backend on 300 eligible training captures with GT rasters, split 80/20 by physical room (seed 17). On the held-out 20%:
- **Kill the deployed-response rows** if trust plus fallback rows are under 40% of absolute-distance items (dev-S1 shows 58.6%: 13.7% failure + 44.9% consistent, `TRACE_RULING_20261115.md:341`), or if the strict program's MRA on answered items is not at least 10 points above the train-fitted constant answer. Then the seal launches with GT trust rows plus simulated-miss fallback rows and records that in its identity (`TRACE_RULING_20261115.md`, section 2.8, row "The deployed cache is late").
- **Kill the selector refit** if its held-out-room candidate AUC falls more than 0.02 below the current selector's AUC on the same held-out candidates, or its top-1 accept accuracy falls more than 2 points below it.
- Stage 1 of the ruling's cue study (does anything printed beyond the status separate right from wrong responses) runs on these held-out rooms, not on the 84-scan cache, because those scans are VSTI/ReVSI rooms.

### 4.7 Memory and time
- **Training step:** no added parameters, no SAM 3 in the graph; responses are precomputed text of the same length class as today's GT responses. Step time stays at the measured 131 s at world 4 (`leg_s1_review/CONTINUATION_FACTS_20261114.md`, section 3).
- **Inference:** SAM 3 adds 0.85B frozen parameters (`DD/GROUNDING_OWN_ENCODER_20261110.md:86`); measured peak 4.07 GB at batch 1 in the teacher smoke (`own_teach/inbox_gpu/r5_20261110/teach_r5/SMOKE_RECEIPT.json`, `peak_gpu_bytes` 4,067,278,336). One (capture, name) call takes 1.9–2.1 s at default density; `dense_aliases` doubles the calls at 1.2–1.6× per call (`TRACE_RULING_20261115.md`, section 2.6), so about 4.6–6.7 s per name (my arithmetic), two names per distance item.
- **Build:** 3–6 GPU-h for the K1 pilot; 20–32 GPU-h for the full 2,189-scene cache (`TRACE_RULING_20261115.md`, section 2.6). Frame staging (about 70,000 PNGs, 20 GB, same section) is heavy IO and needs the user's answer.

## 5. What might not work, and how we would notice
| Risk | Sign | Response |
|---|---|---|
| Training-scene responses are less reliable than dev-S1's | K1 trust + fallback share < 40% | GT trust rows plus simulated misses; record it in the run identity |
| The refit selector is worse | K1 AUC or top-1 below the current model by the margins | Keep the current selector; no ReVSI/VSTI mask read |
| The model learns to skip calls | Native call rate < 95% on dev-S1 (trace ruling F3) | Lower the fallback share to the measured failure rate |
| Live tower and cache disagree | Proof P6 or its GPU check fails the noise-aware rule | Serve reads from the cache with the disclosure; fix parity before a product claim |
| Grounding errors on routed rows stay silent | Silent-wrong share on held-out training rooms ≥ dev-S1's 41.5% | Expected; trust filtering already drops them. A verifier is next-seal work |
| A later seal routes relative distance or counting | Route table changes | Then grounding becomes the lever; run part B and a training-side verifier test first |

## 6. Tests that settle it
| Question | Test | Cost |
|---|---|---|
| Are deployed responses usable on training scenes? | K1 (4.6) | CPU + 3–6 GPU-h |
| Is the refit selector non-inferior? | K1 | CPU after the cache |
| Does the model fall back natively? | Trace ruling F3 at seal steps 100 and 200 | Inside the seal's reads |
| Do cache and live tower agree? | P6 plus one GPU parity run (`sam3_tower/out/run_gpu.sh parity 1`) | Minutes of GPU |
| Can the own encoder replace SAM 3, or recover what it misses? | Part B pilot on training rooms | ≤ 4 A6000-h (`own_head/out/E_C_REPORT.md`) |

## 7. Corrections to the planning report's B6 (`next_queue/out/NEXT_QUEUE_20261115.md:340`)
1. Its inputs `mask_recall/out/NEVER_PROPOSED.md` with "its bound manifests" are the 152 dev-S1 captures; training on them breaks every dev-S1 read.
2. `grd_selector/out/accept2` holds VSI-Bench candidates and the dev-84 tables (44 VSTI rooms, 18 ReVSI rooms).
3. "Learns missing-object recovery" has no payoff in this seal: with fallback, recall is worth −0.59 [−2.29, +1.04] officially.
4. The deployed selector itself, already in the native reads, was fitted on ReVSI and VSTI rooms; B11's native ReVSI adapter must not use it for reported mask reads.

---

# Build brief B6-A: eligible grounding backend for the repair seal

**Lane:** `b6_build`, folder `/scratch/jjyeung/orch_cd/b6_build` (create `BRIEF.md`, `out/`, `work/`, `events/`, `inbox/`). CPU only. No GPU, launch, ssh, agents, Git, downloads, deletion, or heavy IO; any staging of frames needs the user's answer through the orchestrator. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` (use `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` only for SAM 3 CPU stubs, as `grd_selector/STATUS.md` does). Keep the lane under 2 GB. Searches stay inside the named folders.

## Scope
Build everything the seal needs to ground absolute distance with the deployed frozen backend on eligible scenes, up to a GPU-ready run card. Do not change trace forms (owned by `rs_rows` / the trace ruling) or the seal tree (owned by `rs_tree`); deliver adapters and patches they can consume.

## Inputs (read-only)
- Exclusions: `revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json` (`members[*].group`, `benchmarks`); `own_probe/out/EVAL_ROOMS.json` (`evaluation_rooms`, `qualification_rooms`, `alias_rooms`, `arkit_rooms`); `ofs_e1/out/ROOM_SPLIT.json` (dev-84); `devs1_masks/out/MANIFEST.json` (152 dev-S1 captures). Reuse the room rule in `b6_design/work/eligibility_checks.py`.
- Training rows and captures: `dose_pool/out/POOL_S1/*_admitted.jsonl.gz` (stream-read, never extract to /home or /data*), with its `EXCLUDE_DEV_S1.tsv`, `EXCLUDE_EVAL_ROOMS.tsv`, `FRAMES_GATE.json`.
- Backend spec: `legs1_routed/out/ROUTED_READ_SPEC_NOMDG.md` ("Geometry and masks", compatibility bridge); kit_combo3 tar `b3fa05c6…` named in `official_reads/FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md`; `mask_recall/out/kit/` for the dense manifest code; `devs1_masks/out/` (`RUNCARD.md`, `DESIGN_RECORD.md`) for the frozen selector, merge and pricing path.
- Selector code and current model: `grd_selector/work/setsel/` (`cands.py`, `build.py`, `fit.py`, `fit_pairs.py`, `price2.py`, `data/probs*`, `data/pairs_fit`).
- Tower: `sam3_tower/out/API.md`, `sam3_tower/work/c1mix_e2e/student_pilot/sam3_tower.py`, `sam3_tower/out/sam3_tower_batch_final.patch`, noise-aware parity rule in `sam3_tower/out/BATCH_MEASUREMENTS_FINAL.json`.
- Geometry: `devs1_tower` kit (E0 export, per `official_reads/ROUTED_ABSDIST_ROOM_VSI5130_20261113.md`, "Fixed inputs").
- Row forms: `trace_ruling/out/TRACE_RULING_20261115.md` sections 2.1, 2.2 and 2.6; the failure-row example at lines 222-232.

## Files it may touch
Only `/scratch/jjyeung/orch_cd/b6_build/**`. Everything else is read-only. Output patches against other trees go in `b6_build/out/patches/` with the base file SHA256.

## Work items
1. **Eligibility gate** `work/gate.py`: one function `eligible(dataset, capture)` and a CLI over a capture list. It refuses benchmark rooms (all seven benchmarks), evaluation and qualification rooms, dev-84 rooms, dev-S1 captures and their physical rooms, and unknown aliases (fail closed). It writes a receipt with the SHA256 of every input list.
2. **Capture inventory** `out/CAPTURES.json`: every capture behind the absolute-distance and room rows in POOL_S1, with GT raster availability, frame source path and frame count. List where the original frames sit and how many bytes staging needs; mark that staging as a heavy-IO question. Select the K1 pilot: 300 eligible captures with GT rasters, ScanNet / ScanNet++ / ARKitScenes in pool proportion, split 80/20 by physical room, seed 17.
3. **GPU run card** `out/RUNCARD_K1.md` and `work/run_k1.sh` (not run): SAM 3 at `dense_aliases` on the pilot captures' 32 anchors per operand phrase, G3T E0 export with the step-544 heads' scale, then the frozen selector, depth cut and box policy. Append-only journals, resume checks, stall watchdog, time cap, vnice, node-local `/scratch` outputs, explicit card and node arguments. Estimate GPU-h from `devs1_masks/out/RUNCARD.md` rates.
4. **Selector refit kit** `work/refit/`: the unchanged `build.py`/`fit.py`/`fit_pairs.py` logic driven by the gate; it fits only on the K1 training rooms and reports held-out-room AUC, average precision and top-1 accept accuracy for both the refit and the current model on identical candidates. Export coefficients in the exact NumPy format `price2.py` and the native candidate policy read.
5. **Response renderer** `work/render.py`: from K1 cache outputs to per-row printed responses in the sealed 3.14 event schema with the runtime's own status strings; classify each row as trust, fallback or excluded by the trace ruling's rule (within 15% of GT and mask match; failure status). GT values feed only the classifier. Fallback traces never end in a refusal. Output one JSONL per type plus counts; consumers are `rs_rows` and `rs_tree`.
6. **Live-tower parity harness** `work/parity_live.py`: compares `sam3_tower` live outputs with cache entries for the same (frame SHA, phrase) under the noise-aware rule, and prints the GPU command for a 10-scene check.
7. **K1 analysis script** `work/k1_report.py`: computes the 4.6 kill rules (trust + fallback share, answered-item MRA versus the train-fitted constant, refit non-inferiority) and the cue-study AUROC on the held-out rooms. Pre-register its thresholds in `out/K1_RULES.json` with its SHA256 before any GPU output exists.

## CPU proofs (all must pass; record logs in `out/`)
- **P1 gate:** planted cases refuse `scannet/scene0380_01` (dev-S1), `scannet/scene0011_00` (ReVSI and dev-84), any VSI-Bench capture, an ARKit capture of venue 381879, and an unknown alias; an eligible pool capture passes. Every K1 capture passes; the receipt lists 0 refusals among selected captures.
- **P2 selector code parity:** running the refit code on `grd_selector/work/setsel/data/dev_tab.jsonl` reproduces the current DEPLOY coefficients and pair model to 1e-9 (proves code identity; that fit is then discarded).
- **P3 backend replay parity:** on the dev-S1 fixture, the K1 pipeline code with the current selector reproduces the existing priced predictions in `/scratch/jjyeung/mask_recall_run/results/dense_aliases/priced/PER_ITEM.jsonl` (arm `predicted`, source `g3t`, policy `frozen`) for at least 20 items across all three datasets, exactly. Read-only; dev-S1 is used only as a fixture.
- **P4 renderer:** byte-identical status strings to the runtime; a mutation that prints a GT value into a response is refused; a fallback row whose trace ends in a refusal is refused; response spans are marked for zero loss in the schema; every row records capture, frame SHAs and backend hashes.
- **P5 no-label leakage:** the refit's feature table contains no label-derived column (inject one, it must fail); thresholds come from training rooms only.
- **P6 live vs cache:** with a CPU SAM 3 stub and a recorded cache entry, the parity harness passes on identical outputs and fails on a shifted frame, a swapped phrase and a 0.05 score drift.
- **P7 first batch:** hand `rs_tree` a 32-row fixture of rendered absolute-distance rows (trust and fallback) that passes its row admission on CPU; record the call `rs_tree` must run for every rank's first batch.

## Deliverables
`out/CAPTURES.json`, `out/RUNCARD_K1.md`, `out/K1_RULES.json` (+ SHA256), `work/` code with tests, `out/patches/` (if any), `out/PROOFS.md` (P1–P7 with log paths), `out/HEAVY_IO_QUESTION.md` (exact staging bytes and source paths), and a design record `out/DESIGN_RECORD.md` (question, answer, evidence, rejected options, risks, tests, status). One event `events/<stamp>_RESULT_b6_build.md` of at most 40 lines. Defaults if unanswered: if the orchestrator rejects the trace ruling's deployed-response rows, items 4 and 7 still ship and item 5 ships as a fixture only; if the refit fails P2, stop and report rather than patching the fit code.

# Build brief B6-B (side experiment, after B6-A, not seal content): own-encoder grounding pilot

**Lane:** `b6_owngrd`, CPU preparation only; the GPU pilot needs the orchestrator's card. Same rules as B6-A.

- **Goal:** decide on training-side rooms whether the student's own ViT can replace SAM 3 (parity) or recover objects SAM 3 misses (complement), before any next-seal integration.
- **Inputs:** `own_head/out/PILOT_COMMAND_r11.md`, `own_head/out/BUILD_RECEIPT_r11.json`, teacher transport `/dev/shm/jjyeung_evalx/teach_r5_full/head_teacher_full.tar` (SHA `189140d7…`, trinity-2-18), `DD/PILOT_FULL_LABEL_PATH_20261111.md`.
- **Work:** (1) copy the teacher tar once to `/scratch/jjyeung/orch_cd/b6_owngrd/labels/` and verify its SHA256 (a local copy within node scratch; ask before any copy to /data*); (2) add the dev-S1 exclusion to the O1 gate and drop the 5 dev-S1 captures (`work/eligibility_checks.out.json`), rebuilding the label manifest and its receipt; (3) add a complement metric: on held-out training rooms, recall of GT instances that the teacher pass never proposed, at false presence no higher than the tower's; (4) state in the card that the head is fitted on step-544 ViT taps and must be refitted on the seal export before use.
- **CPU proofs:** r11's suite and mutants still pass; the rebuilt manifest contains no dev-S1 capture (planted check); the complement metric matches a hand count on a 3-scene fixture.
- **Kill rules (pre-register):** stop at step 600 if recall@5 < 70% (`DD/GROUNDING_OWN_ENCODER_20261110.md`, section 3.4); at the end, parity fails if on-target at matched coverage is more than 2 points below the tower's on held-out training rooms; the complement path dies if it recovers under 30% of held-out never-proposed instances (kit A's registered bar was 25 of 81, about 31%). Cap 4 A6000-h (`own_head/out/E_C_REPORT.md`).
- **Deliverables:** rebuilt label receipt, updated pilot command, `out/K_RULES.json`, design record, one RESULT event.
