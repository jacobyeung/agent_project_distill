import base64,hashlib,json,os,shutil,stat,subprocess,sys,tarfile,time
from pathlib import Path

CHECKS=('seal','probe','full_before_start','full_during_copy','nonfatal','m100','ck00','ckstop',
        'final_order','response_fields','archive_while_full','local_retry','automatic_recovery','archive_after_recovery','rate','upload_logging')

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def load(p):
 v=json.loads(Path(p).read_bytes())
 if isinstance(v,dict) and v.get('encoding')=='base64-json':
  raw=base64.b64decode(v['payload'],validate=True)
  if hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('E02')
  return json.loads(raw)
 return v

def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')

def fail(n,code):
 p=n/'E3.json';v=load(p) if p.exists() else dict(checks=dict.fromkeys(CHECKS,'FAIL'),objects=[])
 v['status']='FAIL';v['checks'][code]='FAIL';write(p,v)

def stage(d,n,x,job):
 # Stage the report writer before any prerequisite can refuse.
 for name in ('e3.py','observe.py','run.sh'):shutil.copyfile(d/name,n/name)
 pins=load(d/'pins.json')
 for name,h in pins.items():
  if sha(d/name)!=h:raise ValueError('E03')
 shutil.copyfile(d/'k.tgz',n/'k.tgz')
 with tarfile.open(n/'k.tgz','r:gz') as t:
  for m in t.getmembers():
   if not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('E04')
  t.extractall(n/'k',filter='data')
 k=n/'k'
 rows={name:h for h,name in (s.split('  ',1) for s in (k/'SHA256SUMS.txt').read_text().splitlines())}
 actual={str(p.relative_to(k)):sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
 if actual!=rows:raise ValueError('E05')
 if load(k/'BUILD.json')['kit_sha256']!=sha(k/'SHA256SUMS.txt'):raise ValueError('E06')
 p=subprocess.run([sys.executable,'-I','-s','-B',str(k/'b/v.py'),str(k)],capture_output=True,text=True)
 if p.returncode or p.stdout.strip()!=sha(k/'SHA256SUMS.txt'):raise ValueError('E07')
 if load(k/'k/p.json')['n_root']!=str(x):raise ValueError('E08')
 checks=dict.fromkeys(CHECKS,'FAIL');checks['seal']='PASS'
 write(n/'E3.json',dict(status='PENDING',checks=checks,seal=sha(k/'SHA256SUMS.txt'),objects=[],job=job))
 # Read capabilities with the same ownership and mode requirements as pc.py.
 fd=os.open(x/'n_s',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  s=os.fstat(fd)
  if s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('E09')
  f=os.open('sess_'+job+'.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  with os.fdopen(f,'rb') as stream:
   s=os.fstat(stream.fileno())
   if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o600:raise ValueError('E10')
   raw=stream.read(2_000_001)
 finally:os.close(fd)
 if len(raw)>2_000_000:raise ValueError('E11')
 values=json.loads(raw)
 expected={v+'.j'+job+f'.part{i:02d}-of-04' for v in load(k/'k/y.json')['objects'].values() for i in range(4)}
 if not expected.issubset(values):raise ValueError('E101')
 (n/'sess.json').write_bytes(raw);(n/'sess.json').chmod(0o600)
 # Keep one observer outside the sealed kit. It forwards the real response bytes.
 (n/'bin/python3').write_text('#!/bin/bash\nexec "$E3_PY" -I -s -B "$E3_N/observe.py" "$@"\n')
 (n/'bin/python3').chmod(0o700)
 print('E3_STAGE_PASS')

def run(n,x,job):
 k=n/'k';node=n/'n';node.mkdir();train=node/'p/q/r';train.mkdir(parents=True)
 os.environ['TK_UPLOAD_CHUNK_BYTES']=str(256<<10)
 (node/'live_spool').mkdir();(node/'live_spool/stop.request').write_text('requested')
 for label,marker,step in (('m100','artifact.json',100),('checkpoint_7','complete.json',7)):
  d=train/label;d.mkdir()
  size=int(os.environ.get('E3_LOCAL_BYTES','0')) or ((2<<30) if label.startswith('checkpoint') else 3<<20)
  with (d/'q.bin').open('wb') as f:
   for _ in range(size//(1<<20)):f.write(os.urandom(1<<20))
  write(d/marker,dict(step=step,files={'q.bin':sha(d/'q.bin')}))
 for name in ('q.log','t.log'):(node/name).write_text('q 1\n')
 subprocess.run(['mount','-t','tmpfs','-o','size=16m','tmpfs',str(x)],check=True)
 (x/'n_s').mkdir(mode=0o700)
 shutil.copyfile(n/'sess.json',x/'n_s'/('sess_'+job+'.json'))
 (x/'n_s'/('sess_'+job+'.json')).chmod(0o600)
 with (n/'logs/fill.log').open('wb') as f:
  result=subprocess.run(['dd','if=/dev/zero','of='+str(x/'fill'),'bs=1M','count=32'],stdout=f,stderr=f)
  subprocess.run(['df','-B1',str(x)],stdout=f,stderr=f)
 if shutil.disk_usage(x).free!=0 or result.returncode==0:raise ValueError('E12')
 report=load(n/'E3.json');checks=report['checks'];checks['probe']='PASS';checks['full_before_start']='PASS'
 report['free_before_start']=0;write(n/'E3.json',report)
 log=(n/'logs/run.log').open('w');err=(n/'logs/run.err').open('w')
 worker=subprocess.Popen(['bash',str(n/'run.sh')],stdout=log,stderr=err,env={**os.environ,'SLURM_JOB_ID':job})
 def wait_for(test,seconds):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if test():return True
   if worker.poll() is not None:return False
   time.sleep(1)
 def invoke(name,args):
  with (n/'logs'/name).open('w') as f:
   return subprocess.run([sys.executable,'-I','-s','-B',str(n/'observe.py'),*map(str,args)],stdout=f,stderr=f,timeout=900).returncode
 try:
  if not wait_for(lambda:(node/'started').exists(),45):raise ValueError('E13')
  pid=int((n/'pid').read_text());report['publisher_pid']=pid
  # These are the launch's actual archive and final-copy commands.
  os.environ['TK_COPY_DEADLINE']=str(time.time()+240)
  tick=time.monotonic()
  frc=invoke('f.log',[k/'b/pc.py',k,node,job,'--final','--status','0'])
  elapsed=time.monotonic()-tick
  checks['nonfatal']='PASS' if frc==0 and worker.poll() is None else 'FAIL'
  checks['full_during_copy']='PASS' if shutil.disk_usage(x).free==0 else 'FAIL'
  receipts=node/'live_spool/private/sess.json.receipts.jsonl'
  rows=[json.loads(s) for s in receipts.read_text().splitlines()] if receipts.exists() else []
  meta=[load(p) for p in sorted((n/'obs').glob('r_*.json'))]
  byname={r.get('name'):r for r in meta}
  objects=[]
  for r in rows:
   with Path(r['file']).open('rb') as f:f.seek(r['offset']);raw=f.read(r['bytes'])
   response=byname.get(r['name'],{})
   good=(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
         and str(response.get('size'))==str(r['bytes']) and response.get('md5Hash')==r.get('md5')
         and response.get('name')==r['name'])
   objects.append(dict(name=r['name'],bytes=r['bytes'],sha256=r['sha256'],response=response,status='PASS' if good else 'FAIL'))
  report['objects']=objects
  stop_key=load(k/'k/y.json')['objects']['ckstop']+'.j'+job
  rate_rows=[dict(name=r['name'],bytes=r['bytes'],seconds=r.get('seconds'),started_at=r.get('started_at'),finished_at=r.get('finished_at'),MBps=r['bytes']/max(r.get('seconds',0),1e-6)/1e6) for r in rows if r['name'].startswith(stop_key+'.part')]
  report['rate']=dict(payload_bytes=(train/'checkpoint_7/q.bin').stat().st_size,parts=rate_rows,final_pass_seconds=elapsed,total_MBps=sum(r['bytes'] for r in rate_rows)/max(elapsed,1e-6)/1e6,measured_stop_MBps=sum(r['bytes'] for r in rate_rows)/max([r['seconds'] for r in rate_rows]+[1e-6])/1e6)
  if rate_rows:
   duration=max(r['finished_at'] for r in rate_rows)-min(r['started_at'] for r in rate_rows)
   report['rate']['total_seconds']=duration
   report['rate']['total_MBps']=sum(r['bytes'] for r in rate_rows)/max(duration,1e-6)/1e6
  report['SLURM_TMPDIR']=os.environ.get('SLURM_TMPDIR','/tmp')
  report['tmp_free_bytes']=shutil.disk_usage(report['SLURM_TMPDIR']).free
  checks['rate']='PASS' if len(rate_rows)==4 and all(r['seconds']>0 for r in rate_rows) else 'FAIL'
  checks['upload_logging']='PASS' if (node/'live_spool/upload.log').is_file() and 'http' in (node/'live_spool/upload.log').read_text() else 'FAIL'
  names=load(k/'k/y.json')['objects']
  for label in ('m100','ckstop','u'):
   expected={names[label]+'.j'+job+f'.part{i:02d}-of-04' for i in range(4)}
   actual={r['name'] for r in objects if r['status']=='PASS'}
   checks[label]='PASS' if expected.issubset(actual) else 'FAIL'
  checks['response_fields']='PASS' if len(objects)==16 and all(r['status']=='PASS' for r in objects) else 'FAIL'
  checks.pop('ck00',None)
  resume=[json.loads(s) for s in (n/'obs/resume.jsonl').read_text().splitlines()] if (n/'obs/resume.jsonl').exists() else []
  interrupted=next((r for r in resume if r['kind']=='interrupted'),None)
  queried=next((r for r in resume if r['kind']=='resume_status' and interrupted and r['range']==interrupted['range']),None)
  resumed=next((r for r in resume if r['kind']=='resume_chunk' and queried and r['content_range'].startswith('bytes '+str(int(queried['range'].split('-')[-1])+1)+'-')),None)
  checks['resume_real']='PASS' if interrupted and queried and resumed and any(r['name']==interrupted['name'] for r in objects) else 'FAIL'
  report['resume_real']=dict(status=checks['resume_real'],real_service=os.environ.get('E3_OFFLINE')!='1',events=resume)
  report['receipts']=[{k:v for k,v in r.items() if k!='file'} for r in rows]
  archive=node/'o/o.tar';key=names['o']+'.j'+job
  expected=[key+f'.part{i:02d}-of-04' for i in range(4)]
  ar=[next((r for r in objects if r['name']==name),{}) for name in expected]
  done=node/'live_spool/state/gcs_o.done'
  receipt=load(done) if done.is_file() else {}
  good=(archive.is_file() and all(r.get('status')=='PASS' for r in ar)
        and sum(r.get('bytes',0) for r in ar)==archive.stat().st_size
        and receipt.get('sha256')==sha(archive) and receipt.get('object')==key
        and shutil.disk_usage(x).free==0)
  if good:
   with tarfile.open(archive) as t:good=load(node/'o/RESULT.json')==json.load(t.extractfile('RESULT.json'))
  checks['archive_while_full']='PASS' if good else 'FAIL'
  report['archive']=dict(local=archive.is_file(),bytes=archive.stat().st_size if archive.is_file() else 0,
      sha256=sha(archive) if archive.is_file() else None,objects=expected,free_bytes=shutil.disk_usage(x).free,
      result_inside=bool(good),cap_bytes=50_000_000)
  phases=[json.loads(s)['phase'] for s in (node/'live_spool/final_order.jsonl').read_text().splitlines() if json.loads(s).get('final')]
  report['final_order']=phases
  checks['final_order']='PASS' if phases and any(phases[i:i+4]==['stop','exports','logs','o'] for i in range(len(phases))) and all(phases[i-1]=='o' for i,p in enumerate(phases) if p=='checkpoints' and i>0) else 'FAIL'
  retry=node/'live_spool/retry.log'
  retries=[json.loads(s) for s in retry.read_text().splitlines()] if retry.exists() else []
  checks['local_retry']='PASS' if any(r.get('errno')==28 for r in retries) else 'FAIL'
  os.kill(pid,0)
  with (n/'logs/recovery.log').open('w') as f:
   subprocess.run(['mount','-t','tmpfs','-o','remount,size=64m','tmpfs',str(x)],check=True,stdout=f,stderr=f)
   subprocess.run(['df','-B1',str(x)],stdout=f,stderr=f)
  good=wait_for(lambda:(x/'o'/job/'live/copy.json').is_file() and (x/'o'/job/'o.tar').is_file(),660)
  os.kill(pid,0)
  checks['automatic_recovery']='PASS' if good and int((n/'pid').read_text())==pid else 'FAIL'
  checks['archive_after_recovery']='PASS' if good and sha(x/'o'/job/'o.tar')==sha(node/'o/o.tar') else 'FAIL'
  report['status']='PASS' if all(v=='PASS' for v in checks.values()) else 'FAIL'
  write(n/'E3.json',report)
 finally:
  # Finish only this fixture's shell; pc.sh performs its normal finalizer.
  (n/'finish').write_text('1\n')
  rc=worker.wait(timeout=700);log.close();err.close()
  if rc:fail(n,'E14')
 return 0 if load(n/'E3.json')['status']=='PASS' else 1

def finish(n,x,job,rc):
 if not (n/'E3.json').exists():fail(n,'E15')
 report=load(n/'E3.json')
 if (rc or report.get('status')=='PENDING') and report.get('status')!='FAIL':fail(n,'E16');report=load(n/'E3.json')
 report['returncode']=rc;write(n/'E3.json',report)
 # Only selected bounded, screened diagnostics leave the node.
 sys.path.insert(0,str(n/'k/b'))
 try:
  from z import screen
  words=load(n/'k/k/g.json');hashes=load(n/'k/b/wh.json')
 except (ImportError,OSError,ValueError):
  screen=lambda text,*args:text
  words=hashes={}
 safe=n/'pub';safe.mkdir(exist_ok=True)
 shutil.copyfile(n/'E3.json',safe/'E3.json')
 sources=list((n/'logs').glob('*'))+[n/'n/live_spool/retry.log',n/'n/o/retry.log',n/'n/live_spool/upload.log',n/'n/live_spool/final_order.jsonl']+list((n/'n/live_spool/state').glob('*'))
 for i,p in enumerate(sources):
  if p.is_file():
   with p.open('rb') as f:f.seek(0 if p.name=='upload.log' else max(0,p.stat().st_size-32768));raw=f.read()
   text=screen(raw.decode('utf-8','replace'),words,hashes)
   # Transport errors may contain a capability; omit their whole lines.
   text='\n'.join(s for s in text.splitlines() if not any(t in s.lower() for t in ('https://','http://','upload_id','token','authorization')))
   (safe/('l%02d.log'%i)).write_text(text+'\n')
 receipts=n/'n/live_spool/private/sess.json.receipts.jsonl'
 if receipts.exists():
  rows=[{k:v for k,v in json.loads(s).items() if k!='file'} for s in receipts.read_text().splitlines()]
  write(safe/'r.json',rows)
 with tarfile.open(n/'logs.tgz','w:gz') as t:
  for p in sorted(safe.iterdir()):t.add(p,arcname=p.name,recursive=False)
 if (n/'logs.tgz').stat().st_size>2_000_000:raise ValueError('E17')
 dest=x/'o'/job;dest.mkdir(parents=True,exist_ok=True)
 for src,name in ((n/'E3.json','E3.json'),(n/'logs.tgz','logs.tgz')):
  shutil.copyfile(src,dest/(name+'.part'));os.replace(dest/(name+'.part'),dest/name)
 print('E3_'+report['status'])

def main():
 mode=sys.argv[1]
 if mode=='stage':stage(*map(Path,sys.argv[2:5]),sys.argv[5]);return 0
 n=Path(sys.argv[2])
 if mode=='fail':fail(n,sys.argv[3]);return 0
 x=Path(sys.argv[3]);job=sys.argv[4]
 if mode=='finish':finish(n,x,job,int(sys.argv[5]));return 0
 return run(n,x,job)

if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:
  n=Path(sys.argv[3] if sys.argv[1]=='stage' else sys.argv[2])
  code=str(e) if isinstance(e,ValueError) and str(e).startswith('E') and str(e)[1:].isdigit() else 'E99'
  fail(n,code);print('E3_FAIL '+code+' '+type(e).__name__);raise SystemExit(1)
