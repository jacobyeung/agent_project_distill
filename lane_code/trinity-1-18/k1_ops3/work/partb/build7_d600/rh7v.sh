#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7_d600
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$N/evidence/b7_tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%FT%TZ > evidence/B7_RH_START.txt
nice -n 19 $P -B rh_batch.py --diagnostic-python $P > evidence/B7_MAPPED.log 2>&1; echo $? > evidence/B7_MAPPED.rc
RUN=$($P -c "import json;print(json.load(open('evidence/BATCH_LATEST.json'))['run'])"); echo $RUN > evidence/B7_MAPPED.run
nice -n 19 $P -B depth_check.py $RUN/success > evidence/B7_DEPTH_MAPPED.log 2>&1; echo $? > evidence/B7_DEPTH_MAPPED.rc
date -u +%FT%TZ > evidence/B7_MAPPED_END.txt
date -u +%FT%TZ > evidence/B7_RH_END.txt
