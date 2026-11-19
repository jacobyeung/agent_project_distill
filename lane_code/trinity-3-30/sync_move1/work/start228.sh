set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; S=/scratch/jjyeung/distill_sync
git -C $S/repo update-ref refs/remotes/origin/main a38bc5b3c6a6fd7e1162460a96ef04de778cb066 && echo "MAIN $(git -C $S/repo rev-parse refs/remotes/origin/main)"
echo "HEAD $(git -C $S/repo rev-parse HEAD) branch $(git -C $S/repo rev-parse --abbrev-ref HEAD)"
ls -la $S | head -20
tmux has-session -t =lane_sync 2>/dev/null && { echo "lane_sync exists"; exit 0; }
tmux new-session -d -s lane_sync "cd $S && LCS_HOST=trinity-2-28 LCS_HEARTBEAT=$B/code_sync_heartbeat/HEARTBEAT.log nice -n 10 bash $B/tools/lane_code_sync_loop.sh"
sleep 20; tmux ls | grep lane_sync; tail -5 $S/sync.log
