"""Pipeline check on the CPU rehearsal capture under the registered parity rule: counts only, no cell."""
import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G, select_j1 as S
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
d=G.read_json('rehearsal_cpu/scannet__scene0642_01.json.gz')
n=m=st=0
for iid,row in rows.items():
    if row['capture']!='scannet/scene0642_01': continue
    for o in row['objects']:
        p=o['name'].strip().lower()
        if p not in d['text']: continue
        th=[[] for _ in range(32)]
        for q in o['proposals']: th[int(q['frame'])-1].append(dict(mask480=R.unrle(q['mask']),score=float(q['score']),presence=float(q['presence'])))
        for f in range(32):
            mi=[dict(mask480=G.unpack(e['mask']),score=e['score'],presence=e['presence']) for e in d['text'][p][f]]
            ok,why=S.frame_match(mi,th[f]); n+=1; m+=ok; st+=why['strict']
print('operand-frames',n,'registered rule matched',m,'strict matched',st)
