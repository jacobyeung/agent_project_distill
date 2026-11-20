W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls 2>&1 | grep tr18
R=$(ls -d /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24m4h 2>/dev/null | tail -1); echo "== $R"; cat $R/final_message.md 2>/dev/null
ls $W/work/sel24; cat $W/work/sel24/REPORT.md 2>/dev/null
