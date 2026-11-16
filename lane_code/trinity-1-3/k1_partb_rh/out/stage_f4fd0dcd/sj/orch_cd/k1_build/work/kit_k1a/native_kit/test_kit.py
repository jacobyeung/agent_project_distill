"""End-to-end CPU proof and refusal tests; preserves fixtures and records executable-line coverage."""
import os,sys,json,copy,unittest,uuid,trace,types
from pathlib import Path
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
HERE=Path(__file__).resolve().parent;LANE=HERE.parent;sys.path.insert(0,str(HERE))
COUNTS={}
LOCAL_PREFIX=str(HERE)+'/'
def local_trace(frame,event,arg):
 if event=='line':COUNTS.setdefault(frame.f_code.co_filename,set()).add(frame.f_lineno)
 return local_trace

def tracer(frame,event,arg):
 if event=='call':
  name=frame.f_code.co_filename
  if name.startswith(LOCAL_PREFIX) and '/' not in name[len(LOCAL_PREFIX):]:return local_trace
 return None
sys.settrace(tracer)
import numpy as np
import bindings as B,pipeline as P,rehearse,run
from boundaries import CPU
import torch
torch.set_num_threads(1)
ROOT=LANE/'work'/('tests_'+uuid.uuid4().hex[:8]);ROOT.mkdir()

class KitTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c,cls.ex=rehearse.fixture(ROOT/'input');cls.m=dict(schema='o3-training-cache-v1',synthetic=True,captures=[cls.c],exclusions=cls.ex)
  run.validate_manifest(cls.m,True)
  cls.out=ROOT/'run';cls.boundary=CPU();assert run.execute(cls.m,cls.out,cls.boundary,max_bytes=100_000_000)==0
  cls.dest=cls.out/B.digest(cls.c['canonical'])[:16];cls.results=B.load(cls.dest/'responses.json');cls.records={r['id']:r for r in cls.results}
 def test_three_real_pipeline_outcomes(self):
  self.assertEqual([r['decision']['label'] for r in self.results],['trust','fallback','left_out'])
  self.assertEqual(B.load(self.dest/'COMPLETE.json')['geometry']['depth_scale_count'],1)
  self.assertTrue(self.records['distance']['mask_match']['ok'])
 def test_runtime_printed_answer_is_target(self):
  events=B.load(self.dest/'training_events.json');d=next(e for e in events if e['id']=='distance')
  self.assertEqual(d['answer'],'0.96');self.assertIn('distance 0.96 m',d['target'])
  from student_pilot.carrier_c1_routing import render_full
  target,spans,_=render_full(d['events'],d['answer']);self.assertEqual(target,d['target']);self.assertEqual(spans,d['tool_output_spans'])
  self.assertEqual(len(spans),3)
  self.assertTrue(all(target[s['start']:s['end']].startswith('<tool_response>') for s in spans))
 def test_failure_trace_has_no_followup_gap(self):
  r=self.records['failure'];self.assertEqual(len(r['calls']),2);self.assertTrue(P.failure(r['calls'][-1]))
  e=next(e for e in B.load(self.dest/'training_events.json') if e['id']=='failure');self.assertNotIn('<gap',e['target']);self.assertIn('<answer>2.00</answer>',e['target']);self.assertFalse(e['training_admitted'])
 def test_wrong_gt_never_changes_response(self):
  r=self.records['distance'];row=copy.deepcopy(self.c['rows'][0]);row['gt_value']=100
  record=dict(calls=r['calls']);self.assertEqual(P.classify(row,record,{'ok':True})['label'],'left_out')
  self.assertEqual(r['calls'][-1]['response'],'distance 0.96 m')
 def test_numeric_agreement_requires_identity(self):
  row=self.c['rows'][0];self.assertEqual(P.classify(row,self.records['distance'],{'ok':False})['label'],'left_out')
 def test_exact_tolerance_and_zero(self):
  row=dict(self.c['rows'][0],gt_value=100.)
  for value,label in [(115,'trust'),(115.01,'left_out'),(85,'trust'),(84.99,'left_out')]:
   rec={'calls':[dict(response=f'distance {value:.2f} m',kind='gap')]};self.assertEqual(P.classify(row,rec,{'ok':True})['label'],label)
  row['gt_value']=0.;self.assertEqual(P.classify(row,{'calls':[dict(response='distance 0.01 m')]},{'ok':True})['label'],'left_out')
 def test_unknown_success_is_not_fallback(self):
  self.assertEqual(P.classify(self.c['rows'][0],{'calls':[dict(response='unparsed') ]},{'ok':True})['label'],'left_out')
 def test_fallback_requires_evidence(self):
  row=dict(self.c['rows'][1]);row.pop('fallback');self.assertIsNone(P.train_events(row,self.records['failure']))
  row['fallback']=dict(trace='The gap is 2 meters.',answer='2',visual_evidence_verified=True)
  with self.assertRaises(ValueError):P.train_events(row,self.records['failure'])
 def test_sparse_geometry_refused(self):
  c=copy.deepcopy(self.c);c['dense_frames']=c['dense_frames'][::2]
  with self.assertRaises(ValueError):P.validate_capture(c,self.ex)
 def test_unknown_overlap_and_heldout_refused(self):
  for ex in [dict(self.ex,complete=False),dict(self.ex,scenes=[self.c['canonical']]),dict(self.ex,rooms=[self.c['room']])]:
   with self.assertRaises(ValueError):P.validate_capture(self.c,ex)
 def test_frame_and_operand_contracts(self):
  for change in ['anchors','prompt','unit','split','type','duplicate','authority']:
   c=copy.deepcopy(self.c)
   if change=='anchors':c['anchor_indices'][1]+=1
   if change=='prompt':c['rows'][0]['operands'][0]='unmentioned'
   if change=='unit':c['rows'][0]['unit']='feet'
   if change=='split':c['split']='unknown'
   if change=='type':c['rows'][0]['type']='object_counting'
   if change=='duplicate':c['rows'].append(c['rows'][0])
   if change=='authority':c['dense_source_authority']=''
   with self.assertRaises(ValueError,msg=change):P.validate_capture(c,self.ex)
 def test_resume_keeps_bytes(self):
  before=B.sha(self.dest/'responses.json');self.assertEqual(run.execute(self.m,self.out,self.boundary),0);self.assertEqual(before,B.sha(self.dest/'responses.json'))
 def test_stop_and_cap_before_work(self):
  stop=ROOT/'stop';stop.mkdir();(stop/'STOP').write_text('STOP\n')
  self.assertEqual(run.execute(self.m,stop,self.boundary),4)
  self.assertEqual(run.execute(self.m,ROOT/'cap',self.boundary,max_seconds=0),4)
 def test_incomplete_and_halted_are_preserved(self):
  out=ROOT/'partial';(out/B.digest(self.c['canonical'])[:16]).mkdir(parents=True)
  with self.assertRaisesRegex(ValueError,'Incomplete'):run.execute(self.m,out,self.boundary)
  self.assertTrue((out/'HALTED.json').exists())
  with self.assertRaisesRegex(ValueError,'HALTED'):run.execute(self.m,out,self.boundary)
 def test_synthetic_cannot_pass_production(self):
  with self.assertRaises(ValueError):run.validate_manifest(self.m,False)
 def test_manifest_duplicate_and_plan(self):
  m=copy.deepcopy(self.m);m['captures']*=2
  with self.assertRaises(ValueError):run.validate_manifest(m,True)
  p=run.plan(self.m);self.assertEqual(p['captures'],1);self.assertEqual(p['dense_frames'],64);self.assertEqual(p['operand_names'],3)
 def test_corrupt_pin_and_bound_read(self):
  p=ROOT/'small.json';p.write_text('{}');pin=B.pin(p);p.write_text('{"changed":true}')
  with self.assertRaises(ValueError):B.checked(pin)
 def test_gt_anchor_and_identity(self):
  masks=np.ones((32,2,2),bool);packed=dict(mask_shape=list(masks.shape),mask_bits=np.packbits(masks).tolist())
  rec=dict(heads=dict(ground_queries=[dict(name=n,instances=[dict(packed)]) for n in ['chair','table']]))
  row=dict(type=P.TYPES[0],operands=['chair','table'],gt_instances={'chair':1,'table':1})
  gt=dict(frame_indices=np.array(self.c['anchor_indices']),instances=np.ones_like(masks,dtype=int))
  self.assertTrue(P.mask_agreement(rec,row,gt,self.c['anchor_indices'])['ok'])
  row['gt_instances']['table']=2;self.assertFalse(P.mask_agreement(rec,row,gt,self.c['anchor_indices'])['ok'])
  gt['frame_indices'][1]+=1
  with self.assertRaises(ValueError):P.mask_agreement(rec,row,gt,self.c['anchor_indices'])
 def test_native_fixture_response_cues(self):
  r=self.records['distance'];self.assertIn('frames ',r['calls'][0]['response']);self.assertIn('size ',r['calls'][0]['response']);self.assertNotIn('spread ',r['calls'][0]['response'])

