#!/bin/bash
# compact per-step check for the lane
L=/scratch/jjyeung/orch_n30/gpu_fill; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$B/orch_n30/events
date -u +%H%MZ
tail -3 $L/alerts.log | grep -v tick
ls $L/inbox 2>/dev/null
grep -E "1-13|0-28|1-3 |1-18" $E/gpu_fill/FREE_CARDS.md | grep -v Confirm | cut -c1-200
ls -t $B | grep INBOX_TO_DISTILL | head -1
for l in b11_presence b05_owngrd trin_read; do echo "[$l] $(ls -t $E/$l | grep -v STATUS | head -3 | tr '\n' ' ')"; done
