# wait up to $1 seconds for a new event (not STATUS/PROJECT_FS_FREE/N_LAUNCH_CARD) in n_review/tree_rebuild/n_ops or inbox
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; S=/scratch/jjyeung/orch_n30/n_review1i; M=$S/work/.mark
end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  n=$( (for d in n_review tree_rebuild; do for f in $(ls -t $B/events/$d | head -8); do [ "$B/events/$d/$f" -nt $M ] && echo "$d/$f"; done; done; for f in $(ls $S/inbox); do [ $S/inbox/$f -nt $M ] && echo "INBOX $f"; done) | grep -v "COPY_n_ops\|STATUS.md\|PROJECT_FS_FREE\|N_LAUNCH_CARD\|n_review1i" )
  [ -n "$n" ] && break
  sleep 30
done
bash $S/work/poll.sh
