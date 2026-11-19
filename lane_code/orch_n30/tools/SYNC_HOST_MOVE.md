Apply these replacement paragraphs to `tools/GIT_OWNER.md`. Line numbers refer to the supplied input. This package does not install the Markdown file automatically.

Replace lines 3–5 with:

The designated Git owner runs on `LCS_HOST`, which defaults to `trinity-3-30`; lanes supply files and queue rows. Set `LCS_HOST` in every owner command when using another allowed compute node. The hourly sync, kit command, and manual owner Git work share that host's `$S/.sync.lock`, where `S=/scratch/jjyeung/distill_sync`. The kit clone is `$S/repo`, on branch `lane-code`.

Replace line 65 with:

`$S/KITS_LANDED.txt` is local to `LCS_HOST` (default `trinity-3-30`); lanes on other nodes read the shared RESULT event.

Replace lines 98–101 with:

Queue rows are `<UTC> eff/<slug> <40-hex-sha> [<absolute-clone-path>]` in `e_*/PUSH_QUEUE.txt` or `eff_*/PUSH_QUEUE.txt` under `$LANES_ROOT` on `LCS_HOST` only (default `trinity-3-30`). An explicit clone path must be `$LANES_ROOT/<lane>/clone` or `$LANES_ROOT/<lane>/repo`; a relative path is permanently refused. An omitted fourth field selects the lane's clone/repo locally. The default lane root is `/scratch/jjyeung/orch_n30`.

Replace lines 106–108 with:

The health loop stays on `trinity-3-30`. Set `HEARTBEAT="$B/code_sync_heartbeat/HEARTBEAT.log"` and create its parent directory before starting the new sync loop. Only after this heartbeat shows its first `verified GitHub lane-code = ...` line, restart the health loop in tmux there with `LCS_LOG="$HEARTBEAT" LCS_REVIEW2_FIXES=1 LCS_ENABLE_SYNC_HEALTH=1 bash "$T/sync_health_loop.sh"`. Every ten minutes the monitor reads that file, emits one event per incident/recovery, and records delivery in its local `$S/health/` directory. Consumers may move delivered events; only undelivered events replay. Use the default log when both loops run on the default host without a heartbeat.

Add this cutover procedure:

Set `B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`, `T="$B/tools"`, `S=/scratch/jjyeung/distill_sync`, and `HEARTBEAT="$B/code_sync_heartbeat/HEARTBEAT.log"` in the owner shells. The planned destination is `NEW=trinity-2-28`. A failover destination must be an allowed `trinity-<n>-<n>` compute node, excluding `trinity-2-18`, `trinity-0-8`, `trinity-0-18`, `trinity-0-23`, and `trinity-3-23`. Check the cluster dashboard and disk capacity; leave 100–200 GB free. Choose a lane node, or create an empty `/scratch/jjyeung/orch_n30` on the destination. Preserve any existing stopped clone/state by renaming it aside before preparing a fresh destination `$S`; never overwrite unpublished work.

Before the copy, run exactly one `ssh -o BatchMode=yes <new>.ib true` from each source node that will stream to the new receiver. For the planned move, these sources are `trinity-1-18` and `trinity-3-30`, and `<new>` is `trinity-2-28`. Reuse connections and observe the cluster login limits. If this preflight fails, resolve access before starting the loop; `--dry` does not test receiver SSH.

Ask the user before the heavy copy. For both the planned move and failover, use a surviving clone on a compute node and send a Git bundle directly over InfiniBand. Do not route through the head node. Prepare access, directories, and the approved robust budgets before the timing-sensitive cutover. On the old host, take the copy immediately after its loop logs `END ok`, acquire its owner lock, and run this block with `NEW` set to the destination. For a failed host, use the surviving clone's host and lock after the user authorizes recovery; do not rerun killed work without their answer. The destination `$S/repo`, `$S/clone.bundle`, and `$S/transfer-state` must be absent or preserved aside.

```bash
set -euo pipefail
exec 8>"$S/.sync.lock"
flock -n 8
test "$(git -C "$S/repo" config --local gc.auto)" = 0
git -C "$S/repo" bundle create - --all | bash "$B/tools/tssh.sh" "$NEW.ib" \
  'set -eu; S=/scratch/jjyeung/distill_sync; mkdir -p "$S"; test ! -e "$S/clone.bundle"; cat > "$S/clone.bundle"'
state_files=(repo/.git/config LCS_ROBUST_SYNC LCS_ROBUST_BUDGETS)
for receipt in KITS_LANDED.txt PUSH_DONE.txt PUSH_REFUSED.txt; do
  if [ -f "$S/$receipt" ]; then state_files+=("$receipt"); fi
done
tar -C "$S" -cf - "${state_files[@]}" | bash "$B/tools/tssh.sh" "$NEW.ib" \
  'set -eu; S=/scratch/jjyeung/distill_sync; mkdir "$S/transfer-state"; tar -C "$S/transfer-state" -xf -'
flock -u 8
```

