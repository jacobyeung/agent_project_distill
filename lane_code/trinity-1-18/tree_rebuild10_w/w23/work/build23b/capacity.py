from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import sys,os,json,sqlite3,importlib.util,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';O=L/'work/build23/proofs/capacity';T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build23'),str(T),str(L/'work/build21')]
# Retain the synthetic source stores; native mode q rebuilds and audits its stores.
s=(L/'work/build23/native23.py').read_text()
s=s.replace("    cfg['r1_training'].pop('routing_inputs')", "    cfg['r1_training'].pop('routing_inputs')\n    cfg['r1_training']['row_sources']=write(O/'row_sources_minimal.json',{})\n    cfg['r1_training']['source_membership']=write(O/'catalog_minimal.json',dict(schema='r1-source-catalog-v1',sources={}))")
(D/'native23b.py').write_text(s)
spec=importlib.util.spec_from_file_location('native23b',D/'native23b.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
from student_pilot.p3_provenance import file_pin,load,pinned
from student_pilot import r1_persisted as P
from launch_r1 import production_proof as Q,p_opener_witness
from student_pilot.r1_coverage import deferred
root=D/'proofs/400';root.mkdir(parents=True,exist_ok=True)
original_connect=sqlite3.connect
layouts=[]
def connect(database,*args,**kwargs):
    name=str(database);fresh=name.startswith(str(D/'proofs')) and not name.startswith('file:') and not Path(name).exists()
    connection=original_connect(database,*args,**kwargs)
    if fresh:
        connection.execute('PRAGMA page_size=65536');layouts.append(name)
    return connection
original_open=N.original_open
original_mkdir=N.original_mkdir
def retain_open(path,mode='r',*a,**kw):
    return original_open(path,mode.replace('x','w') if path.is_relative_to(O) or path.is_relative_to(D) else mode,*a,**kw)
def retain_mkdir(path,mode=0o777,parents=False,exist_ok=False):
    return original_mkdir(path,mode,parents,True if path.is_relative_to(O) else exist_ok)
summary=dict(GO=False,stand_ins=['Synthetic RGB and labels','Tiny native model dimensions','PatchGridProcessor constructor','CPU local publication collectives'],storage='SQLite page_size=65536 only for new fixture databases; native producers and readers execute unchanged',milestones={})
with ExitStack() as stack:
 stack.enter_context(patch.object(Path,'open',retain_open));stack.enter_context(patch.object(Path,'mkdir',retain_mkdir))
 stack.enter_context(patch.object(N.C,'processor_for',N.processor));stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
 u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
 stack.enter_context(patch.object(sqlite3,'connect',connect))
 with patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'):cfg,model,mp,camera,depth,room=N.host()
 assert 'STUDENT_R2_FRAME_HOST' not in os.environ and 'Q_E7' not in os.environ
 n=N.produce(cfg,model,mp,camera,depth,400)
 deferred(n,read_pins=True)
 config=N.write(root/'request_config.json',n)
 request=dict(config=config,routing_base=n['streams']['routing'],staged_pins=[config,room,mp]+[file_pin(p) for p in (O/'model').iterdir() if p.is_file()],room_audit=room,frame_roots=[str(O)],weights=True,milestone=400,memory_gib=16)
 N.write(root/'request.json',request)
 result=Q.run(request,root/'q');summary['milestones']['400']=result
 print('400',result['status'],result.get('refusal'),flush=True)
 if result['status']=='ADMIT':
  from copy import deepcopy
  next_cfg=deepcopy(load(pinned(result['config'])))
  donor=N.produce(cfg,model,mp,camera,depth,600)
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
