import json,os,re,subprocess,time,traceback
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).parent
DATA=Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')
R=DATA/'runtime_control/gt_teacher_r1313/RELAUNCH_20260918'
ROOT=DATA/'collection_gt_r1313'
PKG=Path('/home/jjyeung/agent_project_r1313_gt_teacher/agent/rounds/candidates/r1313_vsi_distill_gt_training')
PKGS=(PKG,Path('/home/jjyeung/agent_project_distill/collector'))
PY='/data2/jjyeung/envs/planner/bin/python'
COORD='/home/jjyeung/agent_project/agent/coord.py'
WORK='training_trace_collection__r1313_gt__train50k__s17__76e67ed6e8'
os.environ.update(HF_HOME='/data2/jjyeung/cache/huggingface',HUGGINGFACE_HUB_CACHE='/data2/jjyeung/cache/huggingface/hub',TORCH_HOME='/data2/jjyeung/cache/torch',PIP_CACHE_DIR='/data2/jjyeung/cache/pip',AGENT_ID='req232-gt-teacher-r1313',AGENT_COORD_DIR='/data2/jjyeung/agent_project/.coord',PYTHONDONTWRITEBYTECODE='1')
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def append(p,d):
 with p.open('a') as f:f.write(json.dumps(d)+'\n')
def procs():
 result=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
   collector=any(str(pkg/'collect.py') in args for pkg in PKGS) and any(x in args for x in ('worker','start'))
   episode=any(str(pkg/'run_experiment_r1313.py') in args for pkg in PKGS) and any(a.startswith(str(ROOT/'attempts')+'/') for a in args)
   if not (collector or episode):continue
   stat=(p/'stat').read_text().split();result.append(dict(pid=int(p.name),start_ticks=stat[21],uid=p.stat().st_uid,args=args,state=stat[2]))
  except (OSError,UnicodeError):continue
 return result
