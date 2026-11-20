cd /project/community/jjyeung/cp4tk_fr/k6tk && cat INDEX.json | head -c 2400; echo; cat RECEIPT.json | head -c 2400; echo
python3 -c "
import json; d=json.load(open('SCENES.json')); print(type(d).__name__, len(d))
if isinstance(d,dict):
    ks=list(d)[:5]; print(ks); [print(k, json.dumps(d[k])[:400]) for k in ks]
else: print(json.dumps(d[:3])[:1200])
"
zcat MAP.jsonl.gz | python3 -c "
import sys,json,collections
c=collections.Counter(); s=collections.defaultdict(set)
for l in sys.stdin:
    r=json.loads(l); c[r['d']]+=1; s[r['d']].add(r['s'])
print({k:(v,len(s[k])) for k,v in c.items()})
"
