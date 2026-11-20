#!/bin/bash
# usage: launch_118.sh CARD ARM NAME KEYS_FILE   (only on a card the orchestrator named; two empty readings 330 s apart; HOLD file and new main inbox naming 1-18 stop it)
CARD=$1; ARM=$2; NAME=$3; KEYS=$4
L=/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook; LOG=$L/work/gpu_launch.log; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
rd() { echo "$(nvidia-smi -i $CARD --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ') $(nvidia-smi -i $CARD --query-compute-apps=pid --format=csv,noheader | wc -l)"; }
held() { [ -e $L/work/HOLD ] && return 0; n=$(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1); [ "$(basename $n)" != INBOX_TO_DISTILL_ORCH_20261116T172517Z.md ] && grep -q "1-18" $n && return 0; return 1; }
if held; then echo "$(date -u +%FT%TZ) HOLD before $NAME" >> $LOG; exit 0; fi
set -- $(rd); echo "$(date -u +%FT%TZ) card$CARD reading1 mem=$1 procs=$2 before $NAME" >> $LOG; [ "$1" -le 10 ] && [ "$2" -eq 0 ] || { echo "$(date -u +%FT%TZ) NOT_EMPTY" >> $LOG; exit 0; }
sleep 330
if held; then echo "$(date -u +%FT%TZ) HOLD before $NAME" >> $LOG; exit 0; fi
set -- $(rd); echo "$(date -u +%FT%TZ) card$CARD reading2 mem=$1 procs=$2 before $NAME" >> $LOG; [ "$1" -le 10 ] && [ "$2" -eq 0 ] || { echo "$(date -u +%FT%TZ) NOT_EMPTY" >> $LOG; exit 0; }
echo "$(date -u +%FT%TZ) LAUNCH $NAME card $CARD" >> $LOG
bash $L/parity_kit/gpu_inner_118.sh $CARD $ARM $NAME $KEYS > $L/work/gpu_$NAME.log 2>&1
echo "$(date -u +%FT%TZ) ${NAME}_EXIT $?" >> $LOG
