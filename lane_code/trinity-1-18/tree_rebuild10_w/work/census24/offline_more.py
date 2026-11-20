import sys,os,json,resource,copy,traceback
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(15<<30,15<<30))
C=Path.cwd(); B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');T=B/'w24j/work/tree_r1'
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TMPDIR=str(C))
def audit(e,a):
 if e in ('os.remove','os.rmdir','subprocess.Popen','os.system','socket.connect'):raise RuntimeError('AUDIT_FORBIDDEN:'+e)
 if e=='open' and isinstance(a[0],str) and a[0].startswith(('/home/','/data/','/data2/','/data3/','/project/','/lustre/','/scratch/fsw/','/tmp/q_')):raise FileNotFoundError('OFFLINE_UNAVAILABLE:'+a[0])
sys.addaudithook(audit);sys.path.insert(0,str(T))
from student_pilot.r1_persisted import scope,init_policy
from student_pilot.r1_handover import compare_configs
from student_pilot.carrier_c1_sweep import recipe_for
n=json.loads((C/'n_go_c.json').read_text());p=json.loads((B/'inputs/p_configs/cprime_31abe087.json').read_text());x=copy.deepcopy(n);x.update(min_pixels=16384,max_pixels=147456,frame_count=32)
idx=json.loads((C/'source_asset_index.json').read_text());out=[]
def check(name,fn):
 try:
  with scope(idx):v=fn()
  r=dict(name=name,status='PASS',result=v)
 except Exception as e:r=dict(name=name,status='ERROR',exception=type(e).__name__,output=str(e),traceback=traceback.format_exc())
 out.append(r);print(name,r['status'],str(r.get('output',r.get('result')))[:500],flush=True)
check('handover_actual_with_p_preparation',lambda:compare_configs(p,n,metadata=[n['r1_training']['p_run']['preparation']],replicas=idx))
check('handover_pixels_with_p_preparation',lambda:compare_configs(p,x,metadata=[n['r1_training']['p_run']['preparation']],replicas=idx))
check('init_policy_actual',lambda:init_policy(n['r1_training']))
# Conditions evaluated individually, without claiming that full R1 validate completed.
import ast,math
mod=ast.parse((T/'student_pilot/r1_training.py').read_text());fn=next(v for v in mod.body if isinstance(v,ast.FunctionDef) and v.name=='validate')
card=json.loads(Path(idx[n['r1_training']['mix']['sha256']]).read_text());env=dict(cfg=n,value=n['r1_training'],recipe=recipe_for(n),card=card,scale=n['r1_training']['weight_scale'],stop=n['r1_training']['stop_after_step'],math=math)
for node in fn.body:
 if isinstance(node,ast.If) and len(node.body)==1 and isinstance(node.body[0],ast.Raise):
  check('predicate:r1_training.py:'+str(node.body[0].lineno),lambda node=node:dict(refuses=bool(eval(compile(ast.Expression(node.test),'<static-predicate>','eval'),env)),condition=ast.unparse(node.test),error=ast.unparse(node.body[0].exc)))
Path('offline_more_results.json').write_text(json.dumps(out,indent=2)+'\n')
