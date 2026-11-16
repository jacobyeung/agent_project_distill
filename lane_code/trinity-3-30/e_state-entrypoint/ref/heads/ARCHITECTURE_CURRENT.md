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
