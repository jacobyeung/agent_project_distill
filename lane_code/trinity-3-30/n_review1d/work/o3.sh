cd /project/community/jjyeung/okh7/x_22c714e1/o/173626 || exit 1
date -u +%TZ; tail -c 2500 r.log; echo; echo "@@@ q.steps"; tail -8 q.steps
python3 - <<'PY'
import json
v=json.load(open('refresh.json'))
def short(x,d=0):
    if isinstance(x,dict): return {k:(short(v,d+1) if d<2 else '...') for k,v in list(x.items())[:40]}
    if isinstance(x,list): return [short(v,d+1) for v in x[:3]]+(['...%d'%len(x)] if len(x)>3 else [])
    return x
print(json.dumps(short(v))[:5000])
PY
