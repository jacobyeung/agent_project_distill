"""Focused admission and cache read checks on native tiny artifacts."""
import copy,json,os,unittest
from pathlib import Path
from unittest.mock import patch

L=Path(__file__).resolve().parents[2]
def folder(name):
 p=Path(os.environ['R2_PROOFS'])/name;p.mkdir(parents=True,exist_ok=True);return p

class Admission(unittest.TestCase):
 def test_previous_init_contract_gap(self):
  from student_pilot.r2_contract import check_init
  from tests.r2_init_fixture import INIT
  with self.assertRaisesRegex(ValueError,'init identity differs'):
   check_init(dict(init=INIT,contract='foreign'),{})

 def test_reader_checks_exported_layout_before_loading(self):
  from tests.test_r2_build7 import settings
  from evalpath.runtime import check_init_spec
  from student_pilot.p3_provenance import file_pin
  value=settings();p=folder('layout')/'artifact.json'
  artifact={**value,'b7_inputs':value,'trained_groups':{},'trace_program_version':'3.13'}
  p.write_text(json.dumps(artifact));receipt={**value,'trace_program_version':'3.13'}
  self.assertEqual(check_init_spec(receipt,file_pin(p))['groups'],['pose'])
  for update in ({'frame_count':64},{'max_pixels':value['max_pixels']*2}):
   with self.assertRaisesRegex(ValueError,'layout_mismatch'):check_init_spec({**receipt,**update},file_pin(p))

class CacheRead(unittest.TestCase):
 def test_real_cached_read_hit_and_shape_refusals(self):
  import torch
  from student_pilot import gf1_cache as C,gf1
  from tests.test_gf1_cache import model_for,settings
  root=L/'work/build8/proofs/coverage_final/cache'
  row=json.loads((root/'row.json').read_text());block=settings(dict(root=str(root/'bank'),dtype='float32'))
  dense,anchors=gf1.dense_inputs(row,block['gf1']);key=C.clip_key(dense)
  entry=C.load_cached(block['gf1']['cached_bank'],key,anchors)
  model=model_for(block).eval();grid=entry.record['merger_grid']
  batch=dict(input_ids=torch.zeros((1,1),dtype=torch.long),pixel_values_videos=torch.zeros(1,1),
    video_grid_thw=torch.tensor([grid]),aux_gf1_lm_indices=torch.tensor([anchors]),
    aux_gf1_rowbanks=C.RowBanks([entry]))
  first=C.rowbank_features(model,batch);second=C.rowbank_features(model,batch)
  self.assertIs(first,second);self.assertTrue(model.gx_metrics['tower_cache_hit'])
  self.assertTrue(torch.equal(first[1][0][0],entry.tensor.reshape(entry.tensor.shape[0],-1,entry.tensor.shape[-1])))
  changes=[{'aux_gf1_rowbanks':None},{'aux_gf1_lm_indices':None},
           {'aux_gf1_rowbanks':C.RowBanks([None])}, {'aux_gf1_cache':None},
           {'aux_gf1_lm_indices':torch.ones((1,32),dtype=torch.long)}]
  for update in changes:
   bad={k:v for k,v in batch.items() if k!='aux_gf1_cache'};bad.update(update)
   with self.assertRaises(ValueError):C.rowbank_features(model,bad)
  for kind in ('row','entry'):
   bad=copy.deepcopy(batch);bad['aux_gf1_cache']=gf1.ClipCache()
   item=bad['aux_gf1_rowbanks'].entries[0]
   if kind=='row':item.record['anchor_slots']=list(range(32))
   else:item.mapping=torch.arange(32)
   with self.assertRaisesRegex(ValueError,'anchors differ'):C.rowbank_features(model,bad)
  for image,coord in ((torch.zeros(1,1,3,8,8),torch.zeros(1,1,4)),):
   bad={**batch,'aux_gf1_rowbanks':C.RowBanks([None]),'aux_g3t_images':image,'aux_g3t_coords':coord}
   with self.assertRaisesRegex(ValueError,'batch shape'):C.rowbank_features(model,bad)
  fusion=model.auxiliary_heads.gf1
  with self.assertRaises(ValueError):fusion.cached_bank(torch.full((3,1,2048),float('nan')),gf1.CACHED_MARK,grid)
  with self.assertRaisesRegex(ValueError,'affine LayerNorm'):
   fusion.cached_bank(torch.zeros(3,grid[0]*(grid[1]//2)*(grid[2]//2),2047),gf1.CACHED_MARK,grid)
  old=fusion.norms[0].eps;fusion.norms[0].eps=old*2
  with self.assertRaisesRegex(ValueError,'one LayerNorm'):C.model_identity(model,grid,'cpu')
  fusion.norms[0].eps=old
  (folder('cache_read')/'RESULT.json').write_text(json.dumps(dict(
      tensor_sha256=entry.record['tensor']['sha256'],shape=list(entry.tensor.shape),cache_hit=True,
      real_functions=['load_cached','model_identity','rowbank_features'],
      stand_in='native tiny registered tower and language-model architecture; no answer generation'),indent=2)+'\n')

 def test_donor_count_and_key_refusals(self):
  from student_pilot import gf1_cache as C,gf1
  from tests.test_gf1_cache import settings
  row=json.loads((L/'work/build8/proofs/coverage_final/cache/row.json').read_text())
  block=settings();dense,anchors=gf1.dense_inputs(row,block['gf1'])
  donor=dict(schema=C.DONOR_SCHEMA,clip_key=C.clip_key(dense),geometry_dense=dense,
             anchor_slots=anchors,permutation_sha256='fixture')
  for update,pattern in (({'anchor_slots':[0]},'anchor count'),({},'own clip')):
   bad=copy.deepcopy(row);bad['student_input']['geometry_bank_donor']={**donor,**update}
   with self.assertRaisesRegex(ValueError,pattern):C.row_bank(bad,block['gf1'],dense,anchors,False)
