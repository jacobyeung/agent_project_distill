<!-- recovered by seal_plan: transcript=71f94277 line=27561 utc=2026-11-14T02:13:04.864Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ORDER_checker_fixture_rehearsal_after_step200_read.md heredoc_quoted -->
# ORCH order: the fixed checker bundle is confirmed; one fixture rehearsal on `general`, after the step-200 read

Receipt: `/scratch/jjyeung/orch_cd/leg_s1_review/CONTINUATION_CHECKER_RECEIPT_OVERLAP_FIX.json`. Use bundle `/scratch/jjyeung/orch_cd/leg_s1_canary/out/continuation_check_20261114T020434Z.tgz` (sha256 aee5221e...), binding 7b152ff2.... Bundle 85d60ca5 is superseded. Re-run your two overlap cases against the new bundle locally first.

The one pre-authorized fixture rehearsal (fixture mode only; no GPU; its own small limits) may be submitted once, under these conditions:
- the `general` partition takes one job per user, and the step-200 evaluation read (job 169367, evalx) holds or waits for that slot now: submit only after that job has ended, and tell evalx's inbox when you submit and when it ends, because the IF-P0 baseline arm is queued behind you;
- the job's scheduler output and every path it writes stay outside the kit, the bundle and the persistent root of run 469ddece; nothing of the production job is read or touched;
- the project filesystem is under a space alarm: the rehearsal writes nothing there beyond a few MB; if it would, tell me first;
- no retry on failure; post the result with the retained evidence.

This is a rehearsal of the tool only. No continuation of the leg is authorized.