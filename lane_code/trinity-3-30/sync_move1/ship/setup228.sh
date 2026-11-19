#!/bin/bash
set -u
I=/scratch/jjyeung/orch_n30/sm_ship
hostname -s; date -u; df -h /scratch | tail -1; nproc; uptime; /usr/bin/python3 --version; which python3.12 python3.11 2>/dev/null; git --version
ls -d /scratch/jjyeung/distill_sync 2>&1; tmux ls 2>&1 | head -20
for t in filter move; do
  L=/scratch/jjyeung/orch_n30/sm_$t; mkdir -p $L/work $L/out
  [ -d $L/in ] || cp -a $I/in $L/in
done
cp $I/syncmove_filter.md /scratch/jjyeung/orch_n30/sm_filter/PROMPT.md
cp $I/syncmove_host.md /scratch/jjyeung/orch_n30/sm_move/PROMPT.md
T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
for t in filter move; do
  s=syncmove_$t; L=/scratch/jjyeung/orch_n30/sm_$t
  tmux has-session -t "=$s" 2>/dev/null && { echo "$s exists"; continue; }
  tmux new-session -d -s $s "cd /scratch/jjyeung/orch_n30/sync_move1 && export XDG_CACHE_HOME=/scratch/jjyeung/.cache; nice -n 10 bash $T/codex_local.sh implement $L $L/PROMPT.md --model gpt-6-astra --effort high --label $s --skip-git-check > $L/codex.log 2>&1; echo EXIT=\$? >> $L/codex.log"
  echo "started $s"
done
sleep 20; for t in filter move; do tail -3 /scratch/jjyeung/orch_n30/sm_$t/codex.log; done
