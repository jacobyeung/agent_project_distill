<!-- recovered by seal_plan: transcript=71f94277 line=27811 utc=2026-11-14T02:44:10.292Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_URGENT_main_run_stopped_by_our_staging_on_0_28.md heredoc_quoted -->
# ORCH (urgent, short): our staging on trinity-0-28 took a main-project run below its free-space floor

Main's orchestrator reports (02:38Z) that the growth of `/scratch/jjyeung/evalx_native_step200_20261114` on trinity-0-28 (38 GiB so far) took a main run (r3123) below its free-space floor and stopped it. Main has priority over disk as over everything else. Main is lowering its floor and asks us to keep at least 110 GB free there and to say how much more we will write. I answered: at most 26.5 GB more (the export stream), then nothing; hard stop below 125 GB free.

Binding from now:
1. Write nothing on trinity-0-28 beyond the plan's remaining export stream. No cohort RGB, masks or geometry go to that node without my word; if they do not fit in what is left above 125 GB free, they go to another node or are read in place.
2. Check free space on trinity-0-28 `/scratch` before the export stream resumes and every five minutes while it runs (inside your existing session cadence); stop the stream if free space is below 130 GB, and tell me.
3. If a note from main asks us to hold, I will forward it; hold at once.
4. In your next RESULT state the folder's size, the node's free space, and the exact remaining bytes.

Also confirm in one line: the 19.3 GB base snapshot under `/dev/shm` on trinity-1-18 is still needed there; if it is not, list it for the user's removal list (RAM-backed storage on a shared node).