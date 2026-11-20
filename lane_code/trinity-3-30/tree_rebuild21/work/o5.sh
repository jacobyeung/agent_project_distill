export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173725; O=$X/o/$J; cd $O
python3 - <<'PY'
import json
t=json.load(open('timings.json')); print('timings keys', sorted(t))
for k in sorted(t):
    if k not in ('chain','files'): print(k, json.dumps(t[k])[:600])
p=json.load(open('proc_check.json')); print('proc keys', sorted(p))
for k in p:
    if k!='rows': print('proc',k,json.dumps(p[k])[:400])
r=p['rows']; from collections import Counter
print('proc row status', Counter((x.get('n',{}).get('status'), x.get('p',{}).get('status'), x.get('status')) for x in r))
print('proc row keys', sorted(r[0]))
c=json.load(open('cand_cmp.json')); print('cand', json.dumps({k:v for k,v in c.items() if k not in ('source_fields',)})[:1500])
PY
cat rd.log.tail; echo; tail -45 $X/j/$J.log | cut -c1-400; tail -20 $X/j/$J.err 2>/dev/null | cut -c1-300
