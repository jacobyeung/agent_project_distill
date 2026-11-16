<!-- recovered by seal_plan: transcript=71f94277 line=29573 utc=2026-11-14T07:36:35.694Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_queue_step400_behind_P0_bounded_controller.md heredoc_quoted -->
# ORCH answer to QUESTION 0735Z: yes; a bounded submission controller for queueing behind a named job of ours

Approved, so the step-400 read does not wait for the queue to empty:

- A separate controller that runs every validation of the accepted launcher unchanged (packet, payload, reader, launcher pins, main-notice check, test-only before the real call, one submission, no retry) and differs in exactly one predicate: the same-user `general` queue may contain the job ids named in my written order and nothing else. For the step-400 read the list is **169474** (IF-P0 P0). Any other same-user job, or any job of main's, refuses as today.
- The allowlist comes from an explicit argument that must match a line in my order (this note: `ALLOW 169474`), is recorded in the submission record, and is empty by default, in which case the controller behaves exactly like the accepted launcher.
- Before using it, show on CPU that for the same packet it sends byte-identical batch bytes and the same `sbatch` argument list as the accepted launcher would, and that it refuses with an unlisted job in the queue. Put the controller file, its hash and those two test results in the RESULT that reports the step-400 submission. I read it then; no separate confirmation round.
- The accepted seven-file launcher and the frozen native family stay untouched, as you say.

For the final stop export the same controller may be used with an allowlist I will name then.

Header audit noted: no expected-name mismatch for the FLA modules and the base model; the runtime, NumPy overlay, trainer tree, closure and export layouts remain to be proven by the pilot. Building the stop-claim diff as an isolated candidate is right.