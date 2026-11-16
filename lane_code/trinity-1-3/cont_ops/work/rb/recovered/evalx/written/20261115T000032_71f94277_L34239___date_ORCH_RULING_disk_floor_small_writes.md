<!-- recovered by seal_plan: transcript=71f94277 line=34239 utc=2026-11-15T00:00:32.422Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_disk_floor_small_writes.md heredoc_quoted -->
# ORCH ruling: fetch the pilot-7 return now; the 150 GiB floor does not stop small writes

The node's free space is falling because of another user's copy, not our lanes. My 150 GiB line was meant for staging-sized writes. New rule for this lane until I say otherwise:

- Writes of a return, a report, a receipt, a log or a small controller file are allowed while /scratch has at least 110 GiB free, up to 500 MiB in total from now. Fetch the 2.3 MB pilot-7 return at once with the accepted paced fetch, verify it, and report.
- No staging copy, no extraction of large archives and no new object over 100 MiB while the node is under 200 GiB free, as before.
- Below 110 GiB free: stop all writes except one BLOCKER line, and tell me.
- IF8's return (when it ends, about 02:35Z) is covered by this rule if it is under 100 MiB; if larger, tell me its size first.

Then the pilot's RESULT as ordered, cause first if it failed before the items, otherwise the per-item records.