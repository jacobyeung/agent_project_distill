# GX geometry input: feed frozen G3T into the student's CAM carriers (judge record, 2026-11-09)

## Question
The student's held-out camera centre error stays at ~49% of distance, about 20 deg of translation-direction error, and three differently trained heads share that plateau (f17, C1-a, T0). The user asks: has the feature alignment proved useful, and should we use ViPE features instead? If geometry has to enter the forward pass, which GX design do we build and test first?

## Answer
- **Loss-only alignment bought speed, not accuracy.** C1-r (projector + Pearson/CCC to G3T layer-23 camera tokens + G3T head init) led C1-a by -19.6 deg rotation at m100, -8.1 at m200 and -4.8 at m400, and then reached the same centre band (58% at m400 vs C1-a's 61%; C1-a m800 49%). The final run should not carry it beyond warm-up.
- **Do not use ViPE as an input feature.** ViPE runs DROID-style bundle adjustment on dense 10 fps video at 1.7 H100-min per recording. It yields no feed-forward per-frame token for the student's 32 sparse frames and cannot run inside an RGB-only forward. Use it as the pseudo-pose label source for unposed video (centre 0.081 after x1/1.089), as already adopted.
- **Feed G3T as input instead.** The only strong evidence that G3T geometry transfers comes from input-side feeding: PDG v3 m1400, a G3T-fed student, reached 8.3 deg rotation and 0.18 centre on the 38 held-out scenes, against f17's 13.2 deg and 0.42, with 85.5% vs 62.4% 4-way displacement-direction agreement (`/scratch/jjyeung/orch_cd/head_acc/REPORT.md` T1).
- **Chosen design: arm GXC (design 1), with three grafts.** A frozen G3T runs inside the student's forward on the same 32 frames. A zero-initialised connector adds each frame's G3T layer-23 camera token and decoded pose to that frame's CAM carrier input embedding. The grafts: (a) a zero-init output matrix replaces the scalar tanh gate (from designs 2 and 3); (b) the pad slot carries G3T's local-vs-global rotation disagreement (design 3); (c) the step-0 probe compares Qwen-unpatchified frames with natively decoded frames, and the passthrough converter doubles as the ceiling probe (designs 2 and 3).
- **Status: DESIGN, gated on the G3T ceiling probe below.** Before GX enters the paper line, the orchestrator must confirm with the user, who on 11-02 preferred no G3T in the model input (`memory/pd-curriculum-g3t-bet-20261029.md`).

## Scores (1 = poor, 5 = best)
| criterion | D1 carrier-embedding injection (GXC) | D2 carrier cross-attention in top layers (CX) | D3 readout feedback + G3T-seeded residual head |
|---|---|---|---|
| expected centre/direction gain | 3 (dir 11-14 deg, centre 32-40%) | 3 (dir 11-14, centre 30-38%) | 5 (dir 5-8, centre 15-25%, mostly G3T copied) |
| build risk and hours | 5 (8 h; connector, hook and config already exist) | 2 (15 h; FSDP post-hooks under checkpoint recompute, replicated module path, loader change) | 2 (14 h; converter conventions, prompt builder, head rewrite) |
| test cost | 5 (~34 GPU-h, matched rows) | 4 (~30 GPU-h, frozen-LM arm is not matched to its control) | 4 (~32 GPU-h plus a free m0 passthrough) |
| warm-start compatibility | 5 (step 0 bit-identical to C1-a m800; T-line takes it at a change point) | 4 (step 0 exact; production adds hooks and a freeze knob) | 2 (the text line shifts positions and +1.1k tokens; the head is rebuilt) |
| RGB-only, end to end | 5 (the LM carries the geometry to the model's own head) | 5 | 3 (the head starts from G3T's pose, so "own head" may reduce to "G3T plus learned scale") |
| total | 23 | 18 | 16 |

D1 wins because it is the cheapest decisive test that answers the real question: does G3T geometry that enters the LM reach the CPDM head? D2 stays as the fallback if the LM washes the signal out. D3's seeded head becomes an option only if the user accepts "G3T plus learned scale" as the claim.

## Reasons with evidence
- **The plateau belongs to the input and pathway, not the data or the scale.** f17 (34,636 in-domain clips, 2,893 steps), C1-a m800 and T0 m100/m200 all read 48-49% centre and 19-20 deg direction on the 312-scene harness. A per-scene LS scale fit removes only ~1 point (49.3% to 48.2% for C1-a m800), so the error is direction (`evalx/events/20261109T0327Z_RESULT_centre_split.md`). The excess sits on short paths: the 0.45-1.9 m tertile reads 26.3 deg and 59% for T0 m200.
- **Other levers are closed.** P0.5 partner frames lost as a mid-run switch, and from base they tripped the fail-fast at 1.193x loss (`C1AP_P05_FROM_BASE_20261109.md`). With GT pose supervised, a depth-pose consistency term adds no information. More short-path rows only reweight data that f17 already had.
- **G3T has the signal on these frames.** It reaches 2.3-2.9 deg rotation and 0.229 centre at training-scene scale (0.085 at oracle scale) on 32 frames of 58 ScanNet recordings (`VIPE_PILOT_20261108.md`). It has not yet been measured on the 312 harness scenes, which is why the probe gates this design.
- **Pose gains are worth points.** A 15% centre cut is worth +1.0 VSI [+0.5, +1.5] on the program path. Matched simulation at PDG v3-level pose gives 76.6 on the 655 items (VSI 68.6), against 73.0 direct (`POSE_ACCURACY_BRIDGE_20261108.md`). Camera motion breaks even at ~50% centre, room size at 39% and counting at 17%.
- **Scalar gates stay shut.** PDG's zero-init tanh gates read 0.0008-0.011 after 400 steps and 0.037 after 1,550. Under Adam a scalar moves about lr per step, so 1e-4 x 1,550 caps it near 0.04. A zero-init matrix opens faster, because its output sums ~lr-sized steps over its 4,096-wide fan-in. Graft (a) follows from this.
