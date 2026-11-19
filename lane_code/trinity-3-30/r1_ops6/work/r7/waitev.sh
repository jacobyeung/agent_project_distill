#!/bin/bash
# r1_ops7 local wait (no Orchard call): returns on a new events/r1_ops file, inbox file, node-monitor alarm, job state change, or after $1 minutes
W=/scratch/jjyeung/orch_n30/r1_ops6/work; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops
sig() { ls $E | grep -v -E "^(STATUS.md|ops_mirror|PRELAUNCH)" | tail -1; ls $W/../inbox | wc -l; grep -E "^172660 " $W/mon/last.txt | awk '{print $4}' | head -1; tail -1 $W/mon/node_hist.txt | grep -o -E "early rc=[0-9]+|srun rc=[0-9]+" | grep -v "=0" ; }
s0=$(sig); for i in $(seq 1 ${1:-10}); do sleep 60; [[ "$(sig)" != "$s0" ]] && { echo CHANGED; break; }; done
date -u +%T; tail -2 $W/mon/node_hist.txt | cut -c1-200; grep -E "^172660 " $W/mon/last.txt | head -1; ls -t $E | head -2
