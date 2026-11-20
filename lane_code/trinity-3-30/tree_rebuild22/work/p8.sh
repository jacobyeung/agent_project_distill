D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173796/173796; cd $D; date -u +%TZ
cat nd.json; echo; cat routing_types.json; echo; cat rd.log.tail; echo
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
c=json.load(open('chain.json'))
r=c.get('routing',{}); print('ROUTING', json.dumps({k:v for k,v in r.items() if k!='samples'})[:3000])
for k in c:
  if k not in ('routing','population','candidate'): print('C',k, json.dumps(c[k])[:1500])
t=json.load(open('timings.json')); print('T', json.dumps({k:t[k] for k in t if k not in ('chain','files','publication_selection')})[:2500])
p=json.load(open('proc_check.json')); print('PROC', p.get('status'), p.get('n_tree'))
PY
grep -n "Error\|REFUS\|FAIL\|Traceback\|E9[0-9]" job.log | grep -v '{"source\|remove_list' | tail -20 | cut -c1-400
