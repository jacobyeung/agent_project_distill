#!/bin/bash
# Launch queued Codex builds when fewer than 6 swarm_build Codex builds run and >100 GB RAM is available.
R=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; Q=$R/sb_queue/queue.txt
while true; do
  t=$(head -1 $Q 2>/dev/null); [ -z "$t" ] && { sleep 60; continue; }
  n=$(pgrep -f "codex_dispatch.sh implement $R/sb_" | wc -l); a=$(free -g | awk '/Mem:/{print $7}')
  if [ "$n" -lt 6 ] && [ "$a" -gt 100 ]; then
    sed -i 1d $Q
    tmux new-session -d -s $t "bash $B/tools/codex_local.sh implement $R/$t $R/$t/prompts/$t.md --model gpt-6-astra --effort high --label $t --skip-git-check > $R/$t/dispatch.log 2>&1"
    echo "$(date -u +%FT%TZ) launched $t (running before: $n, avail $a)" >> $R/sb_queue/codexq.log; sleep 20
  else sleep 60; fi
done
