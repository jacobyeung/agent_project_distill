#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa
python3 -B - $R/inputs/data_receipt.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
for k,v in d.items():
  s=json.dumps(v); print(k, s[:300] if len(s)<=300 else s[:300]+' ...(%d)'%len(s))
PY
echo "== job.sh c0/log lines"; grep -n -E "c0|exec|>>|2>|LOG|log" $KH/job.sh | cut -c1-250 | head -40
ls -la $KH | head -30
