W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr12; ls $W/w21/out | grep -E '21g|21G'
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21g2 | head -1); stat -c '%s' $d/transcript.log; grep -c "at capacity" $d/transcript.log; ls $d | tr '\n' ' '; cat $d/final_message.md 2>/dev/null | head -20
tail -c 2500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -6
