#!/bin/bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
L=/scratch/jjyeung/orch_n30/so_git
if [[ ! -f $L/work/FIX1_STARTED ]]; then date -u > $L/work/FIX1_STARTED; cp $P/so_git_fix.md $L/PROMPT_FIX1.md
  tmux new-session -d -s so_git_fix "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT_FIX1.md --model gpt-6.1-sol --effort high --label so_git_fix --skip-git-check > $L/work/dispatch_fix1.log 2>&1"; echo "started so_git_fix"; fi
bash $P/poll118k.sh
for t in so_git_fix; do tmux has-session -t "=$t" 2>/dev/null && echo "$t RUNNING" || echo "$t ENDED"; done
