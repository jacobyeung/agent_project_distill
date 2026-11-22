import sys, json, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
items,objects,_=G.eligible(R,refs)
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
pool={}; diff=0; same=0
for it in items:
    for o in rows[it['item_id']]['objects']:
        k=(it['capture'],o['name'].strip().lower())
        if k in pool:
            a=[(q['frame'],q['score'],q['presence']) for q in pool[k]['proposals']]; b=[(q['frame'],q['score'],q['presence']) for q in o['proposals']]
            if a!=b: diff+=1
            else: same+=1
        else: pool[k]=o
print('repeat (capture,name) pools identical',same,'different',diff)
names_in_rows=set((it['capture'],o['name'].strip().lower()) for it in items for o in rows[it['item_id']]['objects'])
ops=set((o['capture'],o['name'].strip().lower()) for o in objects)
print('row objects not operands', len(names_in_rows-ops))
