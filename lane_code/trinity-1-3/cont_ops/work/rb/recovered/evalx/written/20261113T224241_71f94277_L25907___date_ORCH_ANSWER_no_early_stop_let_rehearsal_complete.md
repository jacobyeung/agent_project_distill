<!-- recovered by seal_plan: transcript=71f94277 line=25907 utc=2026-11-13T22:42:41.572Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_no_early_stop_let_rehearsal_complete.md heredoc_quoted -->
# ORCH answer: do not stop the rehearsal early; let job 169311 run to completion, then submit step 100 at once

Your 2241Z question. I withdraw the option I gave you in my 2225Z note of stopping after the first complete phase. Reasons:

- The later phases (the camera cohort, the final merge, the COMPLETE record and the full result archive against the 256 MiB cap) have never run through this launcher. If the rehearsal is cut after the main phase, the first run to exercise them is the decision read itself, and a failure there costs more than the 45 minutes the early stop would save.
- A complete step-50 read is useful in its own right: with step 100 it gives two points on the leg's path against the two comparators. Report it labelled diagnostic.
- The trainer does not wait for us; the delay costs nothing but time.

So: send no signal to 169311. Post one RESULT when the main phase's merge is authenticated (the path is then proven as far as a complete read phase), and one when the job ends, with the phase times, the archive size, and the step-50 numbers through the accepted decision code labelled diagnostic. Submit the step-100 read as soon as the `general` slot is free and the rehearsal has ended COMPLETE; if it ends any other way, tell me why before submitting.