<!-- recovered by seal_plan: transcript=71f94277 line=32483 utc=2026-11-14T16:28:36.985Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_release_P0_now_pilot5_to_advanced.md heredoc_quoted -->
# ORCH order: release P0 now; pilot 5 goes to `advanced`

Our `general` slot has been idle since 15:53Z while the package is repaired. That is longer than holding a ready 3.5-hour job is worth. New plan:

1. In your next batched call, run exactly `scontrol release 169530` once and read it back. P0 then runs on `general`; observe it with the usual stall rule. No cancel without my order.
2. Pilot 5 goes to `advanced`. Build its `advanced` packet first. Main's three jobs there (167859, 167860, 167861) are pending on a dependency; a ten-minute pilot does not get in their way, and main's orchestrator was told such a job may use the allocation. At submission the fresh listing must show, for this account on `advanced`, only those three jobs and each still PENDING with reason Dependency; allow them and 169530. If any of them is RUNNING, or pending for another reason, or another job of the account is on `advanced`, do not submit: tell me in one line.
3. The full read is not decided: after a passed pilot, build its packet for both partitions and report; I order it separately, and on `advanced` only after telling main.
4. My 16:01Z rule "release 169530 if pilot 5 fails" is replaced by item 1.

Your event with the new family sha, object, token and check record is still the next thing I need; I answer with control files for the `advanced` token.