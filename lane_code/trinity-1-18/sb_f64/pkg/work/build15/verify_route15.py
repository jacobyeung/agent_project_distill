from pathlib import Path
from types import SimpleNamespace as NS
import json,sys
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';O=L/'work/build15/proofs/verify_route'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.verify_pass import Session,Config
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.carrier_c1_routing import RenderError
from student_pilot.ground_context import GroundContext
from trace_format.calculator import PrintedPointRegistry
class NoCandidateRequest:
    def verify_request(self,name,context):return None
    def accept_verify(self,*args):raise AssertionError('No candidate was submitted')
heads=HeadState.__new__(HeadState);heads.mdg_backend=None;heads.grounding_head=None
context=GroundContext(heads,None,None,heads.ground,'fixture',None,{}, {},registry=PrintedPointRegistry())
session=Session(None,None,Config(NoCandidateRequest()))
text,info=session.ground('chair',context)
assert text=='chair: not seen' and info['verify_error'] is True
assert info['verify']['error_type']=='RenderError' and info['verify']['error']=='head_readout'
refusal=info['verify']['error']
monitor.save(O)
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',refusal=refusal,
    output=text,diagnostics=info,
    scope='Unit dispatch test: a protocol fixture supplies no candidate request. Real Session.ground, GroundContext.ground_route and HeadState.ground execute. Existing exception-to-text conversion is retained as a product-acceptance blocker, not claimed as model output. No producer claim.'))+'\n')
print(refusal)
