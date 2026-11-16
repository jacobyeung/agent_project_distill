#!/bin/bash
# T2: one stream, 138 mp4 from /data2 into /scratch/jjyeung/k1/src at 8 MB/s
set -o pipefail
K=/scratch/jjyeung/orch_cd/k1_ops/work; W=/scratch/jjyeung/orch_n30/k1_ops3/work
cd /scratch/jjyeung/k1/src || exit 1
echo "T2 start $(date -u +%FT%TZ)" >> $W/T2.log
tar cf - -C / -T $K/MP4_LIST.txt | pv -q -L 8m | tar xf - -C /scratch/jjyeung/k1/src
echo "T2 copy rc=$? $(date -u +%FT%TZ)" >> $W/T2.log
nice python3 $K/verify_mp4.py $K/D12_MP4S.json /scratch/jjyeung/k1/src >> $W/T2.log 2>&1
echo "T2 verify rc=$? $(date -u +%FT%TZ)" >> $W/T2.log
