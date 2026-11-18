#!/bin/bash
export TMPDIR=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp/c HF_HOME=/scratch/jjyeung/orch_n30/review_tree11/work/n1/tmp/hf
ulimit -f 204800
PY="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
cd /scratch/jjyeung/orch_n30/review_tree11/work/s
for s in seal restage restage_r1; do $PY $s.py > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/$s.log 2>&1; echo "$s rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done.txt; done
$PY n5.py /scratch/jjyeung/orch_n30/review_tree11/work/n1/n5s > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/n5.log 2>&1; echo "n5 rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done.txt
for s in n1 n1x t3 f6 f6r; do $PY $s.py > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/$s.log 2>&1; echo "$s rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done.txt; done
$PY f1.py prod > /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/f1.log 2>&1; echo "f1 rc=$?" >> /scratch/jjyeung/orch_n30/review_tree11/work/n1/logs/done.txt
