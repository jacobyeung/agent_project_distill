#!/bin/bash
# T3: ARKit range reads, one thread, capped at 7.5 MB/s
K=/scratch/jjyeung/orch_cd/k1_ops/work; W=/scratch/jjyeung/orch_n30/k1_ops3/work
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p /scratch/jjyeung/k1_frames
echo "WA start $(date -u +%FT%TZ)" >> $W/WA.log
nice -n 10 $PY -s -B $K/wa_rl.py 7500000 /scratch/jjyeung/orch_cd/p2_build/c5d3/k6bin/bin/wa.py $K/D3_FETCH_PLAN.json /scratch/jjyeung/k1_frames k1 $W/WA_OUT.jsonl 1 >> $W/WA.log 2>&1
echo "WA rc=$? $(date -u +%FT%TZ)" >> $W/WA.log
