import sys,os,json,glob,importlib.util,copy,hashlib
OUT='/tmp/q_22c714e1_174134'; IN='/tmp/q_22c714e1'; D='/tmp/a15_f8_174134/t'
NEWR='a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a'
def m(p): p=str(p); return OUT+p[len(IN):] if (p==IN or p.startswith(IN+'/')) else p
T=OUT+'/p/s'; sys.path.insert(0,T)
from student_pilot.p3_provenance import load,pinned,sha256
from student_pilot import r1_persisted
from student_pilot.carrier_c1_run import division_admits
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
from student_pilot.r1_training import store_parameter
from student_pilot.ground_target_filter import TargetFilter
for f in ('carrier_c1_run.py','c1_pose_mix.py','ground_target_filter.py','r1_training.py'): print('tree',f,sha256(T+'/student_pilot/'+f)[:16])
spec=importlib.util.spec_from_file_location('pf_new',D+'/f.py'); pf=importlib.util.module_from_spec(spec); spec.loader.exec_module(pf)
print('f.py',sha256(D+'/f.py')[:16],'r.json',sha256(D+'/r.json'),os.path.getsize(D+'/r.json'),'c0',sha256(D+'/c0.json')[:16],'c1',sha256(D+'/c1.json')[:16])
R=json.load(open(OUT+'/p/q/RESULT.json')); paths={e['sha256']:m(e['path']) for e in R['staged']}; paths[NEWR]=D+'/r.json'
c0=load(D+'/c0.json'); c1=load(D+'/c1.json')
def parts(name,r,division):
    schema=ROUTING_SCHEMA if name=='routing' else 'c1-stream-v1'
    return dict(schema=r.get('schema')!=schema,stream=r['stream']!=name,division=not division_admits(r['division'],division),
                heldout_overlap=r.get('heldout_overlap')!=0,gt_masks_only=(name=='pointing' and r.get('gt_masks_only') is not True))
with r1_persisted.scope(paths):
    print('== T1 kit preflight b/pf.py receipts() on the staged bytes')
    for tag,cfg in (('old 9e809db4 k/c.json',c0),('new 489f7f0f k/c.json',c1)):
        try: pf.receipts(cfg); print('  ',tag,'PASS')
        except ValueError as e: print('  ',tag,'REFUSE',e)
    pose=load(pinned(c1['streams']['pose'])); division=pose['division']; print('   run division',json.dumps(division))
    print('== T2 division_admits(new receipt division, run division)')
    nr=load(pinned(c1['streams']['vqa'])); print('   new receipt',c1['streams']['vqa']['sha256'][:12],'division',json.dumps(nr['division']),'->',division_admits(nr['division'],division))
    print('== T3 five sub-checks, every non-pose stream')
    for name,pin in c1['streams'].items():
        if name=='pose':continue
        p=parts(name,load(pinned(pin)),division); print('   source receipt',name,pin['sha256'][:12],'PASS' if not any(p.values()) else 'REFUSE',json.dumps(p))
    prep=sorted(glob.glob(OUT+'/p/q/p/prepare_*'))[0]
    for name in ('pointing','routing','vqa'):
        r=json.load(open(prep+'/'+name+'/receipt.json'))
        if name=='vqa': r=dict(r,division=nr['division'])  # build_stream copies the source receipt's division pin
        p=parts(name,r,division); print('   rebuilt receipt',name,'(vqa: division from the new receipt)' if name=='vqa' else '','PASS' if not any(p.values()) else 'REFUSE',json.dumps(p))
    print('== T4 lines 543-547 on the rebuilt pointing receipt prepare() compares')
    pr=json.load(open(prep+'/pointing/receipt.json'))
    exp=TargetFilter(c1.get('remove_files',()),shape_filter=True).settings()
    got=pr.get('target_filter',{}).get('settings')
    print('   ground_target_filter',c1.get('ground_target_filter'),'| receipt has target_filter',('target_filter' in pr),'| settings equal',got==exp,'| refuse',bool(c1.get('ground_target_filter')) and got!=exp)
    src=load(pinned(c1['streams']['pointing'])); print('   configured pointing receipt',c1['streams']['pointing']['sha256'][:12],'has target_filter',('target_filter' in src),'(prepare() does not compare this one)')
    print('== T5 store_parameter on old and new pin')
    for tag,cfg in (('old',c0),('new',c1)):
        b=store_parameter(cfg['r1_training']['store_parameter']); print('  ',tag,'count',b['count'],'database',json.dumps(b['database']),'store_hashes.vqa',cfg['r1_training']['store_hashes']['vqa'][:16])
print('DONE')
