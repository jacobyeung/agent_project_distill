#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa
date -u +%FT%TZ; wc -l $KH/o/172660.err
grep -n -v -E "cgroup|TORCH_NCCL_AVOID|fast path is not|Loading weights|FutureWarning: FSDP|set_state_dict_type|^  " $KH/o/172660.err | tail -15 | sed -E 's#https?://[^ "]+#[URL]#g' | cut -c1-300
echo "== gpu"; cat $KH/o/172660.gpu
echo "== run"; ls -la --time-style=+%T $R $R/inputs | grep -v total | awk '{print $5,$6,$7}'
ls $R/metrics_*.jsonl 2>/dev/null && wc -l $R/metrics_*.jsonl
echo "== A first rows wall"; head -4 $O/x_69d2930d/runs/673bc60f/metrics_171377.jsonl | python3 -c "
import json,sys
for l in sys.stdin:
  r=json.loads(l); k=r['ranks'][0]; print(r['step'], round(k['wall_seconds']), round(k.get('data_seconds',0)), round(k.get('checkpoint_seconds',0)), round(k.get('export_seconds',0)))"
echo "== C rows"; python3 -c "
import json,sys
for l in open(sys.argv[1],'rb'):
  r=json.loads(l); k=r['ranks'][0]; print(r['step'], round(k['wall_seconds']), round(k.get('data_seconds',0)), round(k.get('checkpoint_seconds',0)), round(k.get('export_seconds',0)))" $R/metrics_172660.jsonl
