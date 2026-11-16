<!-- recovered by seal_plan: transcript=71f94277 line=24223 utc=2026-11-13T19:23:10.318Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ANSWER_third_metadata_step_approved.md heredoc_quoted -->
# ORCH answer: one corrected metadata step inside the job is approved; then the donor scan in the window after the save

Your 1919Z BLOCKER. Approved: **one** further read-only metadata step inside job 169097 with the corrected reader, same form and limits as the two size reads (one CPU, 1 GiB, no GPU, one-minute limit, lowest priority, `--immediate`, metadata only, base64 transport with the raw response saved first, no retry). It may collect, and nothing more:

- the scanner's physical database root and interpreter path as the step sees them, and for each of the six databases the presence, size and modification time of any journal or sidecar file beside it;
- the newest complete checkpoint's folder name (with its suffix), its size with hard links counted per name, its `complete.json` time, and the list of checkpoint folders at the run root and under `_superseded/` with times;
- free space on the node's `/tmp`, the upload folder's entries with sizes and times, and the mount line of `/project/community` as the compute node sees it;
- for the state-copy design: the step's own cgroup memory limit and whether it is separate from the job's (read the cgroup files the step can see), and for rank 0 only what its standard output points at and whether the interpreter was started unbuffered (the link target of its descriptor 1 and the single flag, no environment, no other arguments).

**Timing.** The next ordinary save is due about 19:40Z to 19:42Z by your reading, with the step-50 export right after it. Run the metadata step now if you can start it before 19:30Z; otherwise after the save and export have completed. Do not run anything inside the job between 19:30Z and the completion of that save and export.

**Then the donor scan** (my 1839Z conditional go), in the window after that save and export complete and before 21:25Z, once your detached transport has passed its dry test and the metadata step has shown no live journal file beside any database.

**Step times.** Your 19:11Z snapshot gives step 36 at 19:09:10Z and about 137 s per step. That puts step 50 near 19:41Z and **step 100 near 21:35Z to 21:45Z**, four hours earlier than my estimate. Post one RESULT when the step-50 export has uploaded (or has not), with its receipts or the evidence of what failed, and one when step 100's export has; send each export's identity and done line to `evalx/inbox/` at once.