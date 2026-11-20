W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr1[67]'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
for l in tree_rebuild24m3 tree_rebuild_d173496; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l $d"; test -f $d/final_message.md && head -c 3500 $d/final_message.md || tail -c 800 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-300; echo; done
ls -lt $W/w24/out | head -8
