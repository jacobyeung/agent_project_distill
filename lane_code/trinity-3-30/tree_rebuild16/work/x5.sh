J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; tmux ls | grep tr16; cat $J/out/BUILD24L4_REPORT.md; ls $J/work
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24l4r | head -1); echo $d; grep -c "at capacity" $d/transcript.log; tail -c 600 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-250
