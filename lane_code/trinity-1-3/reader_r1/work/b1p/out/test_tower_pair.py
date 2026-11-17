import unittest,json,copy
from pathlib import Path
import tower_pair as T
O=Path(__file__).resolve().parent
S,B=T.configure(O/'src')
class Fixture(unittest.TestCase):
 def setUp(self):
  self.items={k:dict(id=k,room_key='r'+k,question_type=T.DISTANCE,question='What is the distance in meters?',ground_truth=10,answer_type='numeric') for k in ('a','b')}
  self.own={k:dict(id=k,room_key='r'+k,type=T.DISTANCE,arm='own',mode='none',complete=True,output=dict(text='<answer>10</answer>',finish='eos',scores={'answer':1},calls={'records':[]})) for k in self.items}
  self.tower=copy.deepcopy(self.own)
  for r in self.tower.values():r['arm']='tower'
 def test_zero_and_difference_and_missing(self):
  x=T.analyse(self.own,{r:self.tower for r in T.RULES},self.items,S,B)
  self.assertEqual(x['rules'][T.RULES[0]]['by_type'][T.DISTANCE]['own_minus_tower']['ci95'],[0,0])
  self.tower['a']['output']['scores']['answer']=0
  x=T.analyse(self.own,{r:self.tower for r in T.RULES},self.items,S,B)
  self.assertEqual(x['rules'][T.RULES[0]]['by_type'][T.DISTANCE]['own_minus_tower']['value'],50)
  x=T.analyse(self.own,{r:{'a':self.tower['a']} for r in T.RULES},self.items,S,B)
  self.assertEqual(x['rules'][T.RULES[0]]['by_type'][T.DISTANCE]['missing_tower'],['b'])
 def test_status_stage_cap_and_ground_subset(self):
  r=self.tower['a'];r['output'].update(finish='max_calls',calls={'records':[dict(family='ground',call='<ground obj="x" mode="box">',response='x: not seen',served=True,stage1=dict(sam3={'kept_per_frame':[1]*32},linked_candidates=1,chosen_index=-1)),dict(family='gap',call='<gap a="x" b="y">',served=False)]})
  x=T.analyse(self.own,{r:self.tower for r in T.RULES},self.items,S,B)['rules'][T.RULES[0]]['distance']
  self.assertEqual(x['capped_reads'],1);self.assertEqual(x['status_shares']['not seen'],.5)
  self.assertEqual(x['task_mra'],.5);self.assertEqual(x['no_failed_ground_items'],1)
  self.assertEqual(x['stage_table']['selector null with candidates'],1)
 def test_duplicate_and_mixed_rule_refused(self):
  p=O/'tests/pair_fixture';p.mkdir(exist_ok=True)
  (p/'environment.json').write_text(json.dumps({'binding':dict(stage1_select_rule=T.RULES[0],arms=['tower'],lineage='SFT',step=544)}))
  f=p/'items.jsonl';row=self.tower['a'];f.write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n')
  with self.assertRaisesRegex(ValueError,'Duplicate'):T.load([f],self.items,'tower',T.RULES[0])
  with self.assertRaisesRegex(ValueError,'identity'):T.load([f],self.items,'tower',T.RULES[1])
if __name__=='__main__':unittest.main(verbosity=2)
