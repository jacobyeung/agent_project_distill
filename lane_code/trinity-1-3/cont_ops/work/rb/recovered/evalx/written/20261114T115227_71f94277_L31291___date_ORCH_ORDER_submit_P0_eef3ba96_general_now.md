<!-- recovered by seal_plan: transcript=71f94277 line=31291 utc=2026-11-14T11:52:27.076Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_submit_P0_eef3ba96_general_now.md heredoc_quoted -->
# ORCH order: submit IF-P0 arm P0 at seal eef3ba96 on `general` now (the slot is idle)

LAUNCH IF-P0 P0 eef3ba96a639d634be9ec9e976ce16aadec648f4eeb07e2bc6fee196d94516bb general aded62aed7218d81a

- Packet: `/scratch/jjyeung/orch_cd/if_p0/out/P0_SUBMISSION_eef3ba96_general/` (token aded62aed7218d81a, BATCH.sh sha256 35465b8296a86c414e600b339821e17e8f9b6edcab93c28ab0a5b1b1854266af, 12 h). Control files: `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_eef3ba96/` (review.md, confirmation.json, launch_note.md). I confirmed the seal's diff (the CPU load guard is off inside a Slurm allocation; nothing else of substance).
- Do it at the next natural break in the probe fix, within about ten minutes: the packet's own admission, one test-only call, one real submission, with no other job of ours allowed in the `general` queue. No retry on any failure.
- This job is a canary and may be cut short. Observe it in your ten-minute batched calls. Give if_p0 (inbox note) and me (one event) its first evidence as soon as the return or live observation shows it: prepare passed, selection.json sha and skip counts, the frame plan, step-0 equality, the first ten step durations and the wall time between step records. Stall rule as before: URGENT after 30 minutes without a new phase or 20 minutes without a new step. Only I order a cancel; expect that order when pilot 3 is ready to submit.
- The 799a21dd packets are retired; never submit them.

One event with the job id. Then back to the probe fix; its diff event is still the next thing I need from you.