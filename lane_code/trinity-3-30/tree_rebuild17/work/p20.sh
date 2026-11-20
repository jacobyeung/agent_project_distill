W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24c/out/kit_n_go; date -u +%TZ; tmux ls | grep tr17
grep -n "n_ck\|ckstop\|50 \* \|GiB\|free" $K/b/*.py $K/b/*.sh $K/job.sh 2>/dev/null | cut -c1-220 | head -30
for l in tree_rebuild_rev24mC tree_rebuild24k4; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l"; test -f $d/final_message.md && head -c 1500 $d/final_message.md || tail -c 500 $d/transcript.log | tr -cd "[:print:]\n" | tail -2 | cut -c1-200; done
