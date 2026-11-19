#!/bin/bash
# swarm_opt5: sha check of the 8 input + 13 runtime pulls on trinity-2-28 (local reads only)
R=/scratch/jjyeung/orch_n30/reads228; D=$R/dl; date -u +%FT%TZ
for n in $(cut -d' ' -f1 $R/r228/PINS_R.txt); do echo "$n: $(tail -1 $D/$n.log 2>/dev/null | cut -c1-160)"; done
cat $R/r228/PINS_FINAL.txt $R/r228/PINS_R.txt | while read -r n p b s; do [[ -f $D/$n.sha_ok ]] && continue
  if [[ $(stat -c %s $D/$n 2>/dev/null) == $b ]]; then got=$(nice -n 10 sha256sum $D/$n | cut -d' ' -f1); [[ $got == $s ]] && { touch $D/$n.sha_ok; echo "$n SHA_OK"; } || echo "$n SHA_BAD $got"; else echo "$n size $(stat -c %s $D/$n 2>/dev/null) of $b"; fi; done
grep -E "r228" /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | cut -c1-200
ok=0; for n in $(cat $R/r228/PINS_FINAL.txt $R/r228/PINS_R.txt | cut -d' ' -f1); do [[ -f $D/$n.sha_ok ]] && ok=$((ok+1)); done; echo "sha_ok $ok of 21"
if [ "$ok" = 21 ]; then G=/data3/jjyeung/orch_n13_20261026/io_governor/streams; for n in $(cut -d' ' -f1 $R/r228/PINS_R.txt); do f=$G/swarm_opt_r228_$n.json; [ -f $f ] && mv $f $G/swarm_opt_r228_$n.done.$(date +%s) && echo "done-renamed $n"; done
  ssh -o ControlPath='/tmp/cm-n30-orchard-%r' -O exit orchard 2>&1; pgrep -af "gov_stream2|ratelimit" | head -3; fi
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; uptime; df -h /scratch | tail -1
