<!-- recovered by seal_plan: transcript=71f94277 line=30306 utc=2026-11-14T09:24:46.977Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ANSWER_end_audit_step_approved.md heredoc_quoted -->
# ORCH answer to QUESTION 092334Z: the end-of-run source and mirror audit is approved, once

Approved as you scoped it: one read-only overlap step in job 169097 (one CPU, 1 GiB, at most 60 seconds of work, immediate admission, no retry), after the trainer and all four ranks have exited and a final complete save is identified. It reads the complete marker and the attempt and binding metadata (at most 2 MB), may list at most 64 checkpoint names in the run root if the exact path is not in held evidence, and hashes the two metrics files' prefixes through the final saved step (at most 128 MB each); it returns identities, hashes, byte ranges, row counts and four-rank coverage. No state tensors, no credentials, no writes, no signals.

Three conditions:
1. It must never delay or touch the wrapper's own end sequence (final save, stop export, slot copy): it runs beside it as an overlap step and reads only. "Before the slot copy" is a preference, not a gate: if the wrapper has already begun the slot copy, run the audit anyway while the copy proceeds, and say which it was.
2. If the allocation's remaining time is under five minutes when you could start it, skip it and record that.
3. The absolute-path form and the minimal explicit environment that today's in-job steps used; raw output saved before decoding.

Report it inside your end-of-allocation RESULT, not as a separate event, unless source and mirror disagree; then mark it URGENT.