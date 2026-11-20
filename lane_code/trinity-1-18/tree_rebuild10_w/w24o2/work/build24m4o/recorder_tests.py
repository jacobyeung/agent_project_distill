from common import *
from contextlib import ExitStack, nullcontext
from types import SimpleNamespace
from unittest.mock import patch
import unittest, torch, numpy as np, math, ast
sys.path.insert(0,str(kit('qd')/'b'))
import f0,rv
from student_pilot import carrier_c1_run as C, carrier_c1_data as data, pose_samples as samples, batches
from student_pilot import r0_exclusion
from launch_r1 import production_proof as proof

STREAMS=('pose','vqa','routing','pointing')
F=D/'recorder';F.mkdir()

class Tokenizer:
 pad_token_id=0
 eos_token_id=3
 def encode(self,text,**kw):return list(map(ord,text))
 def decode(self,ids,**kw):return ''.join(chr(int(i)) for i in ids if int(i)!=1000)

class Processor:
 video_token_id=1000
 def __init__(self):
  self.tokenizer=Tokenizer()
  self.video_processor=SimpleNamespace(temporal_patch_size=2,merge_size=1)
  self.sizes=[]
 def __call__(self,*,text,videos,video_metadata,size,**kw):
  count=len(videos[0]);self.sizes.append(dict(size))
  return dict(input_ids=torch.tensor([self.tokenizer.encode(text[0])+[1000]*(count//2)]),
   video_grid_thw=torch.tensor([[count//2,1,1]]),video_metadata=video_metadata,
   pixel_values=torch.from_numpy(videos[0].copy()),size_tensor=torch.tensor(list(size.values())))

def freeze(value):
 if isinstance(value,torch.Tensor):return ('tensor',str(value.dtype),list(value.shape),value.detach().contiguous().numpy().tobytes().hex())
 if isinstance(value,np.ndarray):return ('array',str(value.dtype),list(value.shape),value.tobytes().hex())
 if isinstance(value,dict):return {k:freeze(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [freeze(v) for v in value]
 return value

class Recorder(unittest.TestCase):
 def exercise(self,label,*,layout=False,count=32,record=True,nonfinite=False,encode_error=False,publish_error=False):
  root=F/label;root.mkdir();live=root/'n/o/123/live';fixture_kit=root/'kit';(fixture_kit/'k').mkdir(parents=True)
  J.write(fixture_kit/'k/p.json',dict(n_root=str(root/'n')))
  proc=Processor();encoded=[];forwards=[];made=[]
  row=dict(target='A',student_input=dict(question='Q',frames=[{} for _ in range(count)],
    frame_indices=list(range(count)),timestamps=[i/30 for i in range(count)],fps=30,total_num_frames=count))
  arrays=np.arange(count*2*2*3,dtype=np.uint8).reshape(count,2,2,3)
  receipt=dict(training_mode='final',frame_count=count,frame_markers=True,
               streams={s:dict(count=4) for s in STREAMS})
  pixels=[16384,147456]
  if layout:
   pixels=[4096,65536]
   receipt['b7_inputs']=dict(frame_count=count,frame_layout='duplicate',frame_markers=True,min_pixels=pixels[0],max_pixels=pixels[1])
  cfg=dict(preparation={'path':'fixture','sha256':'a'*64},world_size=4)
  plans=[[(s,list(range(4))) for s in STREAMS]]
  class Rows:
   def __init__(self,r,p):self.processor=p;made.append(p)
   def get(self,s,index):
    if encode_error and s=='routing':raise ValueError('fixture encode error')
    batch,audit=data.encode_layout_row(self.processor,row,'duplicate',None)
    result=(batch,None,dict(audit,qid=s+str(index)))
    encoded.append(freeze(result));return result
   def close(self):pass
  class Model:
   def parameters(self):return []
   def to(self,device):assert device.type=='cpu';return self
   def eval(self):return self
   def __call__(self,batch,targets,stream):
    assert not torch.is_grad_enabled()
    forwards.append(stream)
    return dict(loss=torch.tensor(float('nan') if nonfinite else 1.25),components={'x':torch.tensor(0.25)})
  prompt=' '.join(f'<{i/30:.1f} seconds>' for i in range(count))
  native_location=rv.location
  def location(*a):
   if publish_error:raise OSError('fixture publication failure')
   return native_location(*a)
  with ExitStack() as stack:
   for obj,name,value in [(C,'validate',lambda c:None),(C,'prepared',lambda *a,**kw:(receipt,{'root':'fixture'})),
    (C,'recipe_for',lambda c:dict(world_size=4,mix={})),(data,'mixed_indices',lambda *a,**kw:iter(plans)),
    (C,'processor_for',lambda root:proc),(C.rehearsal,'fixture_manifest',lambda m:{}),
    (C.routing,'add_routing_tokens',lambda *a,**kw:None),(C,'load_model',lambda m,r,p:Model()),
    (C.full_ft,'base_parameters',lambda m:[]),(C,'Rows',Rows),(samples,'load_frames',lambda i:arrays.copy()),
    (batches,'training_text',lambda p,q,o,t:(prompt,t+'\x03')),
    (batches,'training_stop_token',lambda p:('\x03',3)),
    (r0_exclusion,'reserve',lambda:SimpleNamespace(check=lambda *a:None)),(rv,'location',location),
    (C,'train',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Training called')))]:
    stack.enter_context(patch.object(obj,name,value))
   before={name:getattr(C,name) for name in ('processor_for_receipt','fetch','check_plan_rows','first_batch_check')}
   before_frames=samples.encode_frames;before_layout=data.encode_layout_row
   error=None
   with f0.recording(fixture_kit,root,'123') if record else nullcontext():
    try:result=proof.forward(cfg,root,0,'cpu')
    except ValueError as exc:error=str(exc);result=None
   self.assertTrue(all(getattr(C,n) is fn for n,fn in before.items()))
   self.assertIs(samples.encode_frames,before_frames);self.assertIs(data.encode_layout_row,before_layout)
  self.assertEqual(made,[proc])
  native=J.load(root/'f.json')
  from student_pilot.p3_provenance import load as strict_load
  evidence=strict_load(root/'f1.json') if (root/'f1.json').exists() else None
  if record and not publish_error:
   self.assertEqual((live/'f1.json').read_bytes(),(root/'f1.json').read_bytes())
   self.assertLess((live/'f1.json').stat().st_size,1_000_000)
   self.assertEqual(evidence['rows'],16);self.assertFalse(evidence['reconstructed'])
   self.assertEqual(evidence['observation_errors'],[])
   for stream,v in evidence['streams'].items():
    self.assertTrue({'rows','frame_count','pixel_bounds','token_counts','loss','finite'}<=v.keys())
    self.assertEqual(len(v['rows']),4);self.assertEqual(v['frame_count'],[count]);self.assertEqual(v['pixel_bounds'],[None] if encode_error and stream=='routing' else [pixels])
    for r in v['rows']:
     p=r['processor'];self.assertTrue(r['same_processor']);self.assertEqual(p['_c1_frame_count'],count)
     self.assertTrue(p['_c1_frame_markers']);self.assertEqual(p['_b7_layout'],layout)
     if encode_error and stream=='routing':
      self.assertFalse(r['pixels_observed']);self.assertFalse(r['finite']);continue
     self.assertTrue(r['pixels_observed']);self.assertEqual([c['kind'] for c in r['calls']],['layout','frames'])
     self.assertTrue(all(c['same_processor'] for c in r['calls']))
     self.assertEqual(r['calls'][-1]['pixel_bounds'],pixels);self.assertEqual(r['calls'][-1]['encoded_frame_count'],count*2)
     self.assertEqual(r['tokens'],r['effective_tokens']);self.assertGreater(r['tokens'],0)
     self.assertEqual(r['finite'],not nonfinite)
     if nonfinite:
      self.assertEqual(r['loss'],'NaN')
      self.assertIn('/loss',r['nonfinite_values'])
  clean=[{k:v for k,v in r.items() if k!='seconds'} for r in native['records']]
  return dict(encoded=encoded,sizes=proc.sizes,forwards=forwards,records=clean,error=error,evidence=evidence)

 def test_default_and_explicit_bounds_byte_identity(self):
  for label,layout,count in [('default',False,32),('explicit',True,64)]:
   a=self.exercise(label+'_plain',layout=layout,count=count,record=False)
   b=self.exercise(label+'_recorded',layout=layout,count=count)
   for field in ('encoded','sizes','forwards','records','error'):self.assertEqual(a[field],b[field])
   self.assertIsNone(b['error'])

 def test_existing_failure_and_restoration(self):
  for label,opts in [('nonfinite',dict(nonfinite=True)),('encoding',dict(encode_error=True))]:
   a=self.exercise(label+'_plain',record=False,**opts);b=self.exercise(label+'_recorded',**opts)
   self.assertEqual(a['error'],b['error']);self.assertIsNotNone(b['error'])
   self.assertTrue(all(not v['finite'] for s,v in b['evidence']['streams'].items() if label=='nonfinite' or s=='routing'))

 def test_publication_failure_adds_no_refusal(self):
  v=self.exercise('publication',publish_error=True)
  self.assertIsNone(v['error']);self.assertEqual(len(v['forwards']),16)
  self.assertIn('OSError',v['evidence']['observation_errors'])

 def test_qd_entry_exits_before_training(self):
  source=(kit('qd')/'b/a.py').read_text();tree=ast.parse(source)
  branch=next(n for n in tree.body if isinstance(n,ast.If) and any(isinstance(k,ast.With) and 'scope(paths)' in ast.unparse(k.items[0].context_expr) for k in n.body))
  # The native q branch exits after the observed proof, before the trailing train call.
  self.assertTrue(any(isinstance(n,ast.Call) and ast.unparse(n.func)=='sys.exit' for n in ast.walk(branch)))
  self.assertNotIn('train(',ast.unparse(branch))
  self.assertIn('with recording(kit, root.parent',ast.unparse(branch))
  self.assertFalse(J.load(kit('qd')/'k/a.json')['GO'])
  self.assertFalse(any((kit('qd')/'b'/n).exists() for n in ('t.py','u.py','e.sh')))

r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Recorder))
J.write(D/'RECORDER_TESTS.json',dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=[str(x) for x in r.failures],errors=[str(x) for x in r.errors],
 scope='CPU synthetic rows and processor; real processor_for_receipt, encode_layout_row, encode_frames, first_batch_check, check_plan_rows and proof.forward. Model, prepared stores, text template and frame loading are fixtures. All encoded tensor bytes and audits compared with recorder disabled/enabled; no production assets or GPU.'))
raise SystemExit(not r.wasSuccessful())
