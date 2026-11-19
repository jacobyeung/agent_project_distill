#!/bin/bash
# swarm_opt4: progress and sha check of the trinity-2-28 pulls (local reads only)
R=/scratch/jjyeung/orch_n30/reads228; D=$R/dl; date -u +%FT%TZ; ls -l $D | grep -v log
for f in $D/*.log; do echo "${f##*/}: $(tail -1 $f)"; done
while read -r n p b s; do [[ -f $D/$n.sha_ok ]] && { echo "$n SHA_OK"; continue; }
  if [[ $(stat -c %s $D/$n 2>/dev/null) == $b ]]; then got=$(nice -n 10 sha256sum $D/$n | cut -d' ' -f1); [[ $got == $s ]] && { touch $D/$n.sha_ok; echo "$n SHA_OK"; } || echo "$n SHA_BAD $got"; fi; done < $R/r228/PINS.txt
grep -E "Node agents|r228" /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | cut -c1-260
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; uptime
