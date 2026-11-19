J=/scratch/jjyeung/orch_n30/tree_rebuild14_w24j; date -u +%TZ; tmux ls | grep tr14; free -g | sed -n 2p
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24j | head -1); ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log; tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -3 | cut -c1-300; ls $J/out | tr '\n' ' '
