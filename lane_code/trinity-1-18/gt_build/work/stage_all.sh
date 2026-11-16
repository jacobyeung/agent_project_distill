#!/bin/bash
# Three governed streams in turn (ScanNet, ARKit, ScanNet++); verify each before the next; stop on any failure.
W=/scratch/jjyeung/orch_n30/gt_build/work; S=/scratch/jjyeung/orch_n30/gt_build/stage; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams
run() { # lane root list dest bytes [json]
  /usr/bin/python3 -s $W/launch.py $1 $2 $W/$3 $4 $5 || { echo "STREAM_FAIL $1 $(date -u +%FT%TZ)"; exit 1; }
  python3 $W/verify_stage.py $W/$3 $4 $W/SIZES_$1.tsv $6 || { echo "VERIFY_FAIL $1 $(date -u +%FT%TZ)"; exit 1; }
  mv $G/$1.json $G/$1.done.$(date +%s) && echo "DONE $1 $(date -u +%FT%TZ)"
}
run gt_build_scannet / LIST_scannet.txt $S/scannet 136000000 $W/LIST_scannet.json
run gt_build_arkit /data3/shared/datasets/arkitscenes/3dod/Training LIST_arkit.txt $S/arkit 200000000
run gt_build_scannetpp / LIST_scannetpp.txt $S/scannetpp 3323000000 $W/LIST_scannetpp.json
echo "STAGE_ALL_OK $(date -u +%FT%TZ)"
