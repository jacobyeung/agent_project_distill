#!/bin/bash
D=$1; cd $D; date -u +%FT%TZ > r.txt; hostname >> r.txt; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader >> r.txt 2>&1; free -g | sed -n 2p >> r.txt; ulimit -v >> r.txt
for P in /project/community/jjyeung/distill/*/env/bin/python; do
  echo "== $P" >> r.txt
  for c in none lim mask both restore fixed maskcount; do timeout 180 $P -I -s -B $D/t.py $c >> r.txt 2>> e.txt; echo "rc $c $?" >> r.txt; done
done
date -u +%FT%TZ >> r.txt
