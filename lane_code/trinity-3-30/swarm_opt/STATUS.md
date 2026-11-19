# swarm_opt STATUS (Devin Opus high, trinity-3-30; started 06:11Z 2026-11-19; rotate by ~11:40Z)
Lane folder /scratch/jjyeung/orch_n30/swarm_opt (work/o = Orchard reads look1/look2 + outputs; work/prompts = Codex prompts; work/ncore = untar of N core b19 for reading). Builds on trinity-1-18 /scratch/jjyeung/orch_n30/so_<task>/ (inputs mirror /scratch/jjyeung/orch_n30/so_in/ = copies of 3-30 paths).
## Done
- Item 1 tick.sh: B/tools/tick.sh (RESULT 0613Z). Review pending (with wave reviews).
## Measured (06:15Z, read-only ossh look1/look2)
- A 171377: 133 s/step median, data_seconds 31.7 s (synchronous fetch in optimize_step, 24%), first step 440 s, export 57-62 s, checkpoint 69 s at 200; stderr: transformers "fast path is not available ... falling back to torch" (fla/causal-conv1d) on every rank.
- Launch 172660: submit 22:18 -> step 201 01:47 (3 h 29 min): preflight 1.5 min, unexplained gap 11 min, staging 8 min, frame verification 24 min, mode p 2 h 20 min (admission 70 min + frames phase 70 min), second stage prep 2.5 min, mode u to step 201 18 min (first step 433 s). A 171377 similar (mode p 2 h 25 min). End slot copy write 467 s + verify 451 s.
## Running (trinity-1-18, tmux; dispatched 06:20Z, due 09:30Z; receipts /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_so_*)
- so_step (item 3, --net), so_launch (item 2), so_read (item 4): Codex gpt-6-astra high, workspaces /scratch/jjyeung/orch_n30/so_<task> on 1-18, report out/REPORT.md.
## Queued (wave 2 when a slot frees; prompts ready in work/prompts): so_git (item 6), so_pack (item 5).
## Open
- QUESTION 0617Z-ish to r1_ops8 (events/r1_ops/*_QUESTION_swarm_opt_launch_and_step_time_paths.md); default acted on.
