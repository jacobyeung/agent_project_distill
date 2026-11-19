W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr1
for L in tree_rebuild23c tree_rebuild24; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*$L | head -1); echo "== $L $d"; ls $d | tr '\n' ' '; stat -c %s $d/transcript.log; grep -c "at capacity" $d/transcript.log; tail -c 3000 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -8 | cut -c1-400; done
ls $W/w23/out | tr '\n' ' '
ls $W/w24/out 2>/dev/null | tr "\n" " "
