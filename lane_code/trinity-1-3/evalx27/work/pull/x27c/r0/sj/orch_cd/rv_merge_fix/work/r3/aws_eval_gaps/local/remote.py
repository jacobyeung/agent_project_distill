"""Parent-only deployment and submission payloads; never invoked by CPU checks."""
DEPLOY=r'''
import fcntl,hashlib,json,os,sys,tarfile,time
from pathlib import Path
root=Path(sys.argv[1]);incoming=Path(sys.argv[2]);expected=sys.argv[3]
with incoming.open('rb') as f:
 if hashlib.file_digest(f,'sha256').hexdigest()!=expected:raise ValueError('E01')
with tarfile.open(incoming) as tf:
 members=tf.getmembers();names=set()
 for m in members:
  p=Path(m.name)
  if (p.is_absolute() or '..' in p.parts or not m.isfile() or m.name in names
      or str(p)!=m.name or not (m.name=='SHA256SUMS.txt' or p.parts[0] in ('b','k'))):raise ValueError('E03')
  names.add(m.name)
 if not {'b/0.sh','b/1.py','k/0.tar','k/1.tar','k/2.json','SHA256SUMS.txt'}<=names:raise ValueError('E03')
 manifest=tf.extractfile('SHA256SUMS.txt').read().decode();listed=set()
 for line in manifest.splitlines():
  h,n=line.split('  ',1)
  if n not in names or n in listed or n=='SHA256SUMS.txt':raise ValueError('E04')
  if hashlib.sha256(tf.extractfile(n).read()).hexdigest()!=h:raise ValueError('E05')
  listed.add(n)
 if listed!=names-{'SHA256SUMS.txt'}:raise ValueError('E04')
 if root.is_symlink():raise ValueError('E02')
 root.mkdir(parents=True,exist_ok=True)
 allowed={'m','o','.retained','b','k','SHA256SUMS.txt'}
 for p in root.iterdir():
  if p.name not in allowed or p.is_symlink():raise ValueError('E02')
  if p.name=='SHA256SUMS.txt':
   if not p.is_file():raise ValueError('E02')
  elif not p.is_dir():raise ValueError('E02')
 retained=root/'.retained';retained.mkdir(exist_ok=True)
 with (retained/'deploy.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  previous=[root/n for n in ('b','k','SHA256SUMS.txt') if (root/n).exists()]
  if previous:
   dest=retained/str(time.time_ns());dest.mkdir()
   for p in previous:p.rename(dest/p.name)
  tf.extractall(root,filter='data')
  (root/'o').mkdir(exist_ok=True)
print(json.dumps({'deployed':True}))
'''

SUBMIT=r'''
import datetime as dt,fcntl,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
root=Path(sys.argv[1]);expected=sys.argv[2]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
with (root/'o/submit.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if sha(root/'SHA256SUMS.txt')!=expected:raise ValueError('E01')
 for line in (root/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1)
  p=root/n
  if not p.resolve().is_relative_to(root.resolve()) or sha(p)!=h:raise ValueError('E02')
 auth=json.loads((root/'k/2.json').read_text())
 if auth['build_only']:raise ValueError('E03')
 seconds=int(dt.datetime.fromisoformat(auth['until'].replace('Z','+00:00')).timestamp()-time.time())
 if not 300<seconds<=14400:raise ValueError('E04')
 query=subprocess.check_output(['squeue','-h','-u',os.environ['USER'],'-t','RUNNING,PENDING','-o','%512Z|%128b|%D|%128j'],text=True)
 used=0
 for line in query.splitlines():
  path,gres,nodes,name=[v.strip() for v in line.split('|')]
  if path==str(root) or (path.startswith('/') and Path(path).resolve()==root.resolve()):raise ValueError('E05')
  if not re.fullmatch('a15_cot_ap[0-9A-Za-z]+',name):continue
  counts=re.findall(r'(?:gres/)?gpu(?::[^,: ]+)?:(\d+)',gres)
  if not counts:continue  # CPU-only jobs report gres N/A
  if not nodes.isdecimal():raise ValueError('E06')
  used+=sum(map(int,counts))*int(nodes)
 # Project names no longer separate projects (main also uses opaque names). The parent counts distillation's
 # RUNNING GPUs from the AWS ledger before submitting (orchestrator 1702Z); the name total is only recorded.
 print('name_matched_gpus',used,file=sys.stderr)
 limit='%02d:%02d:%02d'%(seconds//3600,seconds%3600//60,seconds%60)
 result=subprocess.check_output(['sbatch','--parsable','--account=av_alpamayo_aml','--partition=batch','--qos=normal','--cpus-per-task=%d'%min(32,24*auth['gpus']),'--time='+limit,str(root/'b/0.sh')],text=True).strip()
 job=result.partition(';')[0]
 if not job.isdecimal():raise ValueError('E08')
 name=re.search(r'--job-name=(a15_cot_ap[0-9a-f]{8})',(root/'b/0.sh').read_text()).group(1)
 value=dict(job_id=int(job),job_name=name,root=str(root),gpus=auth['gpus'],time_limit=limit)
 (root/'o'/('s'+job+'.json')).write_text(json.dumps(value)+'\n')
 print(json.dumps(value))
'''
