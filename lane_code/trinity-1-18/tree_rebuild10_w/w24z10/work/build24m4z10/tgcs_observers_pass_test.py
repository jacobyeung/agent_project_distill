from pathlib import Path
import os,sys,json,base64,shutil,subprocess
J=Path.cwd();D=J/'work/build24m4z10';W=D/'tgcs_observers_pass';W.mkdir(mode=0o700)
R=W/'runner';R.mkdir()
for name in ('run_tgcs.sh','driver.py','observe.py'):shutil.copyfile(J/'out/tgcs'/name,R/name)
(R/'run_tgcs.sh').chmod(0o700)
def observer(source):
 p=R/'observe.py';s=source.read_text()
 s=s.replace('Original=http.client.HTTPSConnection', "sys.path.insert(0,"+repr(str(D))+")\nfrom strict_sink import Connection as OfflineConnection\n__import__('strict_sink').install()\nos.environ['STRICT_SESSIONS']=os.environ['TG_SESS']\nos.environ['STRICT_SINK']=str(O/'sink')\nOriginal=http.client.HTTPSConnection")
 s=s.replace("d['main'].__globals__['read']=read", "d['main'].__globals__['read']=read\n  import types\n  d['main'].__globals__['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))\n  d['main'].__globals__['deadline']=lambda:time.time()+5\n  d['main'].__globals__['ARCHIVE_SECONDS']=1")
 p.write_text(s)
rows=[]
for version,job,k in [('before','900001',J.parent/'w24z7/out/kit_n'),('after','900002',J/'out/kit_n')]:
 observer(J/'attic/z7_tgcs/observe.py' if version=='before' else J/'out/tgcs/observe.py')
 v=json.loads((k/'k/y.json').read_text());v=json.loads(base64.b64decode(v['payload']))
 values={key+'.j'+job+f'.part{i:02d}-of-04':'https://local.invalid/'+key+'.j'+job+f'.part{i:02d}-of-04' for key in v['objects'].values() for i in range(4)}
 p=W/('sess_'+job+'.json');p.write_text(json.dumps(values));p.chmod(0o600)
 with (W/(version+'.log')).open('w') as log:
  r=subprocess.run(['bash',str(R/'run_tgcs.sh'),job,str(p),str(k),str(W/version),'full'],stdout=log,stderr=log,timeout=40)
 report=json.loads((W/version/'RESULT.json').read_text());count=len(report['receipts'])
 assert r.returncode==(1 if version=='before' else 0) and count==(0 if version=='before' else 16),(version,r.returncode,count)
 logs=W/version/'logs'
 for p in logs.iterdir():
  if p.is_file():assert b'https://' not in p.read_bytes() and b'local.invalid' not in p.read_bytes()
 assert (logs/'gc.stderr').exists()
 if version=='after':assert (logs/'http.jsonl').exists()
 else:assert 'HTTPSConnection.__init__()' in (logs/'gc.stderr').read_text() and 'positional arguments' in (logs/'gc.stderr').read_text()
 rows.append(dict(version=version,returncode=r.returncode,receipts=count,free_bytes=report['free_bytes'],masked=True,adapter='only HTTP transport and polling/deadline clock'))
(W/'RESULT.json').write_text(json.dumps(dict(status='PASS',network_used=False,cases=rows),indent=2)+'\n');print(json.dumps(rows))
