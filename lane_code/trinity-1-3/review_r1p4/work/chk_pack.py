import json,gzip,sys,random,hashlib
sys.path.insert(0,sys.argv[1]); sys.dont_write_bytecode=True
from student_pilot import ground_rows
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/'
srcb=open('/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl','rb').read().splitlines()
pkb=open(sys.argv[2],'rb').read().splitlines()
assert len(srcb)==len(pkb)==747
fm={}
with gzip.open(K+'frame_map.jsonl.gz','rt') as f:
    for l in f:
        v=json.loads(l);fm[(v['d'],v['s'],v['i'])]=v
rates=json.load(open(K+'frame_rates.json'))
print('rates keys',list(rates)[:10])
bad=0;sikeys=set();canon_src=0;ev_eq_pack=0;ev_eq_gr=0;fps_mismatch=0;units={}
for n,(a,b) in enumerate(zip(srcb,pkb)):
    s=json.loads(a);p=json.loads(b)
    if enc(s).encode()==a:canon_src+=1
    extra=set(p)-set(s); miss=set(s)-set(p)
    if extra!={'events','student_input'} or miss: bad+=1;print('keys',n,extra,miss);continue
    for k in s:
        if enc(s[k])!=enc(p[k]): bad+=1;print('field',n,k)
    # raw substring check: each field's raw bytes (non-canonical) re-serialised as in source
    sikeys|=set(p['student_input'])
    env=ground_rows.pack(dict(s['ground_record'],suffix=s['target']),s['provenance'])
    if enc(env['events'])==enc(p['events']):ev_eq_pack+=1
    if enc(s['ground_record'].get('events'))==enc(p['events']):ev_eq_gr+=1
    d,sc=s['provenance']['alias'].split('/',1)
    assert s['dataset']==d and s['scene']==sc
    idx=s['provenance']['frame_indices'];assert idx==s['frame_indices']==s['ground_record']['frame_indices']==p['student_input']['frame_indices']
    fr=p['student_input']['frames']
    for i,x in zip(idx,fr):
        m=fm.get((d,sc,i))
        if m is None or m['path']!=x['path'] or m['sha256']!=x['sha256']: bad+=1;print('pin',n,i)
    exp=rates.get('by_scene',{}).get(d+'/'+sc)
    if exp is None: exp=rates.get('by_dataset',{}).get(d)
    if exp!=p['student_input']['fps']: fps_mismatch+=1
    u=s['provenance']['details']['unit'];units[u]=units.get(u,0)+1
print(dict(bad=bad,canon_src=canon_src,ev_eq_pack=ev_eq_pack,ev_eq_gr=ev_eq_gr,fps_mismatch=fps_mismatch,student_input_keys=sorted(sikeys),units=units))
print('order', [json.loads(a)['qid'] for a in srcb]==[json.loads(b)['qid'] for b in pkb])
