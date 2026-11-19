W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr13; du -s --block-size=1M $W | tail -1
for L in tree_rebuild24d; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*$L | head -1); echo "== $L"; ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log; test -f $d/final_message.md && cat $d/final_message.md || tail -c 1200 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300; done
ls $W/w24/out | tr "\n" " "
