#!/bin/bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
L=/scratch/jjyeung/orch_n30/review_offnative3/work/logs; mkdir -p $L
B=/scratch/jjyeung/orch_n30/b07_offread/builds
H=$($PY -B -c 'import secrets;print(secrets.token_hex(6))')
export ROFF2_ROOT=/tmp/a_900000_$H
echo ROFF2_ROOT=$ROFF2_ROOT > $L/env.txt
(cd $B/R && $PY -B -m pytest -p no:cacheprovider tests/ -q --basetemp=/dev/shm/review_offnative3/bt_r_$H -rA > $L/r_suite.log 2>&1; echo rc=$? >> $L/r_suite.log)
(cd $B/N && $PY -B -m pytest -p no:cacheprovider kit/tests -q --basetemp=/dev/shm/review_offnative3/bt_n_$H -rA > $L/n_suite.log 2>&1; echo rc=$? >> $L/n_suite.log)
# reviewer files with the reviewer's named-ancestor default root (lane says F1/F2 fail only from sim lookup)
mkdir -p /dev/shm/review_offnative3/named/orch_n30/review_offnative2/work
mkdir -p /scratch/jjyeung/orch_n30/review_offnative3/work/named
(cd $B/R && ROFF2_ROOT=/scratch/jjyeung/orch_n30/review_offnative3/work/named $PY -B -m pytest -p no:cacheprovider tests/test_review_offnative2.py -q --basetemp=/dev/shm/review_offnative3/bt_rn_$H > $L/r_reviewer_named_root.log 2>&1; echo rc=$? >> $L/r_reviewer_named_root.log)
echo DONE > $L/DONE
