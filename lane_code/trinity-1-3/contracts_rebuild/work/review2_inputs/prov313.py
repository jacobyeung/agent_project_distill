import sys,json
tree,arm=sys.argv[1],sys.argv[2]
sys.path[:0]=[tree,tree+'/generator/derivgen_v7','/scratch/jjyeung/orch_n30/contracts_rebuild/work/tests_r5']
if arm!='base':
    from trace_format.contracts import contract_epoch
    contract_epoch(arm=='on').__enter__()
from trace_format.ground_v313 import Session
from student_pilot import ground_lifting
from fixtures_contracts import fixture,masks
out={}
for pv in ('3.13','3.14'):
  for gm in ('sensor','predicted'):
    try:
        s=Session(ground_lifting,fixture('landscape')[1](),None,instances=lambda n:[dict(instance_id='1',masks=masks(n).masks,prob=[1.]*32)],program_version=pv,multi_instance=pv=='3.14',geometry_mode=gm)
        r=s.execute('<ground obj="chair" mode="box">')
        out[pv+'/'+gm]=[s.box_provider_id,r]
    except Exception as e: out[pv+'/'+gm]=['ERR',type(e).__name__,str(e)[:200]]
from student_pilot.live_trace313 import AuditSession
try:
    a=AuditSession([dict(box_provider_id='fit_gbox_best_v1')]);out['audit313']=a.box_provider_id
except Exception as e: out['audit313']=['ERR',str(e)]
print(json.dumps(out,indent=1))
