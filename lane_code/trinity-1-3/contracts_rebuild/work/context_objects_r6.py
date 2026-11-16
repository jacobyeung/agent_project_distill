from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[1];sys.path.insert(0,str(L/'work/trees/r6_applied'))
from trace_format.contracts import contract_epoch
from generator.derivgen_v7.derivgen.calculator import PrintedPointRegistry
from generator.derivgen_v7.derivgen.box_v313 import BoxRegistry
out={}
for build in (True,False):
 with contract_epoch(build):r=PrintedPointRegistry();b=BoxRegistry()
 with contract_epoch(False):
  point=r.register(camera=[1,2,3],f1=[4,5,6],spread=0,requested_frame=2)
  out[str(build)]=dict(point=point,point_state={k:str(v) for k,v in r._points['P1'].items()},box_vars=vars(b))
print(json.dumps(out,indent=2))
(L/'work/context_objects_r6.json').write_text(json.dumps(out,indent=2))
