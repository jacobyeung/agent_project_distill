#!/bin/bash
# n_ops8 (ORCH RULING 2152Z item 4): stop the watcher's Orchard calls if any raw check shows a host-key warning
M=/scratch/jjyeung/orch_n30/n_ops1/work/mon; A=/scratch/jjyeung/orch_n30/n_ops8/work/HOSTKEY_ALERT; seen=""
while true; do
  f=$(ls -t $M/raw/*.raw 2>/dev/null | head -1)
  if [[ -n $f && $f != $seen ]]; then seen=$f
    if grep -q -E 'IDENTIFICATION HAS CHANGED|Host key verification failed|POSSIBLE DNS SPOOFING|key for .* has changed' $f; then
      touch $M/stop; { date -u +%FT%TZ; echo "$f"; grep -E -i 'fingerprint|host key|IDENTIFICATION|SHA256:' $f | head -8; } > $A; exit 0; fi
  fi
  sleep 15
done
