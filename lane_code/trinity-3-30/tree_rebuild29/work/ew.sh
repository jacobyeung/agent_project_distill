# wait up to N min for a new event (tree_rebuild, n_review, n_ops) or inbox file
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
s() { ls $B/events/tree_rebuild $B/events/n_review $B/events/n_ops /scratch/jjyeung/orch_n30/tree_rebuild29/inbox | grep -v "STATUS\|N_WATCH\|PROJECT_FS\|CARD" | sort | md5sum; }
a=$(s); for i in $(seq 1 ${1:-9}); do sleep 60; [ "$(s)" != "$a" ] && { echo "NEW $(date -u +%TZ)"; ls -t $B/events/tree_rebuild | grep -v STATUS | head -2; ls -t $B/events/n_review | grep -v STATUS | head -2; ls -t $B/events/n_ops | grep -v "STATUS\|N_WATCH\|PROJECT" | head -2; exit 3; }; done; echo "nothing new $(date -u +%TZ); fix20: $(head -1 fix20/REPORT.md 2>/dev/null | cut -c1-200)"
