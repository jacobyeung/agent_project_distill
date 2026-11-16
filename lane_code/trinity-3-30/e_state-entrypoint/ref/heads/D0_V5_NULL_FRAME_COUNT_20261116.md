# D0 v5: 81 rows without a frame count (2026-11-16)

Question: why do 81 D0 v4 rows carry student_input.total_num_frames null, which the kit's duplicate layout refuses, and can a permitted source fill them?

Answer: no permitted source exists, so v5 (4af43b40…, 152,123 rows) leaves all 81 out. The rows never entered a sealed VQA stream: 43 direction and count rows are ARKitScenes pool programs that the sealed leg deferred, and 38 route-planning rows rode the sealed routing stream, whose s1_routing.resolve sets d3 frame counts to max frame index + 1 (flagged lower bound). D0 moved those types into VQA and kept the pool's null.

Evidence: events/rows_rebuild/d0_v5/D0_V5_EVIDENCE.md. k/frame_rates.json (36ae882f…) holds fps only; the sealed VQA store c180e779… holds no row of the 31 captures; frame_plan.json.gz has no d3 video; the sealed layout_inputs passes every v5 row and fails exactly the 81 in v4.

Options rejected: filling from s1_routing's lower-bound rule (a derivation the ruling forbids unless the orchestrator names it a source); deriving counts from recordings (forbidden).

What might not work and how we notice: the rest of mode p (pose, pointing, routing builds, run.prepare as a whole) did not run on CPU, so job A's rerun is the first full test of it; a refusal there names its function in the traceback.

Tests that would settle it: job A mode p admitting v5 in full.

Status: v5 built and checked; awaiting the orchestrator's admission.
