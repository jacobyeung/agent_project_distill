# E0 camera routed read: v3.11 camera programs on G3T x s against T0 m800 direct (lane mdg_next, 2026-11-10)

## Question
On E0's four camera types (displacement, movement_direction, rotation, bearing; 600 items, 11 MP3D val_unseen scenes), do the v3.11 camera programs on G3T x s pose (s from T0 m800's own depth) beat (a) T0 m800's direct answers under the E0 prompt and (b) the no-information baselines, with the 11-scene bootstrap CI lower bound above 0?

## Answer (pre-launch)
- **Kit:** `/scratch/jjyeung/orch_cd/mdg_next/work/e0kit` (own git; package `e0k`; 7 tests). `run_e0.sh E0.env STAGES` with stages anchors, direct, export, g3t (GPU host) and heads, arms (trinity-2-18). Host scripts: `stage_e0.sh`, `gpu_e0.sh`, `collect_e0.sh`.
- **Arm 3 (GT pose ceiling), done on CPU:** the programs on E0's GT poses score 100 / 100 / 100 / 100. The printed tool text equals the label's response on 600 of 600 items, so the programs and E0's answer rules agree exactly (same rule as lane e0_score, `nav.items` / `nav.geometry` at a1ec46f).
- **Arm 2 (routed):** G3T runs on 64 render states including the 32 clip states when the render holds 64, else on the 32 clip frames and reads its heads at the 32 clip anchors (ttower's n64 schema). rk.geom then scales t by s = median(own depth / G3T depth) (ttower's frozen rule) and rotates into T0's own gravity frame. The programs answer from the result. A refusal (zero displacement, no unique dominant component, quadrant boundary, missing heads) falls back to direct in `routed+fb`.
- **Arm 1 (direct):** T0 m800 loads as plain Qwen3.5 from its full-FT export (no carriers, as in every T0 direct read). Prompts go through nav's `encode_prompt` and nav's greedy `decode`, with tool delimiters suppressed; this is the path f17's E0 direct cell ran. Answers are parsed by `orchard_eval.answers.parse_answer`. The CPU encode of an E0 prompt with T0's processor gives 2,608 prompt tokens and 9,216 video patches for 32 frames.
- **Arm 4 (pose error):** per clip, relative to frame 1 in each source's own frame: rotation error, translation-direction error (steps > 0.25 m), centre error as % of GT path length, and scale ratio (predicted / GT path length), reported apart from the questions.
- **References to beat** (e0_score): f17 head poses through the same rule 40.3 / 58.0 / 66.7 / 60.0; f17 direct 36.3 / 51.3 / 54.7 / 33.3; no-information 47.7 / 56.0 / 51.3 / 44.7 (displacement median constant, else the majority letter; label-derived, so optimistic). f17 heads on E0: rotation 24.4 deg, translation direction 33.0 deg, scale 0.78.

## Decision rule (pre-registered)
Per type, routing wins when routed+fb minus T0 direct AND routed+fb minus the best no-information baseline both have a CI lower bound above 0. Winning types get the G3T x s tool flag for navigation evaluation and become routed rows for navigation training. If a scale ratio's median sits outside [0.8, 1.25], or the rotation median exceeds f17's 24 deg, G3T x s is not trusted on Habitat renders. In that case the scale or rotation source is fixed before any navigation row is built on it, whatever the answer scores.

## Confounds and how the kit handles them
- **Question semantics:** settled by arm 3 (100 on every type, identical printed values).
- **Habitat renders are new to G3T and to T0's depth:** arm 4 reports s per clip against GT path length; displacement depends on s directly, while direction and rotation do not.
- **Frame count:** G3T sees up to 64 dense render states; the LM and T0's own heads see the 32 clip frames.
- **Own-heads prompt:** T0's own depth and gravity come from rkit's export prefill (MDG prompt, a placeholder label, a random decoder whose masks are unused), with the clip's render-state indices as timestamps rather than E0's nominal 0-31. This affects only s and gravity.
- **Clips that repeat a state** (short prefixes) cannot give G3T 32 distinct anchors. They are refused and those items fall back to direct; 2 of the 336 clips (2 items) repeat.
- **Generation config:** the T0 bundle has no generation_config.json, so the kit uses greedy decoding with eos {<|im_end|>, config eos} and a 16,384 cap, recorded per rank.

## Inputs
- Cohort, labels, GT readouts and nav code: trinity-2-18 `/scratch/jjyeung/orch_cd/nav_build/e0_copy_20261110/` (58 MB; staged to the GPU host).
- **Renders (only on trinity-0-13):** 336 clips. The 32 clip frames come to 10,747 PNGs, and the G3T set to 15,099 PNGs (it contains the clip frames; 64 frames for the 136 clips whose render holds 64 states, the 32 clip frames otherwise, because the tower read layer accepts exactly 32, 64 or 96). Lists: `work/out/e0/frames/FILES_{clip,dense}.txt`, relative to `/scratch/jjyeung/orch_cd/nav_build/out`; `tar cf - -C <root> -T FILES_dense.txt` copies them. Bytes are not measurable from 2-18. At 0.3-0.6 MB per 512 x 512 PNG, the G3T set is about 4.5-9 GB and the clip set 3-6 GB. GT depth (.npy) is not needed: 0 bytes.
- T0 m800 export, T0 bundle, G3T weights, envs and vnice come through `work/launch/stage_host.sh`, as for the MDG read.

## Cost (estimates)
