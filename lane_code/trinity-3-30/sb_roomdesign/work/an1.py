import json, glob, collections, statistics as st
rows=[]
for p in sorted(glob.glob('geo_k1/harness/out_merged_mdp/*.json')):
    d=json.load(open(p))
    for it in d['items']:
        if it['type']=='room_size_estimation':
            rows.append(it)
arms=sorted({r['arm'] for r in rows})
print(len(rows), 'room item-arm rows;', len({r['row_id'] for r in rows}), 'items')
def mra(p,g):
    if p is None or g is None or g<=0: return 0.0
    e=abs(p-g)/g
    return sum(1 for t in [0.5+0.05*i for i in range(10)] if e < 1-t+1e-12)/10
def summ(sel):
    out={}
    for a in arms:
        rs=[r for r in sel if r['arm']==a]
        if not rs: continue
        ok=[r for r in rs if r['pred'] is not None]
        rel=[(r['pred']-r['gt'])/r['gt'] for r in ok]
        out[a]=(len(rs), len(rs)-len(ok), 100*sum(r['mra'] for r in rs)/len(rs),
                st.median(rel) if rel else float('nan'), st.median([abs(x) for x in rel]) if rel else float('nan'),
                sum(1 for x in rel if abs(x)<0.1)/max(1,len(rs)), sum(1 for x in rel if abs(x)<0.25)/max(1,len(rs)))
    return out
for split in ('train','heldout'):
    for ds in (None,'scannet','scannetpp'):
        sel=[r for r in rows if r['split']==split and (ds is None or r['dataset']==ds)]
        s=summ(sel)
        print('==',split,ds or 'all')
        print('%-18s %4s %3s %6s %7s %7s %6s %6s'%('arm','n','ref','MRA','medrel','med|rel|','<10%','<25%'))
        for a in arms:
            if a in s and ('R0' in a or 'R2' in a) and not a.startswith(('moge','pi3x')):
                print('%-18s %4d %3d %6.2f %+7.3f %7.3f %6.2f %6.2f'%((a,)+s[a]))
json.dump(rows, open('room_rows_k1.json','w'))
