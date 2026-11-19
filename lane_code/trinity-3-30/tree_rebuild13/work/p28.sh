W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr13
for L in tree_rebuild_rev23d tree_rebuild_q4d; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*$L | head -1); echo "== $L"; cat $d/final_message.md 2>/dev/null; done
tail -c 300 $W/w23/work/build23b/capacity_final_tr13.log; echo; ls $W/w23/work/build23b/CAPACITY.json 2>&1
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24 | head -1); ls $d | tr '\n' ' '; tail -c 1200 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300
