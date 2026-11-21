"""fix8 kit-build preflight on Trinity: the tree's own receipt predicates (b/pf.py receipts) on the old
and the new kit config, every receipt resolved by sha256 from local copies of the staged objects."""
import sys, json, os, traceback
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); F=W/'w30f1'; N=Path(sys.argv[1])
sys.path[:0]=[str(F/'tree'),str(N/'b')]
import importlib.util
from z import load as zload, sha
from student_pilot import r1_persisted
from student_pilot.p3_provenance import load, pinned
from student_pilot.carrier_c1_run import division_admits
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
spec=importlib.util.spec_from_file_location('pf_new',N/'b/pf.py'); pf=importlib.util.module_from_spec(spec); spec.loader.exec_module(pf)
U=F/'uobj'
paths={p.name:str(p) for p in U.iterdir()}; paths[sorted((F/'u').iterdir())[0].name]=str(sorted((F/'u').iterdir())[0])
print('pf.py',sha(N/'b/pf.py'),'objects',len(paths))
for name,kit in (('old 9e809db4',W/'w28fix/n_go'),('new merged w33n',N)):
    cfg=zload(kit/'k/c.json')
    print('==',name,'config',sha(kit/'k/c.json')[:16],'streams.vqa',cfg['streams']['vqa']['sha256'][:12])
    with r1_persisted.scope(paths):
        pose=load(pinned(cfg['streams']['pose'])); division=pose['division']
        print('   run division',json.dumps(division))
        for s,pin in cfg['streams'].items():
            if s in ('pose','mdg'):continue
            r=load(pinned(pin)); schema=ROUTING_SCHEMA if s=='routing' else 'c1-stream-v1'
            parts=dict(schema=r.get('schema')!=schema,stream=r.get('stream')!=s,division=not division_admits(r['division'],division),
                       heldout_overlap=r.get('heldout_overlap')!=0,gt_masks_only=s=='pointing' and r.get('gt_masks_only') is not True)
            print('   %-9s %s receipt %s division %s'%(s,'REFUSE' if any(parts.values()) else 'pass',pin['sha256'][:12],json.dumps(r['division'])),json.dumps(parts))
        legacy=load(pinned(cfg['streams']['routing'])); point=load(pinned(cfg['streams']['pointing']))
        print('   s1_routing:229 division_admits(routing.division, pointing.division) =',division_admits(legacy['division'],point['division']))
        try: pf.receipts(cfg); print('   b/pf.py receipts(cfg): PASS')
        except ValueError as e: print('   b/pf.py receipts(cfg): REFUSE',str(e))
