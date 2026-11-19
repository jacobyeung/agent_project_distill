from pathlib import Path
from types import SimpleNamespace
import sys,os,json
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';O=B/'proofs/opener';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')];os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(T)
import torch
from student_pilot import r2_openers as E,carrier_c1_routing as C
from tests.test_r2_build3 import Embeddings
from tests.test_r2_build_n1 import write
from student_pilot.p3_provenance import load,file_pin
model=Embeddings()
with torch.no_grad():
    model.embed.weight.copy_(torch.arange(24).reshape(8,3));model.head.weight.copy_(100+torch.arange(24).reshape(8,3))
before={'input':model.embed.weight[7].tolist(),'output':model.head.weight[7].tolist()}
C.init_routing_embeddings(model,dict(ids={'<move':7},constituents={'<move':[1,2]}))
after={'input':model.embed.weight[7].tolist(),'output':model.head.weight[7].tolist()}
assert before!=after
parent=load(L/'work/n1fix2/inputs/init_artifact.json')
names=[]
for group in parent['trained_groups']['groups'].values():
    names.extend(n for n in group['names'] if 'scale_token' in n or 'scale_branch' in n)
assert names
P=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/r1_ops/work/snap_6a5c7d00/out/operator/r.json')
assert file_pin(P)['sha256']==load(L/'work/build14/proofs/opener/RESULT.json')['route_tables']['P']['sha256']
N=L/'work/n1fix2/inputs/route_table.json'
assert load(P)==load(N)
write(O/'RESULT.json',dict(keep_rows=before,reset_rows=after,equal=False,
    source='student_pilot/r2_openers.py:38-65; student_pilot/carrier_c1_routing.py:758-768',
    stand_in='Small CPU embedding tensors replace unavailable P weights; native reset arithmetic executes. No assertion about particular P opener row bytes.',
    parent=file_pin(L/'work/n1fix2/inputs/init_artifact.json'),scale_names=names,
    route_tables={'P':file_pin(P),'N':file_pin(N),'content_equal':True}))
m.save(O);print('Reset changes rows; scale parameters are recorded in the parent; route tables have equal content.')
