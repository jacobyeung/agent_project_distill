import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever7/gtcd/kit')
import gtc_common as G
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
row=next(iter(rows.values()))
print('audit',json.dumps(row['audit'],default=str)[:3000])
print('memo',json.dumps(row['perception_memo'],default=str)[:1500])
print('timings',json.dumps(row['timings'],default=str)[:800])
print('geometry keys',list(row['geometry'].keys()))
from collections import Counter
cnt=Counter(); prompts=Counter(); mx=0
for r in rows.values():
    for o in r['objects']:
        fr=Counter(p['frame'] for p in o['proposals']); mx=max([mx]+list(fr.values()))
        for p in o['proposals']: prompts[(p['prompt']==o['name'])]+=1
        jmin=min([float(p['score'])*float(p['presence']) for p in o['proposals']] or [1])
        cnt['objs']+=1; cnt['props']+=len(o['proposals'])
        if jmin<0.05: cnt['below05']+=1
print(cnt, prompts, 'max per frame',mx)
