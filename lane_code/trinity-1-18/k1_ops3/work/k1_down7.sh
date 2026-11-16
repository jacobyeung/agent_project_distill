#!/bin/bash
# K1 downstream after review_k1c pass-3 GO: R2 on one primary portrait capture, then the full run. Run in tmux k1down.
set -u
W=/scratch/jjyeung/orch_n30/k1_ops3/work; LOG=$W/K1_DOWN7.log
export K1_CONVERT_CACHE=/scratch/jjyeung/k1/run_convert_2 K1_REFIT_PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
echo "R2 START $(date -u +%FT%TZ) launcher sha $(sha256sum $W/kc_guard_brief/k1_downstream.guard.sh | cut -c1-64)" >> $LOG
MODE=r2 K1_R2_CAPTURE=arkitscenes/41048124 bash $W/kc_guard_brief/k1_downstream.guard.sh >> $LOG 2>&1; rc=$?
echo "R2 EXIT rc=$rc $(date -u +%FT%TZ)" >> $LOG; [ $rc = 0 ] || exit $rc
echo "FULL START $(date -u +%FT%TZ)" >> $LOG
bash $W/kc_guard_brief/k1_downstream.guard.sh >> $LOG 2>&1; rc=$?
echo "FULL EXIT rc=$rc $(date -u +%FT%TZ)" >> $LOG; exit $rc
