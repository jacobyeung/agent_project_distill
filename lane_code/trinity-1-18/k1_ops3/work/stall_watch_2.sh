#!/bin/bash
# Writes a line to /scratch/jjyeung/k1/STALL2.log whenever the run's output has not grown for 10 minutes.
OUT=/scratch/jjyeung/k1/run_tower_sam_2; last=-1; since=$(date +%s)
while true; do
  cur=$( (du -sb $OUT 2>/dev/null | cut -f1; stat -c %s /scratch/jjyeung/k1/RUN2.log 2>/dev/null) | awk "{s+=\$1} END {print s}")
  now=$(date +%s)
  if [ "$cur" != "$last" ]; then last=$cur; since=$now; elif [ $((now-since)) -ge 600 ]; then echo "$(date -u +%FT%TZ) STALL: no output growth for $(( (now-since)/60 )) min (bytes $cur)" >> /scratch/jjyeung/k1/STALL2.log; since=$now; fi
  grep -q '^EXIT' /scratch/jjyeung/k1/RUN2.log 2>/dev/null && { echo "$(date -u +%FT%TZ) run exited; watcher stops" >> /scratch/jjyeung/k1/STALL2.log; exit 0; }
  sleep 60
done
