#!/bin/bash
# Rung-1 night babysitter loop for 10-28 -> 10-29 (trinity-0-13): plan at 18:20 PT from night_20261028/PLAN.json, then one
# r1night_next.py tick at a time, 60 s apart while a started arm has no step yet, 600 s otherwise; ends at 06:40 PT.
cd /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027/tools || exit 1
export R1_NIGHT_DIR=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027/night_20261028
PY=/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
LOG=/scratch/jjyeung/rung1_push/night_loop_20261028.log
until [ "$(TZ=America/Los_Angeles date +%Y%m%d%H%M)" -ge 202610281820 ]; do sleep 30; done
[ -f $R1_NIGHT_DIR/STATE.json ] || $PY -B r1night_next.py plan >> $LOG 2>&1 || { echo "$(date -Is) plan failed" >> $LOG; exit 1; }
until [ "$(TZ=America/Los_Angeles date +%Y%m%d%H%M)" -ge 202610281830 ]; do sleep 10; done
while :; do
    [ "$(TZ=America/Los_Angeles date +%Y%m%d%H%M)" -ge 202610290640 ] && { echo "$(date -Is) night over" >> $LOG; break; }
    s=$(timeout 1200 $PY -B r1night_next.py tick 2>>$LOG | tail -n 1)
    [[ "$s" =~ ^[0-9]+$ ]] || s=600
    echo "$(date -Is) tick done; next in $s s" >> $LOG
    sleep "$s"
done
