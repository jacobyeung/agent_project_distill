#!/bin/bash
cd /scratch/jjyeung/orch_n30/pooled_rule2/work
export OMP_NUM_THREADS=1 MALLOC_MMAP_MAX_=0
for s in $(seq 501 530); do python3 sim_exec.py $s 100 sims/null_seed$s.npz null > sims/lognull_$s.txt 2>&1 & done
wait
echo ALLDONE > sims/ALLDONE_NULL
