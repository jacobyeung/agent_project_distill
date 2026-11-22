#!/bin/bash
# Poll trinity-0-13 every 5 min for a card with <=100 MiB used; exit when found or after $1 seconds.
end=$(( $(date +%s) + ${1:-3000} ))
while [ $(date +%s) -lt $end ]; do
  r=$(timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-0-13.ib 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits' 2>&1)
  echo "$(date -u +%H%MZ) $(echo $r | tr '\n' ' ')" >> /scratch/jjyeung/orch_n30/lever8/work/cardwait.log
  f=$(echo "$r" | awk -F', ' '$2+0<=100{print $1}' | head -1)
  [ -n "$f" ] && { echo "$(date -u +%H%MZ) free card $f: $r"; exit 0; }
  sleep 300
done
echo "$(date -u +%H%MZ) no free card"
