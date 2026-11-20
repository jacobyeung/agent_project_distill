W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls 2>&1 | grep tr17
for d in cov24c1 cps24t1; do echo "== $d"; ls $W/work/$d 2>/dev/null; cat $W/work/$d/REPORT.md 2>/dev/null | cut -c1-600; done
R=$(ls -d /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24m4f 2>/dev/null | tail -1); echo "== $R"; cat $R/final_message.md 2>/dev/null | head -40 | cut -c1-600
