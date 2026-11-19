#!/bin/bash
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
L=/scratch/jjyeung/orch_n30/so_launch
if [[ ! -f $L/work/FIX1_STARTED ]]; then date -u > $L/work/FIX1_STARTED; cp $P/so_launch_fix.md $L/PROMPT_FIX1.md
  tmux new-session -d -s so_launch_fix "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT_FIX1.md --model gpt-6.1-sol --effort high --label so_launch_fix --skip-git-check > $L/work/dispatch_fix1.log 2>&1"; echo "started so_launch_fix"; fi
[[ -d /scratch/jjyeung/orch_n30/so_cr_pack ]] || bash $P/cursor_start.sh so_cr_pack $P/cr_pack.md
for t in so_read_fix so_launch_fix; do tmux has-session -t "=$t" 2>/dev/null && echo "$t RUNNING" || echo "$t ENDED"; done
for c in so_cr_launch so_cr_git so_cr_step so_cr_pack; do W=/scratch/jjyeung/orch_n30/$c; [[ -d $W ]] && echo "-- $c: verdict=$(head -1 $W/REVIEW_VERDICT.md 2>/dev/null) running=$(tmux has-session -t "=$c" 2>/dev/null && echo y || echo n)"; done
echo "-- so_read: $(head -1 /scratch/jjyeung/orch_n30/so_read/out/REPORT.md | cut -c1-200)"
echo "host $(hostname -s) $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) avail $(free -g | awk '/^Mem:/{print $7}')G"
