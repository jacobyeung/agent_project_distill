from pathlib import Path
import os,sys,shutil,json,base64,hashlib,subprocess
J=Path.cwd();D=J/'work/build24m4z10';W=D/'trinity_local';W.mkdir();R=W/'bundle'
shutil.copytree(J/'out/e3',R)
source=R/'observe.py';source.rename(R/'observe_actual.py')
adapter=(D/'e3_guard/n/observe.py').read_text()
adapter=adapter.replace("X=N.parent/'x'","X=Path('/project/community/jjyeung/okh7/x_22c714e1')")
adapter=adapter.replace("run(str(N/'observe_actual.py'),run_name='__main__')","run("+repr(str(R/'observe_actual.py'))+",run_name='__main__')")
source.write_text(adapter)
pins=json.loads((R/'pins.json').read_bytes());pins['observe.py']=hashlib.sha256(source.read_bytes()).hexdigest()
(R/'pins.json').write_text(json.dumps(pins))
job='240510';v=json.loads((J/'out/kit_n/k/y.json').read_bytes());v=json.loads(base64.b64decode(v['payload']))
sessions={key+'.j'+job+f'.part{i:02d}-of-04':'https://local.invalid/'+key+'.j'+job+f'.part{i:02d}-of-04' for key in v['objects'].values() for i in range(4)}
p=W/'sessions.json';p.write_text(json.dumps(sessions));p.chmod(0o600)
env={**os.environ,'E3_OFFLINE':'1','STRICT_SINK':str(W/'run/sink')}
with (W/'shell.log').open('w') as f:
 r=subprocess.run(['bash',str(R/'trinity.sh'),job,str(p),str(W/'run')],env=env,stdout=f,stderr=f,timeout=60)
assert r.returncode==0,(r.returncode,(W/'shell.log').read_text())
report=json.loads((W/'run/E3.json').read_bytes())
assert report['status']=='PASS' and report['resume_real']['status']=='PASS' and not report['resume_real']['real_service']
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',interface='trinity.sh job sessions out',objects=len(report['objects']),real_GCS=False,checks=report['checks']),indent=2)+'\n')
print('Trinity interface PASS with fake sessions; no sockets')
