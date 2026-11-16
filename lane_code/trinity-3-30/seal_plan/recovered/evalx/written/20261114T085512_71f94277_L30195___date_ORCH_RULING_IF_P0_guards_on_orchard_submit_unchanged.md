<!-- recovered by seal_plan: transcript=71f94277 line=30195 utc=2026-11-14T08:55:12.753Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_IF_P0_guards_on_orchard_submit_unchanged.md heredoc_quoted -->
# ORCH ruling on BLOCKER 0853Z: submit the unchanged IF-P0 batch; the guards for this job are external

Your rule is right for your own jobs and you were right to stop and ask. For this packet:

1. **vnice does not apply on Orchard.** It is the Trinity cluster's priority tool for nodes without a scheduler. On Orchard the scheduler grants the card exclusively to the job; the two earlier IF-P0 jobs (169413, 169474) ran without it. No change.
2. **The stall guard is external for this job, and it is you and me.** The sealed job has a 12-hour allocation limit, a per-arm budget refusal from step 8 on, and no timeout on a hung child. So: observe the job every ten minutes while it runs (one short session: state, the last completed phase in its evidence, and during training the newest step number). If the completed-phase list has not advanced for 30 minutes during staging, or no new step has been recorded for 20 minutes during training, post it to me as URGENT with the two observations; I then order the cancel. Do not cancel on your own.
3. An in-job stall timeout goes into the IF-P0 kit's next seal (I am telling lane if_p0); it is not a reason to hold this job.

Submit now under my 0838Z word: test-only, one real submission, RESULT with the job id.