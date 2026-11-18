#!/bin/bash
cd /scratch/jjyeung/orch_n30/pooled_rule2/work
export OMP_NUM_THREADS=1 MALLOC_MMAP_MAX_=0
for s in $(seq 401 425); do python3 sim_exec.py $s 40 sims/exec_seed$s.npz > sims/log_$s.txt 2>&1 & done
wait
echo ALLDONE > sims/ALLDONE
