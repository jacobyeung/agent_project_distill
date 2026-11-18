#!/bin/bash
export TMPDIR=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp R2_FIXTURES=/scratch/jjyeung/orch_n30/review_tree11/pkg/fixtures CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp/c HF_HOME=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp/hf
ulimit -f 204800
PY="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
cd /scratch/jjyeung/orch_n30/review_tree11/work/s
for s in n1 n1x restage restage_r1 f6; do $PY $s.py > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/$s.log 2>&1; echo "$s rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done2.txt; done
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B n5.py /scratch/jjyeung/orch_n30/review_tree11/work/n1/n5s > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/n5.log 2>&1; echo "n5 rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done2.txt
