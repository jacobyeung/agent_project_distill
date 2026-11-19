#!/bin/bash
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/tmp; ulimit -f 204800
P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; T=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/pkg/work/tree_r1
for s in n1r.py n1c.py t4.py; do echo "== $s"; timeout 1500 $P s/$s > ${s%.py}.log 2>&1; echo rc=$?; done
cd t11/m1 && timeout 600 $P export_tree.py $T /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/t11/m1/modern > export.log 2>&1; timeout 600 $P load_b11.py /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/t11/m1 tamper_b13 > load.log 2>&1; timeout 600 $P m1b.py > m1b.log 2>&1; cd ../parity && timeout 900 $P geo_dump.py $T new b13_new.json 6000 > new.log 2>&1; python3 cmp.py /scratch/jjyeung/orch_n30/review_tree11/work/parity/b11_legacy.json b13_new.json > cmp.out; cd ../l2 && timeout 600 $P probe_int.py > L2_int.out 2>&1
echo DONE
