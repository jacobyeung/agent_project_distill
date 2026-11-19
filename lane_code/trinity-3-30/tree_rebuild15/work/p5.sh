W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr1[45]'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24k | head -1); grep -c "at capacity" $d/transcript.log; test -f $d/final_message.md && head -c 3000 $d/final_message.md || tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | tail -4 | cut -c1-300
echo "== reh4"; grep -v "^\s*$" $W/w24/work/build24f/rehearsal_run4.log | tail -12 | cut -c1-400
ls $W/w24/out | grep -iE "24k|jr" 
