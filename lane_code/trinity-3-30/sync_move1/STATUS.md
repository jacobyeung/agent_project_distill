# sync_move1 STATUS (Devin Opus, trinity-3-30; started 21:08Z 2026-11-19; hard end 02:08Z)
Session /scratch/jjyeung/orch_n30/sync_move1 (3-30, files <5 MB). Events B/events/sync_move. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Brief: B/briefs/sync_move1.md.

## State now
- Hourly sync runs on **trinity-2-28**, tmux `lane_sync`: `cd /scratch/jjyeung/distill_sync && LCS_HOST=trinity-2-28 LCS_HEARTBEAT=$B/code_sync_heartbeat/HEARTBEAT.log nice -n 10 bash $B/tools/lane_code_sync_loop.sh`. Clone /scratch/jjyeung/distill_sync/repo (lane-code; config copied from the 3-30 clone; refs/remotes/origin/main a38bc5b3). Sources: local trinity-2-28, remote trinity-1-18 and trinity-3-30 (tar over IB to trinity-2-28.ib), orch_n30/tools, orch_n30/briefs.
- First 2-28 run 22:01:38-22:05:49Z: committed 6,331 files, verified GitHub lane-code = 5bb86699 (ls-remote from 3-30 agrees). Next run ~23:05:49Z.
- Old loop on 3-30 STOPPED 22:06Z (tmux lane_sync, bash 4081722 + sleep 772551). Health loop on 3-30 restarted 22:06Z in tmux `sync_health` with LCS_LOG=$B/code_sync_heartbeat/HEARTBEAT.log (first tick last_verified=22:05:49Z, active=none). STOP_NOTICES.md line written.
- Installed tools (on shared B/tools): move package 21:52Z (lane_code_sync.sh 34cee9b8, lane_code_stage.sh 5ae794e4, land_kit.py bd78e8c9, new lane_code_sync_loop.sh 70adaf82; backup on 3-30 $S/install-backups/865b5f7be25646e18086d6b4d2df27fc; package copy work/res/sm_move/out, rollback.sh there). Filter package 22:07Z (lane_code_filter.py, dry_count.py; backup $S/install-backups/a4a09f009fb24708bed4099521896bfb; package work/res/f2/out). GIT_OWNER.md updated + B/tools/SYNC_HOST_MOVE.md.
- Reviews (Cursor Opus, on 2-28): sm_cr_move GO AFTER FIXES -> Codex fix1 DONE; sm_cr_filter GO AFTER FIXES (HIGH suffix rule, MEDIUM root gate) -> Codex fix1 DONE (as reviewer specified). Verdicts copied to work/res/sm_cr_*/.

## Measured
- Dry run old -> new filter, files / bytes staged: trinity-1-18 76,849 / 888,532,674 -> 58,903 / 666,148,479 (work/dry118.log, dry118b.log); trinity-2-28 61,543 / 466,857,790 -> 5,431 / 47,199,894 (sm_filter measurements); trinity-3-30 28,123 / 227,580,310 -> 21,905 / 190,384,552 (work/before_3_30.txt, after2_3_30.txt).
- Hourly commit replay on the last 8 commits: 45-232 MB raw before, 22-53 MB after (work/res/f2/out/measurements/totals.tsv).

## Done (lane ended 23:12Z, no successor)
- Second verified push from 2-28: bcd2342f 23:08:26Z (73.0 MB raw, mostly one-off churn after the rule change; work/m2.log, m3.log). REMOVAL_CANDIDATES.md and the final RESULT are in B/events/sync_move.
- Nothing owed. A successor needs only: check HEARTBEAT.log hourly; if a commit exceeds ~50 MB, tighten the filter from that commit's top kept directories (Codex build + one review + the package's install.sh, as done here; packages in work/res/{f2,sm_move}/out).

## Removal candidates (for the list)
- trinity-3-30: /scratch/jjyeung/distill_sync/{repo,stage,stage-robust} after the second push; /tmp/sm_*.txt (25 MB) and /tmp/sm_move_out.tar (my temp files; the guard refuses agent deletions).
- trinity-2-28: /scratch/jjyeung/distill_sync_init (lane-code.bundle 457 MB, inc1.bundle 28 MB), /scratch/jjyeung/orch_n30/{sm_ship,sm_ship2,sm_filter,sm_move,sm_cr_filter,sm_cr_move} (build/review workspaces, finished).
- trinity-1-18: /tmp/sm1 (filter copies for dry runs, <100 KB).
- The guard queued two commands of mine in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md (21:13Z cleanup of /tmp/sm_*.txt; 21:17Z a STATUS heredoc that only mentioned the guard; the second needs no action).
