import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
e=n=0
for r in rows.values():
    for o in r['objects']:
        for q in o['proposals']:
            n+=1; e+= not R.unrle(q['mask']).any()
print('proposals',n,'empty masks',e)
