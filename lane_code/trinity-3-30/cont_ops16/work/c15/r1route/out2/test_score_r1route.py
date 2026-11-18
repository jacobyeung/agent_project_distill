import copy,json,tempfile,unittest
from pathlib import Path
import score_r1route as S
HERE=Path(__file__).resolve().parent
O=HERE.parent if HERE.name in ('A','B') else HERE
(O/'test_tmp').mkdir(exist_ok=True)
class Score(unittest.TestCase):
 def test_544_against_itself_all_zero(self):
  r=S.score(None,None,True)
  for value in list(r['types'].values())+list(r['rooms'].values())+[dict(paired=r['units']['paired'])]:
   self.assertEqual(value['paired']['value'],0);self.assertEqual(value['paired']['ci95'],[0,0]);self.assertEqual(value['paired']['ci9929'],[0,0])
  self.assertEqual(r['camera_calls']['called'],450);self.assertEqual(r['units']['current']['expected'],107);self.assertEqual(r['units']['current']['correct'],29)
  self.assertEqual({k:v['current']['expected'] for k,v in r['rooms'].items()},{'dev-S1':36,'R0-dev':98})
 def test_accepted_bootstrap_matches_reference(self):
  import importlib.util
  p=O/'missing/room_bootstrap.py'
  spec=importlib.util.spec_from_file_location('accepted',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  a=[dict(key=str(i),room=str(i//3),stratum='x',question_type='x',scores={'answer':i/9}) for i in range(10)]
  b=[dict(r,scores={'answer':.5}) for r in a]
  accepted=m.paired(a,b,'answer');ours=S.bootstrap([(r['room'],100*(r['scores']['answer']-.5)) for r in a])
  self.assertAlmostEqual(accepted['delta_pp'],ours['value'],places=12)
  for x,y in zip(accepted['ci95_pp'],ours['ci95']):self.assertAlmostEqual(x,y,places=12)
 def test_physical_rooms_resampled_jointly(self):
  r=S.bootstrap([('a',1),('a',1),('b',0)])
  self.assertEqual(r['rooms'],2);self.assertEqual(r['n'],3);self.assertAlmostEqual(r['value'],2/3)
  self.assertEqual(r['ci95'],[0,1]);self.assertEqual(r,S.bootstrap([('a',1),('a',1),('b',0)]))
 def test_strict_negative_harm_and_missing(self):
  items={'a':dict(id='a',room_key='room',question_type=S.DISTANCE,question='Distance in feet?',ground_truth=1,answer_type='numeric')}
  r=dict(id='a',room_key='room',type=S.DISTANCE,arm='tower',complete=True,mode='none',output=dict(finish='eos',text='<answer>1</answer>',scores={'answer':1},calls={'records':[]}))
  bad=copy.deepcopy(r);bad['output']['scores']['answer']=0
  result=S.compare({'a':bad},{'a':r},items,['a'],'fixture')
  self.assertTrue(result['harm9929']);self.assertEqual(result['paired']['ci9929'],[-100,-100])
  result=S.compare({}, {'a':r},items,['a'],'fixture');self.assertFalse(result['complete']);self.assertIsNone(result['harm9929']);self.assertEqual(result['current']['missing'],['a'])
 def test_unit_count_uses_printed_gap_and_requested_units(self):
  items={'a':dict(id='a',room_key='r',question_type=S.DISTANCE,question='Distance in feet?')}
  row=dict(output=dict(finish='eos',text='<answer>3.2808399</answer>',calls={'records':[dict(call='<gap a="x" b="y">',response='distance 1 m',served=True)]}))
  self.assertEqual(S.unit_count({'a':row},items,['a'])['correct'],1)
  row['output']['text']='<answer>1</answer>';self.assertEqual(S.unit_count({'a':row},items,['a'])['correct'],0)
  row['output']['text']='<answer>3.2808399</answer>';row['output']['finish']='max_calls';self.assertEqual(S.unit_count({'a':row},items,['a'])['correct'],0)
 def fixture(self):
  # Rebuild only a small negative-admission fixture. This is not a saved job return.
  import hashlib
  root=Path(tempfile.mkdtemp(prefix='score_',dir=O/'test_tmp'));oldbase=S.BASE
  self.addCleanup(setattr,S,'BASE',oldbase)
  base=root/'synthetic_baseline';pkg=base/'b1';pkg.mkdir(parents=True)
  for name in ('src','package'):(pkg/name).symlink_to(oldbase/'b1'/name,target_is_directory=True)
  for name in ('READ_PLAN.json','tower_sequence.py'):(pkg/name).write_bytes((oldbase/'b1'/name).read_bytes())
  (base/'SYNTHETIC_FIXTURE.json').write_text('{"baseline_measurement":false}\n')
  S.BASE=base
  plan=S.read(pkg/'READ_PLAN.json');public=S.read(pkg/'package/0.json');manifest=S.read(pkg/'src/items/devs1_routed.json')
  identity=dict(plan=public['plan_sha256'],operator_sha256=S.digest(pkg/'tower_sequence.py'),reads=plan['read_settings'])
  src=pkg/'work/ret';(src/'metadata').mkdir(parents=True);(src/'metadata/IDENTITY.json').write_text(json.dumps(identity))
  expected=plan['read_settings'][0]
  settings={k:expected[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')}
  binding=dict(settings,arms=['tower'],modes=[{'name':'none'}],step=544,lineage='SFT',fixture=False,items_sha256=S.digest(pkg/'src/items/devs1_routed.json'),item_set_sha256=manifest['item_set_sha256'],settings_sha256=S.canonical(settings),export_sha256='fixture',artifact_manifest_sha256='fixture')
  from h1eval.cli import code_hash
  from h1eval.h10.parity_adapter import reader_code_hash
  from h1eval.h10 import parity_adapter
  binding.update(reader_sha256=code_hash(pkg/'src/b/e2e_reader'),parity_code_sha256=reader_code_hash(pkg/'src/b'),evaluator_code_sha256=code_hash(),maker_sha256=S.digest(Path(parity_adapter.__file__)))
  baseline_journal=src/'metadata/reads/0/metadata/journals/0/0';baseline_journal.mkdir(parents=True)
  (baseline_journal/'environment.json').write_text(json.dumps(dict(binding=binding,settings=settings)))
  ret=root/'candidate';(ret/'metadata').mkdir(parents=True);(ret/'metadata/IDENTITY.json').write_text(json.dumps(identity))
  d=ret/'metadata/reads/0/metadata/journals/0/0';d.mkdir(parents=True)
  (d/'environment.json').write_bytes((baseline_journal/'environment.json').read_bytes());(d/'STARTED.json').write_text('{}\n')
  item=manifest['items'][0];row=dict(id=item['id'],room_key=item['room_key'],type=item['question_type'],arm='tower',mode='none',complete=True,output=dict(text='<answer>1</answer>',finish='eos',scores={'answer':1},calls={'records':[]}))
  (d/'items.jsonl').write_text(json.dumps(row)+'\n')
  return ret,d
 def test_wrong_step_and_rule_refused(self):
  root,d=self.fixture();env=S.read(d/'environment.json');env['binding']['step']=200;(d/'environment.json').write_text(json.dumps(env))
  with self.assertRaisesRegex(ValueError,'step'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
  env['binding']['step']=544;env['binding']['stage1_select_rule']='candidates_argmax';(d/'environment.json').write_text(json.dumps(env))
  with self.assertRaisesRegex(ValueError,'stage1_select_rule'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
 def test_duplicate_and_partial_tail_refused(self):
  root,d=self.fixture();raw=(d/'items.jsonl').read_text();(d/'items.jsonl').write_text(raw+raw)
  with self.assertRaisesRegex(ValueError,'Duplicate'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
  (d/'items.jsonl').write_text(raw.rstrip())
  with self.assertRaisesRegex(ValueError,'tail'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
 def test_wrong_plan_and_fixture_refused(self):
  root,d=self.fixture();identity=S.read(root/'metadata/IDENTITY.json');identity['plan']='bad';(root/'metadata/IDENTITY.json').write_text(json.dumps(identity))
  with self.assertRaisesRegex(ValueError,'plan'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
  (root/'metadata/IDENTITY.json').write_bytes((S.BASE/'b1/work/ret/metadata/IDENTITY.json').read_bytes());env=S.read(d/'environment.json');env['binding']['fixture']=True;(d/'environment.json').write_text(json.dumps(env))
  with self.assertRaisesRegex(ValueError,'fixture'):S.load(root,S.BASE/'b1',0,544,'null_argmax')
if __name__=='__main__':
 (O/'test_tmp').mkdir(exist_ok=True);unittest.main(verbosity=2)
