from common import *
D=L/'work/build24m4s/sample'
import importlib.util,sqlite3,gzip,subprocess,copy,tarfile,random,shutil
from unittest.mock import patch
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=module('rcj_l',L/'out/rcj/x.py');PC=module('pc_l',L/'out/rcj/pc.py')
F=D/'rcj_l';F.mkdir();records=[]
def database(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(p) as c:
  c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
  c.executemany('INSERT INTO rows VALUES(?,?,?)',rows)
 return J.sha(p)
rawrows=[(7+i*3,json.dumps(dict(qid='q'+str(i),s1_source=dict(name='U_Faithful' if i%2 else 'x'))),'text'+str(i)) for i in range(100)]
db=F/'p.sqlite';h=database(db,rawrows);req=F/'request.json';J.write(req,dict(schema='p_sample_request_v1',uniform_positions=[0,2,80,99]))
rd=F/'rd0';rd.mkdir();(rd/'rdiff.json.gz').write_bytes(gzip.compress(json.dumps(dict(P_absent=[dict(i=rawrows[i][0]) for i in range(0,70,3)])).encode()))
real_subprocess=R.subprocess.run
def fixture_sample(database,request,output,rd0=None,gate=h):
 def invoke(cmd,**kw):
  assert kw['env']['PS_GATE']=='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
  kw['env']['PS_GATE']=gate
  return real_subprocess(cmd,**kw)
 with patch.object(R.subprocess,'run',side_effect=invoke):return R.sample(database,request,output,rd0)
result=fixture_sample(db,req,F/'sample.json',rd)
ref=module('ps_reference',L/'out/rcj/ps.py')
with patch.object(ref,'GATE',h):ref.main(db,req,rd,F/'reference.json')
assert (F/'sample.json').read_bytes()==(F/'reference.json').read_bytes()
v=J.load(F/'sample.json');assert [r['i'] for r in v['rows'][:4]]==[rawrows[i][0] for i in (0,2,80,99)]
assert len([r for r in v['rows'] if r['class']=='U_Faithful'])==20 and len([r for r in v['rows'] if r['class']=='P_absent'])==20
records.append(dict(case='reference_exact',rows=len(v['rows']),sha256=J.sha(F/'sample.json')))
for name,base,gate in [('gate',db,R.DB),('large',F/'large.sqlite',None)]:
 if name=='large':gate=database(base,[(0,json.dumps(dict(text='x'*5_000_001)),'a')]);J.write(F/'large_request.json',dict(schema='p_sample_request_v1',uniform_positions=[0]))
 with patch.object(R,'DB',gate):
  try:fixture_sample(base,req if name=='gate' else F/'large_request.json',F/(name+'_out.json'),gate=gate)
  except ValueError as e:assert ('PS_GATE_FAILED' if name=='gate' else 'PS_TOO_LARGE') in str(e);records.append(dict(case=name,refusal=str(e)))
  else:raise AssertionError(name)
 assert not (F/(name+'_out.json')).exists()


J.write(D/'SAMPLE_TESTS.json',dict(status='PASS',records=records))
print('Sample reference, gate and size checks PASS')
