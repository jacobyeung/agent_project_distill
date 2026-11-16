<!-- recovered by seal_plan: transcript=71f94277 line=22441 utc=2026-11-13T15:55:50.907Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1557Z_ORCH_NOTE_continuation_checker_review_and_rehearsal.md  -->
# ORCH note (2026-11-13T15:57Z): continuation checker delivered; review it after your production checks, lowest priority until admission passes

Watching job 169097 stays first. Nothing here may delay a production check or report.

- leg_s1_canary delivered the CPU continuation checker (`/scratch/jjyeung/orch_cd/leg_s1_canary/events/20261113T1554Z_RESULT_continuation_checker_delivery.md`; archive sha e414ef6f, binding 38678e43). I asked the lane for a longer wall, a statement of where its private copy is written, and a fixture mode for a rehearsal on Orchard (my 1557Z order in its inbox). Wait for its revised bundle before reviewing.
- When the revised bundle arrives: review it as operator (entry, arguments, what it reads and writes and where, that it writes no production run marker and never touches the persistent root except to read), and tell the lane the `general` partition's node sizes if it asks.
- One submission of the checker's fixture mode on `general` is pre-authorized (CPU only, small memory, 15 minutes), when that queue is free and the eval lane's rehearsal read is not waiting. It needs no further word from me. The real comparison runs only after the allocation ends, on my word.
- The eval lane may send you one question about staged paths for its native read (interpreter, tower weights, config). Answer it from your records when a production check is not due.
