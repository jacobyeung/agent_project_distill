import sys, json, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
d=G.read_json('rehearsal_cpu/scannet__scene0642_01.json.gz')
seen=set()
for iid,row in rows.items():
    if row['capture']!='scannet/scene0642_01': continue
    for o in row['objects']:
        p=o['name'].strip().lower()
        if p not in d['text'] or p in seen: continue
        seen.add(p)
        for f in range(32):
            th=[q for q in o['proposals'] if int(q['frame'])==f+1]
            mi=d['text'][p][f]
            ok,why=S.frame_match([G.unpack(e['mask']) for e in mi],[R.unrle(q['mask']) for q in th])
            if not ok:
                print(p,f+1,why['reason'],'dump',[(round(float(q['score']),3),round(float(q['score'])*float(q['presence']),3)) for q in th][:6],
                      'j1',[(round(e['score'],3),round(e['score']*e['presence'],3)) for e in mi][:6])
