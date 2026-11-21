from pathlib import Path
import importlib.util,json,os,sys,shutil,tarfile
J=Path.cwd();D=J/'out/e3';B=J/'work';W=B/('e3_'+sys.argv[1]);W.mkdir()
N=W/'n';X=W/'x';N.mkdir();X.mkdir()
for name in ('tmp','probe','logs','obs','bin'):(N/name).mkdir()
job='24057'
os.environ.update(E3_N=str(N),E3_PY=sys.executable,SLURM_JOB_ID=job,TMPDIR=str(N/'tmp'),E3_LOCAL_BYTES=str(3<<20),OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',STRICT_SINK=str(N/'sink'))
s=importlib.util.spec_from_file_location('e3_driver',D/'e3.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
original=m.load
def load(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
m.load=load
(X/'n_s').mkdir(mode=0o700)
with tarfile.open(D/'k.tgz') as t:
 names=json.load(t.extractfile('k/y.json'))
 if names.get('encoding')=='base64-json':names=json.loads(__import__('base64').b64decode(names['payload']))
 names=names['objects']
values={v+'.j'+job+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j'+job+f'.part{i:02d}-of-04' for v in names.values() for i in range(4)}
p=X/'n_s'/('sess_'+job+'.json');p.write_text(json.dumps(values));p.chmod(0o600)
m.stage(D,N,X,job);shutil.copyfile(N/'observe.py',N/'observe_actual.py')
os.environ.update(E3_TEST_WORK=str(B),E3_TEST_MAP=str(X))
shutil.copyfile(B/'offline_observer.py',N/'observe.py')
rc=m.run(N,X,job);report=m.load(N/'E3.json');m.finish(N,X,job,rc)
assert report['status']=='PASS',report
assert len(report['objects'])==16 and all(v=='PASS' for v in report['checks'].values())
assert report['rate']['payload_bytes']==3<<20
with tarfile.open(N/'logs.tgz') as t:
 for member in t:
  raw=t.extractfile(member).read();assert b'https://' not in raw and b'local.invalid' not in raw
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=report['checks'],objects=16,local_bytes=3<<20,real_rate='NOT_MEASURED'),indent=2)+'\n')
print(json.dumps(dict(status=report['status'],checks=report['checks'],rate_scope='3 MiB offline fixture; not real GCS throughput')))