start=time.time();last_hb=0;last_lease=0;last_census=0;last_status=0;census=None;census_log=None;summary=None;last_terms=None;silent=0
save(OUT/'MONITOR_IDENTITY.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],utc=now()))
while not ((OUT/'MONITOR_STOP').exists() and (OUT/'MONITOR_STOP').read_text().strip()==str(os.getpid())):
 tick=time.time()
 try:
  ps=procs();workers=[p for p in ps if 'worker' in p['args']];controllers=[p for p in ps if 'start' in p['args']];children=[p for p in ps if any(str(pkg/'run_experiment_r1313.py') in p['args'] for pkg in PKGS)]
  terms=list((ROOT/'terminals').glob('*.json'))
  errors=[dict(path=str(p),mtime=p.stat().st_mtime,data=json.loads(p.read_text())) for p in (ROOT/'pool_b16384/worker_errors').glob('*.json')]
  lock_errors=[p for p in errors if 'POOL_CAP.lock' in p['data'].get('message','')]
  target=json.loads((ROOT/'pool_b16384/WORKER_TARGET.json').read_text())['total_workers']
  silent=silent+1 if last_terms is not None and len(terms)==last_terms else 0
  obs=dict(utc=now(),unix=tick,controllers=controllers,workers=workers,worker_count=len(workers),episode_children=children,episode_child_count=len(children),target=target,terminals=len(terms),new_terminals=None if last_terms is None else len(terms)-last_terms,lock_timeouts_total=len(lock_errors),lock_timeouts_since_watchdog=sum(e['mtime']>=start for e in lock_errors),silent_checks=silent)
  
  if terms and workers+children and tick-max(p.stat().st_mtime for p in terms)>=1800:
   save(OUT/'ALARM_FINALIZATION_FLAT.json',dict(utc=now(),reason='No new terminal for 30 minutes while episode processes remain',worker_count=len(workers),episode_children=len(children)))
  append(OUT/'OBSERVATIONS_v5.jsonl',obs);save(OUT/'HEALTH_v5.json',obs);last_terms=len(terms)
  if silent==2:
   logs=sorted((ROOT/'logs').glob('*.log'),key=lambda p:p.stat().st_mtime,reverse=True)[:3]
   append(OUT/'SILENCE_DEBUG.jsonl',dict(utc=now(),workers=len(workers),target=target,latest_errors=errors[-5:],logs=[dict(path=str(p),tail=p.read_text(errors='replace')[-2500:]) for p in logs]))
  if tick-last_hb>=300:
   with (OUT/'HEARTBEAT.log').open('a') as f:f.write(f'{now()} | monitor: {len(controllers)} controller, {len(workers)} workers, {len(terms)} terminals, target {target}\n')
   last_hb=tick
  if not controllers and tick-last_lease>=600:
   p=subprocess.run([PY,'-B',COORD,'heartbeat',WORK,'--note','Watchdog v5 supervising bounded recovery on '+os.uname().nodename],capture_output=True,text=True,timeout=120)
   append(OUT/'LEASE_HEARTBEATS.jsonl',dict(utc=now(),rc=p.returncode,output=p.stdout,stderr=p.stderr));last_lease=tick
  if census is not None and census.poll() is not None:
   census_log.close()
   if census.returncode==0:
    summary=json.loads(census_path.read_text());save(OUT/'LATEST_CENSUS.json',summary)
   else:append(OUT/'MONITOR_ERRORS.jsonl',dict(utc=now(),error='census failed',rc=census.returncode,log=str(census_path)))
   census=None
  if tick-last_census>=600 and census is None:
   census_path=OUT/f'census_{int(tick)}.json';census_log=census_path.open('w')
   census=subprocess.Popen([PY,'-B',str(PKG/'census.py'),'--run-root',str(ROOT),'--output-root',str(DATA/'census_r1313')],stdout=census_log,stderr=(OUT/'census_stderr.log').open('a'));last_census=tick
  if tick-last_status>=600 or (summary and not (R/'STATUS_v5.md').exists()):
   finalized=[];calls=[];nulls=0;rate_errors=[]
   for q in (ROOT/'attempts').iterdir():
    p=q/'b16384/finalized'/q.name/f'trace_{q.name}.json'
    if not p.exists():continue
    d=json.loads(p.read_text());ft=datetime.fromisoformat(d['finished_utc'].replace('Z','+00:00')).timestamp();finalized.append(ft);nulls+=d.get('pred') is None
    err=str(d.get('error') or '')
    if re.search(r'\b429\b|RESOURCE_EXHAUSTED|rate.?limit',err,re.I):rate_errors.append(dict(path=str(p),error=err[:300]))
    for fam in (d.get('llm_usage') or {}).values():
     if not isinstance(fam,dict):continue
     for call in fam.get('calls_detail',[]):
      calls.append((call.get('started_unix',0),(call.get('usage') or {}).get('input_tokens',0)))
      err=str(call.get('error') or '')
      if re.search(r'\b429\b|RESOURCE_EXHAUSTED|rate.?limit',err,re.I):rate_errors.append(dict(path=str(p),error=err[:300]))
   rates={str(m):sum(tick-m*60<=t<=tick for t in finalized)*60/m for m in (10,30,60)}
   tokens=sum(n for t,n in calls if tick-600<=t<=tick)/10
   admissions=json.loads((R/'ADMISSION_STATE_v5.json').read_text()) if (R/'ADMISSION_STATE_v5.json').exists() else {'ready_questions':0}
   attempted=summary['distinct_attempted'] if summary else None;remaining=admissions['ready_questions']-attempted if attempted is not None else None
   controller_log=(R/'controller_v5.log').read_text(errors='replace') if (R/'controller_v5.log').exists() else ''
   coordination_timeouts=controller_log.count('subprocess.TimeoutExpired:')
   metrics=dict(coordination_timeouts=coordination_timeouts,host=os.uname().nodename,utc=now(),census=summary,questions_per_hour=rates,completed_trace_input_tokens_per_minute_10m=tokens,tokens_per_worker_minute=tokens/len(workers) if workers else None,null_predictions=nulls,rate_error_count=len(rate_errors),rate_errors=rate_errors,admitted=admissions['ready_questions'],remaining=remaining,eta_hours=remaining/rates['10'] if remaining is not None and rates['10'] else None)
   append(OUT/'METRICS_v5.jsonl',metrics);save(OUT/'LATEST_METRICS.json',metrics)
   status=f'Collector status at {now()}.\n\nHost {os.uname().nodename}. Controller PIDs: {[p["pid"] for p in controllers]}; live workers {len(workers)}; episode children {len(children)}; target {target}. Watchdog PID: {(R/"watchdog_v5.pid").read_text().strip() if (R/"watchdog_v5.pid").exists() else "pending admission"}.\n\n'
   if summary:status+=f'Fresh immutable census: {summary["snapshot"]}/SUMMARY.json. Attempted {attempted}; finalized {summary["distinct_finalized"]}; accepted {summary["distinct_accepted"]}; accepted/attempted {summary["yield_over_all_attempted"]:.2%}; accepted/finalized {summary["distinct_accepted"]/max(1,summary["distinct_finalized"]):.2%}.\n\n'
   status+=f'Questions/hour (10/30/60 minutes): {rates}. Input tokens/min over 10 minutes: {tokens:,.0f}; completed-trace accounting excludes unfinished episodes and calls. Null final predictions: {nulls}.\n\nPOOL_CAP lock timeouts: {len(lock_errors)} total, {obs["lock_timeouts_since_watchdog"]} since watchdog launch. Coordination timeouts: {coordination_timeouts}. Trace error 429/rate matches: {len(rate_errors)}.\n\nAdmitted: {admissions["ready_questions"]}; unattempted admissible remaining: {remaining}; ETA hours at 10-minute finalization rate: {metrics["eta_hours"]}.\n\nContention ceiling: 24 until a tolerant successor is sealed; see WATCHDOG_EVENTS.jsonl for target changes. Atomic claims prevent duplicate episodes; controllers do not adopt survivor processes. Every relaunch allows three minutes, sends SIGTERM, waits 30 seconds, then sends SIGKILL to verified survivors.\n'
   (R/'STATUS_v5.md').write_text(status)
   note=f'r1313 watchdog active; controllers {len(controllers)}, workers {len(workers)}/{target}, terminals {len(terms)}, lock timeouts since watchdog {obs["lock_timeouts_since_watchdog"]}; census '+(f'{attempted}/{summary["distinct_finalized"]}/{summary["distinct_accepted"]}' if summary else 'pending')
   p=subprocess.run([PY,'-B',COORD,'status','--state','running','--work-id',WORK,'--note',note],capture_output=True,text=True,timeout=120)
   append(OUT/'COORD_STATUS.jsonl',dict(utc=now(),rc=p.returncode,output=p.stdout,stderr=p.stderr));last_status=tick
 except Exception:
  append(OUT/'MONITOR_ERRORS.jsonl',dict(utc=now(),error=traceback.format_exc()))
 time.sleep(max(1,60-(time.time()-tick)))
