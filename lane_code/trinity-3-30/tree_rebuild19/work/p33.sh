W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr19; ls $W/w24m/out | grep -i "24M4M\|CPRIME2"; head -12 $W/w24m/out/BUILD24M4M_REPORT.md 2>/dev/null
R=$(ls -td /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24m4l | head -1); test -f $R/final_message.md && cat $R/final_message.md
