<!-- recovered by seal_plan: transcript=a97ad692 line=2833 utc=2026-11-15T08:26:50.735Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_orchard_video_path_and_one_call.md heredoc_unquoted(vars_unexpanded) -->
# ORCH ANSWER to your 0825Z blocker: the videos are on Orchard under the project root; one call is cleared

You diagnosed it correctly: the kit's `video_root` is a path of the other cluster, taken from an old request file. The record of where the 288 official videos live on Orchard is `$R/official_reads/OFFICIAL_RESULTS.md`, lines 41 to 51 (read them): the staged view is
`/project/community/jjyeung/cp4tk_eval/inputs/data2root/jjyeung/agent_project_data/vsibench_videos/`
and Orchard CPU job 165643 loaded all 5,130 official tasks over it with 288 of 288 videos, byte-identical to the set behind the reference model's read.

Cleared: ONE Orchard call that (a) tests that directory exists, (b) creates your opaque link (same alias name you chose, under the opaque parent you used) pointing at it, (c) prints the count of video files it resolves to and their total bytes from a single listing. If (a) fails, print what `ls -d` shows for the three parents of that path and stop: no second call without my word. Expected count 288.

Then: order official544 (one note in its inbox) to regenerate `LAUNCHER_INPUT.json` with the alias and to correct its site evidence (the "already held on Orchard" claim must cite this record, not the old request file), build 04's refusal test, the packet, and your RESULT. Good that build 03 is done and the pilot rehearsal is starting.