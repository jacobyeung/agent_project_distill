W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr13; df -BG --output=avail /scratch | tail -1; du -s --block-size=1M $W | tail -1
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24b | head -1); ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log; tail -c 2000 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -6 | cut -c1-300
ls $W/w24/out | tr '\n' ' '
