<!-- recovered by seal_plan: transcript=a97ad692 line=3401 utc=2026-11-15T09:49:31.939Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_upload_option_B_final_object_13.md heredoc_quoted -->
# ORCH RULING on your 0948Z blocker: option (B), after the build has exited

One object should fly, and it should be the one whose embedded controller snapshots equal the live files.
1. Wait until build 07's process has exited. Then verify, read-only, that `code_override_13.tar` (e747f4f3) is final: every embedded snapshot equals the live file, `CANDIDATE_FAMILY_14.json` (7018efdf) binds it, the 143 tests and the pilot proof still bind to it (rerun the bind checks, not the rehearsals), and no later object exists.
2. Stop your own queued upload of object 12 (it has transferred nothing) by the governor's documented way so its record closes, and record object 12 and its family as retired, never uploaded.
3. Register object 13 as the single attempt (honest bytes, tier 2, priority 180, no priority change).
4. My 0949Z order stands with the names replaced: when the upload of object 13 confirms, seal `CANDIDATE_FAMILY_14` and send the final review event. Submission needs a further order.
For your notes: act on a build's output only after its process has exited and its final RESULT is written; a RESULT that names an object "final" while the process still runs is not final.