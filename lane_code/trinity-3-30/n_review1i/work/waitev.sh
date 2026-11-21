# wait up to $1 s (checks every 60 s) for a new event for me in n_review/tree_rebuild or my inbox; then print poll.sh
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; S=/scratch/jjyeung/orch_n30/n_review1i; M=$S/work/.mark
end=$(( $(date +%s) + $1 ))
while [ $(date +%s) -lt $end ]; do
  n=$( (for d in n_review tree_rebuild; do for f in $(ls -t $B/events/$d | head -8); do [ "$B/events/$d/$f" -nt $M ] && echo "$d/$f"; done; done; for f in $(ls $S/inbox); do [ $S/inbox/$f -nt $M ] && echo "INBOX $f"; done) | grep -v "STATUS.md\|PROJECT_FS_FREE\|N_WATCH\|n_review1i\|evidence" )
  [ -n "$n" ] && break
  sleep 60
done
bash $S/work/poll.sh
