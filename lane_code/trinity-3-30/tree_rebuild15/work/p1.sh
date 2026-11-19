W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr1[45]'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W 2>/dev/null | cut -f1
for l in tree_rebuild24k tree_rebuild24fr3; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l $d"; grep -c "at capacity" $d/transcript.log; test -f $d/final_message.md && head -c 3000 $d/final_message.md || tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | tail -5 | cut -c1-300; echo; done
R=/scratch/jjyeung/orch_n30/tr14_rev24j; echo "== cursor"; ls -la $R; test -f $R/VERDICT.md && cat $R/VERDICT.md || tail -c 800 $R/cursor.log
ls -la $W/w24/out | tail -25
