<!-- recovered by seal_plan: transcript=71f94277 line=30046 utc=2026-11-14T08:32:29.464Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_NOTE_seal_799a21dd_in_independent_confirmation.md heredoc_quoted -->
# ORCH note: seal 799a21dd is in independent confirmation

Thorough work on the production kernel path. An independent reviewer is confirming the diff from 0fa68201 (brief `/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_IF_P0_SEAL_799a21dd_CONFIRMATION.md`; verdict `leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md`), with particular attention to the two checks that have never run on a GPU (the Triton compile probe and the per-layer path rule) and whether either could refuse a correct runtime. Keep the seal frozen.

A fact for you meanwhile: the routed-read pilot (a sister job using the same production interpreter, NumPy overlay and FLA closure) is running on Orchard now and has passed its own overlay and `ptxas` assertions with file modes restored the way you now do it. So the staging side of your fix is consistent with a real job.

When the verdict is READY I write the control files for 799a21dd and name the partition. The one-GPU slot is held by that pilot for up to 90 minutes and the step-400 read is next in line, so P0 will most likely go on `general` after those two, or on `advanced` from about 15:00Z; prepare the launcher commands for both.