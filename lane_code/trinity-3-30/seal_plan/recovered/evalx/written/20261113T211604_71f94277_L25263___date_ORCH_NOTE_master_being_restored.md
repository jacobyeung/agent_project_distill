<!-- recovered by seal_plan: transcript=71f94277 line=25263 utc=2026-11-13T21:16:04.567Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_NOTE_master_being_restored.md heredoc_quoted -->
# ORCH note: the shared connection is being restored by the operator; make your one attempt when it says so

Your 2113Z BLOCKER is right: `/tmp/cm-okit-orchard` is gone, and the launcher and `oc.sh` only reuse it. I ordered orchard_cp2 to restore the master with one call through `orchard_kit/work/ossh.sh` and to tell you in your inbox when it is up.

- When that line arrives (or when the socket exists again at a fresh local check), make **one fresh queue check and submission attempt** for the step-50 rehearsal: this is the authorization you asked for. The failed attempt reached no intent, notice or `sbatch`, so nothing is spent.
- Do not open a master yourself and do not change the launcher's connection options.
- If the socket is still absent at 21:30Z, tell me.