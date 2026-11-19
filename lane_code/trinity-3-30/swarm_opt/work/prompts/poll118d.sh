#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
n=0; for t in so_git so_pack so_step_c so_launch_c; do tmux has-session -t "=$t" 2>/dev/null && n=$((n+1)); done
echo "builds running: $n"
for t in so_launch so_step; do
  L=/scratch/jjyeung/orch_n30/$t
  if ! tmux has-session -t "=${t}_c" 2>/dev/null && [[ ! -f $L/work/CONT_STARTED ]] && (( n < 3 )); then
    cp $P/${t}_cont.md $L/PROMPT_CONT.md; date -u > $L/work/CONT_STARTED
    tmux new-session -d -s ${t}_c "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT_CONT.md --model gpt-6.1-sol --effort high --label ${t}_c --skip-git-check > $L/work/dispatch_c.log 2>&1"
    echo "started ${t}_c"; n=$((n+1))
  fi
done
echo "host $(hostname -s) $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) avail $(free -g | awk '/^Mem:/{print $7}')G"
for t in so_git so_pack so_step so_launch so_rv_tick2; do
  L=/scratch/jjyeung/orch_n30/$t; [[ -d $L ]] || continue
  R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_$t 2>/dev/null | tail -1)
  echo "== $t report=$( [[ -f $L/out/REPORT.md ]] && head -1 $L/out/REPORT.md | cut -c1-160 || echo none) meta_exit=$(grep -o '"exit_code": [0-9]*' $R/meta.json 2>/dev/null) capacity=$(grep -c 'at capacity' $R/transcript.log 2>/dev/null)"
  [[ -f $L/work/STATUS.md ]] && tail -2 $L/work/STATUS.md | cut -c1-200
done
for t in so_step_c so_launch_c; do R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_$t 2>/dev/null | tail -1); [[ -n "$R" ]] && echo "$t receipt $R exit=$(grep -o '"exit_code": [0-9]*' $R/meta.json 2>/dev/null) capacity=$(grep -c 'at capacity' $R/transcript.log 2>/dev/null)"; done
R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_so_rv_tick2 | tail -1); [[ -s $R/final_message.md ]] && { echo "#### rv_tick2"; head -c 5000 $R/final_message.md; }
