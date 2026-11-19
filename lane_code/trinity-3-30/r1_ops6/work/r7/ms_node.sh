#!/bin/bash
# r1_ops7: compact per-step summary from 172660's node-local metrics (read-only srun step)
export TZ=UTC; date -u +%FT%TZ
cat > /dev/null <<'NOTE'
NOTE
timeout 120 srun --overlap --jobid 172660 -n1 -N1 timeout 90 nice -n 19 bash -s < /dev/stdin <<'INNER' 2>&1 | cut -c1-400
F=/tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa/metrics_172660.jsonl
ls -la --time-style=+%T $F; ls -d /tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa/checkpoint_* /tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa/m* 2>/dev/null
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
INNER
echo "srun rc=$?"
