C1 sweep modes bind `carrier_placement`, `training_mode`, `depth_enabled`, the
schedule, and every input pin into the configuration identity. Preparation,
checkpoint resume and artifact loading preserve these bindings. All arms start
from the original Qwen3.5 base and train the LM with full FT.

| Arm | `carrier_placement` | Placement and attention |
|---|---|---|
| C1-a | `append_after_temporal_group_video_tokens_v1` | Two ordered CAMs follow each native fused temporal group; attention remains causal. |
| C1-b | `append_all_after_video_frame_embeddings_v1` | All 32 CAMs follow the final visual group and precede the question; attention remains causal. Each CAM has a learned frame embedding and its frame's native M-RoPE temporal ID. |
| C1-c | `append_after_temporal_group_video_tokens_bidirectional_v1` | C1-a placement; standard-attention layers allow every prefix token through the final CAM to attend to that whole prefix. Question and answer tokens remain outside the bidirectional region. |

Qwen3.5 fuses two RGB frames into each temporal patch. Those frames share its
native temporal ID; C1-b's separate embeddings distinguish their ordered slots.
Each frame embedding starts at `N(0, 1e-4)`; each CAM uses its frame's first
visual token as the origin for all three M-RoPE coordinates. Its temporal ID
still exactly matches the frame. Non-CAM positions and the separate text/cache
axis retain native values. C1-b exports bind `carrier_position_policy:
"frame_grid_anchor_v2"`; loading an older C1-b artifact without that policy fails.
The parent must reseal the changed source and prepare a new run; an old C1-b
checkpoint cannot resume under the new source binding. C1-c changes only standard
attention. **Gated DeltaNet remains recurrent and causal.** A later recurrent
layer may consume states contextualized by an earlier bidirectional standard
layer. Neither option changes the frozen base visual tower. Cached generation
applies the placement's positions and masks during prefill.

The native CPU learning guard fixes 32 rows, 32 frames, 200 updates, and pooled
mean rotation below 30 degrees. Controlled C1-b runs retained the same fixture,
seed, targets, loss and guard; the LR counterfactual alone overrides the frame
embedding group's LR after the guard sets it. The measurements were:

| Intervention from B30b C1-b | Final mean rotation (degrees) |
|---|---:|
| Original: frame embedding std 0.02; only temporal coordinates copied | 56.38 |
| Frame embedding std 0.0001 alone | 44.65 |
| Frame-grid spatial coordinates alone | 50.13 |
| Zero frame embedding initialization alone | 53.26 |
| Frame embedding LR multiplied by 0.1 | 56.55 |
| Odd CAM temporal ID incremented by one (diagnostic counterfactual) | 56.58 |
| Small initialization plus frame-grid spatial coordinates | 25.86 |
| Original plus pooled pair content (outside the requested hypothesis) | 9.22 |

The combined control rescales the original random draw. The implementation draws
directly at standard deviation 0.0001. The final uninstrumented suite passes all
three arms: C1-a 7.15, C1-b 20.52, and C1-c 17.55 degrees. C1-b's worst row mean
is 49.58 degrees; the unchanged guard applies its threshold to the pooled mean.

These controls identify an interaction between initialization and coordinate
assignment in this fixture. They do not establish that tied temporal IDs prevent
learning: the guard gives paired frames identical targets. The original CAMs'
mean attention to their own pair, conditional on attending to video, changes
from 5.93% to 5.97%; uniform attention would give 6.25%. The combined correction
ends at 6.13%, so passing the guard does not establish localized attention. Qwen
fuses each pair into shared visual tokens; this measurement cannot distinguish
the two RGB frames within a pair. The content experiment supplies another route
to learning, but the in-spec correction passes without it; runtime C1-b adds no
pooled content. All measurements use a tiny randomly initialized native model,
not a production convergence or GPU-fit measurement. The permanent guard and
its threshold remain unchanged.

