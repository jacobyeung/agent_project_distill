import os,sys,json,time,shutil,importlib.util,subprocess,tarfile,hashlib,traceback
from pathlib import Path
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z7';R=D/('core_'+sys.argv[1]);R.mkdir()
OLD=J.parent/'w24z4/out/kit_n';NEW=J/'out/kit_n';rows=[]
def load_module(k):
 s=importlib.util.spec_from_file_location('test_pc_'+k.parent.name,k/'b/pc.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def fixture(tag,k=NEW):
 C=load_module(k);r=R/tag;r.mkdir();kit=r/'kit';(kit/'k').mkdir(parents=True);(kit/'b').mkdir()
 for name in ('pc.py','o.py','gc.py','z.py','wh.json'):shutil.copyfile(k/'b'/name,kit/'b'/name)
 for name in ('n.json','y.json','g.json'):shutil.copyfile(k/'k'/name,kit/'k'/name)
 x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir();(n/'p/q/r').mkdir(parents=True)
 (kit/'k/p.json').write_text(json.dumps(dict(n_root=str(x))))
 values={v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+v+'.j41'+f'.part{i:02d}-of-04' for v in C.read(k/'k/y.json')['objects'].values() for i in range(4)}
 p=x/'n_s/sess_41.json';p.write_text(json.dumps(values));p.chmod(0o600)
 c=C.Copier(kit,n,'41',writer=D/'strict_writer.py');c.deadline=time.time()+20;c.archive_due=time.time()+15;c.upload_until=c.archive_due
 os.environ.update(STRICT_KIT=str(k),STRICT_SINK=str(r/'sink'),STRICT_OLD='1' if k==OLD else '0',STRICT_FAIL='',TK_UPLOAD_LOG=str(c.spool/'upload.log'))
 return C,c
def state(C,c,name,step,size=1<<20):
 p=c.train/name;p.mkdir();(p/'q.bin').write_bytes(b'q'*size)
 marker=p/('complete.json' if name.startswith('checkpoint') else 'artifact.json');C.put(marker,dict(step=step));return marker
def run(name,fn):
 try:detail=fn();row=dict(name=name,status='PASS',detail=detail)
 except Exception as e:row=dict(name=name,status='FAIL',error=str(e),output=traceback.format_exc())
 rows.append(row);(R/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
def protocol():
 got={}
 for tag,k in [('before',OLD),('after',NEW)]:
  C,c=fixture('protocol_'+tag,k);state(C,c,'m100',100);c.exports()
  got[tag]=(c.state/'gcs_m100.done').exists()
  events=[json.loads(s) for s in (c.root.parent/'sink/events.jsonl').read_text().splitlines()]
  assert all(e['http']==400 for e in events) if tag=='before' else any(e['http']==308 for e in events)
 assert got==dict(before=False,after=True),got
 return got
def cache():
 got={}
 for tag,k in [('before',OLD),('after',NEW)]:
  C,c=fixture('cache_'+tag,k);(c.spool/'private/sess.json').write_text('{}')
  try:C.Copier(c.kit,c.root,'41');got[tag]='accepted'
  except ValueError:got[tag]='refused'
 assert got==dict(before='accepted',after='refused'),got
 C,c=fixture('cache_modes');p=c.spool/'private/sess.json';p.chmod(0o644)
 try:c.cached_sessions();raise AssertionError('mode accepted')
 except ValueError:pass
 p.chmod(0o600);p.write_text('{')
 try:c.cached_sessions();raise AssertionError('JSON accepted')
 except ValueError:pass
 return got
def live_priority():
 got={}
 for tag,k in [('before',OLD),('after',NEW)]:
  C,c=fixture('priority_'+tag,k);state(C,c,'checkpoint_7',7);state(C,c,'m101',101)
  (c.spool/'stop.request').write_text('1');(c.train/'run_0.json').write_text('{"last_step":7}');(c.root/'o').mkdir();(c.root/'o/o.tar').write_bytes(b'x')
  calls=[]
  with patch.object(c,'send',side_effect=lambda d,m,labels,**kw:calls.append(labels)):
   c.pass_once(final=False,small=False)
  got[tag]=calls
 assert got['before'][0]!=['ckstop'] and any(x==['o'] for x in got['before'])
 assert got['after'][0]==['ckstop'] and got['after'][1][0]=='mstop'
 assert not any(x==['o'] or x[0]=='ck00' for x in got['after'])
 return got
def retry_all():
 got={}
 for tag,k in [('before',OLD),('after',NEW)]:
  C,c=fixture('retry_'+tag,k);state(C,c,'m100',100)
  C.put(c.state/'gcs_o.done',{});C.put(c.state/'o_copy.done',{});C.put(c.state/'logs.done',{});c.logs_complete=True
  calls=[]
  def once(**kw):
   calls.append(1)
   if len(calls)==3:C.put(c.state/'gcs_m100.done',{})
  with patch.object(C,'Copier',return_value=c),patch.object(c,'pass_once',side_effect=once),patch.object(C.time,'sleep'),patch.object(sys,'argv',['pc',str(c.kit),str(c.root),'41','--final']):C.main()
  got[tag]=len(calls)
 assert got==dict(before=1,after=3),got
 return got
def archive_result():
 got={}
 for tag,k in [('before',OLD),('after',NEW)]:
  C,c=fixture('result_'+tag,k);(c.root/'q.log').write_text('initial\n');(c.root/'j2.log').write_text('batch\n');(c.root/'j2.err').write_text('batch error\n')
  env={**os.environ,'SLURM_JOB_ID':'41'}
  subprocess.run([sys.executable,'-I','-s','-B',str(c.kit/'b/o.py'),str(c.root),'7','9','--local'],check=True,env=env)
  (c.root/'q.log').write_text('final tail\n');c.final_pass=True;c.exit_status=7;c.exit_archive()
  with tarfile.open(c.root/'o/o.tar') as t:
   result=json.load(t.extractfile('RESULT.json'));tail=t.extractfile('q.log').read();names=t.getnames()
  assert result['proof_rc']==7 and result['rooms_rc']==9,result
  got[tag]=dict(final_tail=tail==b'final tail\n',batch='j2.log' in names)
  if tag=='after':
   raw=(c.root/'o/o.tar').read_bytes();(c.root/'q.log').write_text('later');c.exit_archive();assert (c.root/'o/o.tar').read_bytes()==raw
 assert got==dict(before=dict(final_tail=False,batch=False),after=dict(final_tail=True,batch=True)),got
 return got
def failed_stop():
 got={}
 for mode in ('fail','stall'):
  for tag,k in [('before',OLD),('after',NEW)]:
   C,c=fixture(mode+'_'+tag,k);state(C,c,'checkpoint_7',7);c.exit_status=0
   os.environ.update(STRICT_FAIL=mode,STRICT_SELECT='ckstop')
   c.pass_once(final=True)
   got[mode+'_'+tag]=(c.state/'gcs_o.done').exists()
 assert got==dict(fail_before=False,fail_after=True,stall_before=False,stall_after=True),got
 return got
def resume():
 C,c=fixture('resume');state(C,c,'m100',100,10<<20);os.environ.update(STRICT_FAIL='lost',STRICT_SELECT='m100')
 c.exports();assert not (c.state/'gcs_m100.done').exists()
 os.environ['STRICT_FAIL']='';c.exports();assert (c.state/'gcs_m100.done').exists()
 events=[json.loads(s) for s in (c.root.parent/'sink/events.jsonl').read_text().splitlines()]
 # Lost final replies recover by querying completed metadata; no data PUT repeats.
 assert sum(e['bytes']>0 for e in events)==0,events
 receipts=[json.loads(s) for s in (c.spool/'private/sess.json.receipts.jsonl').read_text().splitlines()]
 assert len(receipts)==4
 before=(c.spool/'private/sess.json.receipts.jsonl').read_bytes();c.exports();assert before==(c.spool/'private/sess.json.receipts.jsonl').read_bytes()
 return dict(parts=4,lost_response_recovered=True)
for name,fn in [('protocol',protocol),('cache',cache),('live_priority',live_priority),('retry_all',retry_all),('archive_result',archive_result),('failed_stop',failed_stop),('resume',resume)]:run(name,fn)
raise SystemExit(any(r['status']!='PASS' for r in rows))
