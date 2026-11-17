import json,collections
F='f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
R=[json.loads(l) for l in open(F)]
print(len(R))
r=[x for x in R if x['mode']=='none' and any('not seen' in (c.get('response') or '') for c in x['output']['calls']['records'])][0]
print(json.dumps({k:v for k,v in r.items() if k!='output'},indent=1)[:3000])
o=r['output']
print(o['text'][:3000])
for c in o['calls']['records']: print(json.dumps(c)[:1500])
print(o.keys())
