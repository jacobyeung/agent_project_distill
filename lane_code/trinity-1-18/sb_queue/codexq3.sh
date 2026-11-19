#!/bin/bash
# Launch queued Codex builds (entries "label" or "label:workspace") when fewer than 3 swarm_build Codex builds run (counted by unique label) and >100 GB RAM is available; every build runs under nice 10 with 8-thread limits.
R=/scratch/jjyeung/orch_n30; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; Q=$R/sb_queue/queue.txt
while true; do
  e=$(head -1 $Q 2>/dev/null); [ -z "$e" ] && { sleep 60; continue; }
  t=${e%%:*}; w=${e#*:}; [ "$w" = "$e" ] && w=$t
  n=$(pgrep -af "codex_dispatch.sh implement $R/sb_" | grep -o "label [a-zA-Z0-9_]*" | sort -u | wc -l); a=$(free -g | awk '/Mem:/{print $7}')
  if [ "$n" -lt 3 ] && [ "$a" -gt 100 ]; then
    sed -i 1d $Q
    tmux new-session -d -s $t "OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash $B/tools/codex_local.sh implement $R/$w $R/$w/prompts/$t.md --model gpt-6-astra --effort high --label $t --skip-git-check > $R/$w/dispatch_$t.log 2>&1"
    echo "$(date -u +%FT%TZ) launched $t in $w (running before: $n, avail $a)" >> $R/sb_queue/codexq.log; sleep 20
  else sleep 60; fi
done
