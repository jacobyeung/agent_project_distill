#!/bin/bash
# one monitor poll: curl, parse, write FREE_CARDS.md, append ledger
cd /scratch/jjyeung/orch_n30/gpu_fill
T=$(date -u +%Y%m%dT%H%MZ)
timeout 60 curl -s -m 50 http://trinity.vision.cs.cmu.edu:53240/ -o mon.html || { echo "$T curl_fail" >> ledger.txt; exit 1; }
python3 parse.py mon.html hist/$T.json > hist/$T.txt
FC=$(head -1 hist/$T.txt)
echo "$T free_big_permitted=$FC" >> ledger.txt
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/gpu_fill
# one batched reading of trinity-1-13 per tick (cards + /dev/shm total), ORCH 1504Z
timeout 180 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh trinity-1-13 'bash -s' < read_shm.sh > hist/s113_$T.txt 2>&1
SL=$(python3 shm_line.py hist/s113_$T.txt 2>/dev/null || echo "Reading trinity-1-13 failed at $T")
{ echo "# Free 48 GB cards on permitted nodes (monitor page), $T"
  echo "Free = no process and >45 GB available. Excludes 0-8, 0-18, 0-23, 3-23, 2-18, 2-28. 'upd' is the monitor's EST stamp; stale rows unreliable."
  echo "Free cards total: $FC"
  tail -n +2 hist/$T.txt
  echo "$SL"
  [ -f notes.txt ] && cat notes.txt
} | head -40 > $E/FREE_CARDS.md
cat hist/$T.txt
