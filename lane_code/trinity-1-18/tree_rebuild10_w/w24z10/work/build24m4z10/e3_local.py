from pathlib import Path
import importlib.util,json,os,sys,shutil,tarfile
J=Path.cwd();D=J/'out/e3';B=J/'work/build24m4z10';W=B/('e3_'+sys.argv[1]);W.mkdir()
N=W/'n';X=W/'x';N.mkdir();X.mkdir()
for name in ('tmp','probe','logs','obs','bin'):(N/name).mkdir()
job='24057'
os.environ.update(E3_OFFLINE='1',E3_N=str(N),E3_PY=sys.executable,SLURM_JOB_ID=job,TMPDIR=str(N/'tmp'),E3_LOCAL_BYTES=str(3<<20),OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',STRICT_SINK=str(N/'sink'))
s=importlib.util.spec_from_file_location('e3_driver',D/'e3.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
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
m.stage(D,N,X,job);shutil.copyfile(N/'observe.py',N/'observe_actual.py')
(N/'observe.py').write_text('''import sys,os,runpy,http.client,time,types
from pathlib import Path
N=Path(os.environ['E3_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,'''+repr(str(B))+''')
from strict_sink import Connection
__import__("strict_sink").install()
if '--writer' in sys.argv:os.environ['STRICT_SESSIONS']=sys.argv[sys.argv.index('--writer')+3]
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=='pc.py':
  d=original(path,run_name='case_pc');g=d['main'].__globals__;old=g['read']
  def read(p):
   v=old(p)
   if Path(p).name=='p.json':v['n_root']=str(X)
   return v
  g['read']=read;g['deadline']=lambda:time.time()+5;g['ARCHIVE_SECONDS']=1
  g['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
  if '--writer' in sys.argv:raise SystemExit(d['writer_main'](sys.argv[sys.argv.index('--writer')+1:]))
  elif '--seconds' in sys.argv:print(6)
  else:d['main']()
  return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
''')
rc=m.run(N,X,job);report=m.load(N/'E3.json');m.finish(N,X,job,rc)
assert report['status']=='PASS',report
assert len(report['objects'])==16 and all(v=='PASS' for v in report['checks'].values())
assert report['rate']['payload_bytes']==3<<20
with tarfile.open(N/'logs.tgz') as t:
 for member in t:
  raw=t.extractfile(member).read();assert b'https://' not in raw and b'local.invalid' not in raw
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=report['checks'],objects=16,local_bytes=3<<20,real_rate='NOT_MEASURED'),indent=2)+'\n')
print(json.dumps(dict(status=report['status'],checks=report['checks'],rate_scope='3 MiB offline fixture; not real GCS throughput')))
