from pathlib import Path
from copy import deepcopy
import sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=D/'proofs/before23b/tree'
if not T.exists():
 T.mkdir(parents=True)
 with tarfile.open(D/'proofs/capacity/source.tar') as archive:archive.extractall(T,filter='data')
sys.path[:0]=[str(D),str(T),str(L/'work/build21')]
import joblib as J
from launch_r1.production_proof import _run
from student_pilot.r1_persisted import scope
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
aliases={x['sha256']:x['local_path'] for x in J.load(D/'UPLOADS_q.json')['files']}
results={}
run=D/'proofs/before23b'/('run'+str(len(list((D/'proofs/before23b').glob('run*')))));run.mkdir()
for name in ('recovery','camera_wording'):
 cfg=J.load(D/'kits/q/k/n.json');cfg['r1_training']['row_slice_inputs']={name:dict(path='/unread/'+name+'.jsonl',sha256='0'*64)}
 root=run/name;root.mkdir(parents=True,exist_ok=True);cp=J.write(root/'c.json',cfg)
 with scope(aliases):r=_run(dict(config=cp,staged_pins=[cp],routing_base=cfg['streams']['routing'],room_audit=cfg['r1_training']['room_audit']),root/'q')
 assert r['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED',r
 results[name]=r
J.write(D/'BEFORE23B.json',dict(tree=digest(inventory(T)),mutations=results));print('Before: recovery and camera bindings both silently reach the frame-host boundary')
