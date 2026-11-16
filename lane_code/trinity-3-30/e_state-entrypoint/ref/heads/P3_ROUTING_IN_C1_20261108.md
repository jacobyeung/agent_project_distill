# P3 self-routing inside the C1 trainer: routing stream, scheduled sampling, one FoV (p3_build, 2026-11-08)

## Question
How does the final run (one run from base Qwen3.5-9B: pose and depth heads with their losses, VQA, pointing, routing traces) train P3's self-routing, and what does the Sunday mixed gate run?

## Answer
- P3 lives in the C1 trainer (b42 line, `carrier_c1_*`), not in the older L1-based P3 kit. Code: branch `p3-mixed-20261108` in `/scratch/jjyeung/orch_cd/p3_build/work/c1mix` (clone of 6f97471). New mode `training_mode: final` with streams pose, vqa, pointing, routing.
- Routing rows are derivgen `derivgen-row-v2` rows (form `spec-v3.8-calculator-v2`). The target is the producer's text verbatim. Every `<tool_response>…</tool_response>` span, delimiters included, gets no language loss; everything else in the assistant suffix does (plan, calls, arithmetic prose, answer). The opening `<think>\n` sits in the generation prompt, so it is never a target.
- Scheduled sampling (USER 11-07; gates per SELF_ROUTING_DESIGN_20261108 1.2): per (step, microstep) rank 0 draws (depth_own, pose_own) from per-head gates on all-reduced pose-stream EMAs and broadcasts them. Depth opens on a Stage-1 V-C init plus FoV EMA < 2 deg (else depth AbsRel EMA < 0.25) at p 0.5; pose opens below 20 deg and reaches p 0.5 at 10 deg (orchestrator 12:56Z); `force_from_step` opens both (test run: 100). Rows with pose calls stay GT until pose is own; depth-only rows use own depth with GT pose (`gt_pose9`, `gt_up`); pose-own rows with GT depth place recorded GT clicks with own pose. Own values: one no-grad forward of the question-independent video+carrier prefix reads the pose head (32 per-frame codes, gravity) and the private depth head at 25 stencil points per click. A fixed, parameter-free layer turns them into derivgen's printed numbers. The vendored printed-point calculator (derivgen `calculator.py`, sha 538b9346…) recomputes every calculator response from the printed points. The suffix is re-tokenized and spliced after the unchanged prompt and video. The model-authored text stays GT.
- One FoV (FOV_INTRINSICS_EXTRINSICS_20261108): with `depth_fov_source: pose_head` (required in final mode), the depth head is conditioned on the pose head's slots 7:9 (detached) in training and in the readout, and the fixed layer unprojects with the same values. The private FoV branch trains nothing in this mode.
- Mix and world size are config. Test run: (pose, pose, vqa, pointing, routing, routing), 48 rows per update at world 8, 200 steps, milestones 100/200. World 8/16/32 give one row per rank per microstep.
- Head openers `<depth_at <move <pose <turn <box_3d` are dedicated tokens (mean-of-constituents init); calculator commands stay text. Routed evaluation uses `carrier_c1_decode.generate` (same fixed layer and calculator as training) and `carrier_c1_canary` (C1/C2/C3/C7).
- Answer-only DIRECT rows (empty think) are admitted for DIRECT-policy types (USER 05:05 PT); route rows must be v3.9 `per_frame` except interim pools (`--allow-paired-anchor`).

## Why (evidence)
- The L1-based P3 kit (4ed4a27) normalizes 0/33 canonical v3.7 fixtures (`inbox/20261107T1356Z_canonical37_consumer_probe.md`), has no carrier pose head, and refuses own-head values in production training (`PRELAUNCH.md`). The C1 trainer already has mixed streams, the m400 pose/pointing/VSI-500 gate, FSDP, timed resume and the AWS kit.
- Rendering is exact: all 625 review-pool v1 rows re-render byte-identically from their events, and replaying their recorded values through the vendored calculator reproduces every target and span (`tests/test_carrier_c1_routing.py`).
- Masks are exact on the real Qwen3.5 tokenizer: `<tool_response>`/`</tool_response>` are single special tokens (248066/248067), so no token straddles a span edge; the masked token text equals the span text on all 625 rows (39.6% of suffix tokens are masked).
- The fixed layer matches derivgen's GT conventions (frame-1 level basis from gravity, public y up, p30 over a ±10 5×5 stencil, spread (p80−p20)/max(p50,1e-3), move in the start camera's level frame, turn as wrapped heading difference): a synthetic-world test compares it with derivgen's formulas on poses, moves, turns and clicks.
- Pose code convention: E_k = inv(C_k)·C_1 (t, q xyzw, FoV vertical, FoV horizontal), gravity = frame-1 OpenCV up (`camera_targets.py`). Frame 1 is the identity by definition.

## Options considered and rejected
- Keep the L1-based P3 kit and bolt on carrier pose: rejected; its data adapter targets old grammars and its admission machinery blocks own-value training.
- Re-derive the answer and reasoning from own values (faithful policy): rejected for now; it needs derivgen's full program materializer per row and step. The user ruling asks for routed values from own heads with value spans masked, which this implements.
- Per-row own/GT draws: rejected; the readout forward is an FSDP collective, so ranks must agree per microstep.
- Re-encoding the video for own rows: rejected; the splice reuses the processed video and carriers and only re-tokenizes the suffix.
- Conditioning depth on GT FoV (teacher forcing) in training: rejected by the one-FoV rule.

## What might not work (and why)
- Mismatch between injected own values and GT-authored text teaches the LM to ignore tool outputs (the gt_answer failure mode). Keep `max_own_probability` ≤ 0.5 and start own values only once the heads are good (pose ≤ 39° at m400). Watch routed-answer accuracy in own mode versus GT mode at each milestone.
