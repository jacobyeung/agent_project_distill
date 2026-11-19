K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1
cat > /tmp/tr14_dec.py <<'PY'
import json,base64,sys
d=json.load(open(sys.argv[1]))
c=json.loads(base64.b64decode(d['payload'])) if 'payload' in d else d
keys=sys.argv[2].split(',')
def show(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items():
      kk=p+'.'+k if p else k
      if any(s in k.lower() for s in keys): print(kk, json.dumps(v)[:400])
      elif isinstance(v,dict): show(v,kk)
show(c)
PY
nice -n 10 python3 -B /tmp/tr14_dec.py $K/k/c.json output,recipe,milestone,checkpoint,stop,steps,persist,durable,upload,init,schedule,wall,resume,training_mode,world </dev/null | cut -c1-400 | head -60
sed -n 1,30p $T/launch_r2/persistence.py </dev/null | cut -c1-200
sed -n 60,125p $T/launch_r2/persistence.py </dev/null | cut -c1-200
