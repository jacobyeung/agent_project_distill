from common import *
import subprocess
F=D/'native_reconstruction';F.mkdir()
runner=F/'run.py'
runner.write_text("""from pathlib import Path
import sys,json,types
from unittest.mock import patch
L=Path("""+repr(str(L))+""");D=L/'work/build24m2d';F=D/'native_reconstruction'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(L/'out/kit_qd/b')]
import native24 as N
N.C.processor_for=N.processor
from z import load,write,sha
from student_pilot.p3_provenance import file_pin
import rb
base=Path('/tmp/qd/p/q/selection');receipt=load(base/'receipt.json')
cfg=load(D/'tiny_routing/cfg.json');cfg['streams']['routing']=file_pin(base/'receipt.json')
p=write(F/'p_config.json',cfg)
request={'r1_training':{'p_run':{'config':p}}}
source=Path(rb.__file__).read_text().replace('ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984',cfg['streams']['routing']['sha256']).replace('4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84',receipt['database']['sha256'])
module=types.ModuleType('fixture_rb');exec(compile(source,'fixture_rb','exec'),module.__dict__)
root=F/'ok';root.mkdir()
original=Path(receipt['database']['path']);calls=[]
from student_pilot import p3_provenance as P
native=P.pinned
def pin(value):
 if value.get('path')==str(original):raise AssertionError('READ_ORIGINAL_DATABASE')
 calls.append(value['path']);return native(value)
with patch.object(P,'pinned',pin):
 output=module.reconstruct(request,root)
assert sha(output)==receipt['database']['sha256']
# The real native builder must refuse an authenticated output-hash mismatch.
root=F/'changed';root.mkdir()
from student_pilot import s1_routing
native_build=s1_routing.build
def changed(*args,**kwargs):
 value=native_build(*args,**kwargs);value['database']['sha256']='f'*64;return value
# Return the output file directly in this mutation so the helper itself must reject it.
with patch.object(s1_routing,'build',changed),patch.object(P,'pinned',lambda value:Path(value['path'])):
 try:module.reconstruct(request,root)
 except ValueError as e:assert str(e).startswith('P_TRAINED_ROUTING_RECONSTRUCTION_DIFFERS:')
 else:raise AssertionError('changed output accepted')
write(F/'result.json',dict(status='PASS',native_build=True,original_database_never_opened=True,hash_mismatch_refuses=True,sha256=sha(output),boundary='Only the two fixed production pin constants are replaced with native fixture receipt/database hashes; producer, refresh and SHA checks execute.'))
""")
node=D/'tiny_routing/r'
args=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--ro-bind',str(node),'/tmp/qd','--bind',str(F),str(F),sys.executable,'-B','-s',str(runner)]
subprocess.run(args,check=True)
J.write(D/'RECONSTRUCTION_TESTS.json',J.load(F/'result.json'))
print('native P reconstruction without opening original database; changed hash refuses PASS')
