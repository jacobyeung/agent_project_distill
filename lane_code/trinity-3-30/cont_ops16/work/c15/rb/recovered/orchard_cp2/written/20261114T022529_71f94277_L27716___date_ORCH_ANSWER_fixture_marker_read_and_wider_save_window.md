<!-- recovered by seal_plan: transcript=71f94277 line=27716 utc=2026-11-14T02:25:29.848Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ANSWER_fixture_marker_read_and_wider_save_window.md heredoc_quoted -->
# ORCH answers (0224Z events)

## 1. Fixture and the protected run's static marker: allowed

My 0213Z condition was worded too broadly. The fixture rehearsal may read and hash the persistent root's `RUN.json` (the 93-byte static marker, sha 7f9b2593...), at the two places the checker does (bootstrap and finalizer), as its read-only protection check. It reads no other file of the production run and writes nothing under that root, the kit or the bundle. Everything else in the 0213Z order stands, including waiting for evalx job 169367 to end and telling evalx when you submit and finish.

## 2. The dip: widen the window at the next save

Your facts place the step-214 save's disk-guard line at about 01:49:40Z and the save at 71.6 s, so the 362 GB sample at 01:54:13Z came about three minutes **after** the save ended, and the 438 GB sample at 01:49:13Z just before it began. So at the next ordinary save (about 03:49Z by the same schedule; take the time from the stdout's disk-guard line when it appears), sample the plain free-space query every 15 seconds from two minutes before the expected start until four minutes after the save ends, then every 30 seconds until ten minutes after it ends, in one routine session. Post the series with the save's start (stdout mtime) and its duration. If free space drops by more than 20 GB in that window and returns, name the folder that grew only if you can do it without scanning (for example the persistent root's own top-level entries, by listing that one directory once during the dip).

## 3. Noted

Space is steady at 437 GB (02:24Z). Step 214 saved in 71.6 s on four ranks; training through step 220 at ordinary step times.