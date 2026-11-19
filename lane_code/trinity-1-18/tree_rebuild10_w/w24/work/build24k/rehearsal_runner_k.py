from pathlib import Path
import sys,json,os,signal,subprocess,time,base64,hashlib
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';R=D/'rehearsal_k';ns='/tmp/q_22c714e1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f')]
import joblib as J
from kit24f import reseal
kit=R/'kit_n_go';py=sys.executable;records=[]
def rss(pid):
 try:
  own=int(next(s.split()[1] for s in Path(f'/proc/{pid}/status').read_text().splitlines() if s.startswith('VmRSS:')))*1024
  return own+sum(rss(int(p)) for p in Path(f'/proc/{pid}/task/{pid}/children').read_text().split())
 except (OSError,StopIteration):return 0
def run(stage,cmd,phase='fresh'):
 env={**os.environ,'TK_REHEARSAL_PHASE':phase,'S1_REHEARSAL_ATTEMPT':'b24k_'+phase,'SLURM_JOB_ID':'91'}
 env['TK_JOB_START']=str(int(time.time())-90000) if phase=='budget' else os.environ['TK_JOB_START'] if phase=='fresh' else str(int(time.time()))
 peak=0
 with (R/(stage+'.log')).open('w') as log:
  p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  while p.poll() is None:
   peak=max(peak,rss(os.getpid()))
   if peak>19_000_000_000:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=30);raise RuntimeError('Aggregate 19 GB guard; no retry')
   time.sleep(1)
 records.append(dict(stage=stage,returncode=p.returncode,peak_rss_bytes=peak,TK_JOB_START=env['TK_JOB_START']))
 J.write(R/'STAGES.json',records);print(stage,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(stage+' refused; inspect its log; no automatic retry')
if (R/'STAGES.json').exists():raise ValueError('Preserve existing rehearsal before another attempt')
args=['--ro-bind' if x=='--bind' else x for x in J.load(L/'work/build24d/GO_VIEW.json')]
args+=['--bind',str(R),str(R),'--bind',str(R),ns]
J.write(R/'VIEW.json',args)
# Both passes use the same logical paths and the same planner/copier. Only the
# fixture routing comparison omits the production-only ca0616db equality check.
run('routing',args+[py,'-B',str(D/'rehearsal_boundary.py'),str(kit/'b/a.py'),'r',ns+'/p2',ns+'/r2.json'])
selection=R/'p2/routing_selection.json';h=J.sha(selection);(R/'target/u'/h).write_bytes(selection.read_bytes())
(R/'p2').rename(R/'routing_retained')
host=J.load(kit/'k/h.json');host['routing_selection']=dict(path='u/'+h,sha256=h)
doc=json.loads((kit/'k/h.json').read_text());raw=(json.dumps(host,sort_keys=True,indent=2)+'\n').encode()
doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());(kit/'k/h.json').write_text(json.dumps(doc))
request=J.load(R/'r2.json');request['_resolved']['kit_sha256']=reseal(kit);J.write(R/'r2.json',request)
run('canary',args+[py,'-B',str(D/'rehearsal_boundary.py'),str(kit/'b/a.py'),'q',ns+'/p2',ns+'/r2.json'])
result=J.load(R/'p2/q/RESULT.json');assert result['status']=='ADMIT' and result['host_receipt']['sha256']==J.sha(R/'p2/q/host.json')
run('rooms',args+[py,'-B',str(kit/'b/d.py'),ns+'/p2/s',ns+'/r.json',ns+'/n.json',ns+'/rooms.json'])
run('v_config',args+[py,'-B',str(kit/'b/h.py'),ns+'/p2',ns+'/v.json'])
run('review',args+[py,'-B',str(D/'rehearsal_review.py')])
copier=subprocess.Popen([py,'-I','-B',str(D/'rehearsal_copier.py')])
try:
 for phase in ('fresh','budget','resume'):
  if phase!='fresh':run('authorize_'+phase,args+[py,'-B',str(D/'rehearsal_authorize.py'),phase],phase)
  run('train_'+phase,args+[py,'-B',str(D/'rehearsal_boundary.py'),str(kit/'b/t.py'),ns+'/p2',ns+'/v.json'],phase)
finally:
 copier.send_signal(signal.SIGTERM);copier.wait(timeout=60)
