import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever7/gtcd/kit')
import gtc_common as G
from collections import Counter
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
r=next(iter(refs.values())); print(sorted(r.keys())); print({k:str(v)[:200] for k,v in r['task'].items()}); print(sorted(r['mapping'].keys()))
items,objects,gtp=G.eligible(R,refs)
print(len(items),len(objects))
names=Counter(o['name'] for o in objects); print(len(names), names.most_common(8)); print('heater', names.get('heater'))
caps=sorted({i['capture'] for i in items})
u=Counter(); 
for c in caps: u[c]=len({o['name'].strip().lower() for o in objects if o['capture']==c})
print('unique names per cap total',sum(u.values()), min(u.values()), max(u.values()))
print('inst per cap total', sum(len({o['instance_id'] for o in objects if o['capture']==c}) for c in caps))
print(Counter(refs[i['item_id']]['task'].get('question_type') for i in items))
f=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
print(Counter(tuple(c['hw']) for c in f['captures']))
