from pathlib import Path
import sys, json, sqlite3, unittest, copy, gzip, time, re, importlib.util
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4t';F=D/('fixtures_'+str(time.time_ns()));F.mkdir()
sys.path[:0]=[str(L/'out/rcj'),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import ch,pc,nd,z
from student_pilot import r1_coverage
from student_pilot.p3_provenance import digest,file_pin,write,load
from student_pilot.extent_receipt import content
from student_pilot.r0_exclusion import reserve
from student_pilot.r2_contract import CONTRACT

def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
x=module('rcj_x',L/'out/rcj/x.py')
def row(q='ok'):
 return dict(qid=q,dataset='d1',scene='fixture_safe',question='safe',target='<think>clear trace</think>\nA',student_input=dict(question='safe',frames=[]),routing=dict(question_type='camera_rotation',category='route',events=[],answer='A'))
def db(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(path) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  c.executemany('insert into rows values(?,?,?)',[(i*3+2,json.dumps(r),'{}') for i,r in enumerate(rows)])
 return file_pin(path)
def pin(path,value):write(path,value);return file_pin(path)
def cfg():return dict(r1_training=dict(enabled=True))
class Tests(unittest.TestCase):
 def test_each_native_check_pass_refuse_and_short_circuit(self):
  for check in ch.CHECKS:
   root=F/check;root.mkdir();a=row();b=row('bad');c=cfg();bindings=[]
   if check=='wording':
    p=pin(root/'w.json',dict(held_out=['forbidden '+str(i) for i in range(8)]));c['r1_training']['wording_exclusion']=p
    b['question']='forbidden 0';bindings=[patch.object(r1_coverage,'SPLIT',p['sha256'])]
   if check=='text':b['target']='<think>heading unavailable</think> A'
   if check=='extents':
    for r in (a,b):
     r['routing'].update(question_type='object_abs_distance',ground_record=dict(program_audit=dict(independent_ordered_boxes=[dict(id='b')])))
    entries={r['qid']:dict(content_sha256=digest(content(r)),box_statuses=['full'],repair_sha256=None) for r in (a,b)}
    c['extent_receipt']=pin(root/'e.json',dict(schema='full-extent-receipt-v1',rows=entries));b['question']='changed copied field'
   if check=='r1':b['own_valued']=True
   if check=='reserve':b['provenance']=dict(input=sorted(reserve().names)[0])
   if check=='r2':c['r2_membership']=pin(root/'a.json',dict(contract=CONTRACT,rows={'ok':digest(dict(row=a,target={},stream='routing'))}))
   database=db(root/'rows.sqlite',[a,b])
   from contextlib import ExitStack
   with ExitStack() as stack:
    for bnd in bindings:stack.enter_context(bnd)
    v=ch.scan(c,'routing',[dict(database=database)])
   self.assertEqual(v['status'],'FAIL',v);self.assertEqual(v['rows_checked'],2);self.assertEqual(v['refused_rows'],1)
   self.assertTrue(v['complete']);self.assertEqual(v['database_rows'],2)
   self.assertEqual(v['counts'][check],dict(PASS=1,FAIL=1));self.assertEqual(v['first_ten_refusals'][0]['check'],check)
   for later in ch.CHECKS[ch.CHECKS.index(check)+1:]:
    if 'NOT_BOUND' not in v['counts'][later]:self.assertEqual(v['counts'][later]['NOT_REACHED'],1)
   self.assertEqual(v['database_key_set_sha256'],v['checked_key_set_sha256'])
 def test_zero_refusal_pass_and_nested_text_not_double_counted(self):
  root=F/'clean';root.mkdir();database=db(root/'rows.sqlite',[row('a'),row('b')])
  v=ch.scan(cfg(),'routing',[dict(database=database)]);self.assertEqual(v['status'],'PASS',v)
  self.assertEqual(v['counts']['text'],dict(PASS=2));self.assertEqual(v['counts']['r1'],dict(PASS=2))
 def test_all_rows_and_first_ten_full_exceptions(self):
  root=F/'many';root.mkdir();rows=[dict(row(str(i)),own_valued=True) for i in range(15)]
  v=ch.scan(cfg(),'routing',[dict(database=db(root/'rows.sqlite',rows))])
  self.assertEqual((v['database_rows'],v['rows_checked'],v['refused_rows']),(15,15,15));self.assertEqual(len(v['first_ten_refusals']),10)
  self.assertEqual(v['first_ten_refusals'][0]['exception'],'ValueError: OWN_VALUED_ROW_REFUSED')
 def test_other_stream_sample_seed_and_part_keys(self):
  root=F/'sample';root.mkdir();sources=[dict(database=db(root/(str(i)+'.sqlite'),[row(str(j)) for j in range(4)])) for i in range(2)]
  a=ch.scan(cfg(),'pose',sources,20000);b=ch.scan(cfg(),'pose',sources,20000)
  self.assertEqual(a['status'],'PASS',a);self.assertEqual(a['rows_checked'],20000);self.assertEqual(a['unique_rows_checked'],8)
  self.assertTrue(a['replacement']);self.assertEqual(a,b)
 def test_pinned_relocation_connects_native_reader(self):
  from student_pilot.r1_persisted import scope
  root=F/'relocate';root.mkdir();p=db(root/'a.sqlite',[row()]);logical=dict(p,path='/not-present/rows.sqlite')
  with scope({p['sha256']:p['path']}):v=ch.scan(cfg(),'routing',[dict(database=logical)])
  self.assertEqual(v['status'],'PASS',v)
 def test_candidate_carries_only_p_audit_and_matches_exact_pool(self):
  root=F/'candidate';root.mkdir();a=row('p1');a['s1_source']=dict(name='pool');b=copy.deepcopy(a);b['question']='copied field'
  d=row('p2');d['s1_source']=dict(name='pool');legacy=row('legacy')
  db(root/'base/rows.sqlite',[a,d,legacy]);db(root/'selection/rows.sqlite',[b,legacy])
  old=dict(schema='full-extent-receipt-v1',producer='fixture',rows={r['qid']:dict(content_sha256=digest(content(r)),box_statuses=['full'],repair_sha256=None,extra=dict(a=3)) for r in (a,d)})
  c=cfg();c['extent_receipt']=pin(root/'e.json',old)
  
  with patch.object(ch,'DB',file_pin(root/'base/rows.sqlite')['sha256']):v=ch.candidate(c,root,root)
  self.assertEqual(v['status'],'PASS',v);self.assertFalse(v['candidate_pinned'])
  got=json.loads(gzip.decompress((root/'cand.json.gz').read_bytes()));self.assertEqual(set(got['rows']),{'p1'})
  self.assertEqual(got['rows']['p1'],dict(old['rows']['p1'],content_sha256=digest(content(b))))
  self.assertEqual(v['fields']['content_sha256'],dict(equal=0,changed=1));self.assertEqual(v['fields']['box_statuses'],dict(equal=1,changed=0))
  self.assertEqual(load(c['extent_receipt']['path']),old)
  self.assertEqual(v['candidate_sha256'],__import__('hashlib').sha256(gzip.decompress((root/'cand.json.gz').read_bytes())).hexdigest())
 def test_candidate_refuses_source_digest_or_missing_entry(self):
  for label,entry in [('changed',dict(content_sha256='0'*64)),('missing',None)]:
   root=F/label;root.mkdir();r=row();r['s1_source']=dict(name='pool');db(root/'base/rows.sqlite',[r]);db(root/'selection/rows.sqlite',[r])
   c=cfg();c['extent_receipt']=pin(root/'e.json',dict(schema='full-extent-receipt-v1',rows={'ok':entry} if entry else {}))
   with patch.object(ch,'DB',file_pin(root/'base/rows.sqlite')['sha256']):v=ch.candidate(c,root,root)
   self.assertEqual(v['status'],'REFUSE');self.assertFalse((root/'cand.json.gz').exists())
 def test_final_exception_ignores_buffered_lines_and_chained_errors(self):
  p=F/'exception.log';p.write_text('Traceback (most recent call last):\n  File "a", line 1\nValueError: first\n\nDuring handling of the above exception, another exception occurred:\n\nTraceback (most recent call last):\n  File "b", line 2\nRuntimeError: actual failure\nINFO: buffered output\nCustomError: buffered output\n')
  self.assertEqual(pc.child_reason(p,'n',1),'E95:n:1:RuntimeError: actual failure')
  self.assertEqual(pc.child_reason(p,'p',2),'E95:p:2')
  p.write_text('INFO: output only\n');self.assertEqual(pc.child_reason(p,'n',1),'E95:n:1')
 def test_native_family_rejects_bare_types_and_distribution(self):
  from student_pilot.r1_population import family
  counts={k:int(v*100) for k,v in nd.QUOTAS.items()};actual={}
  for kind,n in counts.items():
   r=row();r['routing']['question_type']=kind
   self.assertEqual(nd.row_type(r),family(r,'routing'));actual[nd.row_type(r)]=n
  self.assertEqual(nd.type_table(counts)['status'],'PASS');self.assertEqual(nd.type_table(actual)['status'],'FAIL')
  self.assertIn('unassigned:absolute_distance',actual);self.assertIn('unassigned:units',actual)
 def test_metadata_pins_scope_and_minimal_mounts(self):
  from student_pilot.r1_persisted import scope
  root=F/'metadata';(root/'m').mkdir(parents=True);files={}
  for name in ['config.json','tokenizer.json','chat_template.jinja','model.safetensors.index.json','model-00001.safetensors']:
   p=root/'m'/name;p.write_text('{}');files[name]=file_pin(p)['sha256']
  v=dict(root='/project/community/example/runs/models/hash/snapshots/rev',files=files)
  mounts=pc.metadata_mounts(v,root)
  self.assertEqual({Path(p).name for p in mounts},{'config.json','tokenizer.json','chat_template.jinja'})
  self.assertTrue(all(p.startswith(v['root']+'/') for p in mounts))
  files['config.json']='1'*64
  with self.assertRaises(ValueError):pc.metadata_mounts(v,root)
 def test_timing_budget_includes_exact_final_metadata(self):
  root=F/'budget';root.mkdir();(root/'nd.json').write_bytes(b'x'*900)
  timing=dict(files={},returncode=0)
  with patch.object(x,'LIMIT',1000):x.publication_size(root,timing)
  z.write(root/'timings.json',timing)
  actual=sum(p.stat().st_size for p in root.iterdir());self.assertEqual(timing['aggregate_publication_bytes'],actual)
  self.assertEqual(timing['helper_publication_bytes'],actual);self.assertEqual(timing['aggregate_limit_status'],'FAIL');self.assertEqual(timing['helper_limit_status'],'FAIL')

 def test_chain_runs_after_regeneration_failure_without_changing_exception(self):
  import rg,px
  from types import SimpleNamespace
  root=F/'run_hook';root.mkdir();native=root/'dr/p/q';native.mkdir(parents=True)
  z.write(root/'pins.json',dict(paths={}))
  c=cfg();c['streams']={}
  database=db(native/'selection/rows.sqlite',[row()])
  oldload=z.load
  def loadp(p):return dict(namespace=str(root/'dr')) if str(p).endswith('k/p.json') else oldload(p)
  Z=SimpleNamespace(load=loadp,write=z.write,checked=z.checked)
  reached=[]
  def regen(config,directory,compare=True):
   reached.append('build');raise ValueError('native after DB')
  def chain(config,directory,output):
   self.assertEqual(config,c);self.assertEqual(Path(directory),native)
   reached.append('chain');v=ch.scan(config,'routing',[dict(database=database)])
   z.write(Path(output)/'chain.json',dict(status=v['status'],streams=dict(routing=v)));return v
  def program(*a,**k):return rg.regenerate(c,native)
  with patch.object(x,'attach',return_value=Z),patch.object(rg,'regenerate',side_effect=regen),patch.object(x.runpy,'run_path',side_effect=program),patch.object(ch,'run',side_effect=chain):
   with self.assertRaisesRegex(ValueError,'native after DB'):x.run_r(L/'out/kit_qd',root,'123')
  self.assertEqual(reached,['build','chain']);self.assertEqual(z.load(root/'ch_cfg.json'),c)
  self.assertEqual(z.load(root/'chain.json')['status'],'PASS')
 def test_diagnostic_failure_does_not_change_success_or_native_refusal(self):
  import rg
  from types import SimpleNamespace
  for failed in (False,True):
   root=F/('diag_failure_'+str(failed));native=root/'dr/p/q';native.mkdir(parents=True)
   db(native/'selection/rows.sqlite',[row()]);z.write(root/'pins.json',dict(paths={}))
   oldload=z.load
   def loadp(p):return dict(namespace=str(root/'dr')) if str(p).endswith('k/p.json') else oldload(p)
   Z=SimpleNamespace(load=loadp,write=z.write,checked=z.checked)
   def regen(*a,**k):
    if failed:raise ValueError('native refusal')
    return {'status':'PASS'}
   def program(*a,**k):return rg.regenerate(cfg(),native)
   with patch.object(x,'attach',return_value=Z),patch.object(rg,'regenerate',side_effect=regen),patch.object(x.runpy,'run_path',side_effect=program),patch.object(ch,'run',side_effect=RuntimeError('diagnostic failure')):
    if failed:
     with self.assertRaisesRegex(ValueError,'native refusal'):x.run_r(L/'out/kit_qd',root,'123')
    else:x.run_r(L/'out/kit_qd',root,'123')
   self.assertEqual(z.load(root/'chain.json')['status'],'UNAVAILABLE')
 def test_later_publication_failure_still_publishes_chain_and_timing(self):
  import ep
  from types import SimpleNamespace
  root=F/'later';root.mkdir();remote=root/'remote';target=remote/'o/123'
  z.write(root/'mode.json',dict(mode='r'));z.write(root/'chain.json',dict(status='FAIL',streams=dict(routing=dict(rows_checked=2,database_rows=2,refused_rows=1))))
  oldload=z.load
  def loadp(p):return dict(n_root=str(remote)) if str(p).endswith('k/p.json') else oldload(p)
  Z=SimpleNamespace(load=loadp,write=z.write,sha=z.sha)
  with patch.object(x,'attach',return_value=Z),patch.object(ep,'artifact_entries',side_effect=ValueError('later publication')):
   with self.assertRaisesRegex(ValueError,'R1_PUBLICATION_INCOMPLETE'):x.publish(L/'out/kit_qd',root,'123',7)
  self.assertEqual((target/'chain.json').read_bytes(),(root/'chain.json').read_bytes())
  timing=z.load(target/'timings.json');self.assertEqual(timing['chain']['status'],'FAIL');self.assertEqual(timing['returncode'],7)
  self.assertEqual(timing['chain']['routing']['rows_checked'],2)
 def test_full_run_uses_current_pin_and_never_candidate(self):
  root=F/'full';root.mkdir();native=root/'q';native.mkdir()
  a=row();a['s1_source']=dict(name='pool');a['routing'].update(question_type='object_abs_distance',ground_record=dict(program_audit=dict(independent_ordered_boxes=[{}])))
  b=copy.deepcopy(a);b['question']='changed copy'
  db(native/'base/rows.sqlite',[a]);db(native/'selection/rows.sqlite',[b])
  c=cfg();c['streams']={};c['extent_receipt']=pin(root/'e.json',dict(schema='full-extent-receipt-v1',rows={'ok':dict(content_sha256=digest(content(a)),box_statuses=['full'],repair_sha256=None)}))
  for stream in ('vqa','pointing','pose'):
   p=db(root/(stream+'.sqlite'),[row()]);c['streams'][stream]=pin(root/(stream+'.json'),dict(database=p))
  before=copy.deepcopy(c)
  with patch.object(ch,'DB',file_pin(native/'base/rows.sqlite')['sha256']):v=ch.run(c,native,root)
  self.assertEqual(c,before);self.assertEqual(v['status'],'FAIL');self.assertEqual(v['candidate']['status'],'PASS')
  self.assertEqual(v['streams']['routing']['counts']['extents'],dict(FAIL=1))
  self.assertTrue(all(v['streams'][s]['rows_checked']==20000 for s in ('vqa','pointing','pose')))
  self.assertEqual(v['population']['status'],'NOT_REACHED');self.assertEqual(v['population']['database_rows'],1)
  self.assertFalse(v['candidate_used']);self.assertFalse(v['candidate']['candidate_pinned'])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 z.write(D/'NEW_TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=[str(x) for x in result.failures],errors=[str(x) for x in result.errors],fixtures=str(F)))
 raise SystemExit(not result.wasSuccessful())