Set `training_mode: "pose_only"`, `streams: {"pose": <A1 preparation pin>}`,
and `depth_enabled: false` for the pure pose sweep. `prepare` scans the existing
A1 database once in the parent's CPU data job and writes a pinned integer index
of exactly 283,200 dense `all_frames32` rows. It reuses the 321,152-row database
and excludes its 37,952 A0 rows. Every update uses 32 pose rows: four aligned
microsteps across eight ranks. No VQA, pointing or routing stream is admitted.
All text labels are masked. Gravity and trajectory-scale loss weights are zero;
the CPDM pose loss includes translation, quaternion and FoV. The private depth
branch is absent unless an arm explicitly enables it. With depth enabled, only
rows with valid depth labels drive that branch and its private FoV loss; enabling
it does not admit A0 or invent dense-row depth labels.

The parent fills `schedule` with `startup_seconds`, `p95_step_seconds`,
`checkpoint_seconds`, and `export_seconds` measured for the same arm. Set
`recipe = carrier_c1_sweep.recipe_for(config)` after filling these fields. The
planner fits updates, periodic and final saves, and milestone/final exports into
14,400 seconds with a further 900-second reserve. These times are identity-bound.
An unfilled template cannot pass validation. Production memory and throughput
remain parent smoke measurements; CPU synthetic timings cannot fill this plan.
Changing a sealed schedule starts a new identity, so resume retains the original
schedule. m400 still pauses for a gate if the schedule reaches it. All allocations
keep the four-hour runtime stop and explicit checkpoint resume; there is no
automatic relaunch. Checkpoint/export reserves require parent timing validation.

Every `evaluate` call writes `c1-readout-v2` with BOTH `detail` (unchanged sparse
32-anchor `head_acc_origin_metric_v1`, including its even-frame subset) and
`contiguous_clip`. The latter uses raw recording ordinals 0,3,...,93 from one
pinned recording per held-out scene. Its fixed denominator is all 38 scenes.
No sparse bank frames, invalid-pose skipping, or alternate recording selection
can silently replace a clip. The parent must bind the recording selection before
training. The builder refuses short or sparse inventories.

The separate parent `build-clips` CPU job needs a pinned `recordings` manifest,
`heldout_scenes` and `training_scenes` pins, and a new output path. Each recording
has `dataset`, `scene`, `recording_id`, `fps`, `total_num_frames`, `frames` and
`poses`. The frame pin names JSON `{frames:[{path,sha256}, ...]}` in complete raw
ordinal order. The pose pin names NPZ `{c2w:[N,4,4], frame_indices:arange(N)}` in
metric OpenCV camera-to-world coordinates. The parent extracts original RGB and
calibrated poses from full recordings; the existing 38-scene sparse bank cannot
supply this job. `build-clips` selects and authenticates the required RGB pins
and embeds the matching 32 GT poses. Bind its output as `readout.contiguous_clips`.

The metric converts head extrinsics into camera-to-world poses, fits one proper
Sim(3) per clip to camera centres, and applies its rotation and scale to the
predicted trajectory. It reports ATE RMSE in metres and adjacent sampled-frame
RPE translation RMSE in metres and rotation RMSE in degrees. The aggregate is an
equal-scene mean of the 38 clip RMSEs; each clip has 31 relative pairs. Invalid or
degenerate trajectories fail evaluation rather than shrinking the denominator.

[Cambrian-P section 5.1 and Table 5](https://arxiv.org/html/2605.22819v2#S5)
use Sim(3) and stride 3, with 90 frames at inference. This sweep follows the
binding 32-frame request, so its values are not a reproduction of that table.
The RMSE reductions and adjacent-frame pairing follow
[MonST3R's evo evaluation calls](https://github.com/Junyi42/monst3r/blob/main/dust3r/utils/vo_eval.py).
CPU tests compare the implementation with an independent Horn quaternion
alignment and scalar SE(3) reference on exact and noisy trajectories.

The m400 gate pins the combined pose report to the same config and artifact,
requires both readouts and all 38 scenes, and checks the existing sparse rotation
threshold of 39 degrees. No new clip threshold has been invented. Pose-only
gates need only the combined pose report. Mixed-mode gates additionally retain
their pointing and VSI-500 checks. CPU fixtures exercise these bindings; actual
held-out measurements and production full-recording inputs remain parent jobs.
