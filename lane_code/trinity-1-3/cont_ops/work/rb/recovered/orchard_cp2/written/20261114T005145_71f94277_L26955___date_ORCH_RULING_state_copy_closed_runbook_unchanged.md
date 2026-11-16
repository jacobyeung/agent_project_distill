<!-- recovered by seal_plan: transcript=71f94277 line=26955 utc=2026-11-14T00:51:45.140Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_state_copy_closed_runbook_unchanged.md heredoc_quoted -->
# ORCH ruling: the state-copy line is closed for this allocation; the runbook is unchanged

Thank you for the complete dispositions (0041Z) and the memory table (0036Z). Decisions:

1. **No further state-copy execution of any kind in job 169097**, during training or at the end. The end-of-allocation fallback is unavailable: the installed wrapper exits at once on a space refusal, and nothing may change or signal it. The agreed runbook (`out/RUNBOOK_END_OF_ALLOCATION_469ddece.md`) stands exactly as written.
2. **If the slot is skipped for space at the end:** the stop export is the surviving state; record the skip and the export's attestation, and do nothing else. A continuation, if any, would warm-start from an export; that decision is mine and the user's.
3. **Space watch continues** with your alarms. The earlier it is known that the project filesystem will not hold the slot (about 113 GB, guard about 133 GB), the better: if your projection says the free space at about 14:25Z will be below 150 GB, post it as URGENT with the projection.
4. **For the user's removal list** (you remove nothing): the two login spools under `/var/tmp/state_copy_login_169097_*`, the five unused upload sessions of 23:08Z, the cheap copy's five objects on GCS, and the fetched result files of the two evaluation jobs under `/home/jjyeung/okit/evalx_results/`. Keep one file `out/REMOVAL_CANDIDATES_ORCHARD_20261114.md` with path, size and why each is safe to remove, and update it as items appear.

Next milestones for you: the step-200 export (due about 01:20Z) with its attestation, as for steps 50 and 100; the ordinary saves; the end runbook.