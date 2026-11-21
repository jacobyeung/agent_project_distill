import os,sys,json,base64,hashlib,time,shutil,subprocess,importlib.util,traceback
from pathlib import Path
J=Path.cwd();D=J/'work/build24m4z12';W=D/('findings_'+sys.argv[1]);W.mkdir();rows=[]
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v
def test(name,fn):
 try:r=dict(name=name,status='PASS',detail=fn())
 except Exception:r=dict(name=name,status='FAIL',output=traceback.format_exc())
 rows.append(r);(W/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(r),flush=True)
def fixtures():
 results=[]
 for mode in ('nominal','signal','forecast','diagnostics'):
  for version in ('before','after'):
   source=J.parent/'w24z7/out/kit_n' if version=='before' else J/'out/kit_n'
   r=W/(mode+'_'+version);r.mkdir();k=r/'kit';shutil.copytree(source,k);x=r/'x';x.mkdir();n=r/'n';n.mkdir();t=n/'p/q/r';t.mkdir(parents=True)
   subprocess.run(['mount','-t','tmpfs','-o','size=16m','tmpfs',str(x)],check=True)
   (x/'n_s').mkdir(mode=0o700);objects=load(k/'k/y.json')['objects']
   values={v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j41'+f'.part{i:02d}-of-04' for v in objects.values() for i in range(4)}
   p=x/'n_s/sess_41.json';p.write_text(json.dumps(values));p.chmod(0o600)
   with (r/'fill.log').open('w') as f:subprocess.run(['dd','if=/dev/zero','of='+str(x/'fill'),'bs=1M','count=20'],stdout=f,stderr=f)
   assert shutil.disk_usage(x).free==0
   b=r/'bin';b.mkdir();(b/'python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(D/'runtime.py')+' "$@"\n');(b/'python3').chmod(0o700)
   recipe=load(k/'k/n.json')['recipe']
   env={**os.environ,'TEST_W':str(r),'TEST_X':str(x),'FAKE_SINK':str(r/'sink'),'ROOT':str(k),'N':str(n),'SLURM_JOB_ID':'41','PATH':str(b)+':'+os.environ['PATH'],'STRICT_FAIL':'once' if mode=='diagnostics' else '','STRICT_SELECT':'_o.tar','TK_JOB_START':str(time.time()-(recipe['wall_seconds']-recipe['stop_before_seconds']+1) if mode=='nominal' else time.time())}
   with (r/'shell.log').open('w') as log:
    shell=subprocess.Popen(['bash','-c','set -euo pipefail; source "$ROOT/b/pc.sh"; touch "$N/started"; while [[ ! -f "$N/finish" ]]; do sleep .03; done; exit 0'],env=env,stdout=log,stderr=log)
    def wait(fn,seconds=2):
     end=time.time()+seconds
     while time.time()<end:
      if fn():return True
      time.sleep(.02)
     return bool(fn())
    try:
     assert wait(lambda:(n/'started').exists())
     if mode=='signal':(n/'live_spool/stop.request').write_text('requested')
     ck=t/'checkpoint_7';ck.mkdir();(ck/'q.bin').write_bytes(b'q'*(1<<20));(ck/'complete.json').write_text('{"step":7}')
     if mode in ('forecast','diagnostics'):
      assert wait(lambda:(n/'live_spool/state/gcs_checkpoint_7.done').exists())
      (t/'run_0.json').write_text('{"last_step":7}')
     immediate=wait(lambda:(n/'live_spool/state/gcs_checkpoint_7_stop.done').exists(),.8)
     if mode in ('nominal','signal'):
      assert immediate==(version=='after'),(mode,version,immediate)
      assert not (t/'run_0.json').exists() and not (t/'m100').exists()
     ex=t/'m100';ex.mkdir();(ex/'q.bin').write_bytes(b'e'*1000);(ex/'artifact.json').write_text('{"step":100}')
     (t/'run_0.json').write_text('{"last_step":7}')
    finally:
     (n/'finish').write_text('1')
     rc=shell.wait(timeout=20)
    assert rc==0,rc
   state=n/'live_spool/state';events=[json.loads(l) for l in (r/'sink/events.jsonl').read_text().splitlines()]
   stop_bytes=sum(v['bytes'] for v in events if '_ckstop.' in v['name'])
   if mode=='forecast':
    assert (stop_bytes==0)==(version=='after'),(version,stop_bytes)
    if version=='after':assert load(state/'ckstop.json')['reused_ordinary']
   final_log=b''
   if 'u' in objects:
    for i in range(4):
     name=objects['u']+'.j41'+f'.part{i:02d}-of-04'
     final_log+=(r/'sink'/(hashlib.sha256(name.encode()).hexdigest()+'.data')).read_bytes()
    assert len(final_log)==2<<20 and b'https://' not in final_log
    assert (state/'gcs_u.done').exists()
   if mode=='diagnostics':
    if version=='after':
     attempts=[l for l in (n/'live_spool/upload.log').read_bytes().splitlines() if b'_u.log' not in l and l.strip()]
     assert all(l in final_log for l in attempts),[l for l in attempts if l not in final_log][:3]
     assert b'"http": 503' in final_log and b'"http": 200' in final_log
    else:assert not final_log
   results.append(dict(mode=mode,version=version,immediate=immediate,stop_uploaded_bytes=stop_bytes,final_log_bytes=len(final_log),full_X=shutil.disk_usage(x).free==0,real_exit=True))
 return results
def observers():
 got=[]
 for kind in ('e3','tgcs'):
  for version in ('before','after'):
   source=J/'attic'/('z7_'+kind)/'observe.py' if version=='before' else J/'out'/kind/'observe.py'
   n=W/(kind+version);n.mkdir();(n/'logs').mkdir();(n/'obs').mkdir();k=n/'k';shutil.copytree(J/'out/kit_n',k)
   env={**os.environ,'E3_N':str(n),'TG_OUT':str(n),'TG_KIT':str(k),'TG_DIR':str(source.parent)}
   p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'observer_probe.py'),str(source),str(k/'b/o.py')],env=env,capture_output=True,text=True)
   (n/'probe.log').write_text(p.stdout+p.stderr)
   assert (p.returncode==0)==(version=='after'),(kind,version,p.stderr)
   got.append(dict(kind=kind,version=version,returncode=p.returncode))
 return got
