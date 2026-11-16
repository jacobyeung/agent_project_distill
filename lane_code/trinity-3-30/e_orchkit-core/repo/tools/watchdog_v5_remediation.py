"""Supervise the sealed collector with bounded recovery and asynchronous resizing."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from recover_boundary_remediation import R,ROOT,PKG,OUT,now,save,processes,identity,signal_exact
PY='/data2/jjyeung/envs/planner/bin/python'
os.environ.update(PYTHONDONTWRITEBYTECODE='1',AGENT_COORD_DIR='/data2/jjyeung/agent_project/.coord',AGENT_ID='req232-gt-teacher-r1313',HF_HOME='/data2/jjyeung/cache/huggingface',HUGGINGFACE_HUB_CACHE='/data2/jjyeung/cache/huggingface/hub',TORCH_HOME='/data2/jjyeung/cache/torch',PIP_CACHE_DIR='/data2/jjyeung/cache/pip')
def event(kind,**data):
 with (OUT/'WATCHDOG_EVENTS.jsonl').open('a') as f:
  f.write(json.dumps(dict(utc=now(),event=kind,**data))+'\n');f.flush();os.fsync(f.fileno())
def errors():
 return [dict(path=str(p),mtime=p.stat().st_mtime,data=json.loads(p.read_text())) for p in (ROOT/'pool_b16384/worker_errors').glob('*.json')]
def logtail():
 p=R/'controller_v5.log'
 if not p.exists():return ''
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-12000));return f.read().decode(errors='replace')
def request_resize(n):
 path=R/f'resize_v5_{time.time_ns()}.log'
 event('resize_requested',workers=n,log=str(path))
 with path.open('ab',buffering=0) as log:
  proc=subprocess.Popen([PY,'-B',str(PKG/'collect.py'),'set-workers','--config',config,'--workers',str(n)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 return dict(proc=proc,target=n,path=path,started=time.time())
lock=(Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/RELAUNCH_20260918/watchdog_v5.flock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
config=json.loads((R/'ADMISSION_STATE_v5.json').read_text())['config']
me=identity(os.getpid());me.update(host=os.uname().nodename,utc=now());save(R/'watchdog_identity_v5.json',me);(R/'watchdog_v5.pid').write_text(str(os.getpid())+'\n')
controller=None;controller_id=None;phase='prepare_launch';deadline=0;launches=[];target=16;last_ramp=0;last_hb=0;seen={e['path'] for e in errors()};cooldown=False;rate_seen=0;baseline_terms=0;resize=None;ready_target=None
save(R/'watchdog_control_v5.json',dict(config=config,workers=16,enabled=True,ceiling=64))
pool=ROOT/'pool_b16384'
seen_coord={p.name for p in (pool/'coordination_failures').glob('*.json')}
seen_contention={str(p) for p in (pool/'worker_telemetry').glob('*/*.json')}
metrics=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_r1313_watchdog_v5/out/LATEST_METRICS.json')
if metrics.exists():rate_seen=json.loads(metrics.read_text()).get('rate_error_count',0)
seen_terms=set();finalized=0;null_predictions=0;last_progress=time.time()
event('watchdog_started',identity=me,ceiling=64,reason='reviewed tolerant successor; ramp from 16 to ceiling 64')
try:
 while True:
  tick=time.time()
  if (ROOT/'pool_b16384/BLOCKED.json').exists():raise RuntimeError('durable collector BLOCKED; operator review required')
  control=json.loads((R/'watchdog_control_v5.json').read_text())
  if not control.get('enabled',True):raise RuntimeError('operator paused watchdog')
  requested=control.get('workers',target)
  if type(requested) is not int or not 0<=requested<=64:raise ValueError('worker target outside 0..64')
  if requested!=target:target=requested;cooldown=True

  if tick-last_hb>=300:
   with (OUT/'HEARTBEAT.log').open('a') as f:f.write(f'{now()} | watchdog phase {phase}, target {target}, host {os.uname().nodename}\n')
   last_hb=tick
  for path in (ROOT/'terminals').glob('*.json'):
   if path.name in seen_terms:continue
   row=json.loads(path.read_text());qid=row['question_id']
   trace=Path(row['output'])/'finalized'/qid/f'trace_{qid}.json'
   if trace.is_file():
    value=json.loads(trace.read_text());seen_terms.add(path.name);finalized+=1
    null_predictions+=value.get('pred') is None;last_progress=tick
  if null_predictions or tick-last_progress>=1800:
   save(OUT/'WATCHDOG_ALARM.json',dict(utc=now(),finalized=finalized,null_predictions=null_predictions,seconds_without_finalized_progress=tick-last_progress))
  new=[e for e in errors() if e['path'] not in seen];seen.update(e['path'] for e in new)
  lock_errors=[e for e in new if 'timed out acquiring' in e['data'].get('message','')]
  if new:event('new_worker_errors',errors=new)
  if controller is not None and controller.poll() is not None:
   tail=logtail();event('controller_exit',identity=controller_id,returncode=controller.returncode,newest_worker_errors=sorted(errors(),key=lambda e:e['mtime'])[-12:],log_tail=tail)
   if 'TimeoutExpired' in tail:cooldown=True
   if controller.returncode==0:
    event('collection_complete');break
   controller=None;phase='grace';deadline=tick+180;ready_target=None
   event('orphan_grace_started',deadline_unix=deadline,processes=processes(),terminals=len(list((ROOT/'terminals').glob('*.json'))))
  contention=[p for p in (pool/'worker_telemetry').glob('*/*.json') if str(p) not in seen_contention]
  seen_contention.update(str(p) for p in contention)
  coordination=[p for p in (pool/'coordination_failures').glob('*.json') if p.name not in seen_coord]
  seen_coord.update(p.name for p in coordination)
  if any(json.loads(p.read_text()).get('error',{}).get('type')=='TimeoutExpired' for p in coordination):
   cooldown=True;event('coordination_timeout_cooldown',receipts=[str(p) for p in coordination])
  if lock_errors or contention:
   target=max(8,target-8);cooldown=True;last_ramp=tick;event('lock_stepdown',target=target,errors=lock_errors,contention_receipts=[str(p) for p in contention])
  metrics_path=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_r1313_watchdog_v5/out/LATEST_METRICS.json')
  if metrics_path.exists():
   rate_count=json.loads(metrics_path.read_text()).get('rate_error_count',0)
   if rate_count>rate_seen:
    rate_seen=rate_count;target=max(8,target//2);cooldown=True;last_ramp=tick;event('rate_limit_stepdown',target=target,recorded_matches=rate_count)
  if resize is not None:
   rc=resize['proc'].poll()
   if rc is not None:
    event('resize_finished',workers=resize['target'],rc=rc,log=str(resize['path']),output=resize['path'].read_text())
    if rc:raise RuntimeError('resize refused; inspect resize log')
    ready_target=resize['target'];resize=None;last_ramp=time.time();baseline_terms=len(list((ROOT/'terminals').glob('*.json')))
    save(R/'watchdog_control_v5.json',dict(config=config,workers=target,enabled=True,ceiling=64))
   elif tick-resize['started']>14400:
    resize['proc'].terminate();raise RuntimeError('resize validation exceeded four hours')
  if phase=='grace':
   ps=processes()
   if any('start' in p['args'] for p in ps):raise RuntimeError('foreign controller appeared during orphan recovery')
   event('orphan_grace_check',processes=ps,terminals=len(list((ROOT/'terminals').glob('*.json'))))
   if not ps:phase='prepare_launch'
   elif tick>=deadline:
    for p in ps:signal_exact(p,signal.SIGTERM)
    event('orphan_SIGTERM',identities=ps);phase='term_wait';deadline=time.time()+30
  elif phase=='term_wait' and tick>=deadline:
   ps=processes()
   if any('start' in p['args'] for p in ps):raise RuntimeError('foreign controller appeared after graceful stop')
   if ps:raise RuntimeError('survivors after graceful stop; refusing overlap')
   phase='verify_zero';deadline=time.time()+5
  elif phase=='verify_zero' and tick>=deadline:
   if processes():raise RuntimeError('survivors after graceful stop; refusing overlap')
   phase='prepare_launch'
  if phase=='running' and target<64 and time.time()-last_ramp>=600 and not cooldown and resize is None and len(list((ROOT/'terminals').glob('*.json')))>baseline_terms:
   target=min(64,target+8);event('clean_ramp_requested',target=target)
  if phase in ('prepare_launch','running') and resize is None and ready_target!=target:
   resize=request_resize(target)
  if phase=='prepare_launch' and resize is None and ready_target==target:
   if processes():raise RuntimeError('processes exist at launch boundary')
   launches=[t for t in launches if tick-t<3600]
   if len(launches)>=12:raise RuntimeError('12 launches/hour cap exhausted')
   with (R/'controller_v5.log').open('ab',buffering=0) as log:
    controller=subprocess.Popen([PY,'-B',str(PKG/'collect.py'),'start','--config',config,'--workers',str(target)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=PKG)
   controller_id=identity(controller.pid);controller_id.update(host=os.uname().nodename)
   launches.append(time.time());last_ramp=time.time();phase='running';baseline_terms=len(list((ROOT/'terminals').glob('*.json')))
   (R/'controller_v5.pid').write_text(f'PID:{controller.pid} HOST:{os.uname().nodename}\n')
   receipt=dict(utc=now(),controller=controller_id,watchdog=me,config=config,workers=target)
   save(R/'LAUNCH_RECEIPT_v5.json',receipt);event('controller_launch',receipt=receipt)
  save(R/'watchdog_control_v5.json',dict(config=config,workers=target,enabled=True,ceiling=64))
  save(OUT/'WATCHDOG_HEALTH.json',dict(utc=now(),phase=phase,target=target,controller=controller_id,watchdog=me,cooldown=cooldown,finalized=finalized,null_predictions=null_predictions,seconds_without_finalized_progress=tick-last_progress,resize_pid=resize['proc'].pid if resize else None))
  time.sleep(5 if phase in ('term_wait','verify_zero') else 60)
except BaseException as exc:
 event('watchdog_failure',error=repr(exc),traceback=traceback.format_exc());save(OUT/'BLOCKED.json',dict(utc=now(),reason=repr(exc)));raise
