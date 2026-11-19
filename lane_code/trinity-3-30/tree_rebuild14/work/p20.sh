W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"; free -g | sed -n 2p; du -s --block-size=1G $W | tail -1
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24f | head -1); ls $d | tr '\n' ' '; echo; grep -c "at capacity" $d/transcript.log; tail -c 2500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -6 | cut -c1-300
ls -t $W/w24/out | head -8 | tr '\n' ' '
