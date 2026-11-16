#!/bin/bash
# Wait up to 9.5 min for a new ORCH file in my events folder or a new inbox file; print what changed.
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b06_a2dense; L=/scratch/jjyeung/orch_n30/b06_a2dense
a0=$(ls $E | grep -c _ORCH_); i0=$(ls $L/inbox | wc -l)
for k in $(seq 1 19); do a=$(ls $E | grep -c _ORCH_); i=$(ls $L/inbox | wc -l); [ $a -ne $a0 ] || [ $i -ne $i0 ] && break; sleep 30; done
date -u +%H:%MZ; [ $a -ne $a0 ] && ls -t $E | grep _ORCH_ | head -$((a-a0)); [ $i -ne $i0 ] && ls -t $L/inbox | head -3; true
