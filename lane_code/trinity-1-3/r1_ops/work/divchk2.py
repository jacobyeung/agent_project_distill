import json,sqlite3,collections
D=json.load(open('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json'))
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/'
train=set(D['train_scenes']); hs=set(D['heldout_scenes']); hg=set(D['heldout_group_ids']); hq=set(D['heldout_qids']); tg=set(D['train_group_ids'])
B=json.load(open(K+'benchmark_scene_exclusions.json')); V=json.load(open(K+'dev_scene_exclusions.json'))
def strs(x,acc):
    if isinstance(x,str): acc.add(x)
    elif isinstance(x,dict): [strs(v,acc) for v in x.values()]; [acc.add(k) for k in x]
    elif isinstance(x,list): [strs(v,acc) for v in x]
    return acc
btok=strs(B,set()); vtok=strs(V,set())
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?immutable=1',uri=True)
hits=collections.Counter(); off=collections.defaultdict(set)
for i,row in c.execute('select i,row from rows'):
    r=json.loads(row); s=r['dataset']+'/'+r['scene']; tok=r['scene']
    if r['qid'] in hq: hits['heldout_qid']+=1
    if s in hs: hits['heldout_scene']+=1
    if s in hg: hits['heldout_group']+=1
    if s not in train:
        g=r.get('pool'); off[g].add(s)
        if s in btok or tok in btok: hits['off_in_bench_v2:'+g]+=1
        if s in vtok or tok in vtok: hits['off_in_dev:'+g]+=1
        if s in tg: hits['off_in_train_group:'+g]+=1
print(dict(hits)); print({k:len(v) for k,v in off.items()}); print({k:sorted(v)[:6] for k,v in off.items()})
