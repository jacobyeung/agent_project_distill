<!-- recovered by seal_plan: transcript=71f94277 line=30420 utc=2026-11-14T09:30:08.051Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_AUTHORIZED_restart_the_watcher_now.md heredoc_quoted -->
# ORCH: the shared master is restored (09:26:03Z); restart your read-only watcher now

I recreated the shared control connection at 09:26:03Z with the kit's script (the socket `/tmp/cm-okit-orchard` exists; a trivial command returned). The cause was its age: created 21:22:31Z yesterday, gone about 09:22Z, twelve hours, as with the one before it.

Authorized: restart the production watcher now through the existing wrapper (no new connection of your own; it reuses the restored master), with the confirmed-sample policy as loaded. Its first check should record the gap 09:19Z to now, production's state and step, and the project space. Post one RESULT with that first check. If the first call fails, stop and tell me.

The next expiry is due about 21:20Z; I recreate the connection before then, after your allocation has ended.