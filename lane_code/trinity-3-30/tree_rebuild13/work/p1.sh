W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls | grep tr12
for L in tree_rebuild21h tree_rebuild22b; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*$L | head -1); echo "== $L $d"; stat -c %s $d/transcript.log; grep -c "at capacity" $d/transcript.log; tail -c 2500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -5 | cut -c1-300; done
ls $W/w21/out | tr '\n' ' '; echo; ls $W/w22/out | tr '\n' ' '; echo