def sink():
 result=[]
 for version in ('before','after'):
  file=J/'work/build24m4z7/strict_sink.py' if version=='before' else D/'strict_sink.py'
  spec=importlib.util.spec_from_file_location('ss',file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  r=W/('sink_'+version);r.mkdir();p=r/'sess.json';p.write_text('{"q":"https://local.invalid/q"}')
  os.environ.update(STRICT_SESSIONS=str(p),STRICT_SINK=str(r),STRICT_FAIL='')
  cases=[('bytes */not-a-size',b''),('bytes */-1',b''),('bytes */+1',b''),('bytes */1.0',b''),('bytes */',b''),('bytes */*',b''),('bytes */01',b''),('bytes */1 ',b''),('bytes */1\n',b''),('Bytes */1',b''),('bytes 0-0/*',b'x'),('bytes 1-0/1',b''),('bytes -1-0/1',b'x'),('bytes 0-1/1',b'xx'),('bytes 0-0/0',b'x'),('bytes 00-00/1',b'x'),('bytes 0-0/1,2-2/3',b'x'),('bytes 0-0/1',b'xx'),('bytes 0-0/2',b'x'),('bytes */1',b'x'),('',b'')]
  codes=[]
  def send(cr,raw,ran=None):
   c=m.Connection();c.putrequest('PUT','/q');c.putheader('Content-Length',str(len(raw)));c.putheader('Content-Range',cr)
   if ran is not None:c.putheader('Range',ran)
   c.endheaders();c.send(raw);return c.getresponse().status
  for cr,raw in cases:codes.append(send(cr,raw))
  for ran in ('bytes=0-0','bytes=','bytes=1-0','items=0-1','bytes=0-0,2-2','garbage',''):codes.append(send('bytes */1',b'',ran))
  if version=='after':
   assert all(c==400 for c in codes),codes
   assert send('bytes 0-0/1',b'x')==200
   final_codes=[send(cr,raw) for cr,raw in cases]
   assert all(c==400 for c in final_codes),final_codes
   c=m.Connection();c.putrequest('PUT','/q');c.putheader('Content-Length','0');c.putheader('Content-Range','bytes */1');c.putheader('Content-Range','bytes */1');c.endheaders()
   assert c.getresponse().status==400
  else:assert codes[0]==308,codes
  result.append(dict(version=version,cases=len(codes),http_codes=codes))
 return result
def setting():
 r=W/'setting';r.mkdir();shutil.copyfile(J/'out/set_stop.py',r/'set_stop.py')
 def inv(k):return {str(p.relative_to(k)):hashlib.sha256(p.read_bytes()).hexdigest() for p in k.rglob('*') if p.is_file()}
 old={};recipes={}
 for name in ('kit_n','kit_n_go'):
  k=r/name;shutil.copytree(J/'out'/name,k);old[name]=inv(k);recipes[name]=load(k/'k/n.json')
 for value in ('3600','6000'):
  p=subprocess.run([sys.executable,'-I','-s','-B',str(r/'set_stop.py'),value],capture_output=True,text=True)
  (r/(value+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 changed={}
 for name in old:
  k=r/name;new=inv(k);diff=sorted(n for n in old[name] if old[name][n]!=new[n]);assert diff==['BUILD.json','SHA256SUMS.txt','k/n.json'],diff
  cfg=load(k/'k/n.json');assert cfg['recipe'].pop('stop_before_seconds')==6000
  prior=recipes[name];assert prior['recipe'].pop('stop_before_seconds')==3600;assert cfg==prior
  changed[name]=diff
 before={name:inv(r/name) for name in old}
 for value in ('3599','3601','10801','-300','abc','6000.0'):
  p=subprocess.run([sys.executable,'-I','-s','-B',str(r/'set_stop.py'),value],capture_output=True,text=True)
  assert p.returncode and before=={name:inv(r/name) for name in old}
 return dict(changed=changed,invalid_refused=6,production_stop=load(J/'out/kit_n/k/n.json')['recipe']['stop_before_seconds'])
test('real_exit_stop_and_diagnostics',fixtures)
test('observer_constructors',observers)
test('malformed_ranges',sink)
test('stop_tool',setting)
raise SystemExit(any(r['status']!='PASS' for r in rows))
