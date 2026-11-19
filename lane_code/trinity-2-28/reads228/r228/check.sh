#!/bin/bash
# swarm_opt4: progress and sha check of the trinity-2-28 pulls (local reads only)
R=/scratch/jjyeung/orch_n30/reads228; D=$R/dl; date -u +%FT%TZ; ls -l $D | grep -v log
for f in $D/*.log; do echo "${f##*/}: $(tail -1 $f)"; done
while read -r n p b s; do [[ -f $D/$n.sha_ok ]] && { echo "$n SHA_OK"; continue; }
  if [[ $(stat -c %s $D/$n 2>/dev/null) == $b ]]; then got=$(nice -n 10 sha256sum $D/$n | cut -d' ' -f1); [[ $got == $s ]] && { touch $D/$n.sha_ok; echo "$n SHA_OK"; } || echo "$n SHA_BAD $got"; fi; done < $R/r228/PINS_FINAL.txt
grep -E "Node agents|r228" /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | cut -c1-260
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; uptime
ok=$(ls $D/*.sha_ok 2>/dev/null | wc -l); echo "sha_ok $ok of 8"
if [ "$ok" = 8 ]; then G=/data3/jjyeung/orch_n13_20261026/io_governor/streams; for n in s4e0 s4e0b s4e1 s4e2 s4e3 g0 a2 a4; do f=$G/swarm_opt_r228_$n.json; [ -f $f ] && mv $f $G/swarm_opt_r228_$n.done.$(date +%s) && echo "done-renamed $n"; done
  ssh -o ControlPath='/tmp/cm-n30-orchard-%r' -O exit orchard 2>&1; pgrep -af "gov_stream2|ratelimit" | head -3; fi
df -h /scratch | tail -1
