import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import score_r1route as S
import bootstrap_reference as REF
R=Path(__file__).resolve().parent;W=R.parent

class Baseline(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.score=json.loads((R/'baseline_check/scores.json').read_text())
 def test_registered_tower_scores_and_counts(self):
  for kind,expected in [('camera_displacement',82.33),('camera_movement_direction',94.67),('camera_rotation',75.60),('object_abs_distance',28.27)]:
   row=self.score['types'][kind];self.assertEqual(row['current']['completed'],150);self.assertEqual(round(100*row['current']['score'],2),expected)
  self.assertEqual(self.score['distance_call_cap']['count'],0)
  self.assertEqual(self.score['camera_calls']['called'],450)
 def test_registered_room_scores_and_hash(self):
  p=R/'bases/b2/work/scores/scores.json';v=json.loads(p.read_text())['sets']['all']
  self.assertEqual(round(100*v['mra_answer'],2),6.57);self.assertEqual(v['completed'],134);self.assertEqual(v['capped_reads'],115)
  self.assertTrue(hashlib.sha256(p.read_bytes()).hexdigest().startswith('9d3809d3'))
 def test_all_self_comparisons_zero(self):
  for row in list(self.score['types'].values())+list(self.score['rooms'].values())+[dict(paired=self.score['units']['paired'])]:
   p=row['paired'];self.assertEqual(p['value'],0);self.assertEqual(p['ci95'],[0,0]);self.assertEqual(p['ci9929'],[0,0])
 def test_return_receipt_provenance(self):
  sys.path.insert(0,str(R/'A'));from fetch_return import validate_exit,validate_receipt
  for token in ['b9ef55293462700029cf5','f40065df28aa30002a1a8']:
   root=W/'in/base_returns'/token;e=json.loads((root/'EXIT.json').read_text());r=json.loads((root/'RETURN_RECEIPT.json').read_text())
   validate_exit(e,root/'result.tar.gz',e['plan_sha256'],token)
   validate_receipt(r,e,root/'EXIT.json',root/'result.tar.gz',e['plan_sha256'],token)
   pin=r['channels']['pool']['files']['JOB.log'];raw=(root/'JOB.log').read_bytes()
   # The publisher pins the initial log, then appends upload records and the receipt.
   self.assertEqual(hashlib.sha256(raw[:pin['bytes']]).hexdigest(),pin['sha256'])
   self.assertEqual(json.loads(raw.splitlines()[0]),e)
   self.assertEqual(json.loads(raw.splitlines()[-1]),r)
 def test_wrong_baseline_provenance_rejected(self):
  for label,token in [('A','b9ef55293462700029cf5'),('B','f40065df28aa30002a1a8')]:
   src=W/'in/base_returns'/token;root=Path(tempfile.mkdtemp(prefix='baseline_negative_',dir=R/'test_tmp'))
   e=json.loads((src/'EXIT.json').read_text());e['plan_sha256']='0'*64;(root/'EXIT.json').write_text(json.dumps(e))
   r=subprocess.run([sys.executable,'-B',str(R/label/'unpack_return.py'),'--baseline','--archive',str(src/'result.tar.gz'),'--exit',str(root/'EXIT.json'),'--out',str(root/'ret')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertNotEqual(r.returncode,0);self.assertIn(b'Return plan differs',r.stderr);self.assertFalse((root/'ret').exists())
 def compare_reference(self,a,b):
  expected=REF.paired(a,b);by={r['key']:r for r in b}
  actual=S.bootstrap([(r['room'],100*(r['score']-by[r['key']]['score'])) for r in a])
  self.assertAlmostEqual(actual['value'],expected['value'],places=12)
  for key in ('ci95','ci9929'):
   for x,y in zip(actual[key],expected[key]):self.assertAlmostEqual(x,y,places=12)
  self.assertAlmostEqual(actual['upper95'],expected['upper95'],places=12)
 def test_independent_reference_unequal_room_sizes(self):
  a=[dict(key=str(i),room=str(i//3),score=i/9) for i in range(10)];b=[dict(r,score=.5) for r in a];self.compare_reference(a,b)
 def test_independent_reference_baseline_perturbation(self):
  rows,items,_,_=S.load(S.BASE/'b1/work/ret',S.BASE/'b1',1,544,'candidates_argmax')
  _,scores=S.metrics(rows,items,list(rows))
  a=[dict(key=k,room=items[k]['room_key'],score=v) for k,v in sorted(scores.items())]
  b=[dict(r,score=max(0,r['score']-(i%7)/10)) for i,r in enumerate(a)]
  self.compare_reference(a,b)
 def test_reference_rejects_mismatched_rooms(self):
  a=[dict(key='x',room='a',score=1)];b=[dict(key='x',room='b',score=1)]
  with self.assertRaisesRegex(ValueError,'room'):REF.paired(a,b)
if __name__=='__main__':unittest.main(verbosity=2)
