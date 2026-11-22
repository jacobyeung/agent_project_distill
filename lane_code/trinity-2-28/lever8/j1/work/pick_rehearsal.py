"""Pick-agreement counts on the CPU rehearsal capture (fp32 CPU vs bf16 dump): counts only, no cell."""
import sys, json, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
items,objects,_=G.eligible(R,refs)
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
d=G.read_json('rehearsal_cpu/scannet__scene0642_01.json.gz')
cap='scannet/scene0642_01'; gp=[i['gt_path'] for i in items if i['capture']==cap][0]
inst=np.load(gp)['inst']; n=a1=a0=0
for o in objects:
    if o['capture']!=cap: continue
    obj={x['name'].strip().lower():x for x in rows[o['item_id']]['objects']}.get(o['name'].strip().lower())
    if obj is None: continue
    th=[[] for _ in range(32)]
    for q in obj['proposals']: th[int(q['frame'])-1].append(dict(mask480=R.unrle(q['mask']),score=float(q['score']),presence=float(q['presence'])))
    t=inst==o['instance_id']
    for f in range(32):
        mi=[dict(mask480=G.unpack(e['mask']),score=e['score'],presence=e['presence']) for e in d['text'][o['name'].strip().lower()][f]]
        m=S.pick_match(mi,th[f],t[f]); n+=1; a1+=m['h1']; a0+=m['h0']
print('operand-frames',n,'h1 picks agree',a1,'h0 picks agree',a0)
