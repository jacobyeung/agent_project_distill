import os,sys,json,resource,traceback,copy,hashlib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(15<<30,15<<30))
C=Path.cwd();B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');T=B/'w24j/work/tree_r1'
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TMPDIR=str(C))
sys.path[:0]=[str(T),str(B/'w24j/out/kit_n_go/b')]
def audit(e,a):
 if e in ('os.remove','os.rmdir','subprocess.Popen','os.system','socket.connect'):raise RuntimeError('AUDIT_FORBIDDEN:'+e)
 if e=='open' and isinstance(a[0],str) and a[0].startswith(('/home/','/data/','/data2/','/data3/','/project/','/lustre/','/scratch/fsw/','/tmp/q_')):raise FileNotFoundError('OFFLINE_UNAVAILABLE:'+a[0])
sys.addaudithook(audit)
from student_pilot import r1_persisted,r1_absence,r1_coverage,r1_launch22,r1_direction_twins,r2_contract,r1_handover
from student_pilot.p3_provenance import load,pinned
import rb
n=json.loads((C/'n_go_c.json').read_text());idx=json.loads((C/'source_asset_index.json').read_text());cfg=copy.deepcopy(n)
cfg['r1_training']['persisted_files']={h:idx.get(h,str(C/'absent'/h)) for h in n['r1_training']['persisted_files']}
results=[];cov=set()
def trace(f,e,a):
 if e=='line' and f.f_code.co_filename.startswith(str(T)):cov.add((str(Path(f.f_code.co_filename).relative_to(T)),f.f_lineno))
 return trace

def check(name,fn):
 sys.settrace(trace)
 try:
  with r1_persisted.scope(idx):v=fn()
  r=dict(name=name,status='PASS',result=v)
 except Exception as e:r=dict(name=name,status='ERROR',exception=type(e).__name__,output=str(e),traceback=traceback.format_exc())
 finally:sys.settrace(None)
 results.append(r);print(name,r['status'],str(r.get('output',r.get('result')))[:250],flush=True)
check('handover_receipt_present',lambda:load(pinned(cfg['r1_training']['handover_receipt'])))
check('persisted_metadata_verify',lambda:r1_persisted.verify(cfg['r1_training']['handover_receipt'],cfg['r1_training']['p_run'],cfg['init_artifact']['artifact'],cfg['r1_training']['persisted_files'],weights=False,proof_mode=cfg['r1_training']['proof_mode'],init_policy=cfg['r1_training']['init_policy']))
check('donor_metadata',lambda:r1_handover.donor(cfg,load(pinned(cfg['init_artifact']['artifact']))))
check('absence_gf1_config',lambda:r1_absence.configuration(n,'heads_gf1_connector'))
check('absence_embeddings_config',lambda:r1_absence.configuration(n,'heads_frame_embeddings'))
check('launch22_removal_order',lambda:r1_launch22.validate_removals(n))
check('deferred_card',lambda:r1_coverage.deferred_card(load(pinned(n['r1_training']['mix']))))
check('twins_specs',lambda:r1_direction_twins.specifications(n))
check('init_identity',lambda:r2_contract.bound_init(n))
check('routing_status',lambda:rb.routing_status(n))
# Inspect authenticated P composition and row-frame declarations, without row databases.
def receipt_closure():
 out={}
 for stream,pin in n['streams'].items():
  try:
   r=load(pinned(pin));out[stream]=r
  except Exception as e:out[stream]={'offline_error':str(e)}
 return out
check('stream_receipt_metadata',receipt_closure)
Path('metadata_results.json').write_text(json.dumps(results,indent=2,default=str)+'\n');Path('metadata_coverage.json').write_text(json.dumps(sorted(cov),indent=2)+'\n')