On the destination, clone the bundle and restore the old `.git/config` before contacting either remote. This preserves remotes, identity, and `gc.auto=0`. The bundle can hold `origin/main` without a local `main` branch; recover that ref from the bundle before considering a network fetch. Use this same block for planned moves and failover copies:

```bash
# BEGIN bundle restore
set -euo pipefail
git clone --branch lane-code "$S/clone.bundle" "$S/repo"
cp "$S/transfer-state/repo/.git/config" "$S/repo/.git/config"
if git bundle list-heads "$S/clone.bundle" refs/remotes/origin/main | grep -q .; then
  git -C "$S/repo" fetch "$S/clone.bundle" refs/remotes/origin/main:refs/remotes/origin/main
elif git bundle list-heads "$S/clone.bundle" refs/heads/main | grep -q .; then
  git -C "$S/repo" fetch "$S/clone.bundle" refs/heads/main:refs/remotes/origin/main
else
  git -C "$S/repo" fetch origin main:refs/remotes/origin/main
fi
git -C "$S/repo" rev-parse --verify refs/remotes/origin/main
test "$(git -C "$S/repo" config --local gc.auto)" = 0
# END bundle restore
```

Restore the regular `LCS_ROBUST_SYNC` marker and approved `LCS_ROBUST_BUDGETS` from `$S/transfer-state/` into `$S/`; preserve the copied kit/queue receipts there as applicable. Run `LCS_HOST="$NEW" bash "$T/lane_code_sync.sh" --dry` on the destination and require success, including its local label. A non-lane destination must have an empty `/scratch/jjyeung/orch_n30` for this check. The dry run must succeed before the loop starts; staging recreates its own slots.

Start the new loop at once in tmux with `LCS_HOST="$NEW" LCS_HEARTBEAT="$HEARTBEAT" bash "$T/lane_code_sync_loop.sh"`. The wrapper appends to `$S/sync.log`, sleeps 3600 seconds between runs, and stops on a driver signal exit. Investigate stopped or killed work and ask the user before rerunning it. Keep the old loop running until the new host's first verified GitHub push. Then stop the old loop and notify its orchestrator immediately. Restart the health loop with `LCS_LOG` only after the shared heartbeat contains that first verified line.

The two hosts have separate locks. If the new loop's first push is rejected as non-fast-forward, stop the new loop before its next run, notify its orchestrator, acquire the new host's owner lock, and run `git -C "$S/repo" fetch origin lane-code && git -C "$S/repo" merge --ff-only FETCH_HEAD`. Restart only if the fast-forward succeeds. If unpublished local work makes it diverge, stop and ask the user to reconcile it; never reset over unpublished work without the user, rewrite history, or force a push. Every stop notice must identify what stopped, the host, and the reason, and say that the orchestrator can restart it whenever it chooses.

A GitHub clone is a last resort only when no clone survives. Ask the user first because the transfer traverses the head node; agree on throttling within 8 MB/s for this download and the 18 MB/s aggregate user limit (shared-filesystem writes count double). Git has no built-in clone bandwidth limit, so do not execute an unthrottled clone. With the user-approved throttle in place, use `git clone --branch lane-code "$GITHUB_URL" "$S/repo"` without a single-branch restriction. Restore the approved origin/home URLs and owner identity, set `git -C "$S/repo" config gc.auto 0`, and ensure `refs/remotes/origin/main` exists (fetch `origin main:refs/remotes/origin/main` if absent). Obtain the approved robust marker, budgets, and applicable receipts before the same dry-run/start/verification procedure. If the total transfer through the head node would exceed about 30 GB, plan it with an admin.

### If the sync host fails
1. Investigate the failure and ask the user before recovery or heavy IO; choose an allowed lane node or prepare an empty `/scratch/jjyeung/orch_n30`, preflight receiver SSH from every source, and use the surviving-clone InfiniBand bundle procedure above, including config and `origin/main` restoration; use the user-approved, throttled GitHub fallback only if no clone survives.
2. Install the regular `$S/LCS_ROBUST_SYNC`, approved `$S/LCS_ROBUST_BUDGETS`, and applicable kit/queue receipts; create the parent of `HEARTBEAT="$B/code_sync_heartbeat/HEARTBEAT.log"` and require `LCS_HOST="$NEW" bash "$T/lane_code_sync.sh" --dry` to succeed.
3. Start `LCS_HOST="$NEW" LCS_HEARTBEAT="$HEARTBEAT" bash "$T/lane_code_sync_loop.sh"` in tmux at once; handle a first non-fast-forward push with the stop-and-fast-forward procedure above, stop any old loop after the first verified push, and only then restart health on `trinity-3-30` with `LCS_LOG="$HEARTBEAT"` after its first verified heartbeat line.
