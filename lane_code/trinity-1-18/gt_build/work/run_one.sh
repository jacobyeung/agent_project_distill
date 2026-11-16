#!/bin/bash
# One governed stream: launch (register, wait) -> verify -> rename record. No retry. usage: run_one.sh LANE ROOT LIST DEST BYTES [LIST_JSON]
W=/scratch/jjyeung/orch_n30/gt_build/work; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams
/usr/bin/python3 -s $W/launch.py $1 $2 $W/$3 $4 $5 || { echo "STREAM_FAIL $1 $(date -u +%FT%TZ)"; exit 1; }
python3 $W/verify_stage.py $W/$3 $4 $W/SIZES_$1.tsv $6 || { echo "VERIFY_FAIL $1 $(date -u +%FT%TZ)"; exit 1; }
mv $G/$1.json $G/$1.done.$(date +%s) && echo "DONE $1 $(date -u +%FT%TZ)"
