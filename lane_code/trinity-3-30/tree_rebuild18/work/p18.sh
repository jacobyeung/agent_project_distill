W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; nice -n 10 python3 - <<'PY'
import json
c=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/cov24c1/n_c.decoded.json'))
s=c.get('s1_routing',{}); print('sel',json.dumps(s.get('selection'))[:300]); print('keys',list(s.keys()))
print('remove_files',[ (r.get('sha256','')[:8] if isinstance(r,dict) else str(r)[:60]) for r in c.get('remove_files',[])])
print('streams.routing',json.dumps(c['streams'].get('routing'))[:400])
print('routing_slices',c.get('routing_slices'), [k for k in c if 'rout' in k])
PY
G=$W/w24g/work/build24m4g/EVIDENCE.json; nice -n 10 python3 -c "
import json;d=json.load(open('$G'));print(list(d.keys())[:40])
for k in d:
  if 'n_' in k.lower() or 'N' in k: print(k, json.dumps(d[k])[:600])
" | head -30
