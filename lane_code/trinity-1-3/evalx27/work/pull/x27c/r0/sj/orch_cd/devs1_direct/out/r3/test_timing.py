"""Timing authority, anti-mixing and immutable membership regression tests."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import adapter as A
import report as R
from transformers.video_utils import VideoMetadata
class Timing(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  _,_,cls.rows,cls.captures=A.payload(ROOT)
  _,cls.media,_=A.kit_import(ROOT.parents[1]/'work/r3/final_cp1/kit')
 def capture(self):return copy.deepcopy(next(iter(self.captures.values())))
 def test_placeholder_refused(self):
  c=self.capture();c['fps']=1
  with self.assertRaisesRegex(ValueError,'timing authority'):A.validate_timing(c)
 def test_unknown_authority_refused(self):
  c=self.capture();c['native']='d1/no-authority'
  with self.assertRaisesRegex(ValueError,'no pinned frame-rate authority'):A.validate_timing(c)
 def test_missing_authority_fields_refused(self):
  c=self.capture();c.pop('fps_rule')
  with self.assertRaisesRegex(ValueError,'timing authority'):A.validate_timing(c)
 def test_changed_index_refused(self):
  c=self.capture();c['anchor_indices'][1]+=1
  with self.assertRaisesRegex(ValueError,'timing authority'):A.validate_timing(c)
 def test_wrong_total_refused(self):
  c=self.capture();c['total_num_frames']+=1
  with self.assertRaisesRegex(ValueError,'timing authority'):A.validate_timing(c)
 def test_wrong_timestamp_refused(self):
  c=self.capture();c['timestamps'][1]+=1
  with self.assertRaisesRegex(ValueError,'timing authority'):A.validate_timing(c)
 def test_all_capture_hf_timestamps(self):
  for c in self.captures.values():
   self.assertEqual(VideoMetadata(fps=c['fps'],frames_indices=c['anchor_indices'],total_num_frames=c['total_num_frames']).timestamps,c['timestamps'])
 def test_duplicate_repeats_training_timestamps(self):
  from trainer.layout_reference import layout_inputs
  for c in self.captures.values():
   si=dict(frames=c['frames'],fps=c['fps'],frame_indices=c['anchor_indices'],timestamps=c['timestamps'],total_num_frames=c['total_num_frames'])
   trained=layout_inputs(dict(student_input=si),layout='duplicate')
   task=dict(benchmark='devrows',example_id='x',native=c['native'],video_path='identity',source_frame_indices=c['anchor_indices'])
   rec=A.receipt_template(task,dict(layout='duplicate'),c,self.media)
   self.assertEqual(rec['audit']['timestamps'],trained['timestamps'])
   self.assertEqual(trained['timestamps'][::2],trained['timestamps'][1::2])
 def test_arkit_flagged_lower_bound(self):
  for c in self.captures.values():
   self.assertEqual(c['total_num_frames_lower_bound'],c['native'].startswith('d3/'))
   if c['total_num_frames_lower_bound']:self.assertEqual(c['total_num_frames'],max(c['anchor_indices'])+1)
 def test_item_strata_labels_byte_identical(self):
  for n in ('ITEMS.jsonl','STRATA.jsonl','CELL_ITEMS.json','EXCLUDED.jsonl'):
   self.assertEqual((ROOT/n).read_bytes(),(ROOT.parent/'r2'/n).read_bytes())
  for n in ('TASKS.jsonl','RELEASED_DEV.jsonl','MISSING_LABELS.jsonl','EXCLUDED_MISSING_ROOM.jsonl'):
   def strip(rows):return ''.join(json.dumps({k:v for k,v in r.items() if k not in ('fps','total_num_frames','total_num_frames_lower_bound')},sort_keys=True)+'\n' for r in rows).encode()
   self.assertEqual(strip(A.jsonl(ROOT/n)),strip(A.jsonl(ROOT.parent/'r2'/n)))
 def test_old_cell_version_refused(self):
  cell=json.loads((ROOT.parent/'r2/cells_cp1m200.json').read_text())[0]
  with self.assertRaisesRegex(ValueError,'Cell protocol'):A.validate_cell(cell,'cp1m200')
 def test_old_bound_run_refused(self):
  with self.assertRaisesRegex(ValueError,'Old timing version'):A.verify_bound(ROOT.parents[1]/'work/r2/dry_release_cp1')
 def test_journal_old_timing_refused(self):
  task=self.rows[0];c=self.captures[task['native']];cell=json.loads((ROOT/'cells_cp1m200.json').read_text())[0]
  t=dict(task,benchmark='devrows',example_id=task['id'],video_path='identity')
  rec=A.receipt_template(t,cell,c,self.media)
  row=dict(status='complete',layout='duplicate',media=rec['audit'],key=task['id'])
  R.check_frames(row,task,cell)
  row['media']['metadata']['fps']=1
  with self.assertRaisesRegex(ValueError,'Journal timing'):R.check_frames(row,task,cell)
 def test_20_hash_chosen_each_kit(self):
  for model in ('cp1m200','f17'):
   evidence=json.loads((ROOT/f'TIMING_EQUIVALENCE_{model}.json').read_text());proofs=evidence['proofs']
   self.assertEqual(len(proofs),20);self.assertEqual(len({p['native'] for p in proofs}),20)
   self.assertEqual({p['dataset'] for p in proofs},{'d1','d2','d3'})
   for p in proofs:
    for field in ('same_keys','same_fps','same_timestamp_formula','same_capture_training_layout_exact','official_vsi_metadata_exact'):self.assertTrue(p[field])
if __name__=='__main__':unittest.main(verbosity=2)
