K=/scratch/jjyeung/orch_n30/nvkey1/work
echo 500000 > $K/ctl/BPS
date -u +%T; tail -2 $K/runner.log; cat $K/meter/METER.json; wc -l $K/out/2*.jsonl $K/out/3*.jsonl $K/out/41*.jsonl 2>/dev/null
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, time
K='/scratch/jjyeung/orch_n30/nvkey1/work'; now=time.time(); b=0; n=0
for l in open(K+'/meter/CALLS.jsonl'):
    r=json.loads(l); t=time.mktime(time.strptime(r['utc'],'%Y-%m-%dT%H:%M:%SZ'))-time.timezone
    if now-t<600: b+=r.get('bytes',0); n+=1
print('last 10 min: calls', n, 'MB', round(b/1e6,1), 'MB/s', round(b/600/1e6,3))
PY
