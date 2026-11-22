"""Pipeline check on the CPU rehearsal capture (fp32 CPU vs the dump's bf16 GPU pool): parity counts only, no cell."""
import sys, json, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
d=G.read_json('rehearsal_cpu/scannet__scene0642_01.json.gz')
from collections import Counter
c=Counter(); ious=[]; ds=[]
for iid,row in rows.items():
    if row['capture']!='scannet/scene0642_01': continue
    for o in row['objects']:
        p=o['name'].strip().lower()
        if p not in d['text']: continue
        theirs=[[] for _ in range(32)]; ts=[[] for _ in range(32)]
        for q in o['proposals']: theirs[int(q['frame'])-1].append(R.unrle(q['mask'])); ts[int(q['frame'])-1].append(float(q['score']))
        for f in range(32):
            mine=[G.unpack(e['mask']) for e in d['text'][p][f]]
            ok,why=S.frame_match(mine,theirs[f]); c[why['reason']]+=1
            if 'min_iou' in why: ious.append(why['min_iou'])
            if ok and mine: ds+= [abs(a['score']-b) for a,b in zip(d['text'][p][f],ts[f])]
print(dict(c), 'min IoU over compared frames', min(ious) if ious else None, 'max |score diff| on matched', max(ds) if ds else None)
