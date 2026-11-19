#!/bin/bash
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp
ulimit -f 204800
P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
for s in n1c.py n1r2.py t4.py "f1.py prod" seal.py f6.py f6r.py restage.py restage_r1.py; do
  set -- $s; echo "== $s $(date -u +%T)"; timeout 1500 $P s/$1 $2 > $(basename $1 .py)$2.log 2>&1; echo "rc=$?"
done
echo DONE $(date -u +%T)
