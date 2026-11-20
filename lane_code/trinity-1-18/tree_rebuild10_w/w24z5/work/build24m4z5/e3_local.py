"""Execute the submitted E3 driver against a local transport in a network namespace."""
from pathlib import Path
import importlib.util,json,base64,os,sys,shutil,subprocess,tarfile,hashlib
J=Path.cwd();D=J/'out/e3';W=J/'work/build24m4z5/e3_verified';W.mkdir()
N=W/'n';X=W/'x';N.mkdir();X.mkdir()
for name in ('tmp','probe','logs','obs','bin'):(N/name).mkdir()
job='24045'
os.environ.update(E3_N=str(N),E3_PY=sys.executable,SLURM_JOB_ID=job,TMPDIR=str(N/'tmp'),OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4')
spec=importlib.util.spec_from_file_location('e3_driver',D/'e3.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
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
N=Path(os.environ['E3_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
import importlib.util
spec=importlib.util.spec_from_file_location('q_transport',str(N.parents[1]/'transport.py'))
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
Connection=transport.Connection
os.environ['FAKE_SINK']=str(N/'sink')
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
  g['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
  d['main']();return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
''')
m.RATE_BYTES=4<<20
rc=m.run(N,X,job)
report=m.load(N/'E3.json')
assert report['status']=='PASS' and report['checks']['archive_while_full']=='PASS',report
assert all(v=='PASS' for k,v in report['checks'].items() if k!='archive_while_full'),report
assert len(report['objects'])==20
assert len(list((N/'sink').iterdir()))==20
m.finish(N,X,job,rc)
pub=X/'o'/job
assert (pub/'E3.json').is_file() and (pub/'logs.tgz').stat().st_size<2_000_000
with tarfile.open(pub/'logs.tgz') as t:
 assert all('sess' not in i.name for i in t.getmembers())
 for item in t.getmembers():
  raw=t.extractfile(item).read()
  assert b'https://' not in raw and b'local.invalid' not in raw
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',job_status=report['status'],checks=report['checks'],objects=20,capability_leak=False),indent=2)+'\n')
print(json.dumps(dict(local_validation='PASS',checks=report['checks'],objects=20)),flush=True)
