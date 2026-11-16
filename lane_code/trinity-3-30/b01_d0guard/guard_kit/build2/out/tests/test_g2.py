from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work';K=B/'out/guard_kit'
sys.path[:0]=[str(K),str(W/'from113/work/tree')]
import closure,packet
from guard_core import read,write,sha,digest
from transport import regular_tar,Publisher,archive_result,verify_return,extract

class G2(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.family=read(B/'out/FAMILY.json');cls.trainer=packet.source_identity(cls.family)
  cls.files=closure.members(W/'d0closure/closure_359fcc3c.tar')
  cls.base=W/'from113/work/obj/m544_artifact.json'
 def setUp(self):
  self.d=B/'work/tests'/uuid.uuid4().hex;self.d.mkdir(parents=True)
 def auth(self,files=None,step=50,exported=None):return closure.authenticate(files or self.files,step,self.trainer,self.base,exported)
 def test_real_metadata(self):
  r=self.auth();self.assertEqual(r['config_identity'],closure.CONFIG_ID);self.assertEqual(r['source_tree'],closure.TREE_SHA)
 def test_export_byte_equality(self):
  p=self.d/'artifact.json';p.write_bytes(self.files['runs/359fcc3c/m50/artifact.json']);self.auth(exported=p)
  p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'byte-equal'):self.auth(exported=p)
 def test_foreign_step(self):
  with self.assertRaisesRegex(ValueError,'requested step'):self.auth(step=200)
 def test_tampered_step(self):
  files=deepcopy(self.files);a=json.loads(files['runs/359fcc3c/m50/artifact.json']);a['step']=51;files['runs/359fcc3c/m50/artifact.json']=json.dumps(a).encode()
  with self.assertRaisesRegex(ValueError,'foreign step'):self.auth(files)
 def test_wrong_config(self):
  files=deepcopy(self.files);d=json.loads(files['runs/359fcc3c/inputs/data_receipt.json']);name=d['config']['path'][len(closure.ROOT):]
  cfg=json.loads(files[name]);cfg['world_size']=8;files[name]=json.dumps(cfg).encode();d['config']['sha256']=hashlib.sha256(files[name]).hexdigest()
  files['runs/359fcc3c/inputs/data_receipt.json']=json.dumps(d).encode()
  with self.assertRaisesRegex(ValueError,'config identity'):self.auth(files)
 def test_wrong_chain(self):
  files=deepcopy(self.files);a=json.loads(files['runs/359fcc3c/m50/artifact.json']);a['trained_groups']['groups']['pose']['initial_sha256']='0'*64
  files['runs/359fcc3c/m50/artifact.json']=json.dumps(a).encode()
  with self.assertRaisesRegex(ValueError,'chain'):self.auth(files)
 def test_wrong_binding(self):
  files=deepcopy(self.files);v=json.loads(files['runs/359fcc3c/binding.json']);v['preparation']['sha256']='0'*64
  files['runs/359fcc3c/binding.json']=json.dumps(v).encode()
  with self.assertRaisesRegex(ValueError,'receipt binding'):self.auth(files)
 def test_wrong_trainer(self):
  files=deepcopy(self.files);v=json.loads(files['runs/359fcc3c/binding.json']);v['trainer_commit']='sha256:'+'0'*64
  files['runs/359fcc3c/binding.json']=json.dumps(v).encode()
  with self.assertRaisesRegex(ValueError,'trainer'):self.auth(files)
 def test_closure_roundtrip(self):
  meta=read(B/'out/candidate_m50/CLOSURE.json');actual=packet.packed_files(meta);self.assertEqual(actual,self.files)
  self.assertFalse(any(__import__('names').BAD.search(n) for n in meta['members']))
 def test_regular_archive(self):
  regular_tar(B/'out/candidate_m50/metadata.tar')
 def test_archive_hardlink_refused(self):
  p=self.d/'x.tar'
  with tarfile.open(p,'x') as t:
   m=tarfile.TarInfo('a');m.type=tarfile.LNKTYPE;m.linkname='b';t.addfile(m)
  with self.assertRaisesRegex(ValueError,'no links'):regular_tar(p)
 def test_archive_traversal_refused(self):
  p=self.d/'x.tar'
  with tarfile.open(p,'x') as t:
   m=tarfile.TarInfo('../a');m.size=1;t.addfile(m,io.BytesIO(b'x'))
  with self.assertRaises(ValueError):regular_tar(p)
 def test_streamed_frame_archive_needs_no_seek(self):
  from staging import extraction_guard,CORE
  sys.path.insert(0,str(CORE))
  import orchard_stage
  data=io.BytesIO()
  with tarfile.open(fileobj=data,mode='w') as t:
   m=tarfile.TarInfo('frame');m.size=3;t.addfile(m,io.BytesIO(b'abc'))
  class Pipe:
   def __init__(self,raw):self.source=io.BytesIO(raw)
   def read(self,size):return self.source.read(size)
  checked=extraction_guard(orchard_stage.extract_stream)
  inventory=checked(Pipe(data.getvalue()),self.d/'frames',None,10240)
  self.assertEqual(inventory['frame']['sha256'],hashlib.sha256(b'abc').hexdigest())
 def test_runtime_hardlink_refused_before_extraction(self):
  from staging import extraction_guard,CORE
  sys.path.insert(0,str(CORE))
  import orchard_stage
  data=io.BytesIO()
  with tarfile.open(fileobj=data,mode='w') as t:
   m=tarfile.TarInfo('a');m.size=1;t.addfile(m,io.BytesIO(b'x'))
   m=tarfile.TarInfo('b');m.type=tarfile.LNKTYPE;m.linkname='a';t.addfile(m)
  data.seek(0)
  with self.assertRaisesRegex(ValueError,'hard link'):
   extraction_guard(orchard_stage.extract_stream)(data,self.d/'runtime',None,10240,links=True)
  self.assertFalse((self.d/'runtime').exists())
 def test_subset_preserves_the_sealed_canary(self):
  from checkpoint import selection
  items=read(B/'out/inputs/items.json');chosen=set(items['canary_keys'])
  for key in items['keys']:
   if len(chosen)>=20:break
   chosen.add(key)
  subset=[key for key in items['keys'] if key in chosen]
  selected,canary=selection(items,subset)
  self.assertEqual(selected,subset);self.assertEqual(canary,items['canary_keys'])
  with self.assertRaisesRegex(ValueError,'sealed canary'):selection(items,[k for k in subset if k!=canary[0]])
  with self.assertRaisesRegex(ValueError,'preserve order'):selection(items,list(reversed(subset)))
 def test_publication_readback_and_no_overwrite(self):
  p=self.d/'CANARY.json';write(p,dict(status='PASS'));pub=Publisher(dict(kind='local',root=str(self.d/'store')),'a'*16,self.d/'checks')
  r=pub(p);self.assertTrue(r['verified']);self.assertEqual(sha(r['uri']),sha(p))
  with self.assertRaises(FileExistsError):pub(p)
 def fixture_packet(self,step=200):
  # Explicit authority fixtures test packet plumbing; no submission is performed.
  # The real m50 metadata is copied with only artifact step/counters changed for the packet test.
  files=deepcopy(self.files);old='runs/359fcc3c/m50/artifact.json';a=json.loads(files[old]);a['step']=step;a['trained_groups']['step']=step
  files['runs/359fcc3c/m'+str(step)+'/artifact.json']=json.dumps(a).encode()
  src=self.d/'closure.tar'
  with tarfile.open(src,'x') as t:
   for name,raw in sorted(files.items()):
    m=tarfile.TarInfo(name);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
  closure.pack(src,self.d/'meta',step,self.trainer,self.base)
  family=deepcopy(self.family);family.update(release_ready=True,blockers=[]);write(self.d/'FAMILY.json',family)
  done=self.d/'candidate.done';done.write_text(f'q8/8865619b/359fcc3c_m{step}.tar 10240 '+'f'*64+'\n')
  config=packet.prepare(self.d/'FAMILY.json',done,step,self.d/'meta/CLOSURE.json',self.d/'plan','b'*16)
  write(self.d/'REVIEW.json',dict(verdict='ACCEPT',reviewer='Test fixture; no production authority',family_sha256=sha(self.d/'FAMILY.json')))
  (self.d/'ORDER.md').write_text(packet.order_line(config)+'\n')
  return config
 def test_packet_emits_and_validates(self):
  c=self.fixture_packet();p=packet.packet(self.d/'plan/CONFIG.json',self.d/'REVIEW.json',self.d/'ORDER.md',self.d/'packet')
  extract(self.d/'packet/p.tar',self.d/'payload')
  __import__('transport').copy_verified(self.d/'packet/m.tar',self.d/'payload/metadata.tar')
  packet.validate_packet(self.d/'payload')
  self.assertIn('--gres=gpu:1',p['submit_argv']);self.assertTrue((self.d/'packet/BATCH.sh').is_file())
  self.assertNotIn('#SBATCH',(self.d/'packet/BATCH.sh').read_text())
  write(B/'out/PACKET_TEST.json',dict(status='PASS',fixture=True,production_authority=False,packet=str(self.d/'packet'),payload=p['payload']))
 def test_all_registered_milestones(self):
  parent=self.d;results=[]
  for step in (200,400,600,800,1000):
   self.d=parent/str(step);self.d.mkdir()
   c=self.fixture_packet(step)
   p=packet.packet(self.d/'plan/CONFIG.json',self.d/'REVIEW.json',self.d/'ORDER.md',self.d/'packet')
   results.append(dict(step=step,packet=str(self.d/'packet/PACKET.json'),batch_bytes=(self.d/'packet/BATCH.sh').stat().st_size))
  write(B/'out/ALL_STEPS_TEST.json',dict(status='PASS',fixture=True,production_authority=False,results=results))
 def test_missing_review_refused(self):
  self.fixture_packet();write(self.d/'REVIEW.json',dict(verdict='ACCEPT',reviewer='fixture',family_sha256='0'*64))
  with self.assertRaisesRegex(ValueError,'review'):packet.packet(self.d/'plan/CONFIG.json',self.d/'REVIEW.json',self.d/'ORDER.md',self.d/'packet')
 def test_missing_order_refused(self):
  self.fixture_packet();(self.d/'ORDER.md').write_text('fixture order for another plan\n')
  with self.assertRaisesRegex(ValueError,'ORCH GO'):packet.packet(self.d/'plan/CONFIG.json',self.d/'REVIEW.json',self.d/'ORDER.md',self.d/'packet')
 def test_missing_closure_refused(self):
  c=self.fixture_packet();c['closure']['sha256']='0'*64;c['plan_sha256']=digest({k:v for k,v in c.items() if k!='plan_sha256'});write(self.d/'plan/CONFIG.json',c)
  (self.d/'ORDER.md').write_text(packet.order_line(c)+'\n')
  with self.assertRaisesRegex(ValueError,'digest'):packet.packet(self.d/'plan/CONFIG.json',self.d/'REVIEW.json',self.d/'ORDER.md',self.d/'packet')
 def test_family_blockers_refused(self):
  c=self.fixture_packet();f=read(self.d/'FAMILY.json');f['blockers']=['fixture outstanding check'];write(self.d/'FAMILY.json',f)
  c['family']['sha256']=sha(self.d/'FAMILY.json');c['plan_sha256']=digest({k:v for k,v in c.items() if k!='plan_sha256'})
  with self.assertRaisesRegex(ValueError,'Release blocked'):packet.admit(c,f,{},'')
 def test_plan_mutation_refused(self):
  c=self.fixture_packet();c['done']['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'seal'):packet.admit(c,read(self.d/'FAMILY.json'),read(self.d/'REVIEW.json'),(self.d/'ORDER.md').read_text())

class MergeAdmission(unittest.TestCase):
 """Exercise production merge with JSON journals and small metadata/model boundaries."""
 def setUp(self):
  self.d=B/'work/tests'/uuid.uuid4().hex;self.d.mkdir(parents=True)
  self.keys=['devrows:a','devrows:b']
  self.tasks=[dict(id=k.split(':')[1],question_type='camera',room='r',stratum='primary') for k in self.keys]
  self.request=dict(keys=self.keys,inputs={},artifact=dict(sha256='a'*64),binding={'fixture':True},
                    perceptions={t['id']:{'fixture':t['id']} for t in self.tasks},geometry_refusals=[],
                    grounding=dict(geometry_manifest=str(self.d/'geometry.json')),adapter_sources={})
  self.rows=[dict(key=k,arm='unflagged',question_type='camera',room='r',stratum='primary',
                  checkpoint_sha256='a'*64,binding=self.request['binding'],
                  perception_identity=digest(self.request['perceptions'][t['id']]),mask_source='fixture',
                  called=True,no_answer=False,call_errors=0,version_errors=0,scores={'released_answer':1.0},
                  coordinates={'nested':[(1,2),(3,4)]}) for k,t in zip(self.keys,self.tasks)]
  self.journal=self.d/'paired/results/items.jsonl';self.journal.parent.mkdir(parents=True)
  self.record(self.rows)
  write(self.d/'paired/request.json',self.request)
  write(self.d/'paired/results/GPU_PARITY.json',{'pass':True})
  write(self.d/'geometry.json',{'records':[]})
  N=SimpleNamespace(load=read,validate_request=lambda request,live:request,
      rows=lambda p:[json.loads(line) for line in p.read_text().splitlines()],
      tasks_and_captures=lambda inputs:(self.tasks,[]),family=lambda q:q,FAMILIES=['camera'],
      mask_source=lambda q:'fixture',checked=lambda p:p,Q=SimpleNamespace(REPORT_SEMANTICS={}),
      pin=lambda p:dict(path=str(p),sha256=sha(p)))
  self.session=SimpleNamespace(N=N,destination=self.d)
  self.output=self.d/'merged'
 def record(self,rows):
  self.journal.write_text(''.join(json.dumps(row)+'\n' for row in rows))
 def merge(self,rows=None,keys=None,fixture=False):
  from admission import merge
  modules={'r1':SimpleNamespace(accounting=lambda decoded:{}),
           'gravity_guard':SimpleNamespace(report=lambda:{},identity=lambda:{}),
           'native_metrics':SimpleNamespace(validate_gravity_guard=lambda *args:None,program_refusals=lambda rows:{})}
  with patch.dict(sys.modules,modules):
   return merge(self.session,self.rows if rows is None else rows,self.keys if keys is None else keys,self.output,fixture)
 def assert_no_admission(self):
  self.assertFalse((self.output/'R1.json').exists())
  self.assertFalse((self.output/'IN_JOB_ADMISSION.json').exists())
 def test_tuple_list_equal_rows_admit_journal_values(self):
  self.assertNotEqual(self.rows,self.session.N.rows(self.journal))
  result=self.merge()
  self.assertEqual(result['arms']['unflagged'],self.session.N.rows(self.journal))
  self.assertIsInstance(result['arms']['unflagged'][0]['coordinates']['nested'][0],list)
  self.assertEqual(read(self.output/'IN_JOB_ADMISSION.json')['status'],'PASS')
  self.assertFalse((self.output/'MERGE_DIFF.json').exists())
 def test_changed_score_refuses_with_diff(self):
  rows=deepcopy(self.rows);rows[0]['scores']['released_answer']=0.5
  with self.assertRaisesRegex(ValueError,'authenticated native journal'):self.merge(rows)
  self.assertEqual(read(self.output/'MERGE_DIFF.json'),{'keys':[self.keys[0]],'fields':{self.keys[0]:['scores']}})
  self.assert_no_admission()
 def test_missing_journal_key_refuses(self):
  self.record(self.rows[:1])
  with self.assertRaisesRegex(ValueError,'cardinality'):self.merge()
  self.assert_no_admission()
 def test_foreign_journal_key_refuses(self):
  rows=deepcopy(self.rows);rows[1]['key']='devrows:foreign';self.record(rows)
  with self.assertRaisesRegex(ValueError,'authenticated native journal'):self.merge()
  self.assert_no_admission()
 def test_missing_memory_key_refuses(self):
  with self.assertRaisesRegex(ValueError,'membership'):self.merge(self.rows[:1])
  self.assert_no_admission()
 def test_duplicate_journal_key_refuses(self):
  self.record([self.rows[0],self.rows[0]])
  with self.assertRaisesRegex(ValueError,'cardinality'):self.merge()
  self.assert_no_admission()
 def test_absent_versus_null_field_is_reported(self):
  rows=deepcopy(self.rows);rows[0]['optional']=None
  with self.assertRaisesRegex(ValueError,'authenticated native journal'):self.merge(rows)
  self.assertEqual(read(self.output/'MERGE_DIFF.json')['fields'],{self.keys[0]:['optional']})
  self.assert_no_admission()
 def test_boolean_integer_difference_refuses(self):
  rows=deepcopy(self.rows);rows[0]['called']=1
  with self.assertRaisesRegex(ValueError,'authenticated native journal'):self.merge(rows)
  self.assertEqual(read(self.output/'MERGE_DIFF.json')['fields'],{self.keys[0]:['called']})
  self.assert_no_admission()
 def test_json_equality_still_checks_gpu_parity(self):
  write(self.d/'paired/results/GPU_PARITY.json',{'pass':False})
  with self.assertRaisesRegex(ValueError,'GPU parity failed'):self.merge()
  self.assert_no_admission()
 def test_json_equality_still_checks_full_denominator(self):
  self.record(self.rows[:1])
  with self.assertRaisesRegex(ValueError,'full denominator'):self.merge(self.rows[:1],self.keys[:1])
  self.assert_no_admission()

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);r=unittest.TextTestRunner(verbosity=2).run(suite)
 write(B/'out/G2_TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'))
 sys.exit(not r.wasSuccessful())
