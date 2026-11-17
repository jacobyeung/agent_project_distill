PN=/project/community/jjyeung/okh7/e6fc152498/p446
grep -n "def program_decision" -A25 $PN/h1eval/scorers.py | head -40
grep -n "def answer_equals" -A10 $PN/h1eval/scorers.py | head -14
python3 - <<'PYEOF'
import json,collections,re
P='/project/community/jjyeung/okh7/e6fc152498/p446/items/devs1_routed.json'
M=json.load(open(P)); by={r['id']:r for r in M['items']}
r=by['vsi590k_042613']; print({k:(str(v)[:300]) for k,v in r.items() if k not in ('frames',)})
F='/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
R=[json.loads(l) for l in open(F)]
u=collections.Counter()
for x in R:
    if x['mode']!='none': continue
    q=json.dumps(by[x['id']]).lower()
    unit=next((w for w in ('centimet','inch','feet','foot','meter','metre') if w in q),'?')
    clean=not any('not seen' in (c.get('response') or '') for c in x['output']['calls']['records'])
    u[(unit,clean)]+=1; u[(unit,clean,'acc')]+=x['measurements']['M2']['task_accuracy']
for k in sorted(u,key=str): print(k, round(u[k],2))
x=next(x for x in R if x['id']=='vsi590k_042613' and x['mode']=='none'); print(repr(x['output']['text'][-500:])); print(x['measurements']['M2'])
PYEOF
