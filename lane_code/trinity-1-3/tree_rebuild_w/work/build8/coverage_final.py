"""Native kit/cache producers and readers, with explicit tiny tower fixtures."""
import copy,hashlib,io,json,os,runpy,sys,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

L=Path(__file__).resolve().parents[2]
def folder(name):
 p=Path(os.environ['R2_PROOFS'])/name;p.mkdir(parents=True,exist_ok=True);return p

class NativeInputs(unittest.TestCase):
 def test_real_kit_builder_with_required_and_fixture_selected_inputs(self):
  from launch_r2.build import build,verify,scan
  from tests.test_r2_build import inputs
  from tests.r2_init_fixture import PIN
  from tests.test_r2_build7 import settings
  values=json.loads((L/'work/build8/kits/RESULTS.json').read_text())[0]['launch_inputs']
  for arm,connector,selected in [('a2','gf1',None),('a0','none',PIN)]:
   value=copy.deepcopy(values)
   if selected:value['init']=settings()['init']
   result=build(L/'fixtures/work/kit07ca49df_meta/m',folder('kits')/arm,
       connector=connector,records=inputs(),launch_inputs=value,init_pin=selected)
   self.assertEqual(result['kit_sha256'],verify(folder('kits')/arm))
   self.assertEqual(scan(folder('kits')/arm)['status'],'CLEAN')
   self.assertTrue(result['blockers']);self.assertEqual(result['claim_reader'],'harness_served')
   self.assertEqual(result['launch_inputs'],value)

 def test_real_staging_check_authenticates_before_packet_reader(self):
  from tests.test_r2_build5_host_order import fixture
  from tests.test_r2_build7 import settings
  from launch_r2.checklist import Checklist
  from student_pilot.p3_provenance import file_pin,load,write
  root,packet,cfg,entries,executable=fixture()
  plan=load(root/'plan.json')
  for runtime in ('venv','bwrap'):plan[runtime]=dict(file=str(executable),sha256=file_pin(executable)['sha256'])
  for entry in plan['entries'].values():
   if 'archive' in entry:entry['archive']['inventory']={entry['member']:entry['sha256']}
  (root/'plan.json').write_text(json.dumps(plan));(root/'k/0.json').write_text(json.dumps(dict(staging=file_pin(root/'plan.json'))))
  value=settings();source=folder('staging')/'source_input';source.write_bytes(b'fixture pin')
  for pin in [value['init']]+sum(value['row_stores'].values(),[]):
   pin.update(location=str(source),sha256=file_pin(source)['sha256'])
  cfg.update(b7_inputs=value,geometry_connector='none')
  result=Checklist(root,packet,cfg).step(2,Checklist(root,packet,cfg).stage_inputs)
  self.assertEqual(set(result),set(entries))
  self.assertTrue(all(file_pin(root/name)['sha256']==entry['sha256'] for name,entry in entries.items()))

 def test_model_trainable_policy_matches_optimizer_and_refuses_bad_pins(self):
  from student_pilot import b7_inputs as I
  from tests.test_carrier_c1 import fixture
  from tests.test_r2_build7 import settings
  model,_,_=fixture(training_mode='final');cfg={}
  actual=I.module_trainability(model,cfg);policy={}
  for kind,parameters in actual.items():
   if kind=='other':continue
   states={p['trainable'] for p in parameters}
   rates=sorted({p['learning_rate'] for p in parameters if p['trainable']})
   if kind!='private_vit':self.assertLessEqual(len(states),1)
   self.assertLessEqual(len(rates),2)
   policy[kind]=dict(trainable=bool(states and True in states),learning_rate=rates[0] if rates else 0.,
                     inherited_learning_rate=rates[-1] if rates else 0.)
  cfg['b7_inputs']={'trainable_modules':policy}
  self.assertEqual(I.assert_policy(model,cfg),actual)
  for change in ({'trainable':False},{'learning_rate':9.,'inherited_learning_rate':9.}):
   bad=copy.deepcopy(cfg);bad['b7_inputs']['trainable_modules']['pose_head'].update(change)
   with self.assertRaisesRegex(ValueError,'pin_mismatch'):I.assert_policy(model,bad)
  value=settings();bound={'r2_identity':{},'streams':{}}
  I.configure(bound,value,'a0')
  self.assertEqual(bound['b7_inputs'],value);self.assertEqual(bound['routing_policy'],'both-path-20261116')
  self.assertEqual(bound['streams']['vqa']['bindings'],value['row_stores']['vqa'])

 def test_metadata_and_row_refusals(self):
  from student_pilot import r2_mix as M,response_spec as S,row_text_audit as R,stop_control as C
  from student_pilot.r0_exclusion import aliases
  from student_pilot.p3_printed_calculator_v2 import PrintedPointRegistry
  from student_pilot.p3_provenance import file_pin
  from student_pilot.carrier_c1_routing import BOTH_TYPES
  mix=M.table(both_path={'minority_count':2});self.assertEqual(mix['both_types'],list(BOTH_TYPES));M.validate_table(mix)
  for v in ({},{'minority_count':0},{'minority_count':True}):
   with self.assertRaises(ValueError):M.table(both_path=v)
  root=folder('mix');p=root/'mix.json';p.write_text(json.dumps(mix))
  row=dict(question_type='object_counting',answer_form='direct',response_heads=[])
  item=dict(stream='vqa',row=row,mix_cell=dict(type='counting'))
  with self.assertRaisesRegex(ValueError,'missing_minority'):
   M.reindex([item],dict(mix_pin=file_pin(p),artifact_heads=[]),root/'out')
  self.assertEqual(hashlib.sha256(S.document()).hexdigest(),S.sha256())
  clean=dict(target='The printed displacement is 1.00 m.');self.assertIs(R.check(clean,'camera'),clean)
  self.assertIn('tower_scale_provenance_not_from_head',R.reasons(dict(ground_record=dict(geometry_mode='tower'))))
  for value in (0,-1,True,1.5):
   with self.assertRaises(ValueError):C.requested(False,dict(stop_after_step=value),1)
  names=aliases('arkitscenes','fixture');token='v'+hashlib.sha256(b'arkitscenes/fixture').hexdigest()[:12]
  self.assertIn('d3/'+token,names)
  registry=PrintedPointRegistry(64)
  point=registry.register(camera=[0,0,1],f1=[0,0,1],spread=0,requested_frame=64)
  self.assertEqual(point['actual_frame'],64)
  with self.assertRaises(ValueError):registry.register(camera=[0,0,1],f1=[0,0,1],spread=0,requested_frame=65)

