#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
echo "host $(hostname -s) $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) avail $(free -g | awk '/^Mem:/{print $7}')G"
R=/scratch/jjyeung/orch_n30/so_rv_tick
if [[ ! -d $R ]]; then mkdir -p $R && cp $P/tick.sh.copy $R/tick.sh && cp $P/so_rv_tick.md $R/PROMPT.md && sha256sum $R/tick.sh > $R/SHA256
  tmux new-session -d -s so_rv_tick "cd $R && nice -n 10 bash $B/tools/codex_local.sh review $R $R/PROMPT.md --model gpt-6-astra --effort high --label so_rv_tick --skip-git-check > $R/dispatch.log 2>&1"; echo "started so_rv_tick"; fi
for t in so_step so_launch so_read so_git so_pack so_rv_tick so_rv_tick2; do
  L=/scratch/jjyeung/orch_n30/$t; [[ -d $L ]] || continue
  tmux has-session -t "=$t" 2>/dev/null && st=RUNNING || st=ENDED
  echo "== $t $st report=$( [[ -f $L/out/REPORT.md ]] && head -1 $L/out/REPORT.md | cut -c1-200 || echo none)"
  [[ -f $L/work/STATUS.md ]] && tail -4 $L/work/STATUS.md | cut -c1-250
  tail -2 $L/work/dispatch.log 2>/dev/null | cut -c1-200
done
ls -t /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs | grep so_ | head
