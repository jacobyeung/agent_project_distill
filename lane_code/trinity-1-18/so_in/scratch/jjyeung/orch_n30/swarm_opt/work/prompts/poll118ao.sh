#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
G=/scratch/jjyeung/orch_n30/so_git/work
[[ -d $G/realgit5_by_swarm_opt ]] || tmux new-session -d -s so_realgit5 "bash $P/realgit5.sh > $G/realgit5.log 2>&1"
if [[ -f $G/realgit5_by_swarm_opt/DONE ]]; then echo "realgit5: $(grep -h -E '^Ran |^OK|FAILED|skipped|^rc=' $G/realgit5_by_swarm_opt/run_*.txt | tr '\n' ' ')"; grep -q '^rc=0' $G/realgit5_by_swarm_opt/run_py36.txt && grep -q '^rc=0' $G/realgit5_by_swarm_opt/run_py312.txt && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_git5 ]] && bash $P/cursor_start.sh so_cr_git5 $P/cr_git5.md; fi
bash $P/poll118an.sh
echo "cr_git5: $(head -1 /scratch/jjyeung/orch_n30/so_cr_git5/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =so_cr_git5 2>/dev/null && echo y || echo n)"