class NativeCache(unittest.TestCase):
 def row(self):
  from tests.test_gf1_cache import write_clip_frames
  p=folder('cache');path=p/'row.json'
  if path.exists():return json.loads(path.read_text())
  row=write_clip_frames(p,'frames',17);path.write_text(json.dumps(row));return row

 def test_cli_native_writer_and_reader_with_tiny_tower(self):
  import torch
  from student_pilot import gf1_cache as C,g3t_online as G,gf1,pose_samples
  from tests.test_gf1_cache import Tiny,settings,small_square
  row=self.row();p=folder('cache');cfg=p/'config.json';rows=p/'rows.jsonl';cache=p/'bank'
  block=settings();cfg.write_text(json.dumps(dict(geometry_online=block)))
  rows.write_text('\n'.join(map(json.dumps,[dict(category=pose_samples.CATEGORY,pose_sample={}),row,row]))+'\n')
  torch.manual_seed(17);encoder=Tiny(block).eval();loaded=[]
  args=['cache','--run-config',str(cfg),'--rows',str(rows),'--root',str(cache),'--dtype','float32','--device','cpu']
  output=io.StringIO()
  with patch.object(G,'G3TEncoder',return_value=encoder),patch.object(encoder,'load_pinned',side_effect=lambda p:loaded.append(p)), \
       patch.object(G,'native_square_518',small_square),patch.object(sys,'argv',args),redirect_stdout(output):
   C.main()
  dense,anchors=gf1.dense_inputs(row,block['gf1']);key=C.clip_key(dense)
  entry=C.load_cached(dict(root=str(cache),dtype='float32'),key,anchors)
  self.assertTrue(torch.isfinite(entry.tensor).all());self.assertEqual(len(loaded),1)
  self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['clips'],1)
  self.assertIs(C.RowBanks([entry,None]).to('cpu').entries[0],entry)
  before=(cache/(key+'.safetensors')).read_bytes()
  with patch.object(G,'G3TEncoder',return_value=encoder),patch.object(encoder,'load_pinned',return_value=None), \
       patch.object(G,'native_square_518',small_square),patch.object(sys,'argv',args+['--limit','1']),redirect_stdout(io.StringIO()):
   runpy.run_module('student_pilot.gf1_cache',run_name='__main__')
  self.assertEqual((cache/(key+'.safetensors')).read_bytes(),before)
  (p/'PROOF.json').write_text(json.dumps(dict(real_functions=['gf1_cache.main','write_clip','load_cached','frame_grid'],
      stand_ins=['Tiny registered G3T tower with seeded fixture weights','small_square resize to tiny raster','load_pinned acknowledges unavailable production tower weights'],
      tensor_sha256=hashlib.sha256(before).hexdigest(),shape=list(entry.tensor.shape),finite=True),indent=2)+'\n')

 def test_cache_invalid_shapes_and_donor_metadata(self):
  import torch
  from student_pilot import gf1_cache as C,gf1
  from tests.test_gf1_cache import settings,Tiny
  row=self.row();block=settings();dense,anchors=gf1.dense_inputs(row,block['gf1'])
  with self.assertRaises(ValueError):C.clip_key(dict(frames=[{}],frame_indices=[0]))
  with self.assertRaises(ValueError):C.pooled_nhat(torch.zeros(1,2,3,4),torch.zeros(2,4),(2,4,4),1e-5)
  with self.assertRaises(ValueError):C.RowBank('invalid',None)
  with self.assertRaises(ValueError):C._check_anchors([1],64)
  for dtype,grid in [('float16',(32,4,4)),('float32',(31,4,4))]:
   with self.assertRaises(ValueError):C.write_clip(Tiny(block),row,folder('invalid_cache'),grid=grid,dtype=dtype)
  for donor,pattern in [({},'Invalid'),(dict(schema=C.DONOR_SCHEMA,clip_key='bad',geometry_dense={'frames':[]},anchor_slots=anchors,permutation_sha256='x'),'configured ordered')]:
   bad=copy.deepcopy(row);bad['student_input']['geometry_bank_donor']=donor
   with self.assertRaisesRegex(ValueError,pattern):C.row_bank(bad,block['gf1'],dense,anchors,False)
  units=[dict(clip_key=k,dataset=d,grid=[32,4,4]) for k,d in [('a','one'),('b','one'),('c','two')]]
  result=C.shuffled_bank_plan(units,17,True)
  self.assertTrue(all(p['clip_key']!=p['donor_clip_key'] for p in result['pairs']))
  for data,seed in [(units,True),(units+[dict(units[0],dataset='other')],17)]:
   with self.assertRaises(ValueError):C.shuffled_bank_plan(data,seed)
  with self.assertRaises(ValueError):C._dataset(dict(student_input={}))
