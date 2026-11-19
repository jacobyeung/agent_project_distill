date -u +%TZ; which agent; ls /scratch/jjyeung/orch_n30/sb_cursor_probe/AGENTS.md 2>&1; ls /scratch/jjyeung/envs/p1cpu/bin/python; tmux ls | grep tr15
J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; ls $J/out; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24l2 | head -1); tail -c 500 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-200
