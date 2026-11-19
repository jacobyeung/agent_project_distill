# swarm_opt STATUS (Devin Opus high, trinity-3-30; started 06:11Z 2026-11-19; rotate by ~11:40Z)
Lane folder /scratch/jjyeung/orch_n30/swarm_opt (work/o = Orchard reads look1/look2 + outputs; work/prompts = Codex prompts; work/ncore = untar of N core b19 for reading). Builds on trinity-1-18 /scratch/jjyeung/orch_n30/so_<task>/ (inputs mirror /scratch/jjyeung/orch_n30/so_in/ = copies of 3-30 paths).
## Done
- Item 1 tick.sh: B/tools/tick.sh (RESULT 0613Z). Review pending (with wave reviews).
## Measured (06:15Z, read-only ossh look1/look2)
- A 171377: 133 s/step median, data_seconds 31.7 s (synchronous fetch in optimize_step, 24%), first step 440 s, export 57-62 s, checkpoint 69 s at 200; stderr: transformers "fast path is not available ... falling back to torch" (fla/causal-conv1d) on every rank.
- Launch 172660: submit 22:18 -> step 201 01:47 (3 h 29 min): preflight 1.5 min, unexplained gap 11 min, staging 8 min, frame verification 24 min, mode p 2 h 20 min (admission 70 min + frames phase 70 min), second stage prep 2.5 min, mode u to step 201 18 min (first step 433 s). A 171377 similar (mode p 2 h 25 min). End slot copy write 467 s + verify 451 s.
## Running / state (07:45Z)
- gpt-6-astra hit "Selected model is at capacity" at 06:52-06:59Z (so_step, so_launch, so_git, so_pack all exit 1). Continuations and wave 2 run on gpt-6.1-sol (brief allows Codex fallback); reviews: Cursor Opus (claude-opus-5-5-xhigh, `agent -p -f --sandbox disabled --trust`, probe READY 07:36Z) or Codex astra review.
- so_read (item 4): DONE 07:00Z; review so_rv_read (Codex astra) NO-GO 7 findings (trinity-1-18 /scratch/jjyeung/orch_n30/so_rv_read/REVIEW_VERDICT.md); fix round so_read_fix (Sol, tmux so_read_fix) running, due 09:15Z; then Cursor re-review.
- so_step (item 3): PARTIAL (sandbox blocks gloo sockets). I ran the full suite myself in tmux so_step_gloo: 1 error = test harness bug (0-dim tensor .view(uint8) in tests/test_so_joint.py:83); fixed as out/patches/04_test_joint_hash_0dim.diff; rerun tmux so_step_gloo2 -> work/full_suite_by_swarm_opt2.txt. Then Cursor review.
- so_launch (item 2): PARTIAL 07:35Z (4 patches; cache hits only for the same logical run). Cursor review so_cr_launch running.
- so_git (item 6), so_pack (item 5): Sol builds running, due ~09:30Z.
- tick.sh v3 (sha 5e26c7a4): v2 + 5 s alarm, preview-cut marker, ps-failure "unknown". Review 2 (Codex) NO-GO on residual hardening (ancestor symlinks, pid-identity matching); accepted as risk, not fixing further.
## Polling: one batched tssh call to trinity-1-18 every ~10 min (scripts work/prompts/poll118*.sh shipped by IB tar into so_in).
