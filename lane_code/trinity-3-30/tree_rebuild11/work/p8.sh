W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr11"; ls -la $W/w20/work/build20/ | tail -15; 
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild20 | head -1); ls -la $d | tail -4; tail -c 1500 $d/transcript.log | tr -cd '[:print:]\n' | tail -15 | cut -c1-250
