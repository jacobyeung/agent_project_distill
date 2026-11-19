#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
G=/scratch/jjyeung/orch_n30/so_git/work
[[ -d $G/realgit4_by_swarm_opt ]] || tmux new-session -d -s so_realgit4 "bash $P/realgit4.sh > /scratch/jjyeung/orch_n30/so_git/work/realgit4.log 2>&1"
sleep 5; head -2 $G/realgit4.log
bash $P/poll118ai.sh
