#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
R=/scratch/jjyeung/orch_n30/so_rv_read
if [[ ! -d $R ]]; then mkdir -p $R && cp $P/so_rv_read.md $R/PROMPT.md
  tmux new-session -d -s so_rv_read "cd $R && nice -n 10 bash $B/tools/codex_local.sh review $R $R/PROMPT.md --model gpt-6-astra --effort high --label so_rv_read --skip-git-check > $R/dispatch.log 2>&1"; echo "started so_rv_read"; fi
bash $P/poll118e.sh
