W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | head -2; df -h /scratch | tail -1
tmux ls 2>/dev/null | grep tr2
ls -la $W/w24r/out 2>/dev/null | tail -15
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4r 2>/dev/null | tail -1); echo $d; ls -la $d 2>/dev/null | head; tail -c 1500 $d/*.log 2>/dev/null | tail -20
