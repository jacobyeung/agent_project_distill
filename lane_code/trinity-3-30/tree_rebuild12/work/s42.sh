W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr12; ls $W/w22/out 2>/dev/null | tr '\n' ' '; echo
cat $W/w22/out/LOOKAHEAD_KITQ.md 2>/dev/null | cut -c1-300
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild22b | head -1); stat -c %s $d/transcript.log; grep -c "at capacity" $d/transcript.log; tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4
