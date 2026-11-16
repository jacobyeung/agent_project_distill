#!/bin/bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
L=/scratch/jjyeung/orch_n30/review_offnative3/work/logs
B=/scratch/jjyeung/orch_n30/b07_offread/builds
H=$($PY -B -c 'import secrets;print(secrets.token_hex(6))')
export ROFF2_ROOT=/tmp/a_900000_$H
(cd $B/N && $PY -B -m pytest -p no:cacheprovider kit/tests -q --basetemp=/dev/shm/b07_n7/a${H}_n -rA > $L/n_suite2.log 2>&1; echo rc=$? >> $L/n_suite2.log)
(cd $B/R && $PY -B -m pytest -p no:cacheprovider tests/test_rebind.py -q --basetemp=/dev/shm/b07_n7/a${H}_r -rA > $L/r_rebind2.log 2>&1; echo rc=$? >> $L/r_rebind2.log)
echo DONE > $L/DONE2
