"""K1 held-out + R0 room check of vehicle N's three routing slices (lane tree_rebuild10), with b12_cntapp's rooms.py rule."""
import builtins, collections, hashlib, io, json, sys
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; E=W+'/ext/b12'
R0=W+'/inputs/rooms/R0_ROOMS.txt'; r0b=open(R0,'rb').read(); assert hashlib.sha256(r0b).hexdigest().startswith('bdb5d402')
orig=builtins.open
def op(f,m='r',*a,**k):
    s=str(f)
    if s.endswith('events/b10_reserve/R0_ROOMS.txt'): return io.BytesIO(r0b) if 'b' in m else io.StringIO(r0b.decode())
    if s.startswith('/scratch/jjyeung/orch_n30/b12_cntapp/work/auth/'): f=E+'/work/auth/'+s.rsplit('/',1)[1]
    return orig(f,m,*a,**k)
builtins.open=op; sys.path.insert(0,E+'/code')
import rooms
builtins.open=orig
d3=json.load(open(E+'/work/d3_token_map.json'))
SL={'recovery':'/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl','units':'/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl',
    'absolute_distance':'/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl'}
DS={'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}
out=dict(authorities=dict(rooms_py=hashlib.sha256(open(E+'/code/rooms.py','rb').read()).hexdigest(),k1split=hashlib.sha256(open(E+'/work/auth/K1SPLIT_R0.json','rb').read()).hexdigest(),
    teacher_k1=rooms._K['teacher_k1']['sha256'],AUTH=rooms.AUTH,k1_heldout_rooms=len(rooms.K1_HELDOUT),r0_rooms=len(rooms.R0_ROOMS)),slices={})
for fam,p in SL.items():
    c=collections.Counter();hits=collections.defaultdict(list);how=collections.Counter()
    for l in open(p,'rb'):
        r=json.loads(l);c['rows']+=1
        can=r.get('canonical') or (r.get('provenance') or {}).get('canonical') or (r.get('ground_record') or {}).get('canonical')
        if can: how['row_field']+=1
        else:
            ds=r.get('dataset','');sc=r.get('scene','')
            can=d3.get(ds+'/'+sc) or d3.get(DS.get(ds,'?')+'/'+sc)
            if can: how['d3_map']+=1
            elif ds in ('scannet','scannetpp','scannetppv2') and sc: can=ds+'/'+sc; how['dataset_scene']+=1
            elif ds=='arkitscenes' and sc.isdigit(): can='arkitscenes/'+sc; how['dataset_scene']+=1
        if not can: c['unresolved']+=1; hits['unresolved'].append(r.get('qid')); continue
        s=rooms.status(can)
        if s!='ok': hits[s].append(r.get('qid'))
    out['slices'][fam]=dict(path=p,sha256=hashlib.sha256(open(p,'rb').read()).hexdigest(),counts=dict(c),canonical_from=dict(how),hits={k:len(v) for k,v in hits.items()},hit_qids={k:v for k,v in hits.items()})
json.dump(out,open(W+'/work/k1check/K1R0_CHECK.json','w'),indent=1)
print(json.dumps({k:{x:y for x,y in v.items() if x!='hit_qids'} for k,v in out['slices'].items()},indent=1)); print(json.dumps(out['authorities'],indent=1))
