from pathlib import Path
import os,sys,runpy,json,importlib.util,hashlib,time
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z5';R=D/'resume';R.mkdir()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=module('pc',J/'out/kit_n/b/pc.py');T=module('transport',D/'transport.py')
payload=R/'q.bin';payload.write_bytes(os.urandom(4<<20));local=R/'sess.json';key='q9/rate'
sessions={key+f'.part{i:02d}-of-04':'https://local.invalid/'+key+f'.part{i:02d}-of-04' for i in range(4)}
C.put(local,sessions);os.environ.update(FAKE_SINK=str(R/'sink'),TK_COPY_DEADLINE=str(time.time()+90))
lost=[False]
class Connection(T.Connection):
 def getresponse(self):
  response=super().getresponse()
  if self.name.endswith('part00-of-04') and self.data and not lost[0]:
   lost[0]=True;raise OSError('lost response after accepted range')
  return response
helper=J/'out/kit_n/b/gc.py';g=runpy.run_path(str(helper));g['CHUNK']=256<<10
args=[str(helper),'split',str(local),key,str(payload),'4','4']
with patch.object(C.http.client,'HTTPSConnection',Connection),patch.object(C.runpy,'run_path',return_value=g):
 assert C.writer_main(args)==1
 receipts=Path(str(local)+'.receipts.jsonl');first=[json.loads(x) for x in receipts.read_text().splitlines()];assert len(first)==3
 assert C.writer_main(args)==0
 rows=[json.loads(x) for x in receipts.read_text().splitlines()];assert len(rows)==4
 count=len((R/'requests.jsonl').read_text().splitlines());assert C.writer_main(args)==0
 assert len((R/'requests.jsonl').read_text().splitlines())==count
req=[json.loads(x) for x in (R/'requests.jsonl').read_text().splitlines()]
assert sum(r['sent'] for r in req)==payload.stat().st_size
assert any(r['range'].startswith('bytes 262144-') for r in req if r['name'].endswith('part00-of-04'))
for row in rows:
 raw=(R/'sink'/hashlib.sha256(row['name'].encode()).hexdigest()).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==row['sha256']
# Lost final reply: the next status query supplies the committed metadata.
name='q9/final';uri='https://local.invalid/'+name
class LostFinal(T.Connection):
 def getresponse(self):
  reply=super().getresponse()
  if self.data:raise OSError('lost final response')
  return reply
with patch.object(C.http.client,'HTTPSConnection',LostFinal):
 try:C.upload_range(uri,payload,0,256<<10,name,256<<10,time.time()+30)
 except OSError:pass
 else:raise AssertionError('failure injection absent')
 row=C.upload_range(uri,payload,0,256<<10,name,256<<10,time.time()+30)
 assert row['bytes']==256<<10
result=dict(status='PASS',payload_bytes=4<<20,first_completed_parts=3,final_completed_parts=4,bytes_resent=0,interrupted_part_resumed_at=256<<10,lost_final_reply_recovered=True,atomic_receipts=True)
(D/'RESUME.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
