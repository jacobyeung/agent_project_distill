import ast
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import unittest
import uuid
B=Path(__file__).resolve().parents[2]
ROOT=B/'out/guard_kit';CORE=ROOT/'sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(ROOT),str(CORE/'orchard_native')]
import guard_core as C
import native_arm as A
import names
import kernels
ITEMS=C.read(B/'out/inputs/items.json');REF=C.read(B/'out/inputs/reference.json')

class G1(unittest.TestCase):
 def setUp(self):
  self.path=B/'work/unit'/uuid.uuid4().hex;self.path.mkdir(parents=True)
  self.raw=b'q8/8865619b/359fcc3c_m200.tar 10240 '+b'c'*64+b'\n'
 def test_done_all_steps(self):
  for step in C.STEPS:
   raw=self.raw.replace(b'm200',('m'+str(step)).encode())
   self.assertEqual(C.parse_done(raw,C.RUN,step)['bytes'],10240)
 def test_wrong_run(self):
  for run in ('469ddece','359fcc3d',''):
   with self.assertRaises(ValueError):C.parse_done(self.raw,run,200)
 def test_wrong_step(self):
  for step in (1,100,544,1001,True,'200'):
   with self.assertRaises(ValueError):C.parse_done(self.raw,C.RUN,step)
 def test_wrong_object(self):
  for raw in (self.raw.replace(b'm200',b'm400'),self.raw.replace(b'359fcc3c',b'469ddece'),b'gs://x/'+self.raw,self.raw.replace(b'.tar ',b'.tar.part00-of-04 ')):
   with self.assertRaises(ValueError):C.parse_done(raw,C.RUN,200)
 def test_done_format(self):
  for raw in (self.raw+b'extra',self.raw.replace(b'10240',b'0'),self.raw.replace(b'10240',b'-1'),self.raw.replace(b'10240',b'1.2'),self.raw.replace(b'c',b'z'),self.raw.replace(b' ',b'  ')):
   with self.assertRaises(ValueError):C.parse_done(raw,C.RUN,200)
 def test_wrong_archive_sha(self):
  p=self.path/'a.tar';p.write_bytes(b'bytes')
  with self.assertRaisesRegex(ValueError,'digest'):C.verify_archive(p,dict(bytes=5,sha256='a'*64))
 def test_wrong_archive_bytes(self):
  p=self.path/'a.tar';p.write_bytes(b'bytes')
  with self.assertRaisesRegex(ValueError,'bytes'):C.verify_archive(p,dict(bytes=6,sha256=C.sha(p)))
 def test_archive_match(self):
  p=self.path/'a.tar';p.write_bytes(b'bytes');d=dict(bytes=5,sha256=C.sha(p));self.assertEqual(C.verify_archive(p,d),d)
 def test_independent_change(self):
  old={'kernel':'c4a505fc','scale':'original'}
  with self.assertRaisesRegex(ValueError,'independent'):C.immutable(dict(old,scale='altered'),old)
 def test_proof_pass(self):
  r=C.proof(REF,lambda keys:deepcopy(REF),self.path/'PROOF.json')
  self.assertEqual(r['status'],'PASS');self.assertFalse(r['candidate_started'])
 def test_proof_token_mismatch_no_candidate(self):
  calls=[];bad=deepcopy(REF);bad[0]['decode']['tokens'][0]+=1
  with self.assertRaises(ValueError):C.pipeline(bad,lambda keys:deepcopy(REF),lambda keys:calls.append(keys),ITEMS['keys'],ITEMS['canary_keys'],self.path)
  self.assertEqual(calls,[]);self.assertEqual(C.read(self.path/'PROOF.json')['status'],'FAIL');self.assertFalse((self.path/'CANARY.json').exists())
 def test_proof_call_response_answer_mismatch(self):
  for field in ('call','response','text'):
   bad=deepcopy(REF)
   if field=='text':bad[0]['decode']['text']+=' altered'
   else:bad[0]['decode']['calls'][0][field]+=' altered'
   with self.assertRaises(ValueError):C.proof(bad,lambda keys:REF,self.path/(field+'.json'))
 def test_proof_exception_receipt(self):
  def fail(keys):raise RuntimeError('fixture load failed')
  with self.assertRaisesRegex(ValueError,'fixture load failed'):C.proof(REF,fail,self.path/'PROOF.json')
  self.assertEqual(C.read(self.path/'PROOF.json')['status'],'FAIL')
 def test_canary_before_full(self):
  keys=[r['key'] for r in REF];chosen=keys[:10];by={r['key']:r for r in REF};events=[]
  def publish(p):events.append(p.name)
  def reader(selected):
   if selected!=chosen:
    self.assertEqual(C.read(self.path/'CANARY.json')['status'],'PASS');self.assertIn('CANARY.json',events)
   return [by[k] for k in selected]
  result=C.pipeline(REF,lambda k:REF,reader,keys,chosen,self.path,publish)
  self.assertEqual(list(result['arms']),['unflagged']);self.assertEqual(result['expected_keys'],keys)
 def test_full_exception_keeps_canary(self):
  keys=[r['key'] for r in REF];chosen=keys[:10]
  def reader(selected):
   if selected!=chosen:raise RuntimeError('fixture later fault')
   return REF[:10]
  with self.assertRaisesRegex(RuntimeError,'later fault'):C.pipeline(REF,lambda k:REF,reader,keys,chosen,self.path)
  self.assertEqual(C.read(self.path/'CANARY.json')['status'],'PASS');self.assertFalse((self.path/'R1.json').exists())
 def test_item_order(self):
  request=C.read(B.parents[1]/'work/ret544/native/paired/request.json')
  self.assertEqual(ITEMS['keys'],request['keys'])
  with self.assertRaises(ValueError):C.rows_in_order(list(reversed(REF)),[r['key'] for r in REF])
 def test_one_arm_refuses_scripted(self):
  bad=deepcopy(REF);bad[0]['arm']='scripted'
  with self.assertRaises(ValueError):C.rows_in_order(bad,[r['key'] for r in REF])
 def test_kernel_selection(self):
  paths=dict(nomdg=CORE/'native/out2/nomdg.py',geometry=CORE/'native/out2/geometry.py')
  pins=C.read(B/'out/BASELINE_FAMILY.json')['worker_contract']['kernel_source_pins']
  parts=kernels.load_parts(paths,pins);before=parts['pair'];after=A.select_native(before)
  def serve(node):return next(n for n in ast.walk(node) if isinstance(n,ast.FunctionDef) and n.name=='serve_pair')
  pre,post=serve(before),serve(after)
  self.assertEqual([ast.dump(n) for n in pre.body[:len(post.body)-1]],[ast.dump(n) for n in post.body[:-1]])
  self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr=='scripted' for n in ast.walk(after)))
 def test_mutated_script_boundary_refused(self):
  parts=kernels.partition((CORE/'native/out2/nomdg.py').read_text().replace("'Scripted runtime replay differs'","'foreign'"),(CORE/'native/out2/geometry.py').read_text())
  with self.assertRaises(ValueError):A.select_native(parts['pair'])
 def test_kernel_files_unchanged(self):
  source=B.parents[1]/'work/c8r_code'
  for p in source.rglob('*'):
   if p.is_file():self.assertEqual(p.read_bytes(),(ROOT/p.relative_to(source)).read_bytes())
 def test_reference_coverage(self):
  from collections import Counter
  counts=Counter(r['question_type'] for r in REF)
  self.assertEqual(counts,{'camera_displacement':4,'camera_movement_direction':3,'camera_rotation':3,'object_abs_distance':10})
  units={r['question_unit']['unit'] for r in REF if r['question_type']=='object_abs_distance'}
  self.assertEqual(units,{'meters','centimeters','feet','inches'})
 def test_zero_nonanswers_keep_denominator(self):
  source=deepcopy(REF[:3]);source[0]['no_answer']=True;source[1]['decode']['finish']='program_refusal';source[2]['geometry_refusal']={'reason':'fixture'}
  result=C.zero_nonanswers(source);self.assertEqual(len(result),3)
  self.assertTrue(all(all(v in (None,0.) for v in r['scores'].values()) for r in result))
 def test_name_roundtrip(self):
  source={'path':'/project/qwen35/x','key':'vsi590k_1','bytes':10,'sha256':'d'*64};mapping={source['path']:'/project/okh7/abc/x',source['key']:'k123'}
  result=names.rename(source,mapping);self.assertTrue(names.prove(source,result,mapping));self.assertEqual(names.scan_json(result),[])
  result['bytes']=11
  with self.assertRaises(ValueError):names.prove(source,result,mapping)
 def test_name_scan(self):
  for word in ('distill','qwen','qwen35','vsi','vsi590k','scannet','arkit','devs1','dev-S1','native routed-read'):
   self.assertTrue(names.scan_json({'path':'/a/'+word+'/b'}))

if __name__=='__main__':unittest.main(verbosity=2)
