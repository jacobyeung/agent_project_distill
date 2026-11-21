import sys, ast, json, os, glob, copy, collections, sqlite3, hashlib
W=sys.argv[1]; T=W+'/t'; S=W+'/ship'
sys.dont_write_bytecode=True; sys.path.insert(0,T)
from student_pilot.p3_provenance import load, pinned, sha256
from student_pilot import r1_persisted
def grab(path, names, ns):
    src=open(path).read(); got=[]
    for node in ast.parse(src).body:
        nm=getattr(node,'name',None)
        if isinstance(node,ast.Assign): nm=getattr(node.targets[0],'id',None)
        if nm in names:
            exec(compile(ast.get_source_segment(src,node),path,'exec'),ns); got.append(nm)
    return got
import types
mix={'load':load,'pinned':pinned,'__name__':'student_pilot.c1_pose_mix','__package__':'student_pilot'}
print('verbatim c1_pose_mix:',grab(T+'/student_pilot/c1_pose_mix.py',{'DIVISION_SCHEMA','_pin','_division','MAX_ANCESTRY','ancestor_admits'},mix))
stub=types.ModuleType('student_pilot.c1_pose_mix'); stub.ancestor_admits=mix['ancestor_admits']; sys.modules['student_pilot.c1_pose_mix']=stub
run={'load':load,'pinned':pinned,'__name__':'student_pilot.carrier_c1_run','__package__':'student_pilot'}
print('verbatim carrier_c1_run:',grab(T+'/student_pilot/carrier_c1_run.py',{'division_admits'},run))
rt={}; print('verbatim carrier_c1_routing:',grab(T+'/student_pilot/carrier_c1_routing.py',{'ROUTING_SCHEMA'},rt))
division_admits=run['division_admits']
# the predicate text from the tree, lines 536-541, evaluated as written
src=open(T+'/student_pilot/carrier_c1_run.py').read().splitlines()
print('tree lines 536-542:'); [print('   %d %s'%(n+1,src[n])) for n in range(535,542)]
def predicate(name,receipt,division):
    schema = rt['ROUTING_SCHEMA'] if name == 'routing' else 'c1-stream-v1'
    parts=dict(schema_differs=receipt.get('schema') != schema, stream_differs=receipt['stream'] != name,
               division_not_admitted=not division_admits(receipt['division'], division),
               heldout_overlap_nonzero=receipt.get('heldout_overlap') != 0,
               pointing_not_gt_masks=(name == 'pointing' and receipt.get('gt_masks_only') is not True))
    refuse=(name != 'pose' and (receipt.get('schema') != schema or receipt['stream'] != name
                or not division_admits(receipt['division'], division) or receipt.get('heldout_overlap') != 0
                or (name == 'pointing' and receipt.get('gt_masks_only') is not True)))
    assert refuse==any(parts.values())
    return refuse, parts
DIV='/scratch/jjyeung/orch_n30/n_review/r1j/div/'
paths={os.path.basename(p):p for p in glob.glob(S+'/*')}
paths={k.split('.')[0]:v for k,v in paths.items()}
paths['f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5']=DIV+'f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5'
paths['0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad']=DIV+'0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad'
ROWS='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
for k,v in paths.items(): assert sha256(v)==k,(k,v)
CAND='bf2e7ebb4cc94db032004c914fa00563c93a2acb4df11c8e15e31aea9971c2b2'
cand_pin={'path':paths[CAND],'sha256':CAND}
with r1_persisted.scope(paths):
    spec=load(pinned({'path':'u/8957d119','sha256':'8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f'}))
    division=spec['division']; print('run pose division pin (spec 8957d119):',json.dumps(division))
    cand=load(pinned(cand_pin)); old=load(pinned({'path':'x','sha256':'e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0'}))
    print('candidate division == run pin (dict ==):', cand['division']==division)
    print('candidate keys == e3ee51da keys:', sorted(cand)==sorted(old), '; fields that differ:', [k for k in old if old[k]!=cand[k]])
    for name,pin in (('pointing','93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a'),('routing','ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984')):
        r=load(pinned({'path':'x','sha256':pin})); print('T1',name,pin[:8],*predicate(name,r,division))
    print('T1 vqa e3ee51da (old)',*predicate('vqa',old,division))
    print('T1 vqa CANDIDATE',CAND[:8],*predicate('vqa',cand,division))
    # tree's _division on the pinned a3v2 and the store's own count check (lines 548-551)
    d,train,held=mix['_division'](cand['division'])
    print('tree _division(candidate pin): train',len(train),'heldout',len(held))
    c=sqlite3.connect('file:'+ROWS+'?mode=ro',uri=True)
    n,lo,hi=c.execute('SELECT count(*),min(i),max(i) FROM rows').fetchone()
    print('db count check (lines 548-551):', n==cand['count'] and lo==0 and hi==n-1, n, lo, hi)
    sc=collections.Counter(); scenes=set(); bys=collections.Counter()
    for (raw,) in c.execute('SELECT row FROM rows ORDER BY i'):
        r=json.loads(raw); s=r['dataset']+'/'+r['scene']; scenes.add(s)
        k='train' if s in train else 'heldout' if s in held else 'outside'; sc[k]+=1; bys[(k,s)]+=0
    per=collections.Counter(k for k,s in bys)
    print('RECOUNT vs candidate division: rows',dict(sc),'scenes',dict(per),'distinct scenes',len(scenes),'== receipt scenes',len(scenes)==cand['scenes'])
    print('heldout_overlap recomputed',sc['heldout'],'== receipt',sc['heldout']==cand['heldout_overlap'])
    # r1_training.store_parameter and configure_store (tree functions)
    try:
        from student_pilot import r1_training
        b=r1_training.store_parameter(cand_pin); print('store_parameter OK count',b['count'],'db',b['database']['sha256'][:12])
    except Exception as e: print('store_parameter ERR',repr(e)[:300])
    # build_stream precondition at admission: rows kept after REMOVE list 02315a74 must lie in train, not held out
    from student_pilot.row_removals import Removals
    remf=glob.glob(DIV+'*601.jsonl')[0]
    rem=Removals([{'path':remf,'sha256':'02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'}])
    viol=collections.Counter(); kept=0
    for (raw,) in c.execute('SELECT row FROM rows ORDER BY i'):
        r=json.loads(raw)
        if not rem.keep(r): continue
        kept+=1; s=r['dataset']+'/'+r['scene']
        if s not in train or s in held: viol[s]+=1
    print('after 02315a74 alone: kept',kept,'removed',rem.removed,'scene violations under candidate division',sum(viol.values()))
    tw=glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/up24/u/7b3d696d*')
    print('twin rows file',tw)
    if tw:
        p=tw[0]; print('twin sha ok', sha256(p)=='7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e')
        txt=open(p).read(); 
        try: rows=[json.loads(l) for l in txt.splitlines() if l.strip()]
        except Exception: rows=json.loads(txt)
        if isinstance(rows,dict): print('twin file keys',list(rows)[:10]); rows=rows.get('rows',[])
        tv=collections.Counter(('train' if r['dataset']+'/'+r['scene'] in train else 'heldout' if r['dataset']+'/'+r['scene'] in held else 'outside') for r in rows if isinstance(r,dict) and 'scene' in r)
        print('twin rows',len(rows),'by candidate division',dict(tv))
print('DONE')
