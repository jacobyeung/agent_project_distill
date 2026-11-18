import copy,json,tempfile,unittest
from pathlib import Path
import score_r1route as S
O=Path(__file__).resolve().parent
class Score(unittest.TestCase):
 def test_544_against_itself_all_zero(self):
  r=S.score(None,None,True)
  for value in list(r['types'].values())+list(r['rooms'].values())+[dict(paired=r['units']['paired'])]:
   self.assertEqual(value['paired']['value'],0);self.assertEqual(value['paired']['ci95'],[0,0]);self.assertEqual(value['paired']['ci9929'],[0,0])
  self.assertEqual(r['camera_calls']['called'],450);self.assertEqual(r['units']['current']['expected'],107);self.assertEqual(r['units']['current']['correct'],29)
  self.assertEqual({k:v['current']['expected'] for k,v in r['rooms'].items()},{'dev-S1':36,'R0-dev':98})
 def test_accepted_bootstrap_matches_reference(self):
  import importlib.util
  p=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/room_bootstrap.py')
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
  root=Path(tempfile.mkdtemp(prefix='score_',dir=O/'test_tmp'));src=S.BASE/'b1/work/ret';(root/'metadata').mkdir()
  (root/'metadata/IDENTITY.json').write_bytes((src/'metadata/IDENTITY.json').read_bytes())
  source=src/'metadata/reads/0/metadata/journals/0/0';d=root/'metadata/reads/0/metadata/journals/0/0';d.mkdir(parents=True)
  (d/'environment.json').write_bytes((source/'environment.json').read_bytes());(d/'STARTED.json').write_text('{}\n')
  (d/'items.jsonl').write_text((source/'items.jsonl').read_text().splitlines()[0]+'\n')
  return root,d
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
