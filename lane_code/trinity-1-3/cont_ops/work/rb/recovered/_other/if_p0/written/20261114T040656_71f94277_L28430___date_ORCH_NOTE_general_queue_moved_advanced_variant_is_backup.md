<!-- recovered by seal_plan: transcript=71f94277 line=28430 utc=2026-11-14T04:06:56.633Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_NOTE_general_queue_moved_advanced_variant_is_backup.md heredoc_quoted -->
# ORCH note: the one-GPU queue moved; the `advanced` variant is now a backup

The step-200 evaluation read (job 169367) started at 03:32Z, far ahead of its forecast, and should end at about 04:40Z. Your P0 job 169413 is pending only on the one-running-job limit, so it may start on `general` right after that.

Finish the `advanced` admission you are working on and deliver it as ordered (it is a small diff and I want it sealed and confirmed as a backup, and for the later arms), but do not expect it to be submitted for P0: if 169413 starts first, the `advanced` packet for P0 is never sent. No rush on it.

When P0 starts, evalx posts its staging, preflight and namespace smoke test observations; I will forward anything that needs you.