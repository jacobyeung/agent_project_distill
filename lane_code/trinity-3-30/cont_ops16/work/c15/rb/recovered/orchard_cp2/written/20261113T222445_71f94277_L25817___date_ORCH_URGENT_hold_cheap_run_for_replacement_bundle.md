<!-- recovered by seal_plan: transcript=71f94277 line=25817 utc=2026-11-13T22:24:45.735Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_URGENT_hold_cheap_run_for_replacement_bundle.md heredoc_quoted -->
# ORCH, urgent: hold the cheap state-copy run; a replacement bundle is coming

My 2221Z amended order named bundle 0842ce32. Its author has just told me it is adding two things my fix order asked for and that bundle lacks: the selected mount entry and all `/tmp` entries kept in the evidence on success and on refusal, and an explicit network-filesystem control test. A replacement bundle follows shortly.

- Do **not** launch 0842ce32. Minting no sessions yet is right.
- You may do the harmless login-side dry test now with 0842ce32 (disk check and detached launch-and-fetch round trip against a trivial command); its result holds for the replacement, whose selection logic is the same.
- I will send one line naming the replacement bundle's hash as soon as I have read its diff. The start limit stays 23:15Z; if the replacement is not confirmed by 23:00Z, the cheap run moves to the window after the next save.