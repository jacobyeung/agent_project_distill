from common import *
import importlib.util,sqlite3,copy,subprocess,ast
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_k',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
F=D/'rcj_k';F.mkdir()
records=[]
real_load=J.load
class Z:
 sha=staticmethod(J.sha);write=staticmethod(J.write);checked=staticmethod(J.checked)
 @staticmethod
 def load(p):
  if str(p).endswith('k/p.json'):return dict(n_root=str(F/'remote'),namespace='/tmp/q_22c714e1')
  return real_load(p)

def db(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(path) as c:
  c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
  c.executemany('INSERT INTO rows VALUES(?,?,?)',rows)
 return J.sha(path)

small=F/'small.sqlite';h=db(small,[(1,'row','target'),(7,'seven','two')])
for tag,request in (('list',[7,1]),('seed',dict(seed=12,i=[1]))):
 p=F/(tag+'.json');J.write(p,request);out=F/(tag+'_out.json')
 r=R.sample(small,p,out,expected=h)
 assert json.loads(out.read_bytes())==([[1,'row','target'],[7,'seven','two']] if tag=='list' else [[1,'row','target']])
 records.append(dict(case=tag,result=r))
for tag,request in (('bool',[True]),('float',[1.0]),('negative',[-1]),('repeat',[1,1]),('object',{'i':'x'})):
 p=F/(tag+'.json');J.write(p,request)
 try:R.sample(small,p,F/(tag+'_out.json'),expected=h)
 except ValueError as e:assert str(e)=='R1_SAMPLE_I_INVALID'
 else:raise AssertionError(tag)
 assert not (F/(tag+'_out.json')).exists()
large=F/'large.sqlite';lh=db(large,[(0,'x'*5_000_001,'a')]);J.write(F/'large.json',[0])
try:R.sample(large,F/'large.json',F/'large_out.json',expected=lh)
except ValueError as e:assert str(e)=='R1_SAMPLE_TOO_LARGE'
else:raise AssertionError('size cap')
assert not (F/'large_out.json').exists()
# JSON escaping can exceed the cap even when SQLite payload bytes do not.
escaped=F/'escaped.sqlite';eh=db(escaped,[(0,'\x01'*900_000,'a')])
try:R.sample(escaped,F/'large.json',F/'escaped_out.json',expected=eh)
except ValueError as e:assert str(e)=='R1_SAMPLE_TOO_LARGE'
else:raise AssertionError('escaped size cap')
assert not (F/'escaped_out.json').exists()
try:R.sample(small,F/'list.json',F/'gate_out.json')
except ValueError as e:assert str(e)=='R1_SAMPLE_GATE_FAILED'
else:raise AssertionError('gate')
assert not (F/'gate_out.json').exists()
records.append(dict(case='sample_negative',size_cap=True,escaped_size_cap=True,gate_failed=True))

root=F/'node';q=root/'dr/p/q';q.mkdir(parents=True)
J.write(root/'mode.json',dict(mode='r'));J.write(root/'staging.json',dict(seconds=1.25));J.write(root/'build.json',dict(seconds=2.5,status='PASS'))
for part in ('base','selection','pr'):
 db(q/part/'rows.sqlite',[(1,'row','target'),(7,'seven','two')])
 for fn in ('receipt.json','materialization.json'):J.write(q/part/fn,dict(count=2))
J.write(q/'base_imports.json',dict(status='PASS'));J.write(root/'dr/p/routing_selection.json',dict(rows=2))
J.write(F/'remote/rcj/P_SAMPLE_I.json',[7])
calls=[]
actual_sample=R.sample
with patch.object(R,'attach',return_value=Z),patch.object(R,'DB',h),patch.object(R,'rdiff',side_effect=lambda *a:calls.append(a) or 0),patch.object(R,'sample',side_effect=lambda *a:actual_sample(*a,expected=h)):
 assert R.publish(kit('qd'),root,'101',0)==0
target=F/'remote/o/101';v=J.load(target/'db_bytes.json');assert len(v['files'])==2 and v['equal_target']
assert all(vv['size']==small.stat().st_size and bytes.fromhex(vv['header'])==b'SQLite format 3\0' for vv in v['files'])
assert J.load(target/'timings.json')['mode_r_seconds']==2.5 and len(calls)==1
assert (target/'routing_selection.json').is_file() and (target/'k_b1r.json').is_file() and (target/'p_sample.json').is_file()
assert not list(target.rglob('*.sqlite'))
records.append(dict(case='publication_success',two_databases=True,k_artifacts=True,sample=True,rdiff=True))
with patch.object(R,'attach',return_value=Z),patch.object(R,'rdiff',side_effect=AssertionError('gate did not pass')):
 assert R.publish(kit('qd'),root,'102',1)==0
assert not (F/'remote/o/102/p_sample.json').exists()
assert J.load(F/'remote/o/102/timings.json')['returncode']==1
copyfile=R.shutil.copyfile
def copy_fail(a,b):
 if Path(b).name=='receipt.json':raise PermissionError('fixture')
 return copyfile(a,b)
with patch.object(R,'attach',return_value=Z),patch.object(R.shutil,'copyfile',side_effect=copy_fail):
 try:R.publish(kit('qd'),root,'103',1)
 except ValueError as e:assert str(e)=='R1_PUBLICATION_INCOMPLETE'
 else:raise AssertionError('hidden publication failure')
assert (F/'remote/o/103/materialization.json').is_file() and (F/'remote/o/103/db_bytes.json').is_file()
records.append(dict(case='publication_refusal',independent_artifacts=True,failed_gate_no_sample=True))

# The inner run cannot publish; its writable root excludes the destination.
sys.path.insert(0,str(kit('qd')/'b'));import rb
rebuild=F/'rebuild';rebuild.mkdir();J.write(rebuild/'env.json',dict(paths=[]));J.write(rebuild/'plan.json',dict(paths={},config={}))
for tag,side in (('success',None),('refusal',ValueError('fixture'))):
 with patch.object(R,'attach',return_value=Z),patch.object(rb,'reconstruct',side_effect=side),patch.object(R,'publish',side_effect=AssertionError('inner publish')):
  try:R.run(kit('qd'),rebuild,'201')
  except ValueError as e:assert str(e)=='fixture' and tag=='refusal'
  else:assert tag=='success'
 assert J.load(rebuild/'build.json')['status']==('PASS' if tag=='success' else 'REFUSE')
 with patch.object(R,'attach',return_value=Z):R.publish(kit('qd'),rebuild,'20'+('1' if tag=='success' else '2'),int(tag=='refusal'))

stageroot=F/'stage_failure';stageroot.mkdir()
class BadZ(Z):
 @staticmethod
 def load(p):
  if str(p).endswith('k/a.json'):return dict(source=dict(path='missing',sha256='0'*64))
  return Z.load(p)
with patch.object(R,'attach',return_value=BadZ):
 try:R.stage(kit('qd'),stageroot,'203','r')
 except ValueError:pass
 else:raise AssertionError('stage accepted missing input')
 assert (stageroot/'staging.json').is_file()
 R.publish(kit('qd'),stageroot,'203',1)
assert J.load(F/'remote/o/203/timings.json')['staging_seconds']>=0
records.append(dict(case='inner_and_stage',inner_never_publishes=True,stage_failure_published=True,rebuild_mode=True))

# The real a.py entry receives r and the authenticated resolver record.
J.write(root/'pins.json',dict(paths={}))
seen=[]
with patch.object(R,'attach',return_value=Z),patch.object(R.runpy,'run_path',side_effect=lambda p,**kw:seen.append((p,list(sys.argv),kw))):R.run_r(kit('qd'),root,'301')
assert seen[0][0]==str(kit('qd')/'b/a.py') and seen[0][1][1:]==['r','/tmp/q_22c714e1/p','/tmp/q_22c714e1/r.json']
records.append(dict(case='native_entry',argv=seen[0][1][1:]))

# A separate process mounts the actual destination read-only.
readonly=F/'ro';readonly.mkdir();J.write(F/'ro_params.json',dict(root=str(root),stage_root=str(stageroot),target=str(readonly)))
script=D/'rcj_ro.py'
script.write_text('''from common import *
import importlib.util
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_ro',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
v=J.load(D/'rcj_k/ro_params.json');orig=J.load
class Z:
 sha=staticmethod(J.sha);write=staticmethod(J.write)
 @staticmethod
 def load(p):return dict(n_root=v['target']) if str(p).endswith('k/p.json') else orig(p)
for case,root,rc in (('success',v['root'],0),('refusal',v['root'],1),('stage',v['stage_root'],1)):
 with patch.object(R,'attach',return_value=Z):
  try:R.publish(kit('qd'),root,'401',rc)
  except ValueError as e:assert str(e)=='R1_PUBLICATION_INCOMPLETE'
  else:raise AssertionError('read-only target accepted')
 r=J.load(Path(root)/'publication.json');assert any(x['file']=='timings.json' for x in r['publication_errors']);assert len(r['publication_errors'])>5 and r['returncode']==rc
 J.write(D/('RO_'+case+'.json'),r)
 print('READ_ONLY_TARGET_PASS',case,len(r['publication_errors']))
''')
cmd=['bwrap','--ro-bind','/','/','--bind',str(L),str(L),'--ro-bind',str(readonly),str(readonly),'--dev-bind','/dev','/dev','--proc','/proc',sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(script)]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(D/'rcj_ro.log').write_text(p.stdout);assert p.returncode==0,p.stdout
records.append(dict(case='actual_readonly_mount',output=p.stdout))
subprocess.run(['/bin/bash','-n',str(L/'out/rcj/rcj.sh')],check=True)
compile((L/'out/rcj/x.py').read_text(),str(L/'out/rcj/x.py'),'exec')
J.write(D/'RCJ_K_TESTS.json',dict(status='PASS',records=records,production_executed=False))
print('RCJ_K PASS',len(records),'groups')
