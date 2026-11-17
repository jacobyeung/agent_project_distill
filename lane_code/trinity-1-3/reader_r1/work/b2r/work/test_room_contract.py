import copy,json,sys,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src';B=W.parent/'b1g/out'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P),str(O)]
import e2e_reader
from h1eval.items import load_manifest,digest,read_contract
from h1eval.room134 import validate,bind
class Room(unittest.TestCase):
 def setUp(self):self.m=load_manifest(P/'items/room134.json')
 def test_exact_membership(self):
  dev=[r for r in json.loads((B/'src/items/devs1_routed.json').read_text())['items'] if r['question_type']=='room_size_estimation']
  self.assertEqual([r for r in self.m['items'] if r['id'] in self.m['sets']['dev-S1']],dev)
  self.assertEqual(len(self.m['items']),134);self.assertEqual(len({r['id'] for r in self.m['items']}),134);self.assertEqual(len({r['room_key'] for r in self.m['items']}),107)
  self.assertEqual({r['question_type'] for r in self.m['items']},{'room_size_estimation'})
  self.assertEqual((O/'ITEM_KEYS.txt').read_text().splitlines(),[r['id'] for r in self.m['items']])
 def test_binding_all_frames(self):
  s={'frames_root':str(W/'work/frames')};mapped,receipt=bind(self.m['items'],s)
  self.assertEqual(len(mapped),134);self.assertEqual(len(receipt['items']),134)
  proof=json.loads((O/'FRAME_CHECK.json').read_text());self.assertTrue(proof['passed']);self.assertEqual(proof['frames'],3136)
  for r in self.m['items']:
   if r['id'] not in self.m['sets']['R0-dev']:continue
   c=s['frames_json']['captures'][r['native']]
   self.assertEqual([f['path'] for f in c['frames']],r['frame_paths']);self.assertEqual(c['anchor_indices'],r['source_frame_indices']);self.assertEqual(len(c['frames']),32)
   self.assertTrue(all(len(f['sha256'])==64 for f in c['frames']))
 def test_development_only_and_label_refusals(self):
  for field,value in [('development_only',False),('fitting_permitted',True)]:
   m=copy.deepcopy(self.m);m[field]=value
   with self.assertRaises(ValueError):validate(m)
  m=copy.deepcopy(self.m);m['items'][0]['question']='changed'
  with self.assertRaises(ValueError):validate(m)
 def test_read_contract(self):
  read_contract(self.m,['tower'],[{'name':'none'}],'room_size_estimation')
  for arm,mode,kind in [(['own'],[{'name':'none'}],'room_size_estimation'),(['tower'],[{'name':'donor'}],'room_size_estimation'),(['tower'],[{'name':'none'}],None)]:
   with self.assertRaises(ValueError):read_contract(self.m,arm,mode,kind)
 def test_selector_null_slot_and_room_cap(self):
  from h1eval.h10.parity_adapter import PER_READ_CALL_CAP
  self.assertEqual(PER_READ_CALL_CAP['room_size_estimation'],2)
  self.assertEqual((P/'b/e2e_reader/stage1.py').read_bytes(),(B/'src/b/e2e_reader/stage1.py').read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
