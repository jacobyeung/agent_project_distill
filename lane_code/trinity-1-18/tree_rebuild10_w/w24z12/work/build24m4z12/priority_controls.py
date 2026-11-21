import sys,os,json,time,runpy
from pathlib import Path
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z12'
scope={'__file__':str(D/'core_tests.py')};text=(D/'core_tests.py').read_text().split('def protocol():',1)[0].replace("'core_'","'priority_'")
with patch.object(sys,'argv',['controls','verified']):exec(compile(text,str(D/'core_tests.py'),'exec'),scope)
fixture=scope['fixture'];state=scope['state'];C,c=fixture('new_export');sys.path.insert(0,str(D));import strict_sink
state(C,c,'checkpoint_30',30);(c.spool/'stop.request').write_text('1')
C.put(c.state/'priority_settled.json',C.priority_version(c.train,c.state,c.nominal_stop()))
p=c.root/'payload';p.write_bytes(b'q'*(1<<20));name=C.read(c.kit/'k/y.json')['objects']['ck00']+'.j41.part00-of-04';uri=json.loads(c.cached_sessions())[name]
os.environ.update(STRICT_SESSIONS=str(c.spool/'private/sess.json'),TK_PRIORITY_TRAIN=str(c.train),TK_PRIORITY_STATE=str(c.state),TK_NOMINAL_STOP='inf',TK_UPLOAD_DEADLINE=str(time.time()+10),TK_UPLOAD_CHUNK_BYTES=str(256<<10))
respond=strict_sink.Connection.respond;created=[]
def arrival(self):
 reply=respond(self)
 if self.data and not created:
  created.append(state(C,c,'m100',100));
 return reply
with strict_sink.transport(),patch.object(strict_sink.Connection,'respond',arrival):
 try:C.upload(uri,p,0,p.stat().st_size,name);raise AssertionError('new export failed to interrupt')
 except InterruptedError:pass
assert not C.priority_settled(c.train,c.state,c.nominal_stop())
events=[json.loads(l) for l in (c.root.parent/'sink/events.jsonl').read_text().splitlines()];assert sum(e['bytes'] for e in events)==256<<10
c.exports();C.put(c.state/'priority_settled.json',C.priority_version(c.train,c.state,c.nominal_stop()))
with strict_sink.transport():receipt=C.upload(uri,p,0,p.stat().st_size,name)
assert receipt['bytes']==1<<20
last=[json.loads(l) for l in (c.root.parent/'sink/events.jsonl').read_text().splitlines() if json.loads(l)['name']==name]
assert sum(e['bytes'] for e in last)==1<<20 and any(e['bytes']==0 and e['range']=='bytes=0-262143' for e in last)
# A priority item appearing after the export stage cannot inherit that pass's settlement.
C,c=fixture('during_pass');state(C,c,'checkpoint_2',2);state(C,c,'checkpoint_30',30);calls=[]
def logs():state(C,c,'m100',100);return 1
with patch.object(c,'small',new=logs),patch.object(c,'send',side_effect=lambda d,m,labels,**kw:calls.append(labels)),patch.object(c,'exit_archive',new=lambda:None):
 c.pass_once(final=True)
assert not C.priority_settled(c.train,c.state,c.nominal_stop()) and not any(v[0]=='ck00' for v in calls),calls
r=dict(status='PASS',settled_writer_started=True,new_export_preempted=True,retained_bytes=256<<10,resume_query_and_no_duplicate_bytes=True,arrival_during_pass_blocks_ordinary=True)
(D/'PRIORITY_CONTROLS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
