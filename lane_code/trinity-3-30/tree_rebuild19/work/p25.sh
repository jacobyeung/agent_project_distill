W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr19; ls $W/work/census24; head -15 $W/work/census24/FINAL.md 2>/dev/null; head -3 $W/work/census24/CANARY.md 2>/dev/null
R=$(ls -td /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24m4k | head -1); test -f $R/final_message.md && cat $R/final_message.md