def main():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(KitTests);result=unittest.TextTestRunner(verbosity=2).run(suite)
 sys.settrace(None)
 cov={};native={}
 for p in HERE.glob('*.py'):
  if p.name=='test_kit.py':continue
  executable=set(trace._find_executable_linenos(str(p)));hit=COUNTS.get(str(p),set())&executable
  cov[p.name]=dict(executable_lines=len(executable),covered_lines=len(hit),coverage_pct=round(100*len(hit)/max(1,len(executable)),2),missing=sorted(executable-hit))
 for p,lines in COUNTS.items():
  if Path(p).parent!=HERE:native[p]=dict(executed_lines=len(lines),lines=sorted(lines))
 report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),success=result.wasSuccessful(),fixture_root=str(ROOT),coverage=cov,native_executed=native,coverage_method='Python executable-line sets from stdlib trace; line events restricted to changed kit modules; GPU paths remain in denominator')
 (LANE/'out/TEST_COVERAGE.json').write_text(json.dumps(report,indent=2)+'\n')
 if result.wasSuccessful():
  proof=dict(results=[dict(id=r['id'],decision=r['decision'],mask_match=r['mask_match'],calls=r['calls']) for r in KitTests.results],capture_receipt=B.load(KitTests.dest/'COMPLETE.json'),tests=report['tests'],scope='Real producer with stand-ins only for neural tower, own heads and SAM forward; no learned accuracy or GPU parity claim')
  (LANE/'out/CPU_REHEARSAL.json').write_text(json.dumps(proof,indent=2)+'\n')
 return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
