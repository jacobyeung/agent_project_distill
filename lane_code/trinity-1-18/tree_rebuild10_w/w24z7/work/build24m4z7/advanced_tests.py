import os,sys,json,runpy,time,hashlib,subprocess,traceback
from pathlib import Path
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z7';K=J/'out/kit_n';W=D/('advanced_'+sys.argv[1]);W.mkdir()
sys.path.insert(0,str(D));from strict_sink import Connection
import importlib.util
s=importlib.util.spec_from_file_location('pc_check',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
rows=[]
def fixture(name):
 r=W/name;r.mkdir();n=r/'n';n.mkdir();x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700)
 values={v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j41'+f'.part{i:02d}-of-04' for v in C.read(K/'k/y.json')['objects'].values() for i in range(4)}
 p=x/'n_s/sess_41.json';p.write_text(json.dumps(values));p.chmod(0o600)
 old=C.read
 def read(p):
  v=old(p)
  if Path(p).name=='p.json':v['n_root']=str(x)
  return v
 with patch.object(C,'read',side_effect=read):c=C.Copier(K,n,'41',writer=D/'strict_writer.py')
 c.train.mkdir(parents=True);c.deadline=time.time()+20;c.archive_due=time.time()+15;c.upload_until=c.archive_due
 os.environ.update(STRICT_KIT=str(K),STRICT_OLD='0',STRICT_SINK=str(r/'sink'),STRICT_FAIL='',TK_UPLOAD_LOG=str(c.spool/'upload.log'))
 return c
def test(name,fn):
 try:row=dict(name=name,status='PASS',detail=fn())
 except Exception as e:row=dict(name=name,status='FAIL',output=traceback.format_exc())
 rows.append(row);(W/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
def partial():
 c=fixture('partial');d=c.train/'m100';d.mkdir();(d/'artifact.json').write_text('{"step":100}')
 with (d/'q.bin').open('wb') as f:
  for _ in range(40):f.write(b'q'*(1<<20))
 os.environ.update(STRICT_FAIL='partial',STRICT_SELECT='m100')
 c.exports();assert not (c.state/'gcs_m100.done').exists()
 events=c.root.parent/'sink/events.jsonl';n=len(events.read_text().splitlines())
 assert len(list((c.root.parent/'sink').glob('*.data')))==4
 assert all(p.stat().st_size==8<<20 for p in (c.root.parent/'sink').glob('*.data'))
 os.environ['STRICT_FAIL']='';c.exports();assert (c.state/'gcs_m100.done').exists()
 after=[json.loads(s) for s in events.read_text().splitlines()[n:]]
 assert sum(v['http']==308 and v['range']=='bytes=0-8388607' for v in after)==4
 assert all(v['bytes']<8<<20 for v in after)
 return dict(parts=4,bytes_retained_each=8<<20,resumed_from_Range=True)
def atomic_cache():
 c=fixture('atomic');calls=[]
 real_sync=C.os.fsync;real_replace=C.os.replace
 with patch.object(C.os,'fsync',side_effect=lambda fd:(calls.append('fsync'),real_sync(fd))[1]),patch.object(C.os,'replace',side_effect=lambda a,b:(calls.append('replace'),real_replace(a,b))[1]):
  C.atomic(c.spool/'private/sess.json',c.cached_sessions())
 assert calls==['fsync','replace','fsync'],calls
 return calls
def stale_copy():
 c=fixture('stale');c.logs_complete=True;C.put(c.state/'gcs_o.done',dict(sha256='new'));C.put(c.state/'o_copy.done',dict(sha256='old'))
 assert c.incomplete();C.put(c.state/'o_copy.done',dict(sha256='new'));assert not c.incomplete()
 c.logs_complete=False;assert c.incomplete()
 return dict(stale_archive_copy_retried=True,failed_final_log_copy_retried=True)
def priority_interrupt():
 c=fixture('interrupt');d=c.train/'m100';d.mkdir();(d/'artifact.json').write_text('{}')
 p=c.root/'payload';p.write_bytes(b'q'*(1<<20));name=C.read(K/'k/y.json')['objects']['ck00']+'.j41.part00-of-04'
 uri=json.loads(c.cached_sessions())[name]
 env=dict(TK_UPLOAD_DEADLINE=str(time.time()+10),TK_PRIORITY_TRAIN=str(c.train),TK_PRIORITY_STATE=str(c.state))
 with patch.dict(os.environ,env),patch.object(C.http.client,'HTTPSConnection',Connection):
  try:C.upload(uri,p,0,p.stat().st_size,name);raise AssertionError('ordinary upload ran')
  except InterruptedError:pass
 log=(c.spool/'upload.log').read_text();assert 'E105' in log and 'https://' not in log
 return dict(ordinary_interrupted_before_request=True)
def protocol_rejection():
 c=fixture('reject');os.environ['STRICT_SESSIONS']=str(c.spool/'private/sess.json')
 from urllib.parse import urlsplit
 name=next(iter(json.loads(c.cached_sessions())));uri=json.loads(c.cached_sessions())[name];path=urlsplit(uri).path
 v=Connection();v.putrequest('PUT',path);v.putheader('Content-Length','1');v.putheader('Content-Range','bytes 0-0/100');v.endheaders();v.send(b'x')
 assert v.getresponse().status==400
 return dict(nonfinal_unaligned_rejected=True)
def reserve():
 c=fixture('reserve');d=c.train/'checkpoint_7';d.mkdir();(d/'q.bin').write_bytes(b'q'*(1<<20));(d/'complete.json').write_text('{"step":7}')
 c.deadline=time.time()+4;c.archive_due=time.time()+1.5;c.upload_until=c.archive_due;c.exit_status=0
 os.environ.update(STRICT_FAIL='block',STRICT_SELECT='ckstop')
 c.pass_once(final=True)
 assert (c.state/'gcs_o.done').exists() and not (c.state/'gcs_checkpoint_7_stop.done').exists()
 archive=(c.root/'o/o.tar').read_bytes();os.environ['STRICT_FAIL']=''
 c.pass_once(final=True)
 assert (c.state/'gcs_checkpoint_7_stop.done').exists()
 assert (c.root/'o/o.tar').read_bytes()==archive
 assert any(v in (c.spool/'retry.log').read_text() for v in ('TimeoutExpired','E104'))
 return dict(reserve_interrupted_stop=True,archive_sent=True,stop_resumed=True,archive_frozen=True)
def atomic_receipts():
 c=fixture('receipts');p=c.root/'payload';p.write_bytes(b'q'*400)
 key=C.read(K/'k/y.json')['objects']['m100']+'.j41';calls=[]
 sync=C.os.fsync;replace=C.os.replace
 def fake(uri,path,offset,length,name):return dict(name=name,bytes=length,offset=offset,sha256='q',generation='1')
 with patch.object(C,'upload',side_effect=fake),patch.object(C.os,'fsync',side_effect=lambda fd:(calls.append('fsync'),sync(fd))[1]),patch.object(C.os,'replace',side_effect=lambda a,b:(calls.append('replace'),replace(a,b))[1]):
  rc=C.writer_main([str(K/'b/gc.py'),'split',str(c.spool/'private/sess.json'),key,str(p),'4','4'])
 assert rc==0 and calls==['fsync','replace','fsync']*4,calls
 return dict(parts=4,atomic_receipts=True)
def stop_slot():
 c=fixture('stop_slot')
 d=c.train/'checkpoint_7';d.mkdir();(d/'complete.json').write_text('{"step":7}')
 (c.spool/'stop.request').write_text('1');calls=[]
 with patch.object(c,'send',side_effect=lambda d,m,labels,**kw:calls.append((d.name,labels))),patch.dict(os.environ,{'TK_JOB_START':str(time.time()-82801)}):
  c.pass_once(final=False,small=False)
  assert calls==[],calls
  d=c.train/'checkpoint_8';d.mkdir();(d/'complete.json').write_text('{"step":8}')
  (c.train/'run_0.json').write_text('{"last_step":8}')
  c.pass_once(final=False,small=False)
 assert calls[0]==('checkpoint_8',['ckstop']),calls
 return dict(pending_stop_did_not_claim_old_state=True,reported_stop_selected=True)
for name,fn in [('partial_resume',partial),('atomic_cache',atomic_cache),('stale_copy',stale_copy),('priority_interrupt',priority_interrupt),('strict_rejection',protocol_rejection),('reserve_resume',reserve),('atomic_receipts',atomic_receipts),('stop_slot',stop_slot)]:test(name,fn)
raise SystemExit(any(r['status']!='PASS' for r in rows))
