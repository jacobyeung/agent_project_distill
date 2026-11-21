B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
tail -3 /scratch/jjyeung/orch_n30/tree_rebuild27/work/watch.log | cut -c1-400
sed -n '4,7p' $B/events/n_ops/N_WATCH_STATUS.md | cut -c1-300
pgrep -f "bash wlong3.sh" >/dev/null && echo wlong=alive || echo wlong=DEAD
ls -t $B/events/tree_rebuild | head -4; ls -t /scratch/jjyeung/orch_n30/tree_rebuild27/inbox | head -2
