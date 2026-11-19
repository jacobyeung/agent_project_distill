W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr12; ls $W/w21/out | grep -E '21f|21F'
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21f | head -1); stat -c '%s' $d/transcript.log; grep -c "at capacity" $d/transcript.log; ls $d | tr '\n' ' '; cat $d/final_message.md 2>/dev/null | head -20
