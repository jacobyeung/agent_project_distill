#!/bin/bash
# Follow-on pipeline for the governed streams (runs in tmux b10pipe on trinity-1-18). Never restarts a stream.
L=/scratch/jjyeung/orch_n30/b10_reserve; S=/data3/jjyeung/orch_n13_20261026/io_governor/streams; PY=/scratch/jjyeung/envs/p1cpu/bin/python
cd $L; export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
done_rename() {  # $1 = list name; rename the record once its log shows a clean exit
  local n=$1
  if grep -q "^EXIT (0, 0, 0)" work/streams/$n.log 2>/dev/null && [ -f $S/b10r0_$n.json ]; then
    mv $S/b10r0_$n.json $S/b10r0_$n.done.$(date +%s); echo "$(date -u +%FT%TZ) renamed b10r0_$n" >> work/pipeline.log
  fi
  if grep -q "^EXIT" work/streams/$n.log 2>/dev/null && ! grep -q "^EXIT (0, 0, 0)" work/streams/$n.log; then
    echo "$(date -u +%FT%TZ) STREAM FAILED $n (no restart)" >> work/pipeline.log; touch work/STREAM_FAILED_$n
  fi
}
gen_done=0
while true; do
  for n in gt vid_dev vid_rl; do done_rename $n; done
  if [ $gen_done = 0 ] && grep -q "^EXIT (0, 0, 0)" work/streams/gt.log 2>/dev/null; then
    echo "$(date -u +%FT%TZ) gen start" >> work/pipeline.log
    nice -n 10 $PY -W ignore code/run_scenes.py gen --workers 12 >> work/pipeline.log 2>&1
    nice -n 10 $PY -W ignore code/aggregate.py out/questions out/qsets > work/aggregate.log 2>&1
    echo "$(date -u +%FT%TZ) gen+aggregate done" >> work/pipeline.log; gen_done=1
  fi
  if grep -q "^EXIT (0, 0, 0)" work/streams/gt.log 2>/dev/null; then
    nice -n 10 $PY -W ignore code/run_scenes.py decode --workers 8 >> work/pipeline.log 2>&1
  fi
  if grep -q "^EXIT" work/streams/vid_rl.log 2>/dev/null && grep -q "^EXIT" work/streams/vid_dev.log 2>/dev/null && [ $gen_done = 1 ]; then
    nice -n 10 $PY -W ignore code/run_scenes.py decode --workers 8 >> work/pipeline.log 2>&1
    nice -n 10 $PY -W ignore code/check_redecode.py 2 >> work/pipeline.log 2>&1
    echo "$(date -u +%FT%TZ) pipeline finished" >> work/pipeline.log; break
  fi
  sleep 300
done
