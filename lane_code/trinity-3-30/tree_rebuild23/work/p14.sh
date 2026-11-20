W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls | grep tr2
tail -c 400 $W/work/rev24m4y2.log; echo; C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild_rev24m4y2 | tail -1); echo $d; test -f $d/final_message.md && cat $d/final_message.md
ls -lt $W/w24z2/out | head -6; ls $W/w24z2/work | head
