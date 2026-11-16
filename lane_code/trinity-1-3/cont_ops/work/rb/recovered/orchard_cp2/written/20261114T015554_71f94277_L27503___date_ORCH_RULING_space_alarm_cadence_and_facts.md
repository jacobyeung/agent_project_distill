<!-- recovered by seal_plan: transcript=71f94277 line=27503 utc=2026-11-14T01:55:54.444Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_space_alarm_cadence_and_facts.md heredoc_quoted -->
# ORCH ruling on the project-space alarm (0154Z)

Received: 362.3 GB free, 154 GB per hour over the last 30 minutes, 1.4 hours to 150 GB at that rate. I have notified the user; only the user can free space, and no agent removes anything.

While any alarm threshold is active:
1. Sample free space every 10 minutes inside your routine sessions (the plain filesystem query only; no directory scans) and post one line per sample to `out/production_169097/project_free.jsonl` as now. Post an event only when a threshold is crossed in either direction, or when the 30-minute rate changes sign.
2. Post URGENT when free space falls below 200 GB, and again below 140 GB (the slot's guard is about 133 GB).
3. Before each of the next save boundaries (ordinary save due about 03:53Z; step-400 export about 08:50Z), record free space and, after it, whether the job's project-side logs still advance and whether the step times stay normal. If the project-side logs stop advancing while the job is RUNNING, that is the standing condition for the read-only health step (at most every 30 minutes); use it and report.
4. Tell me in one line whether anything of ours writes to that filesystem at a rate that matters right now (your monitor's own files, the job's logs and mirrors, the evaluation or IF-P0 jobs), from what you already hold. If something of ours is writing more than a few MB per minute there, name it.

Nothing else changes: no intervention in the job, no manual upload, no state copy.