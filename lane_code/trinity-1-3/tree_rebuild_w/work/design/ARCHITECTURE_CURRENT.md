# Current student architecture (LEG-S1 step 544 -> D0 / Orchard 170111). Read before touching the model.
Question: what is the model that D0 and the next legs train and read? Status: current as of 2026-11-16; items marked UNCONFIRMED were not found in the sealed tree on trinity-3-30.
Abbreviations: T = /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot (sealed b01ce449 trainer source); C = distillation_orchestrator_20260918/orch_n30/events/cont_ops/PRELAUNCH_CARD_D0.md; DD = this folder.

## 1. Forward pass
```
32 RGB frames (frame_layout duplicate, all_frames, frame_markers on) [kit 07ca49df k/b02e4385.json] -> Qwen3.5 ViT -> merger -> visual tokens + per-frame CAM carrier tokens
   |                                         [T/carrier_c1_data.py:232 insert_frame_carriers]
   +-> PRIVATE ViT copy (deepcopy, trainable, merger frozen) -> PointDepthHead (3 ViT taps, cross-frame blocks) -> depth at uv  [T/carrier_c1.py:39-60]
Qwen3.5-9B LM (full fine-tune) -> hidden states
   +-> CAM carrier states -> CameraSupervision pose head (trunk depth 4): pose9, FoV (slots 7:9), gravity (weight 1 in final mode), log-scale token (weight_scale default 0)  [T/carrier_c1.py:148-152, camera_head.py:81-107]
   +-> text tokens: answer, or routing opener  <ground mode=box|room ...> / <gap a= b=>  [T/ground_tokens.py:2]
 routing call -> frozen towers serve it: SAM 3 (0.85B, dense_aliases proposals + frozen selector) -> masks; G3T (frozen) lifting x own-head scale -> metres  [DD/B6_GROUNDING_DESIGN_20261115.md l.11,26]
 result is printed back as text:  <tool_response> ... </tool_response>  (span masked in the loss)  [DD/TRACE_RULING_20261115.md l.225-228]
 LM continues and writes the answer. No external harness in the product path (USER 2026-11-07).
```
Not in D0: GF-1 geometry fusion, online G3T features into the LM (geometry_online unset), MDG/grounding head [C section 8; DD/B6 l.11].

## 2. Components
| Component | State in D0 | LR | Source |
|---|---|---|---|
| Qwen3.5 LM | trained, full (`lm: full`) | 1e-5 x lm_lr_scale 0.6 = 6e-6 | [C section 2; T/carrier_c1.py:22-23,666] |
| Qwen ViT (inside base) | no freeze list in the kit config; trained by full_ft with the base group; exact flag UNCONFIRMED | UNCONFIRMED | [T/carrier_c1.py:131-136] |
| Private ViT copy (encoder_copy) | trainable; merger frozen | 1e-5 (encoder_learning_rate) | [T/carrier_c1.py:47-49,666] |
| Depth head (PointDepthHead) + frame queries + fov linear | trained (heads: [pose, depth]) | 1e-4 | [C section 2; T/carrier_c1.py:23] |
| Pose head, inherited tensors (auxiliary_heads.pose.head.*) | trained | 1e-5 (heads_pretrained) | [T/carrier_c1.py:648-650,666] |
| Pose head, new tensors / frame embeddings | trained | 1e-4 | [T/carrier_c1.py:652,666] |
| Scale | no separate head; a scale token + MLP inside the pose head (has_scale, log d-bar); weight_scale default 0; metric scale for programs comes from the tower scale rule | n/a | [T/camera_head.py:84-107, tower_scale.py, tower_scale_rule.json] |
| Pointing | no head; text JSON stream | LM rate | [DD/MIX_STREAMS_DESIGN_20261108.md] |
| Presence | no head; model's own yes/no probe only | n/a | memory result-presence-pose-routing-20261110 |
| Routing-opener embeddings | re-initialized after LM load in final mode | LM rate | [C confound 1; T/carrier_c1_run.py:781-783] |
| SAM 3 tower | frozen, deployed only | none | [T/sam3_tower.py; DD/B6 l.26] |
| G3T tower | frozen, deployed in programs (lifting) | none | [T/g3t_online.py; DD/B6 l.11] |
Kit recipe (final mode): steps 1000, seed 17, world 4, global batch 288, weight_decay .01, warmup .05, clip 1.0; loss weights pose 1.5, depth .25, depth_fov .05, vqa 1, routing 1, pointing 1; pose_lr_scale 0.6 (pose-group LR 6e-5); camera weight_focal 2.0; depth_fov_source pose_head; pointing weights decision 5, row_mean 2; scheduled sampling off (max_own_probability 0) [kit 07ca49df k/b02e4385.json]. D0 resets optimizer, warmup and LR schedule [C confound 2]. Parameter count: Qwen3.5-9B by name; base_identity c202236235762e1c871ad0ccb60c8ee5ba337b9a; no config.json found (UNCONFIRMED).

## 3. Routing by question type (TRACE_RULING 2026-11-15)
| Route (program with tool_response) | Answer directly (qualitative trace, no stated measurement, no tool tag) |
|---|---|
| object absolute distance, room size, camera displacement, camera movement direction, camera rotation | direction easy/medium/hard, facing twins, relative distance, object size, counting, totals, appearance order, 3D box, route planning |
A direct row that contains `<tool_response>` must fail validation [DD/TRACE_RULING l.285]. Room direct rows wait for A0 [C confound 4].

## 4. Training mix (D0, 288 rows per step, world 4, 1,000 steps)
pose 64 (194,987 rows), VQA 128 (152,123 rows, v5 rows.sqlite 4af43b40), routing 64 (47,732 rows: camera displacement 14,020; movement direction 12,260; rotation 9,143; absolute distance 11,728; room 581), pointing 32 (20,239 rows) [C sections 2, 4].

## 5. Train vs deploy
- Training program rows print ground-truth responses; deployment prints SAM 3 + G3T x own-scale responses on predicted geometry [C confound 5, section 8].
- A direct harness returns no tool response, so the model repeats calls; read routed types only through the native routed read [memory result-legs1-m100-20261114].
- The model does not convert units itself (native cm 6.1 / ft 18.3 / in 24.8 against scripted 63.6 / 48.9 / 49.1) [DD/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md l.51].
- Gravity guard: reviewed guard refuses 1 dev-S1 capture; the sealed guard would refuse 11 [same file l.50].
- D0 withholds the 80 rooms only from VQA; routing, pose and pointing still train on them [C confound 6].
- Eval frame layout must equal the training layout; mismatch costs 3-13 points [memory lesson-eval-frame-layout-must-match-training-20261111].

## 6. Open items
- max_pixels / resolution: not set in the kit config, so the base processor default applies (about 4,160 visual tokens for 32 duplicated frames in the carrier lineage). Value UNCONFIRMED.
- Frame count: 32 (the carrier readout requires all 32 frames [T/carrier_c1.py:590]).
- Qwen ViT trainable flag: the kit config has no freeze list and no train block; full_ft decides. UNCONFIRMED.
- Parameter count and hidden size/layers/vocab: no base config.json reachable on Orchard login paths read. UNCONFIRMED.
- Pose-head scale token supervision: weight_scale is not set in the kit config, so the default 0 applies and the token is unsupervised in final mode. Inferred, not observed in a run.
- Kit config path: Orchard ~/okit/x/07ca49df/k/b02e4385.json (sealed; D0 overrides in trinity-1-3:/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/over_b.json).
