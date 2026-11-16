"""LiveSession box provider vs backend epoch when the ambient epoch differs."""
import sys, json
from types import SimpleNamespace as NS
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/contracts_rebuild/work/tests_r6']
from trace_format.contracts import contract_epoch, new_contracts
from fixtures_contracts import fixture
from student_pilot.live_trace313 import LiveSession, AuditSession
out={}
for ambient in (True, False):
    for backend_epoch in (True, False):
        geo=fixture('landscape')[1]()
        b=NS(geometry=geo, contract_epoch=backend_epoch, heading_plane_min=0.3)
        with contract_epoch(ambient):
            try:
                s=LiveSession(b,program_version='3.13',geometry_mode='sensor')
                rec=dict(box_provider_id=s.box_provider_id, session_epoch=s.contract_epoch)
                # what the query stamp would look like for this session
                with contract_epoch(s.contract_epoch):
                    from trace_format.contracts import contract_identity
                    q=dict(name='chair', geometry_mode='sensor', box_provider_id=s.box_provider_id, **contract_identity())
                try:
                    a=AuditSession([q],'3.13'); rec['audit']=a.box_provider_id
                except Exception as e: rec['audit']='ERR '+str(e)
            except Exception as e: rec='ERR '+type(e).__name__+' '+str(e)[:200]
        out[f'ambient={ambient} backend={backend_epoch}']=rec
print(json.dumps(out,indent=1))
