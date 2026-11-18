#!/bin/bash
# r1_ops4: read-only compact per-step summary of 171377 metrics (no raw rows leave Orchard).
set +x; set -uo pipefail; export TZ=UTC
R=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f
date -u +%FT%TZ; ls -la --time-style=+%H:%M:%S $R | awk '{print $5,$6,$7}' | tail -n +4
ls -la --time-style=+%H:%M:%S /project/community/jjyeung/okh7/x_69d2930d/o/ | grep -i -E 'gcs|m100|m200' | awk '{print $5,$6,$7}'
python3 -B - "$R/metrics_171377.jsonl" <<'PYCODE'
import json,sys,math
rows=[]
with open(sys.argv[1],'rb') as f:
  for line in f:
    if not line.endswith(b'\n'): break
    rows.append(json.loads(line))
tot={}
for r in rows:
  ks=r['ranks']; st={s:sum(k['stream_means'].get(s,float('nan')) for k in ks)/len(ks) for s in ('pose','vqa','routing','pointing')}
  sk=sum(len(k['skipped_microsteps']) for k in ks); nf=any(not math.isfinite(v) for v in st.values())
  for k in ks:
    for t,v in k['h1'].items():
      a=tot.setdefault(t,[0,0,0,0]); a[0]+=v['gt'];a[1]+=v['pose_supervised'];a[2]+=v['pose_missing'];a[3]+=v['own']
  print(r['step'], round(ks[0]['wall_seconds']), ' '.join('%s=%.4f'%(s,v) for s,v in st.items()), 'skip=%d'%sk, 'NONFINITE' if nf else '', 'gn=%s'%json.dumps(ks[0].get('gradient_norms'))[:80])
print('h1 totals gt/sup/miss/own', json.dumps(tot))
PYCODE
