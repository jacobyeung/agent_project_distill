#!/bin/bash
# cont_ops22 post600v: DIAGNOSTIC VSTI read at step 600 (TOK=a4dab97810e): /dev/shm build copy, fetch, unpack, pool move, vsti_summary.py vs 544 base (acb2faedd41) and vs the step-400 read (a4525db2f6a).
set -uo pipefail; K=/scratch/jjyeung/orch_n30/cont_ops/work/h1vsti7; cd $K
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$K/kit/launcher/orchard_launcher.py OMP_NUM_THREADS=1
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
T=${TOK:-a4dab97810e}; S=600; SRC=$K/kit/build/$T; B=/dev/shm/c22/build/$T; W=/scratch/jjyeung/orch_n30/cont_ops22/work; LOG=$W/post600_$T.log
mkdir -p /dev/shm/c22/build; test -d $B || cp -a $SRC $B
{
echo "== $(date -u +%TZ) fetch"; test -s $B/fetched/result.tar.gz || "$PY" -B "$L" fetch --destination "$B" || { echo FETCH_FAILED; exit 2; }
sha256sum $B/fetched/result.tar.gz; cat $B/fetched/EXIT.json; echo
echo "== unpack"; test -d $B/fetched/x || "$PY" -B tools/unpack_return.py --destination "$B" || { echo UNPACK_FAILED; exit 3; }
echo "== pool move"; timeout 300 bash $A_TRANSPORT "T=$T bash -s" < o_mvpool112.sh
echo "== VSTI vs 544 base"; "$PY" -B vsti_summary.py --read $B/fetched/x --base ../h1vsti/kit/build/acb2faedd41/fetched/x | tee $B/VSTI_m${S}_vs544.txt
echo "== VSTI vs step 400"; "$PY" -B vsti_summary.py --read $B/fetched/x --base $K/kit/build/a4525db2f6a/fetched/x | tee $B/VSTI_m${S}_vs400.txt
mkdir -p $W/post600_$T; for f in $B/*.json $B/*.txt; do [ $(stat -c %s $f) -lt 5000000 ] && cp $f $W/post600_$T/; done
echo "== done $(date -u +%TZ)"
} 2>&1 | tee -a $LOG
