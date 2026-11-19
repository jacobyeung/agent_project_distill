import sys,unittest,tempfile,time,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from adapter import *
import score_room_pricing as sc
from gates import authorize,preauthorize,SETTINGS,Budget,prerequisites
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.direct=read(W/'evidence/direct_m200_room134.json')['rows'];cls.echo=[dict(id=r['id'],arm='da3_f32+R0',area_m2=r['direct']/(sc.FT2 if r['unit']=='ft2' else 1),refusal=None) for r in cls.direct]
 def test_full_frame_identity(self):
  m=read(W/'configs/R0DEV_ROOM_MANIFEST.json')
  for item in m['items']:
   mp=W/'configs/frame_manifests'/f"{item['scene']}.json";self.assertEqual(sha(mp),item['frame_manifest_sha256'])
   for i in item['frame_indices']:
    p=R0/'frames/scannetpp'/item['scene']/f'{i:06d}.png';self.assertEqual(sha(p),item['frame_sha256'][str(i)])
 def test_k1_forward_frame_binding(self):
  ledger=W/'review/CPU_INPUT_SHA256.txt';m=read(K1)
  captures=[c for c in m['captures'] if c['canonical'] in ('scannetpp/067e2e4e61','scannetpp/036bce3393')]
  towers=[]
  for line in ledger.read_text().splitlines():
   h,p=line.split('  ',1)
   if p.endswith('/tower.npz'):
    self.assertEqual(sha(p),h)
    with np.load(p,allow_pickle=False) as z:towers.append((z['frame_indices'].tolist(),z['anchor_slots'].tolist()))
  self.assertEqual(len(towers),2)
  for c in captures:
   frames=[f['index'] for f in c['dense_frames']];slots=[frames.index(i) for i in c['anchor_indices']]
   self.assertIn((frames,slots),towers)
 def test_kernel_equality_and_legacy_adapter(self):
  m=read(K1)
  for cap,target in [('scannetpp/067e2e4e61',14.73),('scannetpp/036bce3393',39.35)]:
   c=next(c for c in m['captures'] if c['canonical']==cap);p=Path('/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3')/digest(c)[:16]/'pred.npz'
   g=convert(p,W/'out/tests_geom'/(cap.replace('/','__')+'.npz'))
   self.assertEqual(areas(g)['R0'],(target,None));self.assertEqual(price(g)['area_m2'],target)
 def test_frozen_kernel_matches_selected_training_rows(self):
  import kernel
  result=read(W/'out/S1K_RESULTS.json');winner=result['result_table'][result['winner_index']]
  self.assertEqual(kernel.frozen()['constants'],winner['constants'])
  manifest=read(K1);caps={c['canonical']:c for c in manifest['captures']}
  for cap in ('scannetpp/067e2e4e61','scannetpp/036bce3393'):
   row=next(r for r in winner['rows'] if r['capture']==cap)
   p=Path('/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3')/digest(caps[cap])[:16]/'pred.npz'
   actual=kernel.pipeline(p,W/'out/tests_geom'/('frozen_'+cap.replace('/','__')+'.npz'))
   self.assertEqual(actual['area_m2'],row['area_m2']);self.assertEqual(actual['refusal'],row['refusal'])

 def test_pending_kernel_authorization_blocks_launch(self):
  with self.assertRaisesRegex(ValueError,'clean held-out provenance'):
   prerequisites(W/'configs/KERNEL_PROVENANCE.json',W/'configs/READER_RECEIPT.json')

 def test_trim_exact_far_tenth(self):
  class Geo:
   def cam(self,k):return np.eye(3),np.zeros(3)
  near=np.column_stack([np.arange(1,91),np.zeros(90),np.zeros(90)]);far=np.column_stack([np.arange(1001,1011),np.zeros(10),np.zeros(10)])
  s=dict(points=[np.concatenate([near,far])]*2,frames=[1,2],geometry_mode='predicted',gravity_source='test')
  trimmed=trim(s,Geo());self.assertEqual([len(p) for p in trimmed['points']],[90,90]);np.testing.assert_array_equal(trimmed['points'][0],near)
 def test_refusal_preserved(self):
  class Geo:
   valid=np.array([True]);frame_of=lambda _,k:k
  self.assertEqual(price(Geo())['refusal'],'room_too_few_frames');self.assertEqual(price(Geo(),'T10')['refusal'],'room_too_few_frames')
 def test_ft2(self):self.assertEqual(sc.answer(10,'ft2'),107.64)
 def test_refusals_score_zero(self):
  rows=[dict(r,area_m2=None,refusal='room_no_floor_seen') for r in self.echo]
  table=sc.score(self.direct,rows,'da3_f32+R0',5)
  self.assertEqual(table['sets']['R0-dev']['arms']['da3_f32+R0']['refusals'],98);self.assertEqual(table['decision']['primary_mra'],0)
 def test_missing_primary(self):
  with self.assertRaises(ValueError):sc.score(self.direct,self.echo,'absent',5)
 def test_missing_item(self):
  rows=[p for p in self.echo if p['id']!=next(r['id'] for r in self.direct if r['set']=='R0-dev')]
  with self.assertRaises(ValueError):sc.score(self.direct,rows,'da3_f32+R0',5)
 def test_duplicate_baseline(self):
  with self.assertRaises(ValueError):sc.score(self.direct+[self.direct[0]],self.echo,'da3_f32+R0',5)
 def test_cached_score_corrupt(self):
  d=copy.deepcopy(self.direct);d[0]['direct_mra']=float('nan')
  with self.assertRaises(ValueError):sc.score(d,self.echo,'da3_f32+R0',5)
 def test_resume_all_three_states_and_binding(self):
  root=Path(tempfile.mkdtemp(dir=W/'tmp'));d=root/'capture';b=dict(model='da3',weights='x',code='y',frames=[0,1],slots=[0,1],settings={'seed':0})
  self.assertEqual(resume(d,b),'absent');d.mkdir();(d/'pred.npz').write_bytes(b'pred');write(d/'DONE.json',dict(binding=b,pred_sha256=sha(d/'pred.npz')),{'fixture':digest(b)})
  self.assertEqual(resume(d,b),'valid')
  for key in b:
   changed=dict(b);changed[key]='changed'
   with self.assertRaises(RuntimeError):resume(d,changed)
  (d/'pred.npz').write_bytes(b'corrupt')
  with self.assertRaises(RuntimeError):resume(d,b)
 def test_incomplete_receipt_stops(self):
  d=Path(tempfile.mkdtemp(dir=W/'tmp'));write(d/'STARTED.json',{'state':'RUNNING'},{'fixture':digest('test')})
  with self.assertRaises(RuntimeError):resume(d,{})
 def test_go_binds_actual_host_card_run(self):
  p=W/'tests/test_roomkit.py';sample=dict(unix_time=time.time()-301,gpu_uuid='GPU-f09fbca2-105b-4e94-a50d-41cc5cb73222',process_count=0,input_sha256={str(p):sha(p)})
  note=dict(decision='GO',host='test-host',run_id='test-run',gpu_uuid='GPU-f09fbca2-105b-4e94-a50d-41cc5cb73222',manifest_sha256='m',code_sha256='c',settings_sha256=digest(SETTINGS),max_gpu_seconds=5400,allocation_samples=[sample,dict(sample,unix_time=time.time()-1)])
  args=('test-run','m','c',dict(uuid='GPU-'+str('f09fbca2-105b-4e94-a50d-41cc5cb73222'),total_memory=48_000_000_000),1,'GPU-f09fbca2-105b-4e94-a50d-41cc5cb73222','test-host')
  authorize(note,*args)
  for key in ['host','run_id','gpu_uuid','manifest_sha256','code_sha256','settings_sha256','decision']:
   changed=dict(note);changed[key]='wrong'
   with self.assertRaises(PermissionError):authorize(changed,*args)
  args=list(args);args[4]=2
  with self.assertRaises(PermissionError):authorize(note,*args)
 def test_no_go_rejected_before_cuda(self):
  with self.assertRaises(PermissionError):preauthorize({'decision':'NOT_GO'},'test','m','c','GPU-f09fbca2-105b-4e94-a50d-41cc5cb73222','test-host')
  # The production runner's pure gate precedes its first torch import.
  source=(W/'scripts/gpu_run.py').read_text()
  self.assertLess(source.index('preauthorize(note'),source.index('import torch'))
  self.assertLess(source.index('budget.start()'),source.index('import torch'))
 def test_budget_exhausted_and_interrupted(self):
  d=Path(tempfile.mkdtemp(dir=W/'tmp'))/'cost.json'
  for state,used in [('COMPLETE',5400),('RUNNING',10)]:
   write(d,dict(state=state,charged_seconds=used),{'fixture':digest('test')})
   with self.assertRaises(RuntimeError):Budget(d,{})
 def test_budget_load_and_retry_cumulative(self):
  d=Path(tempfile.mkdtemp(dir=W/'tmp'))/'cost.json';write(d,dict(state='FAILED',charged_seconds=120),{'fixture':digest('test')})
  b=Budget(d,{'fixture':digest('test')});self.assertEqual(b.remaining,5280);b.start();b.finish('COMPLETE');self.assertGreaterEqual(read(d)['charged_seconds'],120)
 def test_budget_exclusive(self):
  d=Path(tempfile.mkdtemp(dir=W/'tmp'))/'cost.json';b=Budget(d,{'fixture':digest('test')})
  with self.assertRaises(RuntimeError):Budget(d,{})
  b.lock.close()
 def test_duplicate_prediction(self):
  with self.assertRaises(SystemExit):sc.score(self.direct,self.echo+[self.echo[0]],'da3_f32+R0',5)
 def test_nan_prediction_fatal(self):
  e=copy.deepcopy(self.echo);e[0]['area_m2']=float('nan')
  with self.assertRaises(ValueError):sc.score(self.direct,e,'da3_f32+R0',5)
 def test_missing_provenance_blocks(self):
  d=Path(tempfile.mkdtemp(dir=W/'tmp'));p=d/'missing.json'
  write(p,dict(status='MISSING'),{**{str(p):sha(p) for p in (W/'tests').glob('*.py')}})
  with self.assertRaises(ValueError):prerequisites(p,p)
 def test_unrounded_bar(self):
  table=sc.score(self.direct,self.echo,'da3_f32+R0',5);self.assertAlmostEqual(table['decision']['bar'],67.75510204081633,places=11)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.discover(str(W/'tests'),pattern='test_*.py');result=unittest.TextTestRunner(verbosity=2).run(suite)
 inputs={**input_code(),**{str(p):sha(p) for p in (W/'tests').glob('*.py')},str(W/'out/S0.json'):sha(W/'out/S0.json'),str(W/'evidence/direct_m200_room134.json'):BASE,str(W/'configs/R0DEV_ROOM_MANIFEST.json'):sha(W/'configs/R0DEV_ROOM_MANIFEST.json'),str(K1):sha(K1)}
 for path in [W/'out/S1K_RESULTS.json',W/'configs/KERNEL_FROZEN.json',W/'configs/KERNEL_PROVENANCE.json',W/'configs/READER_RECEIPT.json']:inputs[str(path)]=sha(path)
 # S0 binds every local frame and stored-prediction input; also bind exact fixtures used here.
 inputs.update(read(W/'out/S0.json')['input_sha256'])
 inputs[str(W/'review/CPU_INPUT_SHA256.txt')]=sha(W/'review/CPU_INPUT_SHA256.txt')
 for line in (W/'review/CPU_INPUT_SHA256.txt').read_text().splitlines():
  h,p=line.split('  ',1)
  if p.endswith('/tower.npz'):inputs[p]=h
 write(W/'out/TESTS.json',dict(verdict='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors)),inputs)
 status('CPU tests '+('PASS' if result.wasSuccessful() else 'FAIL')+f': {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors. Real S1c and R0-dev inference remain unrun; kernel approval and per-run GO are required.')
 raise SystemExit(not result.wasSuccessful())
