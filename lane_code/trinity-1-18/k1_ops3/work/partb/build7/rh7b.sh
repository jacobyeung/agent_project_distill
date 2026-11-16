#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$N/evidence/b7_tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%FT%TZ > evidence/B7B_START.txt
MR=$(cat evidence/B7_MAPPED.run)
nice -n 19 $P -B ns_depth_check.py $MR/success > evidence/B7_NSDEPTH_MAPPEDROOT.log 2>&1; echo $? > evidence/B7_NSDEPTH_MAPPEDROOT.rc
SLURM_JOB_ID=7000072 nice -n 19 $P -B rh_batch.py --namespace --diagnostic-python $P --cases success > evidence/B7_NS2.log 2>&1; echo $? > evidence/B7_NS2.rc
RUN=$($P -c "import json;print(json.load(open('evidence/BATCH_LATEST.json'))['run'])"); echo $RUN > evidence/B7_NS2.run
nice -n 19 $P -B depth_check.py $RUN/success > evidence/B7_DEPTH_NS2.log 2>&1; echo $? > evidence/B7_DEPTH_NS2.rc
nice -n 19 $P -B ns_depth_check.py $RUN/success > evidence/B7_NSDEPTH_NS2.log 2>&1; echo $? > evidence/B7_NSDEPTH_NS2.rc
date -u +%FT%TZ > evidence/B7B_END.txt
