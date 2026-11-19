#!/bin/bash
S=/scratch/jjyeung/orch_n30/so_step
awk '/^## Coordinator command: revised two-rank gloo tests/{f=1} f&&/^```/{n++; if(n==2){exit}; next} f&&n==1{print}' $S/out/REPORT.md > $S/work/gloo_cmd_r1.sh
echo "--- cmd:"; cat $S/work/gloo_cmd_r1.sh
if [[ -s $S/work/gloo_cmd_r1.sh ]] && ! tmux has-session -t =so_step_gloo2 2>/dev/null && [[ ! -f $S/work/review1_full_suite_by_coordinator.txt ]]; then
  tmux new-session -d -s so_step_gloo2 "cd $S && bash work/gloo_cmd_r1.sh; echo EXIT=\$? >> work/review1_full_suite_by_coordinator.txt"; echo started so_step_gloo2; fi
uptime
