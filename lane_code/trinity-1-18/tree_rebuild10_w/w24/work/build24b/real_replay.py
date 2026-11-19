from pathlib import Path
from copy import deepcopy
import sys,traceback
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';E=L.parent/'ext/m400real';E=E if E.exists() else D/'inputs/m400real';O=D/'proofs/real_replay';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot import r1_handover as H,r1_persisted as P,r1_training as T
from student_pilot.p3_provenance import file_pin,load,pinned
allpaths={J.sha(p):str(p) for p in (E/'files').rglob('*.json')}
for x in J.load(D/'UPLOADS_n.json')['files']:
 if x['opaque_name'].startswith('u/'):allpaths.setdefault(x['sha256'],x['local_path'])
h=J.load(E/'e.json');paths={p['sha256']:allpaths.get(p['sha256'],str(O/'absent'/p['sha256'])) for p in h['pins'].values()};allpaths.update(paths)
cfg=J.load(L/'work/build24/kits/n/k/n.json');cfg['r1_training'].update(handover_receipt=file_pin(E/'e.json'),persisted_files=paths)
records=[]
def call(name,fn,summary=lambda x:None):
 try:r=fn();row=dict(reader=name,status='PASS',result=summary(r))
 except Exception as e:r=None;row=dict(reader=name,status='REFUSE',error=type(e).__name__+':'+str(e))
 records.append(row);print(name,row['status'],row.get('error',''),flush=True);return r
with P.scope(allpaths):
 artifact=load(pinned(cfg['init_artifact']['artifact']))
 donor=call('r1_handover.donor',lambda:H.donor(cfg,artifact),lambda x:dict(config_identity=H.export_identity(x[0]),stores=x[2]['stores']))
 if donor:
  call('r1_handover.compare_configs',lambda:H.compare_configs(donor[0],cfg))
  bound=call('r1_handover.bind_target',lambda:H.bind_target(cfg,O/'mapping.json'))
  if bound:
   call('r1_training.start',lambda:T.start(bound),lambda x:x)
   call('r1_persisted.admission',lambda:P.admission(bound),lambda x:dict(status=x['status'],init_milestone=x['init_milestone'],training_start_step=x['absolute_resume_step']))
assert all(x['status']=='PASS' for x in records),records
J.write(D/'REAL_REPLAY.json',dict(status='PASS',without_proof_scope=True,receipt=file_pin(E/'e.json'),artifact=cfg['init_artifact']['artifact'],readers=records,
 limitations='Production tensors, RGB, databases and some metadata are absent locally. This proof authenticates real donor metadata and the weight-init policy; full forward uses the separate synthetic capacity fixture.'))
