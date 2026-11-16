<!-- recovered by seal_plan: transcript=71f94277 line=32184 utc=2026-11-14T15:11:49.700Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_native_pilot_4_launch_advanced.md heredoc_unquoted(vars_unexpanded) -->
# ORCH order: launch native pilot 4 on `advanced` (token e3e6c6421, family e2374d64)

I read the follow-up diff (F1 in the worker, F2 in the gate) and compared the seals: confirmed. Control files: `$C/REVIEW.json` and `$C/ORDER.md`.

1. Real packet, CPU admission and batch validation, one test-only call, one real submission on `advanced` with `ALLOW 169526 169530`. No retry. The general fallback (ee49236ff) stays unsubmitted.
2. If the scheduler does not start it within 20 minutes, tell me in one line with the pending reason; do not move it yourself.
3. RESULT when it returns, gate outcome first (the sealed P1 result, p1_gate with its tie list, P2 with its independent call count, P3, the probe's calls), then load time, peak memory, geometry seconds per capture, seconds per item pair, return size, the traces of the first camera, distance and room items (calls, responses, call and version error counts, the answers against the labels), and the full-read projection for 636 items over 84 captures against the time and return-size limits on `advanced` and on `general`.
4. If it passes, build the full-read packet for `advanced` at once and report its token; I order it separately. Main's orchestrator has been told the allocation is free for it, so a full read there needs my word first.