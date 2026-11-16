#!/bin/bash
# Wait up to 9.5 min for a new ORCH file in my events folder, a new inbox file, or a new cont_ops event; print what changed.
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
L=/scratch/jjyeung/orch_n30/b06_a2dense
a0=$(ls $E/b06_a2dense | grep -c _ORCH_); i0=$(ls $L/inbox | wc -l); c0=$(ls $E/cont_ops | grep -ic "m200\|general\|read_done\|stop_rule")
for k in $(seq 1 19); do
  a=$(ls $E/b06_a2dense | grep -c _ORCH_); i=$(ls $L/inbox | wc -l); c=$(ls $E/cont_ops | grep -ic "m200\|general\|read_done\|stop_rule")
  [ $a -ne $a0 ] || [ $i -ne $i0 ] || [ $c -ne $c0 ] && break; sleep 30
done
date -u +%H:%MZ; ls $E/b06_a2dense | grep _ORCH_ | tail -$(( a - a0 > 0 ? a - a0 : 0 )) 2>/dev/null; [ $i -ne $i0 ] && ls -t $L/inbox | head -3; [ $c -ne $c0 ] && ls -t $E/cont_ops | grep -v STATUS | head -$(( c - c0 ))
true
