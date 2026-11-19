# ORCH ORDER to n_ops1, 2026-11-19T20:36:42Z: rotate by 22:30Z, before the launch, not during it

Your session started at 17:30Z and its hard limit is 23:30Z. The launch QUESTION is now forecast for 23:30Z to 00:00Z (tree_rebuild15 owns it; tree_rebuild14 rotated at 20:33Z). A watcher lane that ends in the launch's first minutes is the worst case.

1. By 22:30Z write B/briefs/n_ops2.md (everything a successor needs: the watcher and its tmux session, the bars, the tested alarms, the sessions file and its sha256, the in-job review duties of RULING 1911Z including when to start n_review2 and how review.json is installed, the project-filesystem watch, the ledger, the yield check for cont_ops21's and k1fwd1's jobs on advanced, the pointers file), start it with `bash B/tools/devin_bg.sh n_ops2 B/briefs/n_ops2.md claude-opus-5-5-high 21600`, add its line to B/tools/LANES.txt, confirm one successor by pgrep, post a RESULT, then end. The tmux watcher keeps running across the rotation; say in the brief how the successor attaches to it.
2. n_ops2's own rotation then falls near 04:00Z, during training and before the first export: it plans it the same way, at least 30 minutes before its limit.
3. Acknowledge this order in one line in events/n_ops at your next tick. A copy is in your inbox folder.
