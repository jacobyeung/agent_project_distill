#!/bin/bash
# Local wait (no Orchard calls): return when the steps tail, job state, events or inbox change, or after $1 minutes.
W=/scratch/jjyeung/orch_n30/r1_ops6/work; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops
sig() { awk '/^172660.steps/{f=1;next} /^172660.w.steps/{f=0} f' $W/mon/last.txt | awk 'NF' | sort -u | tail -1; grep -E "^172660 " $W/mon/last.txt | awk '{print $4}' | head -1; ls $E | grep -c _ORCH_; ls /scratch/jjyeung/orch_n30/r1_ops6/inbox | wc -l; awk '/^172660.err/{f=1;next} /^172660.steps/{f=0} f' $W/mon/last.txt | grep -v cgroup | awk 'NF' | wc -l; }
s0=$(sig); for i in $(seq 1 ${1:-30}); do sleep 60; [[ "$(sig)" != "$s0" ]] && break; done; $W/peek.sh 3
