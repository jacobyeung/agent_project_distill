export TZ=UTC
K=/project/community/jjyeung/okh7/x_c5f3847d/o
squeue -u $USER -o '%i %j %P %T %M %R'
sacct -j 170885 -X -o JobID,State,ExitCode,Elapsed,End -P 2>/dev/null | tail -2
ls -la $K | grep 170885
python3 - <<'PY'
import json
d=json.load(open('/project/community/jjyeung/okh7/x_c5f3847d/o/170885.proof.json'))
def show(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items():
      if k in('files','members','sha256s'): continue
      if isinstance(v,(dict,list)) and len(json.dumps(v))>300: print(p+k,':'); show(v,p+'  ')
      else: print(p+k,':',json.dumps(v)[:300])
  elif isinstance(x,list):
    for i,v in enumerate(x[:40]): show(v,p+'[%d] '%i) if isinstance(v,(dict,list)) else print(p+'[%d]'%i,json.dumps(v)[:300])
show(d)
PY
echo ==== LOGTAIL; tail -60 $K/170885.proof.log 2>/dev/null | cut -c1-400
echo ==== ERR; tail -30 $K/170885.err | cut -c1-400
