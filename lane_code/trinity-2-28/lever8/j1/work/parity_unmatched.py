import sys, json, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
d=G.read_json('rehearsal_cpu/scannet__scene0642_01.json.gz')
seen=set(); un=[]; fr_v3=0; fr_v2=0; n=0
for iid,row in rows.items():
    if row['capture']!='scannet/scene0642_01': continue
    for o in row['objects']:
        p=o['name'].strip().lower()
        if p not in d['text'] or p in seen: continue
        seen.add(p)
        for f in range(32):
            th=[(float(q['score']),float(q['score'])*float(q['presence']),R.unrle(q['mask'])) for q in o['proposals'] if int(q['frame'])==f+1]
            mi=[(e['score'],e['score']*e['presence'],G.unpack(e['mask'])) for e in d['text'][p][f]]
            M=np.array([[S.iou(a[2],b[2]) for b in th] for a in mi]) if mi and th else np.zeros((len(mi),len(th)))
            ui,uj=set(range(len(mi))),set(range(len(th)))
            for flat in np.argsort(-M,axis=None,kind='stable') if M.size else []:
                i,j=divmod(int(flat),M.shape[1])
                if i in ui and j in uj and M[i,j]>=.95: ui.discard(i); uj.discard(j)
            left=[('j1',)+mi[i][:2] for i in ui]+[('dump',)+th[j][:2] for j in uj]
            un+=left; n+=1
            fr_v3+= all(x[2]<.06 for x in left)
            fr_v2+= all(x[2]<.06 or x[1]<.3 for x in left)
print('frames',n,'V3 (unmatched only joint<0.06)',fr_v3,'V2 (unmatched joint<0.06 or score<0.3)',fr_v2)
for x in sorted(un,key=lambda x:-x[2])[:25]: print(x[0],round(x[1],3),round(x[2],3))
