#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
n=0; for t in so_git so_pack so_step_c so_launch_c; do tmux has-session -t "=$t" 2>/dev/null && n=$((n+1)); done
echo "builds running: $n"
for t in so_pack so_git; do
  L=/scratch/jjyeung/orch_n30/$t
  if ! tmux has-session -t "=$t" 2>/dev/null && [[ ! -f $L/work/SOL_STARTED ]] && (( n < 3 )); then
    date -u > $L/work/SOL_STARTED
    tmux new-session -d -s $t "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT.md --model gpt-6.1-sol --effort high --label $t --skip-git-check > $L/work/dispatch.log 2>&1"
    echo "started $t (sol)"; n=$((n+1))
  fi
done
echo "host $(hostname -s) $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) avail $(free -g | awk '/^Mem:/{print $7}')G"
for t in so_git so_pack so_step_c so_launch_c; do
  R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_$t 2>/dev/null | tail -1)
  tmux has-session -t "=$t" 2>/dev/null && st=RUNNING || st=ENDED
  echo "== $t $st $R exit=$(grep -o '"exit_code": [0-9]*' $R/meta.json 2>/dev/null) capacity=$(grep -c 'at capacity' $R/transcript.log 2>/dev/null)"
done
for t in so_git so_pack so_step so_launch; do L=/scratch/jjyeung/orch_n30/$t; echo "-- $t report=$( [[ -f $L/out/REPORT.md ]] && head -1 $L/out/REPORT.md | cut -c1-200 || echo none)"; [[ -f $L/work/STATUS.md ]] && tail -2 $L/work/STATUS.md | cut -c1-220; done
