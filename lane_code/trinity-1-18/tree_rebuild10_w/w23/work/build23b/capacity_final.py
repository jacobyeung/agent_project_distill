"""Replay native capacity preparation on the final tree using authenticated donor assets."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import sys,os,json,sqlite3,importlib.util
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';A=L/'attic/build23b/capacity_first';O=L/'work/build23/proofs/capacity';T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build23'),str(T),str(L/'work/build21')]
spec=importlib.util.spec_from_file_location('native23b',D/'native23b.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
from student_pilot.p3_provenance import file_pin,load,pinned,source_files,sha256
from student_pilot.source_seal import inventory,archive,create
from student_pilot import r1_persisted as P
from launch_r1 import production_proof as Q,p_opener_witness
from student_pilot.r1_coverage import deferred
root=D/'proofs/400';root.mkdir(parents=True,exist_ok=True)
cfg=load(A/'400/request_config.json');request=load(A/'400/request.json')
files=inventory(T);archive(T,D/'source.tar',files,compress=True)
closure={str(p.relative_to(T)):sha256(p) for p in source_files([Path(N.C.__file__)])}
cfg['code']=N.write(D/'code.json',create(T,D/'source.tar',closure,{}))
selection=load(pinned(cfg['s1_routing']['selection']))
N.s1_pool.prepare(selection['manifest'],D/'selected',cfg['remove_files'])
cfg['s1_routing']['selection']=file_pin(D/'selected/receipt.json')
config=N.write(root/'request_config.json',cfg);request['config']=config;request['staged_pins'][0]=config
N.write(root/'request.json',request)
summary=dict(GO=False,stand_ins=['Synthetic RGB and labels','Tiny native model dimensions','PatchGridProcessor constructor','CPU local publication collectives'],storage='SQLite page_size=65536 for new fixture databases; native producers and readers unchanged',milestones={},source_seal=load(D/'code.json')['tree_sha256'])
original_connect=sqlite3.connect
layouts=[]
def connect(database,*args,**kwargs):
 name=str(database);fresh=name.startswith(str(D/'proofs')) and not name.startswith('file:') and not Path(name).exists()
 connection=original_connect(database,*args,**kwargs)
 if fresh:connection.execute('PRAGMA page_size=65536');layouts.append(name)
 return connection
with ExitStack() as stack:
 stack.enter_context(patch.object(N.C,'processor_for',N.processor));stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
 u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
 stack.enter_context(patch.object(sqlite3,'connect',connect))
 assert 'STUDENT_R2_FRAME_HOST' not in os.environ and 'Q_E7' not in os.environ
 deferred(cfg,read_pins=True)
 result=Q.run(request,root/'q');summary['milestones']['400']=result
 print('400',result['status'],result.get('refusal'),flush=True)
 if result['status']=='ADMIT':
  next_cfg=deepcopy(load(pinned(result['config'])));donor=load(O/'600/request_config.json')
  next_cfg['init_artifact']=donor['init_artifact']
  for key in ('p_run','handover_receipt','persisted_files','proof_mode','donor_config_sha256'):next_cfg['r1_training'][key]=donor['r1_training'][key]
  r600=D/'proofs/600';r600.mkdir(parents=True,exist_ok=True)
  with P.proof_scope(),P.scope(next_cfg['r1_training']['persisted_files']):
   deferred(next_cfg,read_pins=True)
   next_cfg['routing_vocabulary']=p_opener_witness.produce(next_cfg,r600/'v.json')
   bound=Q.bind_handover(next_cfg,r600/'h');next_cfg=load(pinned(bound));handover=P.admission(next_cfg,weights=True)
   assert handover['absolute_resume_step']==600
   with P.scope(handover['paths']):forward=Q.forward(next_cfg,r600,600,'cpu')
  summary['milestones']['600']=dict(status='ADMIT',GO=False,config=bound,forward=forward,audit=result['audit'],steps=['reuse_400_native_stores_and_population','persisted_checkpoint_handover','all_rank_full_forward'],proof_root=str(r600))
  print('600 ADMIT',flush=True)
summary.update(status='PASS' if len(summary['milestones'])==2 and all(x['status']=='ADMIT' for x in summary['milestones'].values()) else 'FAIL',sqlite_layout_paths=layouts)
N.write(D/'CAPACITY.json',summary);N.m.save(D/'proofs')
print(json.dumps(dict(status=summary['status'],workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))))
raise SystemExit(summary['status']!='PASS')
