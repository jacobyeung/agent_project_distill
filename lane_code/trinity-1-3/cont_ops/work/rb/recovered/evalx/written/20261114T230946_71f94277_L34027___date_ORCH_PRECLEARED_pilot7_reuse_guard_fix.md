<!-- recovered by seal_plan: transcript=71f94277 line=34027 utc=2026-11-14T23:09:46.015Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_PRECLEARED_pilot7_reuse_guard_fix.md heredoc_quoted -->
# ORCH: pre-cleared for a controller-local fix of the reuse guard, then submit pilot 7

A refusal of your own guard before any Orchard call is not a transport failure. Find what the guard counted as missing or extra, then:

- If the difference is in the staged payload itself (a file of an uploaded object missing, changed or added): stop and send me the list. Do not submit.
- If the payload is intact and the guard miscounted (for example the authorized packet folder, the control files, a log or a receipt written into a namespace it walks, or a path it resolves differently in the real launch than in the offline check): fix the guard or move the stray bookkeeping file's destination for future writes, controller-local only, and add a test in which a real extra and a real missing payload file still refuse. Family 2d35df00, packet eb3422001 and my control files must be byte-unchanged. Then submit under the standing order without asking again, and put the cause, the changed files with hashes and the test result in the submission event.

The offline check passed and the real launch refused, so say in one line why the two differed; that gap is the thing to close.