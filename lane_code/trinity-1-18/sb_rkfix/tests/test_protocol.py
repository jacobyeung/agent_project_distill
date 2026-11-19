"""CPU-only integration tests: real runner/control flow with synthetic I/O and CUDA backend."""
import contextlib,copy,io,os,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import common,gates,adapter,selection,gpu_run,price
from common import W,read,write,sha,digest,resume

class ProtocolTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(dir=W/'tmp'));self.out=self.root/'out/room_pricing';self.out.mkdir(parents=True)
  self.code={str(Path(__file__).resolve()):sha(__file__)}
  self.train=[dict(row_id=str(i),capture=str(i),room=str(i),split='train') for i in range(110)]
  self.direct=read(W/'evidence/direct_m200_room134.json')['rows']
  self.dev=[r for r in self.direct if r['set']=='R0-dev'];self.items=[]
  for i,r in enumerate(self.dev):
   hashes={}
   for j in range(3):
    p=self.root/'frames/scannetpp'/str(i)/f'{j:06d}.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(bytes([j]));hashes[str(j)]=sha(p)
   self.items.append(dict(id=r['id'],scene=str(i),frame_indices=[0,1],union_indices=[0,1,2],frame_sha256=hashes))
  write(self.root/'configs/R0DEV_ROOM_MANIFEST.json',dict(items=self.items),self.code)
  for name in ['KIT_SEAL.json','assets/da3/model.safetensors']:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
  p=self.root/'evidence/direct_m200_room134.json';p.parent.mkdir();p.write_bytes((W/'evidence/direct_m200_room134.json').read_bytes())
  self.uuid='c4c94328-5526-47a7-a601-4824760a42ae';self.calls=[];self.oom=None
  class OOM(RuntimeError):pass
  self.OOM=OOM
  cuda=types.SimpleNamespace(device_count=lambda:1,get_device_properties=lambda _:types.SimpleNamespace(uuid=self.uuid,total_memory=51_527_024_640),reset_peak_memory_stats=lambda:None,synchronize=lambda:None,max_memory_allocated=lambda:123,max_memory_reserved=lambda:456,OutOfMemoryError=OOM)
  self.torch=types.ModuleType('torch');self.torch.cuda=cuda;self.torch.set_num_threads=lambda n:None
  owner=self
  class Backend:
   def __init__(self,*args):pass
   def predict(self,paths,resolution):
    owner.calls.append(paths)
    if owner.oom==len(owner.calls):raise OOM('fixture OOM')
    n=len(paths);return types.SimpleNamespace(depth=np.ones((n,51,51)),intrinsics=np.tile(np.eye(3),(n,1,1)),c2w=np.tile(np.eye(4),(n,1,1)),source_hw=np.array([504,504]))
  self.back=types.ModuleType('geo_bakeoff.backends');self.back.Backend=Backend
  self.contract=types.ModuleType('geo_bakeoff.contract');self.contract.sample_grid=lambda d:d
  self.pkg=types.ModuleType('geo_bakeoff');self.pkg.backends=self.back;self.pkg.contract=self.contract

 @contextlib.contextmanager
 def fixture(self):
  with contextlib.ExitStack() as stack:
   for module in [gates,selection,gpu_run,price]:stack.enter_context(patch.object(module,'W',self.root))
   stack.enter_context(patch.object(gpu_run,'KIT',self.root));stack.enter_context(patch.object(gpu_run,'R0',self.root))
   for module in [gates,gpu_run,price]:stack.enter_context(patch.object(module,'run_code_hashes',lambda:self.code))
   stack.enter_context(patch.object(gpu_run,'prerequisites',lambda *args:None))
   stack.enter_context(patch.object(selection,'training_set',lambda:(self.train,{},dict(self.code))))
   stack.enter_context(patch.dict(sys.modules,{'torch':self.torch,'geo_bakeoff':self.pkg,'geo_bakeoff.backends':self.back,'geo_bakeoff.contract':self.contract}))
   stack.enter_context(patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'GPU-'+self.uuid}))
   yield

 def selected(self,lower=0):
  write(self.out/'SELECTION.json',dict(status='COMPLETE',scope='K1 train only',rule=selection.RULE,pricing_rule='R0',arm=selection.choose(lower),dense64_minus_f32=[lower,lower,lower],rows=self.train,code_sha256=digest(self.code)),self.code)

 def args(self,run='run-1',host='host-1'):
  prov=self.root/'provenance.json';reader=self.root/'reader.json';write(prov,dict(status='fixture'),self.code);write(reader,dict(status='fixture'),self.code)
  sample=dict(unix_time=time.time()-301,gpu_uuid='GPU-'+self.uuid,process_count=0,input_sha256=self.code)
  note=dict(decision='GO',host=host,run_id=run,gpu_uuid='GPU-'+self.uuid,manifest_sha256=sha(self.root/'configs/R0DEV_ROOM_MANIFEST.json'),code_sha256=digest(self.code),settings_sha256=digest(gates.SETTINGS),max_gpu_seconds=5400,allocation_samples=[sample,dict(sample,unix_time=time.time()-1)],provenance_sha256=sha(prov),reader_receipt_sha256=sha(reader))
  go=self.root/(run+'.json');write(go,note,self.code)
  return types.SimpleNamespace(stage='r0dev',run_id=run,go_file=str(go),provenance=str(prov),reader_receipt=str(reader))

 def launch(self,run='run-1',host='host-1'):
  with patch.object(gpu_run.socket,'gethostname',lambda:host),patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'GPU-'+self.uuid}):gpu_run.run(self.args(run,host))

 def pricing(self):
  expected={r['id']:r for r in self.dev}
  def pipeline(p,d,rule):
   self.assertTrue((self.out/'DECISION_REGISTRATION.json').exists());self.assertEqual(rule,'R0')
   item=self.items[int(p.parent.name)];r=expected[item['id']]
   return dict(area_m2=r['direct']/(10.7639104167 if r['unit']=='ft2' else 1),refusal=None)
  with patch.object(adapter,'pipeline',pipeline),patch.object(adapter,'input_code',lambda:self.code),contextlib.redirect_stdout(io.StringIO()):price.run()

 def test_end_to_end_single_arm_resume_and_one_look(self):
  for lower,expected,nframes in [(0,'da3_f32',2),(0.01,'da3_u94',3)]:
   if lower:self.setUp()
   with self.fixture():
    self.selected(lower);self.launch();self.assertEqual(len(self.calls),98);self.assertTrue(all(len(x)==nframes for x in self.calls))
    self.assertEqual({p.name for p in (self.out/'pred').iterdir()},{expected})
    # Change all operational identities without touching prediction identity.
    self.uuid='bbccbbaa-5526-47a7-a601-4824760a42ae'
    with patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'GPU-'+self.uuid}):self.launch('run-2','host-2')
    self.assertEqual(len(self.calls),98)
    done=read(self.out/'pred'/expected/'0/DONE.json');self.assertEqual(done['run_id'],'run-1');self.assertEqual(done['host'],'host-1')
    self.pricing();table=read(self.out/'PRICING_TABLE.json')
    self.assertEqual(list(table['sets']['R0-dev']['arms']),[expected+'+R0']);self.assertEqual(table['sets']['dev-S1']['arms'],{})
    reg=read(self.out/'DECISION_REGISTRATION.json');self.assertEqual(reg['bar'],price.BAR);self.assertEqual(reg['arm'],expected)
    for invoke in [self.pricing,lambda:self.launch('run-3')]:
     with self.assertRaisesRegex(RuntimeError,'look'):invoke()

 def test_missing_selection_rejected_before_cuda(self):
  with self.fixture(),patch.object(self.torch.cuda,'device_count',side_effect=AssertionError('CUDA touched')):
   with self.assertRaisesRegex(FileNotFoundError,'SELECTION'):self.launch()

 def test_no_go_before_prerequisite_hashes_or_cuda(self):
  with self.fixture():
   a=self.args();note=read(a.go_file);note['decision']='NOT_GO';write(a.go_file,note,self.code)
   with patch.object(gpu_run,'prerequisites',side_effect=AssertionError('hashing touched')),patch.object(self.torch.cuda,'device_count',side_effect=AssertionError('CUDA touched')):
    with self.assertRaises(PermissionError):gpu_run.run(a)

 def test_selected_arm_oom_drops_without_fallback_or_price(self):
  with self.fixture():
   self.selected(.1);self.oom=2
   with self.assertRaises(self.OOM):self.launch()
   self.assertEqual(len(self.calls),2);self.assertEqual(read(self.out/'ARM_DROPPED.json')['arm'],'da3_u94')
   with self.assertRaisesRegex(RuntimeError,'dropped'):self.pricing()
   self.assertFalse((self.out/'DECISION_REGISTRATION.json').exists())
   with self.assertRaisesRegex(RuntimeError,'dropped'):self.launch('run-2')

 def test_interrupted_only_requires_manual_closure_and_resumes(self):
  with self.fixture():
   self.selected();self.launch()
   # Construct a fresh interrupted destination, retaining completed receipts elsewhere.
   source=self.out/'pred/da3_f32/0';dest=self.root/'interrupted';started=read(source/'STARTED.json')
   write(dest/'STARTED.json',started,self.code);binding=started['binding']
   with self.assertRaisesRegex(RuntimeError,'manual'):resume(dest,binding)
   closed=dict(state='MANUALLY_CLOSED',authorized_by='orchestrator fixture',accounted_run_ids=['run-1'],charged_seconds=20)
   self.assertEqual(resume(dest,binding,closed),'interrupted')
   with self.assertRaisesRegex(RuntimeError,'manual'):resume(dest,binding,dict(closed,accounted_run_ids=['other']))

 def test_latch_refuses_each_existing_output_and_consumed_registration(self):
  for name in ['ROOM_PRED.jsonl','PRICING_TABLE.json','DECISION_REGISTRATION.json']:
   self.setUp();(self.out/name).write_text('fixture')
   with self.fixture(),self.assertRaisesRegex(RuntimeError,'look'):price.run()

 def test_failed_pricing_keeps_consumed_registration(self):
  with self.fixture():
   self.selected();self.launch()
   with patch.object(adapter,'pipeline',side_effect=ValueError('fixture failure')):
    with self.assertRaisesRegex(ValueError,'fixture failure'):price.run()
   self.assertTrue((self.out/'DECISION_REGISTRATION.json').exists())
   with self.assertRaisesRegex(RuntimeError,'look'):self.pricing()

 def test_selection_strict_positive_bound_and_tampering(self):
  self.assertEqual(selection.choose(0),'da3_f32');self.assertEqual(selection.choose(-1),'da3_f32');self.assertEqual(selection.choose(.00001),'da3_u94')
  with self.fixture():
   self.selected();s=read(self.out/'SELECTION.json');s['arm']='da3_u94';write(self.out/'SELECTION.json',s,self.code)
   with self.assertRaisesRegex(ValueError,'registered rule'):selection.load_selection(self.out,self.code)

 def test_scorer_cli_blocks_pred_even_with_self_test(self):
  import score_room_pricing as sc
  with patch.object(sys,'argv',['score_room_pricing.py','--direct','does-not-exist','--pred','also-missing','--self-test']):
   with self.assertRaisesRegex(PermissionError,'price.py'):sc.main()

 def test_env_does_not_leak_shell_options(self):
  import subprocess
  for opts in ['', 'set -euo pipefail;']:
   cmd=opts+' before=$(set +o); before_flags=$-; source scripts/env.sh; after=$(set +o); test "$before" = "$after"; test "$before_flags" = "$-"'
   result=subprocess.run(['bash','-c',cmd],cwd=W,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)

 def test_s1c_select_prices_every_training_row_and_freezes_choice(self):
  for weaker,expected in [(False,'da3_f32'),(True,'da3_u94')]:
   if weaker:self.setUp()
   caps={};array_values={}
   for r in self.train:
    r.update(gt=10.0,R0=10.0)
    c=dict(canonical=r['capture'],k1_split='train',anchor_indices=list(range(32)),dense_frames=[dict(index=i) for i in range(64)])
    caps[r['capture']]=c
    paths=[self.out/'pred/k1_f32'/r['capture']/'pred.npz',self.root/'dense'/digest(c)[:16]/'pred.npz']
    for j,p in enumerate(paths):
     p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'synthetic prediction fixture')
     b=dict(frames=list(range(32)),item_slots=list(range(32)),code_sha256=self.code)
     write(p.parent/'DONE.json',dict(binding=b,pred_sha256=sha(p)),self.code)
     array_values[str(p)]=dict(frame_indices=np.arange(32 if j==0 else 64),item_slots=np.arange(32))
   source=self.root/'evidence/k1_rule_variants.py';source.write_bytes((W/'evidence/k1_rule_variants.py').read_bytes())
   calls=[]
   def pipeline(p,d,rule):
    calls.append((str(p),rule));return dict(area_m2=None if weaker and 'k1_f32' in p.parts else 10.0,refusal='fixture refusal' if weaker and 'k1_f32' in p.parts else None)
   with self.fixture(),patch.object(selection,'training_set',lambda:(self.train,caps,dict(self.code))),patch.object(selection,'K1_PRED',self.root/'dense'),patch.object(adapter,'input_code',lambda:self.code),patch.object(adapter,'arrays',lambda p:array_values[str(p)]),patch.object(adapter,'pipeline',pipeline):
    result=selection.select(self.out);self.assertEqual(result['arm'],expected);self.assertEqual(len(result['rows']),110)
    self.assertEqual(len(calls),220);self.assertEqual({r for _,r in calls},{'R0'})
    self.assertEqual(selection.load_selection(self.out,self.code)['arm'],expected)
    with self.assertRaisesRegex(RuntimeError,'frozen'):selection.select(self.out)

 def test_real_selection_manifest_is_train_only(self):
  rows,caps,ins=selection.training_set()
  self.assertEqual(len(rows),110)
  self.assertTrue(all(caps[r['capture']]['k1_split']=='train' for r in rows))
  self.assertTrue(ins)

 def test_runner_recomputes_started_only_after_manual_accounting(self):
  with self.fixture():
   self.selected()
   original=self.back.Backend.predict
   def fail_once(backend,paths,resolution):
    if len(self.calls)==1:raise RuntimeError('ordinary fixture interruption')
    return original(backend,paths,resolution)
   with patch.object(self.back.Backend,'predict',fail_once):
    with self.assertRaisesRegex(RuntimeError,'fixture interruption'):self.launch()
   with self.assertRaisesRegex(RuntimeError,'manual'):self.launch('run-2')
   cost=read(self.out/'COST.json');cost.update(state='MANUALLY_CLOSED',authorized_by='fixture orchestrator',accounted_run_ids=['run-1'])
   write(self.out/'COST.json',cost,self.code)
   self.launch('run-3','host-2');self.assertEqual(len(self.calls),98)
   self.assertEqual(read(self.out/'pred/da3_f32/0/DONE.json')['run_id'],'run-1')
   self.assertEqual(read(self.out/'pred/da3_f32/1/DONE.json')['run_id'],'run-3')

 def test_prerequisites_deduplicate_hashes(self):
  with self.fixture():
   prov=self.root/'prov.json';reader=self.root/'reader.json'
   write(prov,dict(status='VERIFIED',kernel_sha256='37c8d5fcfa24bbc29155a18f4400ad91dd5326a22b019edd66809f192afd1d07',benchmark_selected=False,selection_scope='K1 train only',relation_to_benchmark_rule='fixture',authorized_by='fixture'),self.code)
   write(reader,dict(status='VERIFIED',baseline_sha256=common.BASE,step=200,read=0,journal='4/0',items_sha256='607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7',journal_sha256='6150faf39361621c3352de4fa5caa2ccff86858aaffd8f18e133eee6a5c3212f',checkpoint_sha256='0'*64,frame_indices_by_item={i['id']:i['frame_indices'] for i in self.items}),self.code)
   for name in ['S0','DRYRUN','K1_REPRODUCTION','TESTS']:write(self.root/f'out/{name}.json',dict(verdict='PASS'),self.code)
   with patch.object(gates,'verify_inputs',wraps=gates.verify_inputs) as verify:gates.prerequisites(prov,reader)
   self.assertEqual(verify.call_count,1);self.assertEqual(verify.call_args.args[0],self.code)

 def test_registration_precedes_any_r0_prediction_read(self):
  with self.fixture():
   self.selected();self.launch()
   original=price.sha
   def guarded(path):
    if (self.out/'pred') in Path(path).parents:self.assertTrue((self.out/'DECISION_REGISTRATION.json').is_file())
    return original(path)
   with patch.object(price,'sha',guarded):self.pricing()

 def test_s0_binds_own_script(self):
  self.assertEqual(read(W/'out/S0.json')['input_sha256'][str(W/'scripts/s0.py')],sha(W/'scripts/s0.py'))

if __name__=='__main__':unittest.main(verbosity=2)
