#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_launch ]] || bash $P/cursor_start.sh so_cr_launch $P/cr_launch.md
bash $P/poll118e.sh
for t in so_read_fix; do tmux has-session -t "=$t" 2>/dev/null && echo "$t RUNNING" || echo "$t ENDED"; done
echo "-- gloo2: $(tail -4 /scratch/jjyeung/orch_n30/so_step/work/full_suite_by_swarm_opt2.txt | tr '\n' ' ' | cut -c1-300)"
echo "-- cr_launch: $(tail -c 300 /scratch/jjyeung/orch_n30/so_cr_launch/cursor.log 2>/dev/null)"
