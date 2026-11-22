import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G
from collections import Counter
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
bad=0; tot=0; order_bad=0
for r in rows.values():
    for o in r['objects']:
        fr={}
        for p in o['proposals']:
            f,i=p['id'].split(':'); assert f==str(p['frame']); fr.setdefault(int(f),[]).append((int(i),float(p['score'])))
        for f,l in fr.items():
            tot+=1
            if [i for i,_ in l]!=list(range(len(l))): bad+=1
            if [s for _,s in l]!=sorted([s for _,s in l],reverse=True): order_bad+=1
print('frames',tot,'noncontiguous',bad,'not score-sorted',order_bad)
