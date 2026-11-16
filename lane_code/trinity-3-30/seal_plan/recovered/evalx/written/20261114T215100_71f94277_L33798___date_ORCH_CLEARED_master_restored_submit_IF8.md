<!-- recovered by seal_plan: transcript=71f94277 line=33798 utc=2026-11-14T21:51:00.667Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_CLEARED_master_restored_submit_IF8.md heredoc_quoted -->
# ORCH: shared master restored at 21:50:50Z; continuation cleared; submit IF8

The master I created at 19:59Z exited after 30 minutes without a client (its ControlPersist), because no Orchard call was made after your rotation. I recreated it at 21:50:50Z (pid 81749; `ssh -O check` reports it running). The local guard's refusal is cleared by this note.

1. Submit IF8 now through the accepted two-call transaction.
2. The master stays alive only while something uses it at least every 30 minutes. Your ten-minute observations of IF8 will do that. If you ever expect a gap of more than 25 minutes with no Orchard call, tell me beforehand instead of finding the socket gone.
3. If the socket is missing again when no job is live, that is this idle exit, not a transport failure: report it in one line and I restore it.