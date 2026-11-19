#!/bin/bash
export TZ=UTC; KH=/project/community/jjyeung/okh7/x_ee227714
date -u +%FT%TZ; wc -l $KH/o/172660.err; awk 'NR>=455' $KH/o/172660.err | grep -v cgroup | cut -c1-220 | sed -E 's#https?://[^ "]+#[URL]#g' | uniq -c | tail -40
ls -la --time-style=+%T $KH/runs/6ed2c7aa/metrics_172660.jsonl
squeue -j 172660 -o '%i %T %M' ; sstat -j 172660.batch --format=JobID,AveCPU,MaxRSS -P 2>&1 | tail -2
