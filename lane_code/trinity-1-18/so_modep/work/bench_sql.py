from pathlib import Path
import os,sys,time,json,sqlite3,hashlib
os.sched_setaffinity(0,range(8))
sys.path.insert(0,str(Path(__file__).resolve().parent/'tree'))
import torch
torch.set_num_threads(8)
import numpy as np
from student_pilot.s1_exclusions import _database
from student_pilot.p3_provenance import file_pin,sha256
from student_pilot.ground_target_filter import mask_quality
R=Path(__file__).resolve().parent/'bench_sql';R.mkdir()
p=R/'rows.sqlite'
with sqlite3.connect(p) as c:
 c.execute('CREATE TABLE payloads(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
 for i in range(8192):
  row=dict(qid=str(i),dataset='d1',scene='fixture',ground_record=dict(text='test '*512),routing={})
  c.execute('INSERT INTO payloads VALUES(?,?,?)',(i,json.dumps(row),'{}'))
 c.execute("CREATE VIEW rows AS SELECT i,json_set(row,'$.routing.ground_record',json_extract(row,'$.ground_record')) AS row,target FROM payloads")
pin=file_pin(p)
class Rule:
 def counts(self,source):pass
 def expect(self,source,rows,population):
  for row in rows:pass
 def keep(self,row,source):return True
results=[]
for stride in (1,10,100):
 indices=list(range(0,8192,stride))[::-1]
 for enabled in ('0','1','1','0'):
  os.environ['S1_PREP_SELECT_SQL']=enabled
  start=time.perf_counter();out=_database(pin,indices,Rule(),'fixture');elapsed=time.perf_counter()-start
  assert out==indices
  result=dict(fixture=True,kind='selected_view',database_bytes=p.stat().st_size,total_rows=8192,selected_rows=len(indices),enabled=enabled,seconds=elapsed,selected_rows_per_second=len(indices)/elapsed)
  results.append(result);print(json.dumps(result),flush=True)
mask=np.zeros((240,320),bool);mask[30:130,40:170]=True
start=time.perf_counter()
for _ in range(2000):quality=mask_quality(mask)
elapsed=time.perf_counter()-start
result=dict(fixture=True,kind='mask_quality',shape=[240,320],iterations=2000,seconds=elapsed,masks_per_second=2000/elapsed)
results.append(result);print(json.dumps(result),flush=True)
start=time.perf_counter()
for _ in range(16):sha256(p)
elapsed=time.perf_counter()-start
result=dict(fixture=True,kind='warm_sha256',file_bytes=p.stat().st_size,iterations=16,seconds=elapsed,mib_per_second=p.stat().st_size*16/elapsed/2**20)
results.append(result);print(json.dumps(result),flush=True)
(R/'RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
