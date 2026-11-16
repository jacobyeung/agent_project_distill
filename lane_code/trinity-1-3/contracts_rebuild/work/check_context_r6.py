from pathlib import Path
import subprocess,sys,json
L=Path(__file__).resolve().parents[1]
script='''import sys,json,contextlib
sys.path[:0]=[sys.argv[1],sys.argv[2]]
from fixtures_contracts import fixture,rotations,own_geometry
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry
import numpy as np
try:
 from trace_format.contracts import contract_epoch
except ImportError:
 contract_epoch=lambda *a,**kw:contextlib.nullcontext()
def geo():
 c,make=fixture('landscape');c.camera_to_world[0,:3,:3]=rotations(-80)
 c.camera_to_world[1:,:3,:3]=np.array([rotations()@np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]]) for a in np.radians(np.arange(1,32)*7.)])
 return own_geometry(make())
with contract_epoch(sys.argv[3]=='on',heading_plane_min=.3):g=geo();g.pose(3)
with contract_epoch(False,heading_plane_min=.3):
 reg=PrintedPointRegistry()
 print(json.dumps([respond(call,reg,g)[0] for call in ['<depth_at frame=2 pts=[[300,500]]>','<pose frame=3>','<move from=1 to=3>','<turn from=2 to=3>']]))
'''
records={}
for name,tree,build in [('base',L/'work/base/work/base/tree_b01ce449','off'),('off',L/'work/trees/r6_applied','off'),('cross',L/'work/trees/r6_applied','on')]:
 p=subprocess.run([sys.executable,'-I','-s','-B','-c',script,str(tree),str(L/'work/tests_r6'),build],capture_output=True,text=True)
 assert p.returncode==0,p.stderr
 records[name]=dict(tree=str(tree),construction=build,responses=json.loads(p.stdout))
assert records['base']['responses']==records['off']['responses']==records['cross']['responses']
(L/'work/CONTEXT_PARITY_R6.json').write_text(json.dumps(records,indent=2))
