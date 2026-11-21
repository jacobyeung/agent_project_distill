import os,sys,json,shutil,subprocess,time,base64,hashlib,traceback,runpy
from pathlib import Path
import resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z12';W=D/('new_'+sys.argv[1]);W.mkdir();rows=[]
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v
def test(name,fn):
 try:r=dict(name=name,status='PASS',detail=fn())
 except Exception:r=dict(name=name,status='FAIL',output=traceback.format_exc())
 rows.append(r);(W/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(r),flush=True)
def case(version,mode):
 r=W/(version+'_'+mode);r.mkdir();k=r/'kit';shutil.copytree(J.parent/'w24z10/out/kit_n' if version=='before' else J/'out/kit_n',k)
 x=r/'x';x.mkdir();n=r/'n';n.mkdir();t=n/'p/q/r';t.mkdir(parents=True)
 (x/'n_s').mkdir(mode=0o700);objects=load(k/'k/y.json')['objects']
 p=x/'n_s/sess_41.json';p.write_text(json.dumps({v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j41'+f'.part{i:02d}-of-04' for v in objects.values() for i in range(4)}));p.chmod(0o600)
 for step in (2,10,30):
  c=t/('checkpoint_'+str(step));c.mkdir();(c/'q.bin').write_bytes(b'q'*(3<<20));(c/'complete.json').write_text(json.dumps(dict(step=step,tag=c.name)))
 for step in (100,30):
  c=t/('m'+str(step));c.mkdir();(c/'q.bin').write_bytes(b'e'*4096);(c/'artifact.json').write_text(json.dumps(dict(step=step,tag=c.name)))
 (t/'run_0.json').write_text('{"last_step":30}')
 (n/'live_spool').mkdir();(n/'live_spool/stop.request').write_text('1')
 token=load(k/'k/g.json')[0];screen=runpy.run_path(str(k/'b/z.py'))['screen'];expected=screen(token,load(k/'k/g.json'),load(k/'b/wh.json'));assert expected!=token
 for name in ('j2.log','j2.err','q.log','t.log','h.log','rooms.log'):(n/name).write_text('q '+token+' tail\n')
 b=r/'bin';b.mkdir();(b/'python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(D/'new_runtime.py')+' "$@"\n');(b/'python3').chmod(0o700)
 env={**os.environ,'TEST_W':str(r),'TEST_X':str(x),'FAKE_SINK':str(r/'sink'),'ROOT':str(k),'N':str(n),'SLURM_JOB_ID':'41','PATH':str(b)+':'+os.environ['PATH'],'TK_UPLOAD_CHUNK_BYTES':str(256<<10),'NEW_MODE':mode,'STRICT_FAIL':'fail' if mode=='failure' else '','STRICT_SELECT':'ckstop','TK_JOB_START':str(time.time()-82801 if mode=='nominal' else time.time())}
 with (r/'shell.log').open('w') as f:
  z=subprocess.run(['bash','-c','set -euo pipefail; source "$ROOT/b/pc.sh"; sleep .2; exit 0'],env=env,stdout=f,stderr=f,timeout=25)
 assert z.returncode==0,(z.returncode,(r/'shell.log').read_text()[-2000:])
 state=n/'live_spool/state';done=[(state/('gcs_checkpoint_'+str(i)+'.done')).exists() for i in (10,2)]
 assert done==([False,False] if version=='before' or mode=='reserve' else [True,True]),done
 events=[json.loads(l) for l in (r/'sink/events.jsonl').read_text().splitlines()]
 phases=[json.loads(l) for l in (n/'live_spool/final_order.jsonl').read_text().splitlines()]
 if version=='after' and mode!='reserve':
  a=load(state/'gcs_checkpoint_10.done');b=load(state/'gcs_checkpoint_2.done');assert a['generation']=='ck00' and b['generation']=='ck01',(a,b)
  ordinary=next(i for i,e in enumerate(events) if '_ck00.' in e['name'])
  assert any('_mstop.' in e['name'] and e['http']==200 for e in events[:ordinary])
  assert any('_m100.' in e['name'] and e['http']==200 for e in events[:ordinary])
  assert any('_u.log' in e['name'] and e['http']==200 for e in events[:ordinary])
  assert any('_o.tar' in e['name'] and e['http']==200 for e in events[:ordinary])
  if mode=='resume':assert any('_ck00.' in e['name'] and e['bytes']==0 and e['range']=='bytes=0-262143' for e in events),events
 for name in ('j2.log','j2.err','q.log','t.log','h.log','rooms.log'):
  raw=(x/'o/41/live'/name).read_text();assert (token in raw)==(version=='before'),(name,raw)
  if version=='after':assert expected in raw,(name,raw)
 # A fresh live-loop instance must resume the same ordinary queue after settlement.
 if version=='after' and mode=='success':
  env['NEW_MODE']='live_probe'
  with (r/'live_probe.log').open('w') as f:
   z=subprocess.run([sys.executable,'-I','-s','-B',str(D/'new_runtime.py'),str(k/'b/pc.py'),str(k),str(n),'41'],env=env,stdout=f,stderr=f)
  assert z.returncode==0,(r/'live_probe.log').read_text()
 return dict(version=version,mode=mode,ordinary_done=done,screened=version=='after',real_exit=True,strict_sink=True,first_final_phases=[v['phase'] for v in phases if v['final']][:6],passes=sum(v['phase']=='stop' and v['final'] for v in phases),log=str(r.relative_to(J)/'shell.log'))
for mode in ('success','nominal','failure','resume','reserve'):
 for version in ('before','after'):test(version+'_'+mode,lambda version=version,mode=mode:case(version,mode))
raise SystemExit(any(r['status']!='PASS' for r in rows))
