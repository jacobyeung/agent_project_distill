from pathlib import Path
import sys,os,json,uuid,time,resource
from contextlib import ExitStack
from unittest.mock import patch
from types import SimpleNamespace
os.sched_setaffinity(0,range(8))
L=Path(__file__).resolve().parents[1]
T=Path(os.environ.get('MODEP_TREE',L/'work/tree'));O=L/'work'/os.environ.get('MODEP_NATIVE_LABEL','native_parity')
O.mkdir(exist_ok=False)
for name in ('tmp','input','proofs'):(O/name).mkdir()
F=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
B=Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/build21')
os.environ.update(MODEP_TEST_TREE=str(T),MODEP_FIXTURE_LANE=str(F),MODEP_FIXTURE_BUILD=str(B),MODEP_FIXTURE_OUTPUT=str(O/'input'),
 R2_FIXTURES=str(F/'fixtures'),R2_LANE_ROOT=str(F),R2_PROOFS=str(O/'proofs'),LANE_TEST_OUTPUT=str(O/'tmp'),TMPDIR=str(O/'tmp'),
 S1_CPU_REHEARSAL='1',R1_MOUNT=str(O/'input'),STUDENT_ORCHARD='1',STUDENT_MODEL_ROOT=str(O/'input/model'),
 STUDENT_FRAME_ROOT_MAP=json.dumps({'/data2':str(O/'input/data2root')}),STUDENT_R2_FRAME_HOST='1')
for k in ('Q_E1','Q_E2','Q_E3','Q_E4','Q_E5'):os.environ.pop(k,None)
import tempfile
tempfile.tempdir=str(O/'tmp')
sys.path[:0]=[str(T),str(F/'work/n1fix2'),str(L/'work/fixture_modules')]
# Keep every write inside this lane, including writes attempted by fixture helpers.
active_writes=None
def guard(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('Fixture deletion forbidden: '+str(args))
 target=None
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):target=path
 elif event in ('os.mkdir','os.rename','os.link','os.symlink'):target=args[1] if event in ('os.rename','os.link','os.symlink') else args[0]
 if event=='open' and target is not None and active_writes is not None:active_writes.add(str(Path(target).resolve()))
 if target is not None and not Path(target).resolve().is_relative_to(L):raise RuntimeError('Fixture write outside lane: '+str(target))
sys.addaudithook(guard)
import importlib
f=importlib.import_module(os.environ.get('MODEP_FIXTURE_MODULE','modep_native_fixture'))
from student_pilot import s1_admission as admission,first_batch_progress as journal
from student_pilot import orchard_paths, s1_exclusions
from student_pilot.p3_provenance import file_pin,load
from student_pilot.r1_persisted import scope,verify
from launch_r1.p_opener_witness import produce as opener
from student_pilot.r1_handover import bind_target
real_clock=time.perf_counter
phase_times=[]
def timed(module,name):
 original=getattr(module,name)
 def run(*args,**kwargs):
  started=real_clock()
  try:return original(*args,**kwargs)
  finally:phase_times.append(dict(function=module.__name__+'.'+name,seconds=real_clock()-started))
 return patch.object(module,name,run)
