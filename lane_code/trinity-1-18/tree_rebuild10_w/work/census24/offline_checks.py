import os,sys,resource,json,hashlib,tarfile,copy,traceback,ast
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(15<<30,15<<30))
C=Path.cwd();B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');T=B/'w24j/work/tree_r1';D=B/'w24j/work/build24m4j'
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(C/'cache'),HF_HOME=str(C/'hf'),TMPDIR=str(C))
index={}
for d in ['build24m4j/inputs','build24m4i/inputs','build24m4h/inputs','build24m4e/inputs','build24m4d/inputs','build24m4d/upload/u']:
 p=B/'w24j/work'/d
 if p.is_dir():
  for f in p.iterdir():
   if f.is_file() and len(f.name)==64 and f.stat().st_size < 5_000_000:index.setdefault(f.name,str(f))
meta=C/'metadata';meta.mkdir(exist_ok=True)
archive=D/'resolver/proofs/real/pool/h_6ed2c7aa/m400/s.tar'
with tarfile.open(archive) as tf:
 for m in tf:
  if m.isfile() and m.size<5_000_000 and m.name.startswith('files/'):
   raw=tf.extractfile(m).read();h=hashlib.sha256(raw).hexdigest()
   if h not in index:
    f=meta/h;f.write_bytes(raw);index[h]=str(f)
for f in (D/'resolver/proofs/real/pool/h_6ed2c7aa/m400').iterdir():
 if f.suffix=='.json':index[hashlib.sha256(f.read_bytes()).hexdigest()]=str(f)
Path('asset_index.json').write_text(json.dumps(index,indent=2)+'\n')
# Only hash-verified replicas are used. Missing files do not fall back to /data or /home.
verified={h:p for h,p in index.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()==h}
Path('verified_asset_index.json').write_text(json.dumps(verified,indent=2)+'\n')
def audit(event,args):
 if event in ('os.remove','os.rmdir','os.rename','subprocess.Popen','os.system','socket.connect'):raise RuntimeError('AUDIT_FORBIDDEN:'+event)
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=os.fsdecode(args[0]);mode=args[1] or '';flags=args[2]
  if p.startswith(('/home/','/data/','/data2/','/data3/','/project/','/lustre/','/scratch/fsw/','/tmp/q_')):raise FileNotFoundError('OFFLINE_UNAVAILABLE:'+p)
  if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)):
   if not Path(p).absolute().is_relative_to(C):raise RuntimeError('AUDIT_WRITE_OUTSIDE_C:'+p)
sys.addaudithook(audit)
sys.path[:0]=[str(T),str(B/'w24j/out/kit_n_go/b')]
from student_pilot.r1_persisted import scope
from student_pilot import b7_inputs,r1_training,r1_handover,r1_coverage,r1_mix,r1_launch22,r0_exclusion
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.checkpoint_space import Budget,plan
from student_pilot.carrier_c1_run import validate,identity
n=json.loads((C/'n_go_c.json').read_text());p=json.loads((B/'inputs/p_configs/cprime_31abe087.json').read_text());patched=copy.deepcopy(n);patched.update(min_pixels=16384,max_pixels=147456,frame_count=32)
results=[];coverage=set()
def trace(frame,event,arg):
 if event=='line' and frame.f_code.co_filename.startswith(str(T)):
  coverage.add((str(Path(frame.f_code.co_filename).relative_to(T)),frame.f_lineno))
 return trace

def check(name,fn):
 record={'name':name};sys.settrace(trace)
 try:
  with scope(verified):v=fn()
  record.update(status='PASS',result=v if isinstance(v,(dict,list,str,int,float,type(None))) else str(type(v)))
 except Exception as e:record.update(status='ERROR',exception=type(e).__name__,output=str(e),traceback=traceback.format_exc())
 finally:sys.settrace(None)
 results.append(record);print(name,record['status'],str(record.get('output',record.get('result')))[:220],flush=True)
check('layout_actual',lambda:b7_inputs.layout(n))
check('layout_pixels_added',lambda:b7_inputs.layout(patched))
check('reader_layout_same_patched',lambda:b7_inputs.reader_layout(patched,patched))
check('recipe_actual',lambda:recipe_for(n))
check('world_one_recipe',lambda:recipe_for(dict(patched,world_size=1)))
check('r1_validate_actual',lambda:r1_training.validate(n))
check('r1_validate_pixels_added',lambda:r1_training.validate(patched))
check('carrier_validate_actual',lambda:validate(n))
check('disk_plan',lambda:dict(expected=plan(n['recipe'],n['checkpoint_disk_guard']['reserve_bytes'],1),given=n['checkpoint_disk_guard']))
check('coverage_deferred',lambda:r1_coverage.deferred(n,read_pins=True))
check('coverage_validate_binding',lambda:r1_coverage.validate_binding(n))
check('r1_sampler_binding_capsule',lambda:r1_mix.validate_binding(n['r2_sampling']))
check('r0_authority',lambda:dict(names=len(r0_exclusion.reserve().names),rooms=len(r0_exclusion.reserve().rooms)))
check('handover_compare_actual',lambda:r1_handover.compare_configs(p,n,replicas=verified))
check('handover_compare_pixels_added',lambda:r1_handover.compare_configs(p,patched,replicas=verified))
check('target_recipe_identical',lambda:dict(equal=recipe_for(n)==n['recipe']))
check('identity_pixels_changed',lambda:dict(actual=identity(n),patched=identity(patched)))
# Direct evaluation of the pixel comparison branch; no stubs or waived checks.
check('handover_pixel_branch',lambda:{k:dict(p=p.get(k,r1_handover.EFFECTIVE_DEFAULTS[k]),n=patched[k],equal=r1_handover.pin_values(p.get(k,r1_handover.EFFECTIVE_DEFAULTS[k]))==r1_handover.pin_values(patched[k])) for k in ('min_pixels','max_pixels','frame_count')})
(C/'offline_results.json').write_text(json.dumps(results,indent=2,default=str)+'\n')
(C/'offline_coverage.json').write_text(json.dumps(sorted(coverage),indent=2)+'\n')
print('Verified small replicas',len(verified),'checks',len(results),'covered source lines',len(coverage))
