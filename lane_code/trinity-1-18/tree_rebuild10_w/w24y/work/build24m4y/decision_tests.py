from pathlib import Path
import sys,json,sqlite3,copy,hashlib,gzip,unittest,resource,time,base64
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4y';F=D/('decision_'+str(time.time_ns()));F.mkdir()
sys.path[:0]=[str(L/'out/rcj'),str(L/'work/tree_r1c')]
import nd,x,ch
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import file_pin,digest
C=nd.load(L/'out/rcj/f.json')
def row():
 return dict(qid='q',dataset='d1',scene='fixture_clean',category='routing_trace',
  student_input=dict(question='q',options=[],frames=[],frame_indices=[],timestamps=[],fps=30,total_num_frames=32),
  target='<think>\na\n</think>a',routing=dict(events=[],answer='a',category='route',question_type='camera_rotation'))
def db(path,rs):
 path.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(path) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  c.executemany('insert into rows values(?,?,?)',rs)
 return path
class Tests(unittest.TestCase):
 def publish(self,name,a,b,ta='{}',tb='{}',chain_edit=None):
  root=F/name;root.mkdir();scratch=root/'scratch';scratch.mkdir()
  p=db(root/'p.sqlite',[(0,json.dumps(a),ta)]);n=db(root/'n.sqlite',[(1,json.dumps(b),tb)])
  rt=dict(status='PASS',databases=[file_pin(n)],complete=True,rows_checked=1,database_rows=1,refused_rows=0,
   checked_key_set_sha256='a'*64,database_key_set_sha256='a'*64)
  chain=dict(status='PASS',config_sha256='b'*64,streams=dict(routing=rt))
  if chain_edit:chain_edit(chain)
  (scratch/'chain.json').write_bytes(nd.raw(chain))
  rules=(Removals([]),Exclusions(file_pin(L/'work/tree_r1c/student_pilot/r2_dev_merged.json')),dict(tree_sha256=nd.TREE))
  with patch.object(nd,'GATE',nd.reader().sha(p)),patch.object(nd,'native_rules',return_value=rules):
   result=nd.publish(p,n,root/'absent',root/'rd0',root/'out',scratch)
  out=nd.load(root/'out/nd.json');self.assertIn('wl.json.gz',result['files'])
  return out
 def test_metadata_and_ordinal_pass(self):
  a=row();a['s1_source']=dict(name='source',source=dict(path='old'),frame_binding=dict(fps_source='old',authority={k:dict(path='old') for k in ('map','plan','fps_authority')}))
  b=copy.deepcopy(a);b['question']='copied';b['s1_source']['source']['path']='new';b['s1_source']['frame_binding']['fps_source']='new'
  for pin in b['s1_source']['frame_binding']['authority'].values():pin['path']='new'
  v=self.publish('metadata',a,b)
  self.assertEqual(v['task_i'],'PASS');self.assertEqual(v['criteria']['d']['status'],'DEFERRED_TO_DISCOVERY')
  self.assertEqual({k:t['path_differences'] for k,t in v['metadata_classes'].items()},dict(ordinal=1,copied=1,paths=4,fps_source=1))
  self.assertEqual(v['criteria']['a']['differing_rows'],0)
 def test_every_encoder_field_and_raw_target_fail(self):
  for i,path in enumerate(C['content_field_paths']):
   a=row();b=copy.deepcopy(a);parts=path.split('/')[2:]
   if path=='/target':v=self.publish('field'+str(i),a,b,tb='{ }')
   else:
    node=b
    for key in parts[:-1]:node=node.setdefault(key,{})
    node[parts[-1]]={'changed':True}
    v=self.publish('field'+str(i),a,b)
   self.assertEqual(v['criteria']['a']['status'],'FAIL',path)
   self.assertIn(path,v['content_examples']);self.assertEqual(v['task_i'],'FAIL')
 def test_raw_lexical_and_typed_comparison(self):
  for a,b in [('1','1.0'),('"a"','"\\u0061"'),('null','{}')]:
   p='{"student_input":'+a+'}';n='{"student_input":'+b+'}'
   self.assertEqual(nd.exact_fields((0,p,'{}'),(1,n,'{}'),C)[0][0],'/row/student_input')
  self.assertEqual(nd.exact_fields((0,'{}',1),(0,'{}',True),C)[0][0],'/target')
  self.assertEqual(nd.exact_fields((0,'{}','{}'),(1,'{}','{}'),C),[])
 def test_unknown_difference_fails_b(self):
  a=row();v=self.publish('unknown',a,dict(a,unknown='changed'))
  self.assertEqual(v['criteria']['a']['status'],'PASS');self.assertEqual(v['criteria']['b']['status'],'FAIL')
  self.assertEqual(v['unclassified_paths']['/row/unknown']['count'],1)
 def test_chain_refusal_incomplete_mismatched_pins_fail(self):
  for i,change in enumerate([lambda c:c['streams']['routing'].update(refused_rows=1),lambda c:c['streams']['routing'].update(complete=False),lambda c:c['streams']['routing'].update(databases=[]),lambda c:c['streams']['routing'].update(checked_key_set_sha256='c'*64),lambda c:c.update(status='FAIL')]):
   v=self.publish('chain'+str(i),row(),row(),chain_edit=change)
   self.assertEqual(v['criteria']['c']['status'],'FAIL');self.assertEqual(v['task_i'],'FAIL')
 def test_exit_requires_all_steps_but_rd0_is_informational(self):
  t=dict(returncode=0,task_a=dict(status='PASS',task_i='PASS',criteria={k:dict(status='PASS') for k in 'abc'}),routing_types='PASS',proc_returncode=0,chain=dict(status='PASS'),publication_errors=[],rdiff_returncode=1)
  self.assertEqual(x.mode_r_status(t,True),0);self.assertEqual(x.mode_r_status(t,False),1)
  for key,value in [('returncode',7),('routing_types','FAIL'),('proc_returncode',1),('chain',dict(status='FAIL')),('publication_errors',[{}])]:
   trial=copy.deepcopy(t);trial[key]=value;self.assertEqual(x.mode_r_status(trial,True),1,key)
  for k in 'abc':
   trial=copy.deepcopy(t);trial['task_a']['criteria'][k]['status']='FAIL';self.assertEqual(x.mode_r_status(trial,True),1)
 def test_real_stored_control_and_per_store_counts(self):
  # Exact previously supplied source row, stored without edits in a local staged-store fixture.
  rows=[json.loads(v['row']) for v in nd.load(D/'published/p_sample.json')['rows']]
  other=nd.load(D/'a0_pool_abs_distance_reworded_row.json')
  root=F/'stores';root.mkdir();q=root/'q';q.mkdir()
  n=db(q/'selection/rows.sqlite',[(i,json.dumps(r),'{}') for i,r in enumerate(rows)])
  p=db(q/'base/rows.sqlite',[(i,json.dumps(r),'{}') for i,r in enumerate(rows)])
  u=q/'u';u.mkdir();extra=db(u/'source.sqlite',[(0,json.dumps(other),'{}')])
  cfg=dict(extent_receipt=file_pin(D/'c072905b.json'),r1_training=dict(extent_pool_sources=nd.load(D/'SOURCES.json')['names'],row_slice_inputs={'a':file_pin(extra)}))
  with patch.object(ch,'DB',nd.reader().sha(p)):v=ch.scope_report(cfg,q)
  case=v['tests']['cases']['other'];self.assertEqual(case['origin'],'database');self.assertEqual(case['status'],'PASS')
  self.assertEqual(case['database'],file_pin(extra));self.assertEqual(v['tests']['other_rows'],1)
  self.assertEqual([s['rows'] for s in v['tests']['stores']],[100,100,1])
  (D/'STORE_CONTROL.json').write_bytes(nd.raw(v))
  # A fresh fixture with no third class must enumerate stores before using the sealed fallback.
  root=F/'fallback';root.mkdir();q=root/'q';q.mkdir()
  db(q/'selection/rows.sqlite',[(i,json.dumps(r),'{}') for i,r in enumerate(rows)])
  p=db(q/'base/rows.sqlite',[(i,json.dumps(r),'{}') for i,r in enumerate(rows)])
  cfg['r1_training']['row_slice_inputs']={}
  with patch.object(ch,'DB',nd.reader().sha(p)):v=ch.scope_report(cfg,q)
  self.assertEqual(v['tests']['other_rows'],0);self.assertEqual(v['tests']['cases']['other']['origin'],'sealed_reference')
  self.assertEqual(len(v['tests']['stores']),2)
  (D/'STORE_FALLBACK.json').write_bytes(nd.raw(v))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 (D/'DECISION_TESTS.json').write_bytes(nd.raw(dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=[str(v) for v in r.failures],errors=[str(v) for v in r.errors])))
 raise SystemExit(not r.wasSuccessful())
