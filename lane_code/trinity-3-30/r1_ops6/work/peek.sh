#!/bin/bash
# compact local view of the last monitor output + events/inbox (no Orchard call)
M=/scratch/jjyeung/orch_n30/r1_ops6/work/mon/last.txt
date -u +%H:%M:%SZ; head -1 $M; grep -E "^172660 " $M | head -1
awk '/^172660.steps/{f=1;next} /^172660.w.steps/{f=0} f' $M | awk 'NF' | sort -u | tail -${1:-2} | cut -c1-170
awk '/^172660.err/{f=1;next} /^172660.steps/{f=0} f' $M | awk 'NF' | sort -u | tail -3 | cut -c1-200
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops | grep -v -E "^(STATUS.md|ops_mirror|PRELAUNCH)" | head -1
ls /scratch/jjyeung/orch_n30/r1_ops6/inbox
