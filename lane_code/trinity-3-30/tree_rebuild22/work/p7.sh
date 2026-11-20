D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173796/173796; cd $D; date -u +%TZ
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
c=json.load(open('chain.json')); print(json.dumps(c)[:6000])
p=json.load(open('proc_check.json')); print('PROC', {k:v for k,v in p.items() if not isinstance(v,(list,dict))}, list(p)[:20])
n=json.load(open('nd.json')); print('ND', {k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in n.items()})
t=json.load(open('timings.json')); print('T', json.dumps({k:t[k] for k in t if k not in ('chain','files')})[:2500])
PY
grep -n "Error\|REFUS\|FAIL\|Traceback" job.log | grep -v '{"source\|remove_list' | tail -20 | cut -c1-400
cat rd.log.tail
