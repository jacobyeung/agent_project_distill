T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; cd $T
sed -n 2322,2360p student_pilot/carrier_c1_run.py </dev/null | cut -c1-200
sed -n 2425,2492p student_pilot/carrier_c1_run.py </dev/null | cut -c1-200
grep -n -E "^def milestone|gsutil|gcs|upload|marker|print" launch_r2/persistence.py </dev/null | head -30 | cut -c1-200
nice -n 10 python3 -B - <<'PY' </dev/null
import json,base64
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go/k/c.json'))
c=json.loads(base64.b64decode(d['payload'])) if 'payload' in d else d
def show(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items():
      kk=p+'.'+k if p else k
      if any(s in kk.lower() for s in ('output','recipe','milestone','checkpoint','stop','steps','persist','export','lr','warmup','schedule','gcs','timing','init')):
        s=json.dumps(v)
        print(kk, s[:300])
      elif isinstance(v,dict): show(v,kk)
show(c)
PY
