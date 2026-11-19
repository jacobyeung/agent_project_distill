#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
tmux has-session -t =so_step_gloo3 2>/dev/null || [[ -f /scratch/jjyeung/orch_n30/so_step/work/round3_b21_gloo_by_coordinator.txt ]] || tmux new-session -d -s so_step_gloo3 "bash $P/gloo_step3_body.sh; date -u >> /scratch/jjyeung/orch_n30/so_step/work/round3_b21_gloo_by_coordinator.txt"
