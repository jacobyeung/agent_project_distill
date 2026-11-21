import os,sys,json,time,importlib.util
from pathlib import Path
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z10';W=D/'policy';W.mkdir();K=D/'findings_final/setting/kit_n'
s=importlib.util.spec_from_file_location('pc_policy',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
x=W/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=W/'n';n.mkdir()
names=C.read(K/'k/y.json')['objects'];sessions={v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j41'+f'.part{i:02d}-of-04' for v in names.values() for i in range(4)}
p=x/'n_s/sess_41.json';p.write_text(json.dumps(sessions));p.chmod(0o600)
original=C.read
def read(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=str(x)
 return v
recipe=C.read(K/'k/n.json')['recipe'];assert recipe['stop_before_seconds']==6000
start=time.time()-recipe['wall_seconds']+recipe['stop_before_seconds']-1
with patch.dict(os.environ,{'TK_JOB_START':str(start)}),patch.object(C,'read',side_effect=read):
 c=C.Copier(K,n,'41');c.train.mkdir(parents=True)
 assert c.nominal_stop()==start+recipe['wall_seconds']-6000
 old=c.train/'checkpoint_6';old.mkdir();(old/'complete.json').write_text('{"step":6}')
 os.utime(old/'complete.json',(start,start))
 assert not c.stop_ready() and c.stop_requested()
 fresh=c.train/'checkpoint_7';fresh.mkdir();marker=fresh/'complete.json';marker.write_text('{"step":7}')
 calls=[]
 with patch.object(c,'send',side_effect=lambda *a,**kw:calls.append(a[2])):c.pass_once(small=False)
 assert calls==[['ckstop']] and not list(c.train.glob('run_*.json'))
 C.put(c.state/'gcs_checkpoint_7_stop.done',dict(marker_sha256=C.sha(marker)))
 with patch.object(c,'send') as send:c.checkpoints();send.assert_not_called()
 payload=n/'q';payload.write_bytes(b'q'*100);name=names['ck00']+'.j41.part00-of-04'
 env={'TK_PRIORITY_TRAIN':str(c.train),'TK_PRIORITY_STATE':str(c.state),'TK_NOMINAL_STOP':str(c.nominal_stop()),'TK_UPLOAD_LOG':str(c.spool/'upload.log')}
 with patch.dict(os.environ,env):
  try:C.upload(sessions[name],payload,0,100,name);raise AssertionError('ordinary request sent after nominal stop')
  except InterruptedError:pass
result=dict(status='PASS',decoded_stop_before_seconds=6000,stale_marker_ignored=True,new_marker_uploaded_without_report=True,ordinary_held_after_stop_receipt=True,writer_interrupted_before_socket=True)
(W/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
