#!/bin/bash
# One allocation runs the six parts in order: general_qos allows 5 submitted and 1 running job per user,
# so the 6-task array cannot be submitted. Each part gets its own job tag (djob.sh keys /tmp and logs on it).
R=/project/community/jjyeung/okh7/db3954b2; mkdir -p $R/logs; G=$R/logs/dserial.${SLURM_JOB_ID:-x}.log
for i in 0 1 2 3 4 5; do
  K=$([ $i -lt 3 ] && echo a || echo v)
  echo "task $i $K$((i % 3)) start $(date -u +%FT%TZ)" >> $G
  SLURM_JOB_ID=${SLURM_JOB_ID:-x}t$i $R/bin/djob.sh $K $((i % 3)) 3 16
  echo "task $i rc $? end $(date -u +%FT%TZ)" >> $G
done
