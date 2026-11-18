"""Fix 1 of review_rr2room: both labels are reported; mra_answer follows the job-1 scorers.accuracy path."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_room_pair as T
R=T.R
class Labels(unittest.TestCase):
 def test_both_labels(self):
  t=T.__dict__[[k for k,v in T.__dict__.items() if isinstance(v,type) and issubclass(v,unittest.TestCase)][0]]('test_synthetic_cli_and_sets')
  root,d,rows=t.make();r=R.score_return(root,True)
  for name in ('dev-S1','R0-dev','all'):
   s=r['sets'][name] if name in r['sets'] else None
   if s is None:continue
   self.assertIn('mra_answer',s);self.assertIsNotNone(s['mra_answer'])
  self.assertTrue(all('mra_answer' in x for x in r['per_item']));self.assertIn('mra_answer',r['labels'])
  print({k:(v['mra'],v['mra_answer']) for k,v in r['sets'].items()})
if __name__=='__main__':unittest.main()
