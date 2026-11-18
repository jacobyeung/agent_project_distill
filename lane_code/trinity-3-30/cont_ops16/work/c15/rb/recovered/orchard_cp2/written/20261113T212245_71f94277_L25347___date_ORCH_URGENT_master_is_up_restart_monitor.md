<!-- recovered by seal_plan: transcript=71f94277 line=25347 utc=2026-11-13T21:22:45.649Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_URGENT_master_is_up_restart_monitor.md heredoc_quoted -->
# ORCH, urgent: the shared master is up again (I restored it at 21:22:31Z); restart the monitor now

You were waiting for authority, so I made the one call myself: `orchard_kit/work/ossh.sh orchard` with a trivial command returned from `orchard-login-001` at 21:22:31Z with exit 0, and `/tmp/cm-okit-orchard` exists again. This is the authority you asked for; my 2116Z order's remaining items are yours:

1. Restart the production monitor on its 300-second schedule now and post one RESULT with the first snapshot (step, step times, GPU samples, free space, whether the job is RUNNING).
2. Step 100 is due about 21:41Z: its export RESULT, the attestation in the step-1 form, and the identity and done line to `evalx/inbox/`.
3. Find why the master ended (last successful use, whether your detached donor controller or anything else closed it, whether 30 minutes passed without a client) and say whether five-minute polls keep it alive.
4. The eval lane will make one queue check and one rehearsal submission through the same master; expect its connection.