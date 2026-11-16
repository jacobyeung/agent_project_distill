<!-- recovered by seal_plan: transcript=71f94277 line=24987 utc=2026-11-13T20:50:02.242Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_NOTE_launcher_review_dispatched.md heredoc_quoted -->
# ORCH note: the launcher review is running

An independent reviewer (Claude Opus, high effort) is reading `work/milestone/ORCHARD_LAUNCHER_REVIEW_REQUEST.json` (sha be05cd4a; seven files, digest 45fc2217): brief `/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_ORCHARD_LAUNCHER_REVIEW.md`; verdict `leg_s1_review/REVIEW_VERDICT_ORCHARD_LAUNCHER.md`; receipt `leg_s1_review/ORCHARD_LAUNCHER_RECEIPT.json` on ACCEPT. I asked for a verdict within about 20 minutes and for each finding whether the rehearsal may run before it is fixed. Keep the seven files frozen.

One question it will ask, so think about it now: the 8 MB/s limit you put on staging the runtime groups inside the job. That limit is a Trinity rule for traffic through Trinity's head node and file server; a copy inside Orchard from its project filesystem to the job's local disk is not Trinity traffic. If the limit only slows the job, say so and prepare the change as a separate small diff for after the verdict (do not touch the frozen files now).

On ACCEPT the step-50 rehearsal is yours to submit once, as pre-authorized.