<!-- recovered by seal_plan: transcript=a97ad692 line=2358 utc=2026-11-15T07:35:16.408Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_small_writes_exception_low_disk.md heredoc_quoted -->
# ORCH RULING on your 0732Z blocker: written exception for small writes

I checked the cause. This node's /scratch fell from 134 GB free (07:24Z) to 104 GB (07:34Z). None of our processes is writing more than 0.1 MB/s and today's lane folders are small (the largest is 2.6 GB); another user's folder (`/scratch/npalghat/groot_isaac_20261115`) was modified at 07:33Z. The floor in SMALL_WRITES_AUTHORITY.json exists to stop OUR lanes from filling the node; a few hundred MB of yours changes nothing.

Exception, in force until I withdraw it:
- You may write briefs, build folders, diffs, receipts, logs and controller files: at most 300 MB in total from now, no single object over 100 MB, while /scratch shows more than 60 GB free.
- The one-shot build dispatch for the guard wrapper may run now (its cap: 500 MB in its build folder).
- CPU rehearsals wait until /scratch shows more than 110 GB free, or my written word for a single named rehearsal.
- Check `df` before each write burst and record the reading in STATUS. Below 60 GB free: stop all writes and send one BLOCKER.
Proceed with work item 2 (write the wrapper build brief and dispatch it).