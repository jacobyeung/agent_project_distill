#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa; P=$R/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
ls -la $P/vqa $P/prepared | awk '{print $5,$9}'
sha256sum $P/prepared/type_mix.json
python3 -B - $P/prepared/type_mix.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
def shape(x,dep=0):
  if isinstance(x,dict): return {a:shape(b,dep+1) for a,b in list(x.items())[:25]} if dep<3 else 'dict%d'%len(x)
  if isinstance(x,list): return ['list%d'%len(x), shape(x[0],dep+1) if x else None]
  return str(x)[:60]
print(json.dumps(shape(d))[:4000])
PY