with ExitStack() as stack:
 native_uname=os.uname()
 fixture_uname=os.uname_result((native_uname.sysname,'fixture-host',native_uname.release,native_uname.version,native_uname.machine))
 stack.enter_context(patch.object(os,'uname',return_value=fixture_uname))
 stack.enter_context(patch.object(f.C,'processor_for',f.processor))
 stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',f.processor))
 # Fixture builders rebind metadata after synthetic frame catalogs are complete.
 builders=ExitStack();stack.callback(builders.close)
 builders.enter_context(patch.object(Path,'open',f.retain_open))
 builders.enter_context(patch.object(Path,'mkdir',f.retain_mkdir))
 cfg,model,mp,camera,depth,room=f.host()
 cfg['exclude_qids']=f.write(O/'input/held_qids.json',dict(vqa=['vqa'+str(i) for i in range(28)]))
 cfg=f.produce(cfg,model,mp,camera,depth,600)
 builders.close()  # Native admission uses the real exclusive file writers and mkdir.
 value=cfg['r1_training']
 closure=verify(value['handover_receipt'],value['p_run'],cfg['init_artifact']['artifact'],value['persisted_files'],weights=True,proof_mode=value['proof_mode'])
 with scope(closure['paths']):
  cfg['routing_vocabulary']=opener(cfg,O/'input/opener.json')
  cfg=bind_target(cfg,O/'input/handover.json')
 pin=f.write(O/'input/request.json',cfg)
 destination=O/'input/admission'
 from student_pilot import s1_routing,r1_routing,mdg_parent
 for module,name in [(f.D,'build_stream'),(f.C,'prepare'),(f.C,'prepared'),(mdg_parent,'bind'),(s1_routing,'build'),(r1_routing,'compose_native'),(admission,'audit_frames')]:
  stack.enter_context(timed(module,name))
 results=[]
 for label,fast,sql in [('off','0','0'),('paths','1','0'),('sql','0','1'),('both','1','1')]:
  destination.mkdir()
  ids=iter(range(1,1000));ticks=iter(range(10000))
  phase_times.clear()
  active_writes=set()
  started=real_clock()
  with scope(closure['paths']),patch.dict(os.environ,S1_PREP_FAST_PATHS=fast,S1_PREP_SELECT_SQL=sql),\
       patch.object(orchard_paths,'_resolve_read_fast',wraps=orchard_paths._resolve_read_fast) as path_spy,\
       patch.object(s1_exclusions,'_selected_rows',wraps=s1_exclusions._selected_rows) as sql_spy,\
       patch.object(uuid,'uuid4',side_effect=lambda:uuid.UUID(int=next(ids))),\
       patch.object(time,'perf_counter',side_effect=lambda:float(next(ticks))),\
       patch.object(resource,'getrusage',return_value=SimpleNamespace(ru_maxrss=12345)):
   report=admission.admit(pin,destination,[str(O/'input')],threads=8,memory_gib=16,sample_size=8,prepare_only=True,attempt='a'*32)
  calls=dict(paths=path_spy.call_count,sql=sql_spy.call_count)
  assert bool(calls['paths']) == (fast=='1'), calls
  assert bool(calls['sql']) == (sql=='1'), calls
  frame_report=load(next(destination.glob('frames_*/frames.json')))
  assert all(value['unique_frames'] > 1 for value in frame_report['sources'].values()), frame_report
  written=sorted(active_writes);active_writes=None
  assert all(Path(name).is_relative_to(destination) for name in written),written
  files={str(p.relative_to(destination)):file_pin(p)['sha256'] for p in sorted(destination.rglob('*')) if p.is_file()}
  result=dict(label=label,path_calls=calls,frame_sources=frame_report['sources'],native_python_writes=written,files=files,seconds=real_clock()-started,status=report['status'],phase_times=list(phase_times),observed_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if results:assert files==results[0]['files'],[(k,v,results[0]['files'].get(k)) for k,v in files.items() if v!=results[0]['files'].get(k)]
  if results:
   for name in files:assert (destination/name).read_bytes()==(O/'retained_off'/name).read_bytes(),name
  result['byte_compared']=bool(results)
  results.append(result)
  destination.rename(O/('retained_'+label))
  print('MODEP_PARITY '+json.dumps(dict(label=label,files=len(files),seconds=result['seconds'],identical=True,path_calls=calls,unique_frames={k:v['unique_frames'] for k,v in frame_report['sources'].items()})),flush=True)
 (O/'RESULT.json').write_text(json.dumps(dict(results=results,telemetry_fixed=['resources.seconds','resources.peak_rss_kib'],uuid_fixed=True,paths_fixed=True),indent=2)+'\n')
