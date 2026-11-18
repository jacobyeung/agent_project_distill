#!/bin/bash
# prints event files newer than marker c14_mark in r1_ops, reader_r1, cont_ops (non-STATUS) and inbox; then touches marker
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events; M=/scratch/jjyeung/orch_n30/cont_ops/work/c14_mark
date -u +%TZ
for d in $E/r1_ops $E/reader_r1 $E/cont_ops /scratch/jjyeung/orch_n30/cont_ops/inbox; do
  for f in $(ls -t $d 2>/dev/null | head -15); do [ "$d/$f" -nt $M ] && [ "$f" != STATUS.md ] && echo "NEW $d/$f"; done
done
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/ | grep INBOX_TO_DISTILL_ORCH | head -1
touch $M
