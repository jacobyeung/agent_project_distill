import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import unittest,sqlite3,copy,gzip,subprocess,ast
from unittest.mock import patch
from contextlib import ExitStack
import ch,pc,importlib.util
spec=importlib.util.spec_from_file_location("rcj_x",L/"out/rcj/x.py");x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
from student_pilot import r1_coverage
from student_pilot.extent_receipt import content,Extents
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.r0_exclusion import reserve
from student_pilot.r2_contract import CONTRACT
F=D/('unit_'+str(time.time_ns()));F.mkdir()

def db(path,rows):
 with sqlite3.connect(path) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  c.executemany('insert into rows values(?,?,?)',[(i,json.dumps(row),'{}') for i,row in rows])
 return path

def base(q):return dict(qid=q,dataset='d1',scene='fixture_clean',question='A clear question',question_type='object_abs_distance',
 target='<think>Clear observation.</think><answer>1</answer>',student_input=dict(frames=[]),
 ground_record=dict(program_audit=dict(independent_ordered_boxes=[dict(axesLengths=[1,1,1])])),provenance={},s1_source=dict(name='a'))

class Tests(unittest.TestCase):
 def setUp(self):
  self.root=F/self._testMethodName;self.root.mkdir()
 def setup_rows(self):
  rows=[(10+3*i,base(q)) for i,q in enumerate(('pass','wording','text','extents','r1','reserve','r2'))]
  rows[1][1]['question']='Held fixture 0'
  rows[2][1]['target']='<think>not seen</think>'
  rows[4][1]['own_valued']=True
  rows[5][1]['extra']=sorted(reserve().names)[0]
  pin=z.write(self.root/'word.json',dict(held_out=['Held fixture '+str(i) for i in range(8)]))
  ext=dict(schema='full-extent-receipt-v1',builder='synthetic fixture only',rows={r['qid']:dict(content_sha256=digest(content(r)),box_statuses=['full'],repair_sha256=None) for _,r in rows})
  ext['rows']['extents']['content_sha256']='0'*64
  ep=z.write(self.root/'ext.json',ext)
  membership=z.write(self.root/'member.json',dict(contract=CONTRACT,rows={r['qid']:digest(dict(row=r,target={},stream='routing')) for _,r in rows if r['qid']!='r2'}))
  cfg=dict(r1_training=dict(wording_exclusion=pin),extent_receipt=ep,r2_membership=membership)
  return rows,pin,cfg
 def test_native_each_check_and_short_circuit(self):
  rows,pin,cfg=self.setup_rows();path=db(self.root/'rows.sqlite',rows)
  with patch.object(r1_coverage,'SPLIT',pin['sha256']):result=ch.audit(cfg,path,self.root/'chain.json')
  self.assertEqual(result['rows'],{'PASS':1,'FAIL':6});self.assertEqual(result['count'],7)
  self.assertEqual([v['check'] for v in result['first_ten_refusals']],list(ch.CHECKS))
  for i,name in enumerate(ch.CHECKS):
   self.assertEqual(result['checks'][name].get('FAIL'),1)
   self.assertEqual(result['checks'][name].get('PASS'),6-i)
   self.assertEqual(result['checks'][name].get('NOT_REACHED',0),i)
  self.assertIn('EXTENT_ROW_UNAUDITED',result['first_ten_refusals'][2]['exception'])
  self.assertEqual(result['first_ten_refusals'][2]['key'],['routing',19,'extents'])
 def test_passing_chain_all_bound_checks(self):
  rows,pin,cfg=self.setup_rows();path=db(self.root/'rows.sqlite',rows[:1])
  with patch.object(r1_coverage,'SPLIT',pin['sha256']):result=ch.audit(cfg,path,self.root/'chain.json')
  self.assertEqual(result['status'],'PASS');self.assertEqual(result['first_ten_refusals'],[])
  self.assertTrue(all(v=={'PASS':1} for v in result['checks'].values()))
 def test_first_ten_full_messages(self):
  rows=[(i,dict(base(str(i)),target='<think>not seen</think>')) for i in range(23)]
  path=db(self.root/'rows.sqlite',rows);result=ch.audit({},path,self.root/'chain.json')
  self.assertEqual(result['rows'],{'FAIL':23});self.assertEqual(len(result['first_ten_refusals']),10)
  self.assertEqual(result['checks']['wording'],{'UNBOUND':23})
  self.assertTrue(all(v['exception']=='ValueError:rows_lane_rule_only_text:routing:runtime_box_status' for v in result['first_ten_refusals']))
 def test_candidate_uses_native_content_exact_pool_and_no_certification(self):
  a=base('pool');b=base('legacy');b.pop('s1_source')
  entry=dict(content_sha256=digest(content(a)),box_statuses=['full'],repair_sha256=None)
  pin=z.write(self.root/'extent.json',dict(schema='full-extent-receipt-v1',producer='fixture',rows={'pool':entry}))
  a['source_qid']='copied'
  path=db(self.root/'rows.sqlite',[(4,a),(9,b)])
  result=ch.candidate(path,pin,self.root/'cc.json.gz');value=json.loads(gzip.decompress((self.root/'cc.json.gz').read_bytes()))
  self.assertEqual(result['count'],1);self.assertEqual(result['coverage'],{'required':1,'FAIL':1})
  self.assertEqual(value['rows'],[dict(key=['routing',4,'pool'],content_sha256=digest(content(a)))])
  self.assertEqual(result['row_set_sha256'],hashlib.sha256(b'[["routing",4,"pool"]]').hexdigest())
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertFalse(value['applied']);self.assertFalse(value['native_builder_available'])
  self.assertNotIn('schema',value);self.assertNotIn('box_statuses',value['rows'][0]);self.assertEqual(z.load(pin['path'])['rows']['pool'],entry)
 def test_final_traceback_exception_ignores_buffered_stdout(self):
  for i,code in enumerate(("print('INFO: buffered output'); raise RuntimeError('actual failure')", "try:\n raise ValueError('first')\nexcept ValueError:\n print('INFO: buffered output')\n raise RuntimeError('actual failure')")):
   p=self.root/(str(i)+'.log')
   with p.open('wb') as out:r=subprocess.run([sys.executable,'-I','-s','-B','-c',code],stdout=out,stderr=-2)
   self.assertEqual(pc.child_reason(p,'n',r.returncode),'E95:n:1:RuntimeError: actual failure')
  p=self.root/'bare.log';p.write_text('INFO: buffered output\n')
  self.assertEqual(pc.child_reason(p,'n',1),'E95:n:1')
 def test_publication_metadata_crosses_limit(self):
  p=self.root/'nd.json';p.write_bytes(b'x'*(x.LIMIT-250));timing=dict(files={'n':dict(size=1,source='x')})
  x.account(self.root,timing);z.write(self.root/'timings.json',timing)
  actual=sum(p.stat().st_size for p in self.root.iterdir())
  self.assertEqual(timing['aggregate_publication_bytes'],actual);self.assertEqual(timing['helper_publication_bytes'],actual)
  self.assertEqual(timing['aggregate_limit_status'],'FAIL');self.assertEqual(timing['helper_limit_status'],'FAIL')
 def test_metadata_hash_gate_and_weights_excluded(self):
  from student_pilot.r1_persisted import scope
  p=self.root/'cfg';p.write_text('{}')
  value=dict(root='/project/x/a/snapshots/a',files={'config.json':z.sha(p),'weights.safetensors':'0'*64,'model.safetensors.index.json':'0'*64,'generation_config.json':'0'*64})
  with scope({z.sha(p):str(p)}):mounts=pc.metadata_mounts(value)
  self.assertEqual(list(mounts),['/project/x/a/snapshots/a/config.json'])
  with scope({z.sha(p):str(p)}):
   p.write_text('{ }')
   with self.assertRaises(ValueError):pc.metadata_mounts(value)

r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
write(D/'UNIT_TESTS.json',dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=[str(x) for x in r.failures],errors=[str(x) for x in r.errors]))
raise SystemExit(not r.wasSuccessful())
