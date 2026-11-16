<!-- recovered by seal_plan: transcript=71f94277 line=32232 utc=2026-11-14T15:17:22.819Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_pilot4_queue_refusal.md heredoc_quoted -->
# ORCH ruling on the pilot-4 queue refusal

The refusal was right: the account is shared with main, and main has priority. Main's protected jobs (167739, 167857 to 167861, 167894, 168278) may include one that was waiting for `advanced` behind our production job and started when it ended.

1. Authorized: in your next batched observation call, one read-only listing of this account's jobs on every partition (job id, partition, state, reason, start time, time limit, node, GPU count), saved to a file before any validation. No other new call.
2. Then decide by this rule and act without asking again:
   - **An unlisted job is RUNNING or PENDING on `advanced`:** do not submit to `advanced`. Submit the pilot's `general` fallback packet instead (token ee49236ff, family e2374d64), allowing 169526 and 169530. I have written its control files: `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_ee49236ff/`. In the same call hold 169530 with exactly `scontrol hold 169530`, and release it with exactly `scontrol release 169530` once the pilot is RUNNING or finished, so the pilot takes the card when the final stop read ends.
   - **The only unlisted jobs are on other partitions (for example `preempt`) and `advanced` shows none of this account's jobs:** submit the `advanced` packet e3e6c6421 as ordered, with those job ids added to the allowance, and name them in your event.
   - **Anything else** (an unlisted job on `general`, or a job you cannot classify): submit nothing and send me the listing.
3. One event with the listing's rows, what you submitted, and the states.