#!/bin/bash
# Build each batch as soon as its stream is staged and verified (DONE line); then pin check.
W=/scratch/jjyeung/orch_n30/gt_build/work; L=/scratch/jjyeung/orch_n30/gt_build/logs; PY=/scratch/jjyeung/envs/p1cpu/bin/python
declare -A done_; todo="scannet arkit scannetpp"
while [ -n "$todo" ]; do
  for b in $todo; do
    f=$L/$b.log; [ $b = scannet ] && f=$L/finish_scannet.log
    if grep -q "FAIL" $f 2>/dev/null; then echo "SKIP $b (stream failed) $(date -u +%FT%TZ)"; todo=${todo/$b/}; continue; fi
    if grep -q "^DONE gt_build_$b " $f 2>/dev/null; then
      echo "BUILD $b start $(date -u +%FT%TZ)"
      if [ $b = arkit ]; then $PY $W/build_all.py arkit 24; $PY $W/build_all.py arkit_t10 24; else $PY $W/build_all.py t1 24 $b; fi
      echo "BUILD $b end $(date -u +%FT%TZ)"; todo=${todo/$b/}
      python3 $W/pin_check.py
    fi
  done
  todo=$(echo $todo); [ -n "$todo" ] && sleep 60
done
echo "AUTO_BUILD_END $(date -u +%FT%TZ)"
