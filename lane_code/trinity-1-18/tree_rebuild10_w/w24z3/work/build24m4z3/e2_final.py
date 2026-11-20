"""Execute the submitted E2 driver against a local transport in a network namespace."""
from pathlib import Path
import importlib.util,json,base64,os,sys,shutil,subprocess,tarfile,hashlib
J=Path.cwd();D=J/'out/e2';W=J/'work/build24m4z3/e2_final';W.mkdir()
N=W/'n';X=W/'x';N.mkdir();X.mkdir()
for name in ('tmp','probe','logs','obs','bin'):(N/name).mkdir()
job='24045'
os.environ.update(E2_N=str(N),E2_PY=sys.executable,SLURM_JOB_ID=job,TMPDIR=str(N/'tmp'),OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4')
spec=importlib.util.spec_from_file_location('e2_driver',D/'e2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=m.load
def load(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
m.load=load
(X/'n_s').mkdir(mode=0o700)
names=load(J/'out/kit_n/k/y.json')['objects']
values={v+'.j'+job+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j'+job+f'.part{i:02d}-of-04' for v in names.values() for i in range(4)}
p=X/'n_s'/('sess_'+job+'.json');p.write_text(json.dumps(values));p.chmod(0o600)
m.stage(D,N,X,job)
shutil.copyfile(N/'observe.py',N/'observe_actual.py')
# The transport, target mapping and polling clock are the only local adapters.
(N/'observe.py').write_text('''import sys,os,runpy,http.client,json,hashlib,base64,time,types
from pathlib import Path
N=Path(os.environ['E2_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
class Reply:
 status=200
 def __init__(self,data,name):self.data=data;self.name=name
 def read(self):return json.dumps(dict(size=str(len(self.data)),md5Hash=base64.b64encode(hashlib.md5(self.data).digest()).decode(),crc32c='fixture',name=self.name,generation='1')).encode()
class Connection:
 def __init__(self,*a,**kw):self.data=bytearray()
 def putrequest(self,method,path):self.name=path.split('?')[0].lstrip('/')
 def putheader(self,*a):pass
 def endheaders(self):pass
 def send(self,data):self.data.extend(data)
 def getresponse(self):
  p=N/'sink';p.mkdir(exist_ok=True)
  (p/hashlib.sha256(self.name.encode()).hexdigest()).write_bytes(self.data)
  return Reply(self.data,self.name)
http.client.HTTPSConnection=Connection
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=='pc.py':
  d=original(path,run_name='case_pc');old=d['read']
  def read(p):
   v=old(p)
   if Path(p).name=='p.json':v['n_root']=str(X)
   return v
  g=d['main'].__globals__;g['read']=read
  g['time']=types.SimpleNamespace(time=time.time,monotonic=time.monotonic,sleep=lambda s:time.sleep(s*.003))
  d['main']();return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
''')
rc=m.run(N,X,job)
report=m.load(N/'E2.json')
assert report['status']=='PASS' and report['checks']['archive_while_full']=='PASS',report
assert all(v=='PASS' for k,v in report['checks'].items() ),report
assert len(report['objects'])==16
assert len(list((N/'sink').iterdir()))==16
assert m.sha(N/'n/o/o.tar')==report['archive']['sha256']
m.finish(N,X,job,rc)
pub=X/'o'/job
assert (pub/'E2.json').is_file() and (pub/'logs.tgz').stat().st_size<2_000_000
with tarfile.open(pub/'logs.tgz') as t:
 assert all('sess' not in i.name for i in t.getmembers())
 for item in t.getmembers():
  raw=t.extractfile(item).read()
  assert b'https://' not in raw and b'local.invalid' not in raw
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',job_status=report['status'],checks=report['checks'],objects=16,capability_leak=False),indent=2)+'\n')
print(json.dumps(dict(local_validation='PASS',checks=report['checks'],objects=16)),flush=True)
