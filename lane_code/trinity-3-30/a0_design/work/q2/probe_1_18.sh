#!/bin/bash
set -u
echo "=== host $(hostname -s) $(date -u +%FT%TZ)"
for d in /scratch/jjyeung/devs1_mask_run /scratch/jjyeung/devs1_mask_run/kit /scratch/jjyeung/orch_cd/devs1_masks /scratch/jjyeung/orch_cd/devs1_masks/out /scratch/jjyeung/orch_cd/devs1_price/out /scratch/jjyeung/orch_cd/evalx /scratch/jjyeung/orch_cd/devs1_direct/out; do
  echo "=== ls $d"; ls -la "$d" 2>&1 | head -60
done
ROOTS="/scratch/jjyeung/devs1_mask_run /scratch/jjyeung/orch_cd/devs1_masks /scratch/jjyeung/orch_cd/devs1_price /scratch/jjyeung/orch_cd/evalx /scratch/jjyeung/k1 /scratch/jjyeung/mask_recall_run"
echo "=== find"
timeout 60 find $ROOTS -maxdepth 5 -type f \( -iname '*ROUTE*' -o -iname 'PER_ITEM*' -o -iname '*pairs*.jsonl*' -o -iname 'PRICE_DEVS1*' \) -printf '%s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | grep -v '\.py$' | head -80
echo "=== merge results"
head -80 /scratch/jjyeung/orch_cd/devs1_direct/out/r5/MERGE_RESULTS.md 2>&1
P=$(timeout 60 find $ROOTS -maxdepth 5 -type f -name 'ROUTE_PREDICTED.pairs.jsonl' 2>/dev/null | head -1)
if [ -n "$P" ] && [ "$(stat -c %s "$P")" -lt 15000000 ]; then
  echo "=== PAIRS $P"; gzip -c "$P" | base64 -w0; echo; echo "=== END PAIRS"
  for f in "$(dirname "$P")/ROUTE_PREDICTED.md" "$(dirname "$P")/ROUTE_PREDICTED.json"; do
    if [ -f "$f" ] && [ "$(stat -c %s "$f")" -lt 3000000 ]; then echo "=== FILE $f"; gzip -c "$f" | base64 -w0; echo; echo "=== END FILE"; fi
  done
  T=/scratch/jjyeung/orch_cd/devs1_direct/out/TASKS.jsonl
  echo "=== TASKS $T"; gzip -c "$T" | base64 -w0; echo; echo "=== END TASKS"
else
  echo "=== NO PAIRS FILE FOUND"
fi
echo "=== done $(date -u +%FT%TZ)"
