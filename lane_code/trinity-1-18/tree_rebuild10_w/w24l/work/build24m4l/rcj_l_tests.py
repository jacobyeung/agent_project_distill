from common import *
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

# Actual C'/P constructors in separate isolated Python children; only asset loading is stubbed.
ptree=F/'p_tree'
with tarfile.open(L/'work/build24m4h/p.tar') as t:t.extractall(ptree,filter='data')
samples=[]
for i in range(80):
 row=dict(qid='q'+str(i),dataset='fixture',scene='room',target='A',student_input=dict(question='Q'+str(i),options=['A','B'],frames=[{}]*32,frame_indices=list(range(32)),timestamps=[i/30 for i in range(32)],fps=30,total_num_frames=32))
 samples.append((10+3*i,json.dumps(row),'{}'))
ndb=F/'n.sqlite';database(ndb,samples);picked=PC.selected(ndb,80,random.Random(PC.SEED),'routing');J.write(F/'rows.json',picked)
n=J.load(kit('n')/'k/n.json');p=J.load(input_file(n['r1_training']['p_run']['config']['sha256']))
outputs={}
for side,tree,cfg in [('n',T,n),('p',ptree,p),('bad',T,dict(n,frame_count=64))]:
 J.write(F/(side+'.json'),cfg);out=F/(side+'_out.json')
 cmd=[sys.executable,'-I','-s','-B',str(D/'pc_fixture_worker.py'),str(tree),str(L/'out/rcj/pc.py'),str(F/(side+'.json')),str(F/'rows.json'),str(out)]
 child=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(F/(side+'.log')).write_text(child.stdout);assert child.returncode==0,child.stdout
 outputs[side]=J.load(out)
scope=dict(routing=80,vqa=0,vqa_staged=False,vqa_unavailable_reason='Synthetic fixture')
passed=PC.compare(picked,outputs['n'],outputs['p'],scope);failed=PC.compare(picked,outputs['bad'],outputs['p'],scope)
J.write(F/'pass.json',passed);J.write(F/'fail.json',failed)
assert passed['status']=='PASS',passed['rows'][0]
assert failed['status']=='FAIL' and all(r['status']=='FAIL' for r in failed['rows'])
assert outputs['p']['tree_sha256'].startswith('b83a8a35')
records.append(dict(case='processor',pass_rows=80,deliberate_fail_rows=80,sample_sha256=passed['sample_sha256'],scope='Native isolated constructors and text/encoder paths; synthetic rows and tokenizer loader.'))

orig=J.load
class Z:
 sha=staticmethod(J.sha);write=staticmethod(J.write);checked=staticmethod(J.checked)
 @staticmethod
 def load(p):return dict(n_root=str(F/'remote'),namespace='/tmp/q_22c714e1') if str(p).endswith('k/p.json') else orig(p)
J.write(F/'remote/rcj/P_SAMPLE_I.json',dict(schema='p_sample_request_v1',uniform_positions=[0]))
for mode in ('b','r'):
 root=F/('node_'+mode);native=root/'r' if mode=='b' else root/'dr/p/q';base=native if mode=='b' else native/'base'
 base.mkdir(parents=True);shutil.copyfile(db,base/'rows.sqlite')
 if mode=='r':(native/'selection').mkdir();shutil.copyfile(ndb,native/'selection/rows.sqlite')
 J.write(root/'mode.json',dict(mode=mode));J.write(root/'staging.json',dict(seconds=1));J.write(root/'build.json',dict(seconds=2))
 for part in ([base] if mode=='b' else [base,native/'selection']):
  for f in ('receipt.json','materialization.json'):J.write(part/f,dict(count=100))
 for tag,rc,proc,sample_fail,expected in [('pass',0,passed,False,0),('sample_refuse',0,passed,True,0),('build_refuse',7,passed,True,0),('proc_fail',0,failed,False,1 if mode=='r' else 0)]:
  job=str(1000+len(records));calls=[]
  def diff(*args):calls.append('diff');return 0
  def launch(*args,**kwargs):calls.append('check');J.write(root/'proc_check.json',proc);return int(proc['status']!='PASS')
  def sampling(*args):calls.append('sample');assert mode=='b' or calls[0]=='diff';return dict(status='PASS')
  with patch.object(R,'attach',return_value=Z),patch.object(R,'DB',h),patch.object(R,'rdiff',side_effect=diff),patch.object(R,'launch',side_effect=launch),patch.object(R,'sample',side_effect=ValueError('PS_TOO_LARGE:5000001') if sample_fail else sampling):
   assert R.publish(kit('qd'),root,job,rc)==expected
  timing=J.load(F/'remote/o'/job/'timings.json');assert timing['returncode']==rc
  if sample_fail:assert timing['sample']['status']=='REFUSE'
  if mode=='r':assert J.load(F/'remote/o'/job/'proc_check.json')['status']==proc['status']
  records.append(dict(case=mode+'_'+tag,returncode=rc,post_returncode=expected))
stageroot=F/'stage';stageroot.mkdir()
class BadZ(Z):
 @staticmethod
 def load(p):return dict(source=dict(path='missing',sha256='0'*64)) if str(p).endswith('k/a.json') else Z.load(p)
with patch.object(R,'attach',return_value=BadZ):
 try:R.stage(kit('qd'),stageroot,'203','r')
 except ValueError:pass
 else:raise AssertionError('stage failure expected')
 R.publish(kit('qd'),stageroot,'203',1)
assert J.load(F/'remote/o/203/timings.json')['returncode']==1
readonly=F/'ro';readonly.mkdir();J.write(D/'rcj_k/ro_params.json',dict(root=str(F/'node_r'),stage_root=str(stageroot),target=str(readonly)))
script=D/'rcj_ro.py'
cmd=['bwrap','--ro-bind','/','/','--bind',str(L),str(L),'--ro-bind',str(readonly),str(readonly),'--dev-bind','/dev','/dev','--proc','/proc',sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(script)]
child=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(D/'rcj_ro_l.log').write_text(child.stdout);assert child.returncode==0,child.stdout
records.append(dict(case='read_only_publication',output=child.stdout))
J.write(D/'RCJ_L_TESTS.json',dict(status='PASS',records=records,production_rows_checked=False))
print('RCJ L PASS',len(records),'groups')
