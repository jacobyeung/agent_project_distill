#!/bin/bash
# r1_ops6: read-only compact per-step summary of C' (job 172660, run 6ed2c7aa) metrics; no raw rows leave Orchard.
set +x; set -uo pipefail; export TZ=UTC
K=/project/community/jjyeung/okh7/x_ee227714; R=$K/runs/6ed2c7aa
date -u +%FT%TZ; ls -la --time-style=+%H:%M:%S $R 2>&1 | awk '{print $5,$6,$7}' | tail -n +4
F=$(ls $R/metrics_*.jsonl 2>/dev/null | head -1); [[ -n "$F" ]] || { echo NO_METRICS; exit 0; }
python3 -B - "$F" <<'PYCODE'
import json,sys,math
rows=[]
with open(sys.argv[1],'rb') as f:
  for line in f:
    if not line.endswith(b'\n'): break
    rows.append(json.loads(line))
tot={}
for r in rows:
  ks=r['ranks']; st={s:sum(k['stream_means'].get(s,float('nan')) for k in ks)/len(ks) for s in ('pose','vqa','routing','pointing')}
  for k in ks:
    for t,v in k['h1'].items():
      a=tot.setdefault(t,[0,0,0,0]); a[0]+=v['gt'];a[1]+=v['pose_supervised'];a[2]+=v['pose_missing'];a[3]+=v['own']
  print('STEP',json.dumps(dict(step=r['step'],wall=round(ks[0]['wall_seconds']),skip=sum(len(k['skipped_microsteps']) for k in ks),**st)))
print('H1TOT',json.dumps(tot))
PYCODE
echo "== small files"
for f in $R/attempt_172660.json $R/binding.json $R/inputs/first_step_172660.json; do echo "=== $f"; sha256sum $f; cat $f; echo; done
