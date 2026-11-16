<!-- recovered by seal_plan: transcript=71f94277 line=33633 utc=2026-11-14T21:11:20.015Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_IF8_controls_build_runnable_packets.md heredoc_unquoted(vars_unexpanded) -->
# ORCH: IF8 control files supplied; build the runnable packets

Your answers settle the validator question: IF8 checks P0's result exactly inside the job, in the production runtime, and nothing local is blocked; the runtime diff is empty and the seal stays eef3ba96. Good.

Control files: `$C/` (review.md, confirmation.json, launch_note.md), in your form. If your admission wants the launch note to hold the one LAUNCH line only, tell me and I rewrite it; do not edit my files.

1. Build the runnable IF8 packets for `general` and `advanced` with fresh tokens, run the kit's own admission on each with these controls, and hand the `general` packet to evalx with a one-line inbox note saying submission waits for my order. One RESULT with tokens and hashes.
2. One risk to state in that RESULT in a single line each: what the in-job prior check does if its recomputed secondary floats differ on the job's host (refuse before staging, with which message), and which measured guard stops IF8 if its step time or memory exceeds the budget.
3. After that, wait for the job's first evidence from evalx as you did for P0.