#!/bin/bash
bash /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/poll118e.sh
R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_so_rv_read | tail -1); tmux has-session -t "=so_rv_read" 2>/dev/null && echo "so_rv_read RUNNING" || { echo "so_rv_read ENDED"; head -c 6000 $R/final_message.md; }
