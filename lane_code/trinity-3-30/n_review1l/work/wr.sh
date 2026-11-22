#!/bin/bash
# Wait up to $1 s for WAITING_REVIEW (or job end) in the local watcher history; checks every 60 s.
H=/scratch/jjyeung/orch_n30/n_ops1/work/mon/hist.txt
end=$(( $(date +%s) + ${1:-570} ))
while [ $(date +%s) -lt $end ]; do
  l=$(tail -1 $H)
  if echo "$l" | grep -q 'WAITING_REVIEW\|"stage":"waiting\|"stage":"review\|FAILED\|COMPLETED\|CANCELLED'; then date -u +%TZ; echo "$l" | cut -c1-400; exit 0; fi
  sleep 60
done
date -u +%TZ; tail -1 $H | grep -o '"stage":"[^"]*"\|"elapsed":"[^"]*"' | tr '\n' ' '; echo NONE
