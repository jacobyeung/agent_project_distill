#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_git4 ]] || bash $P/cursor_start.sh so_cr_git4 $P/cr_git4.md
bash $P/poll118ai.sh
echo "cr_git4: $(head -1 /scratch/jjyeung/orch_n30/so_cr_git4/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =so_cr_git4 2>/dev/null && echo y || echo n)"
echo "read_fix3: $(head -1 /scratch/jjyeung/orch_n30/so_read/out/REPORT.md | cut -c1-200)"
