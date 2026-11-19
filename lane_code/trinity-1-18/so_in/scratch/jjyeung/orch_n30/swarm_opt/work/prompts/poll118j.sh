#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_git ]] || bash $P/cursor_start.sh so_cr_git $P/cr_git.md
G=/scratch/jjyeung/orch_n30/so_step/work/full_suite_by_swarm_opt2.txt
if grep -q '^EXIT=0' $G && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_step ]]; then bash $P/cursor_start.sh so_cr_step $P/cr_step.md; fi
bash $P/poll118e.sh | grep -v '^$'
tmux has-session -t "=so_read_fix" 2>/dev/null && echo "so_read_fix RUNNING" || echo "so_read_fix ENDED: $(head -1 /scratch/jjyeung/orch_n30/so_read/out/REPORT.md | cut -c1-200)"
echo "-- gloo2: $(grep -E '^(Ran|OK|FAILED|EXIT)' $G | tr '\n' ' ')"
for c in so_cr_launch so_cr_git so_cr_step; do W=/scratch/jjyeung/orch_n30/$c; [[ -d $W ]] && echo "-- $c: verdict=$(head -1 $W/REVIEW_VERDICT.md 2>/dev/null) log_tail=$(tail -c 150 $W/cursor.log 2>/dev/null | tr '\n' ' ')"; done
