export TZ=UTC; date -u +%TZ
timeout 200 srun --overlap --jobid 174134 -N1 -n1 python3 -I -B - <<'PYEOF'
import sys, ast, types, json, os, hashlib, copy
sys.dont_write_bytecode=True
OUT='/tmp/q_22c714e1_174134'; IN='/tmp/q_22c714e1'; T=OUT+'/p/s'
def m(p):
    p=str(p); return OUT+p[len(IN):] if (p==IN or p.startswith(IN+'/')) else p
sys.path.insert(0,T)
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
mix={'load':load,'pinned':pinned,'__name__':'student_pilot.c1_pose_mix','__package__':'student_pilot'}
print('verbatim from tree c1_pose_mix.py:',grab(T+'/student_pilot/c1_pose_mix.py',{'DIVISION_SCHEMA','_pin','_division','MAX_ANCESTRY','ancestor_admits'},mix))
stub=types.ModuleType('student_pilot.c1_pose_mix'); stub.ancestor_admits=mix['ancestor_admits']; sys.modules['student_pilot.c1_pose_mix']=stub
run={'load':load,'pinned':pinned,'__name__':'student_pilot.carrier_c1_run','__package__':'student_pilot'}
print('verbatim from tree carrier_c1_run.py:',grab(T+'/student_pilot/carrier_c1_run.py',{'division_admits'},run))
rt={}; print('verbatim from tree carrier_c1_routing.py:',grab(T+'/student_pilot/carrier_c1_routing.py',{'ROUTING_SCHEMA'},rt))
division_admits=run['division_admits']
Q=OUT+'/p/q'
R=json.load(open(Q+'/RESULT.json')); paths={e['sha256']:m(e['path']) for e in R['staged']}
print('tree file sha: carrier_c1_run.py',sha256(T+'/student_pilot/carrier_c1_run.py')[:16],'c1_pose_mix.py',sha256(T+'/student_pilot/c1_pose_mix.py')[:16])
def predicate(name,receipt,division):
    # carrier_c1_run.py lines 536-541, same expression
    schema = rt['ROUTING_SCHEMA'] if name == 'routing' else 'c1-stream-v1'
    parts=dict(schema_differs=receipt.get('schema') != schema, stream_differs=receipt['stream'] != name,
               division_not_admitted=not division_admits(receipt['division'], division),
               heldout_overlap_nonzero=receipt.get('heldout_overlap') != 0,
               pointing_not_gt_masks=(name == 'pointing' and receipt.get('gt_masks_only') is not True))
    return (name != 'pose' and any(parts.values())), parts
with r1_persisted.scope(paths):
    cfg=load(m(Q+'/c.json'))
    spec=load(pinned(cfg['streams']['pose'])); division=spec['division']
    print('reference division pin:',json.dumps(division))
    prep=sorted(os.path.join(Q,'p',d) for d in os.listdir(Q+'/p') if d.startswith('prepare_'))[0]
    print('== T1 the receipts prepare() saw (expected: only the third stream refuses)')
    seen={}
    for name,sub in (('pointing','pointing'),('routing','routing'),('vqa','vqa')):
        r=json.load(open(os.path.join(prep,sub,'receipt.json'))); seen[name]=r
        refuse,parts=predicate(name,r,division); print('  ',name,'REFUSE' if refuse else 'pass',json.dumps(parts))
    print('== T2 same third-stream receipt, division.path set to the path P pins (expected: pass)')
    fixed=copy.deepcopy(seen['vqa']); fixed['division']={'path':'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json','sha256':seen['vqa']['division']['sha256']}
    refuse,parts=predicate('vqa',fixed,division); print('   vqa','REFUSE' if refuse else 'pass',json.dumps(parts))
    print('== T3 the source receipts on the node naming the same row store (division_admits of each)')
    store=load(pinned(cfg['r1_training']['store_parameter']))['database']['sha256']
    for e in R['staged']:
        p=m(e['path'])
        try:
            if os.path.getsize(p)>200000: continue
            with open(p,'rb') as h:
                if h.read(1)!=b'{': continue
            v=load(p)
        except Exception: continue
        if isinstance(v,dict) and v.get('schema')=='c1-stream-v1' and v.get('stream')=='vqa':
            same=v.get('database',{}).get('sha256')==store
            try: ok=division_admits(v['division'],division)
            except Exception as ex: ok=repr(ex)
            print('  ',e['sha256'][:12],os.path.getsize(p),'B same_store',same,'count',v.get('count'),'scenes',v.get('scenes'),'division_admits',ok)
            print('       division',json.dumps(v.get('division'))); print('       database',json.dumps(v.get('database'))); print('       source',json.dumps(v.get('source'))[:400])
            if 'source_receipt' in v: print('       source_receipt',json.dumps(v.get('source_receipt'))[:300])
    print('== T4 the two division files')
    for pin in (division, seen['vqa']['division']):
        d=load(pinned(pin)); print('  ',pin['sha256'][:12],'resolved',r1_persisted.relocated(pin),'bytes',os.path.getsize(r1_persisted.relocated(pin)),'train',len(d['train_scenes']),'heldout',len(d['heldout_scenes']),'parent',json.dumps(d.get('parent_division')))
    a=load(pinned(division)); b=load(pinned(seen['vqa']['division']))
    print('   parent train kept in child:',set(b['train_scenes'])<=set(a['train_scenes']),' parent heldout kept held out:',set(b['heldout_scenes'])<=set(a['heldout_scenes']),' parent heldout:',b['heldout_scenes'][:3])
print('DONE')
PYEOF
echo srun_rc=$?
squeue -j 174134 -h -o "%i %T %M %N"
