#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
# cursor probe once
[[ -d /scratch/jjyeung/orch_n30/so_cr_probe ]] || bash $P/cursor_start.sh so_cr_probe $P/cursor_probe.md
n=0; for t in so_git so_pack so_launch_c so_read_fix; do tmux has-session -t "=$t" 2>/dev/null && n=$((n+1)); done
L=/scratch/jjyeung/orch_n30/so_read
if (( n < 3 )) && [[ ! -f $L/work/FIX1_STARTED ]]; then date -u > $L/work/FIX1_STARTED; cp $P/so_read_fix.md $L/PROMPT_FIX1.md
  tmux new-session -d -s so_read_fix "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT_FIX1.md --model gpt-6.1-sol --effort high --label so_read_fix --skip-git-check > $L/work/dispatch_fix1.log 2>&1"; echo "started so_read_fix"; fi
bash $P/poll118e.sh
echo "-- gloo: $(tail -3 /scratch/jjyeung/orch_n30/so_step/work/full_suite_by_swarm_opt.txt | tr '\n' ' ' | cut -c1-300)"
echo "-- cursor probe: $(tail -c 300 /scratch/jjyeung/orch_n30/so_cr_probe/cursor.log 2>/dev/null)"
