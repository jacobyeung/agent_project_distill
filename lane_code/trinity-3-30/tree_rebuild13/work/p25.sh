W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr13; ls $W/w23/out | tr '\n' ' '; echo
tail -c 400 $W/w23/work/build23b/capacity_final_tr13.log; echo
for L in tree_rebuild23d tree_rebuild24; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*$L | head -1); echo "== $L"; ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log; tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300; done
