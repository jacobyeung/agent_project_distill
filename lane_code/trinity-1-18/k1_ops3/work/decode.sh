#!/bin/bash
# local decode of T2 mp4 into the frame store (no NFS IO)
K=/scratch/jjyeung/orch_cd/k1_ops/work; W=/scratch/jjyeung/orch_n30/k1_ops3/work
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p /scratch/jjyeung/k1_frames
echo "WD start $(date -u +%FT%TZ)" >> $W/WD.log
nice -n 10 $PY -s -B /scratch/jjyeung/orch_cd/p2_build/c5d3/k6bin/bin/wd.py $K/D12_DECODE_MANIFEST.json.gz $K/D12_DECODE_CONF.json /scratch/jjyeung/k1_frames $W/WD_OUT.jsonl 8 >> $W/WD.log 2>&1
echo "WD rc=$? $(date -u +%FT%TZ)" >> $W/WD.log
