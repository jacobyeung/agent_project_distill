J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; tmux ls | grep tr16; ls -t $J/out | head -5
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24l4r | head -1); test -f $d/final_message.md && head -c 3000 $d/final_message.md || tail -c 600 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-250
