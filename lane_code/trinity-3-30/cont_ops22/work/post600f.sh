#!/bin/bash
# cont_ops22 post600f: DIAGNOSTIC facing read at step 600 (TOK=a0359570077): fetch into a /dev/shm build copy, unpack, pool move, face_look.py --step 600 (vs 544, 99.82%), face_vs400.py (paired vs the step-400 facing read).
set -uo pipefail; K=/scratch/jjyeung/orch_n30/cont_ops/work/h1face7; cd $K
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$K/kit/launcher/orchard_launcher.py OMP_NUM_THREADS=1
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
T=${TOK:-a0359570077}; S=600; SRC=$K/kit/build/$T; B=/dev/shm/c22/build/$T; W=/scratch/jjyeung/orch_n30/cont_ops22/work; LOG=$W/post600_$T.log
mkdir -p /dev/shm/c22/build; test -d $B || cp -a $SRC $B
{
echo "== $(date -u +%TZ) fetch"; test -s $B/fetched/result.tar.gz || "$PY" -B "$L" fetch --destination "$B" || { echo FETCH_FAILED; exit 2; }
sha256sum $B/fetched/result.tar.gz; cat $B/fetched/EXIT.json; echo
echo "== unpack"; test -d $B/fetched/x || "$PY" -B tools/unpack_return.py --destination "$B" || { echo UNPACK_FAILED; exit 3; }
echo "== pool move"; timeout 300 bash $A_TRANSPORT "T=$T bash -s" < o_mvpool112.sh
echo "== facing vs 544 (look level 99.82%)"; "$PY" -B face_look.py --x $B/fetched/x --step $S --out $B/FACE_m$S.json | tee $B/FACE_m$S.txt
echo "== facing paired vs step 400"; "$PY" -B $W/face_vs400.py --x $B/fetched/x --step $S --out $B/FACE_m${S}_vs400.json | tee $B/FACE_m${S}_vs400.txt
mkdir -p $W/post600_$T; for f in $B/*.json $B/*.txt; do [ $(stat -c %s $f) -lt 5000000 ] && cp $f $W/post600_$T/; done
echo "== done $(date -u +%TZ)"
} 2>&1 | tee -a $LOG
