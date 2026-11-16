#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
P=/scratch/jjyeung/envs/p1cpu/bin/python
U=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
date -u +%FT%TZ > evidence/B7D_START.txt
export SLURM_JOB_ID=424242 HOME="$N/jt/home" XDG_CACHE_HOME="$N/jt/cache" TMPDIR="$N/jt/temp" TMP="$N/jt/temp" TEMP="$N/jt/temp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
rc=0
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind "$N/jt" /tmp --bind "$N" /tmp/b7e31d84 --chdir /tmp/b7e31d84 --setenv HOME /tmp/home --setenv XDG_CACHE_HOME /tmp/cache --setenv TMPDIR /tmp/temp --setenv TMP /tmp/temp --setenv TEMP /tmp/temp --setenv HF_HOME /tmp/cache/hf --setenv TORCH_HOME /tmp/cache/torch --setenv TRITON_CACHE_DIR /tmp/cache/triton --die-with-parent "$U" -I -s -B /tmp/b7e31d84/rh_prepare.py > out/outer.log 2>&1 || rc=$?
echo $rc > evidence/B7D_OUTER.rc
nice -n 19 "$U" -I -s -B rh_prepare.py --collect "$rc" > evidence/B7D_COLLECT.log 2>&1; echo $? > evidence/B7D_COLLECT.rc
RUN=$(ls -td evidence/batch_* | head -1)
for c in $(ls -td evidence/batch_*/success | head -2); do
  nice -n 19 /usr/bin/bwrap --dev-bind / / --bind $N/$c/job_tmp/424242 /tmp --die-with-parent $P -I -s -B $N/ns_depth_check.py $N/$c > $N/$c/../NSDEPTH_$(basename $(dirname $c)).log 2>&1; echo "$c $?" >> evidence/B7D_NSDEPTH.rc
done
date -u +%FT%TZ > evidence/B7D_END.txt
