#!/bin/bash
# n_ops9: agent-free N watch loop (tmux nops_auto). Stop: touch .../auto/stop. One nauto.py cycle per 60 s; a crash is logged and the loop goes on.
A=/scratch/jjyeung/orch_n30/n_ops9/work/auto
while [ ! -e $A/stop ]; do
  timeout 600 /scratch/jjyeung/envs/p1cpu/bin/python $A/nauto.py >> $A/nauto.log 2>&1 || echo "$(date -u +%FT%TZ) nauto rc=$?" >> $A/nauto.log
  tail -c 200000 $A/nauto.log > $A/nauto.log.t 2>/dev/null && mv $A/nauto.log.t $A/nauto.log
  sleep 60
done
