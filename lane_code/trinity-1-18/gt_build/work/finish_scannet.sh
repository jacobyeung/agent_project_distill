#!/bin/bash
# The ScanNet launcher (pid 94053) was started by stage_all.sh; wait for its exit line, then verify and rename.
W=/scratch/jjyeung/orch_n30/gt_build/work; G=/data3/jjyeung/orch_n13_20261026/io_governor/streams; L=/scratch/jjyeung/orch_n30/gt_build/logs/stage.log
while kill -0 94053 2>/dev/null; do sleep 30; done
grep -q "exit gt_build_scannet reader=0 ratelimit=0 tar=0" $L || { echo "STREAM_FAIL gt_build_scannet $(date -u +%FT%TZ)"; exit 1; }
python3 $W/verify_stage.py $W/LIST_scannet.txt /scratch/jjyeung/orch_n30/gt_build/stage/scannet $W/SIZES_gt_build_scannet.tsv $W/LIST_scannet.json || { echo "VERIFY_FAIL gt_build_scannet $(date -u +%FT%TZ)"; exit 1; }
mv $G/gt_build_scannet.json $G/gt_build_scannet.done.$(date +%s) && echo "DONE gt_build_scannet $(date -u +%FT%TZ)"
