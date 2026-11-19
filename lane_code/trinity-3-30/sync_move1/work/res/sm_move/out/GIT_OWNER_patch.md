Apply these replacement paragraphs to `tools/GIT_OWNER.md`. Line numbers refer to the supplied input. This package does not install the Markdown file automatically.

Replace lines 3–5 with:

The designated Git owner runs on `LCS_HOST`, which defaults to `trinity-3-30`; lanes supply files and queue rows. Set `LCS_HOST` in every owner command when using another allowed compute node. The hourly sync, kit command, and manual owner Git work share that host's `$S/.sync.lock`, where `S=/scratch/jjyeung/distill_sync`. The kit clone is `$S/repo`, on branch `lane-code`.

Replace line 65 with:

`$S/KITS_LANDED.txt` is local to `LCS_HOST` (default `trinity-3-30`); lanes on other nodes read the shared RESULT event.

Replace lines 98–101 with:

Queue rows are `<UTC> eff/<slug> <40-hex-sha> [<absolute-clone-path>]` in `e_*/PUSH_QUEUE.txt` or `eff_*/PUSH_QUEUE.txt` under `$LANES_ROOT` on `LCS_HOST` only (default `trinity-3-30`). An explicit clone path must be `$LANES_ROOT/<lane>/clone` or `$LANES_ROOT/<lane>/repo`; a relative path is permanently refused. An omitted fourth field selects the lane's clone/repo locally. The default lane root is `/scratch/jjyeung/orch_n30`.

Replace lines 106–108 with:

The health loop stays on `trinity-3-30`. The owner starts `LCS_LOG="$HEARTBEAT" LCS_REVIEW2_FIXES=1 LCS_ENABLE_SYNC_HEALTH=1 bash "$T/sync_health_loop.sh"` in tmux there. `$HEARTBEAT` must name the same shared file supplied to the sync loop as `LCS_HEARTBEAT`, for example `$B/events/code_sync/lane_code_heartbeat.log`. Every ten minutes the monitor reads that file, emits one event per incident/recovery, and records delivery in its local `$S/health/` directory. Use the default log when the sync and monitor both run on the default host without a heartbeat.

Add this loop paragraph:

On the sync host, start `LCS_HOST=trinity-2-28 LCS_HEARTBEAT="$HEARTBEAT" bash "$T/lane_code_sync_loop.sh"` in tmux. The wrapper appends to the host's `$S/sync.log`, sleeps 3600 seconds between runs, and stops when the driver returns a signal exit status. Investigate a stopped or killed run before restarting it. The old host keeps its default behavior until the owner stops its loop after the first verified push from the new host. Host-local locks do not serialize different hosts; a conflicting push requires owner reconciliation without a force push.

### If the sync host fails
1. After the owner investigates the failure and authorizes a restart, choose an allowed compute node with capacity, set `LCS_HOST` to its short hostname, and re-clone GitHub's `lane-code` branch into a fresh `$S/repo` with `git clone --branch lane-code --single-branch "$GITHUB_URL" "$S/repo"`; restore `home` with `git -C "$S/repo" remote add home /home/jjyeung/agent_project_distill` and retain any existing clone by renaming it aside.
2. Install the node-local `$S` state: create the regular `$S/LCS_ROBUST_SYNC` marker, copy the approved `LCS_ROBUST_BUDGETS` file into `$S/LCS_ROBUST_BUDGETS`, and preserve applicable kit/queue receipts; retain the shared heartbeat path and let staging recreate its slots.
3. Start a tmux session on that node and run `LCS_HOST="$LCS_HOST" LCS_HEARTBEAT="$HEARTBEAT" bash "$B/tools/lane_code_sync_loop.sh"`; keep the health loop on `trinity-3-30` with `LCS_LOG="$HEARTBEAT"`, verify the first GitHub push, and stop the old sync loop if it is still running.
