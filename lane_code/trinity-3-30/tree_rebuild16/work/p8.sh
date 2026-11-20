W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr15|tr16'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W 2>/dev/null | cut -f1
for l in tree_rebuild24m2d; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l $d"; grep -c "Selected model is at capacity" $d/transcript.log; test -f $d/final_message.md && head -c 4000 $d/final_message.md || tail -c 800 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-300; echo; done
ls -lt $W/w24/out | head -15
