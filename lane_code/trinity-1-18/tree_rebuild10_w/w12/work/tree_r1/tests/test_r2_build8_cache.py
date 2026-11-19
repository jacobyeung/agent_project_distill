"""Native cache CLI/writer/reader proofs; only the tiny tower boundary stands in."""
import copy,hashlib,io,json,os,runpy,sys,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tests.test_r2_build8 import folder as fresh

def produced_cache(grid=None):
 import torch
 from student_pilot import gf1_cache as C,g3t_online as G
 from tests.test_gf1_cache import Tiny,settings,SIDE,write_clip_frames
 class BoundaryTower(Tiny):
  def forward(self,images,coords=None):
   images=torch.nn.functional.interpolate(images.float(),(SIDE,SIDE),mode='bilinear',align_corners=False).half()
   return super().forward(images,coords)
 root=fresh('cache_reader');row=write_clip_frames(root,'frames',17)
 torch.manual_seed(17);encoder=BoundaryTower(settings()).eval()
 C.write_clip(encoder,row,root/'bank',grid=grid or C.frame_grid(row),dtype='float32')
 return root,row

class NativeCache(unittest.TestCase):
 def row(self):
  from tests.test_gf1_cache import write_clip_frames
  return write_clip_frames(self.root,'frames',17)

 def setUp(self):
  self.root=fresh('native_cache')

 def folder(self,name):
  p=self.root/name;p.mkdir(parents=True,exist_ok=True);return p

 def test_cli_native_writer_and_reader_with_tiny_tower(self):
  import torch
  from student_pilot import gf1_cache as C,g3t_online as G,gf1,pose_samples
  from tests.test_gf1_cache import Tiny,settings,SIDE
  row=self.row();p=self.root;cfg=p/'config.json';rows=p/'rows.jsonl';cache=p/'bank'
  block=settings();cfg.write_text(json.dumps(dict(geometry_online=block)))
  rows.write_text('\n'.join(map(json.dumps,[dict(category=pose_samples.CATEGORY,pose_sample={}),row,row]))+'\n')
  # Raster adaptation is inside the tiny tower boundary. The real frame
  # loader and native resize execute without replacement.
  class BoundaryTower(Tiny):
   def forward(self,images,coords=None):
    images=torch.nn.functional.interpolate(images.float(),(SIDE,SIDE),mode='bilinear',align_corners=False).half()
    return super().forward(images,coords)
  torch.manual_seed(17);encoder=BoundaryTower(block).eval();loaded=[]
  args=['cache','--run-config',str(cfg),'--rows',str(rows),'--root',str(cache),'--dtype','float32','--device','cpu']
  output=io.StringIO()
  with patch.object(G,'G3TEncoder',return_value=encoder),patch.object(encoder,'load_pinned',side_effect=lambda p:loaded.append(p)), \
       patch.object(sys,'argv',args),redirect_stdout(output):
   C.main()
  dense,anchors=gf1.dense_inputs(row,block['gf1']);key=C.clip_key(dense)
  entry=C.load_cached(dict(root=str(cache),dtype='float32'),key,anchors)
  self.assertTrue(torch.isfinite(entry.tensor).all());self.assertEqual(len(loaded),1)
  self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['clips'],1)
  self.assertIs(C.RowBanks([entry,None]).to('cpu').entries[0],entry)
  before=(cache/(key+'.safetensors')).read_bytes()
  with patch.object(G,'G3TEncoder',return_value=encoder),patch.object(encoder,'load_pinned',return_value=None), \
       patch.object(sys,'argv',args+['--limit','1']),redirect_stdout(io.StringIO()):
   runpy.run_module('student_pilot.gf1_cache',run_name='__main__')
  self.assertEqual((cache/(key+'.safetensors')).read_bytes(),before)
  (Path(os.environ['R2_PROOFS'])/'CACHE_CLI.json').write_text(json.dumps(dict(real_functions=['gf1_cache.main','write_clip','load_cached','frame_grid'],
      stand_ins=['Tiny registered G3T tower with seeded fixture weights','raster adaptation inside the tiny tower boundary; native frame loader/resize unchanged','load_pinned acknowledges unavailable production tower weights'],
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
   with self.assertRaises(ValueError):C.write_clip(Tiny(block),row,self.folder('invalid_cache'),grid=grid,dtype=dtype)
  for donor,pattern in [({},'Invalid'),(dict(schema=C.DONOR_SCHEMA,clip_key='bad',geometry_dense={'frames':[]},anchor_slots=anchors,permutation_sha256='x'),'configured ordered')]:
   bad=copy.deepcopy(row);bad['student_input']['geometry_bank_donor']=donor
   with self.assertRaisesRegex(ValueError,pattern):C.row_bank(bad,block['gf1'],dense,anchors,False)
  units=[dict(clip_key=k,dataset=d,grid=[32,4,4]) for k,d in [('a','one'),('b','one'),('c','two')]]
  result=C.shuffled_bank_plan(units,17,True)
  self.assertTrue(all(p['clip_key']!=p['donor_clip_key'] for p in result['pairs']))
  for data,seed in [(units,True),(units+[dict(units[0],dataset='other')],17)]:
   with self.assertRaises(ValueError):C.shuffled_bank_plan(data,seed)
  with self.assertRaises(ValueError):C._dataset(dict(student_input={}))

class CacheRead(unittest.TestCase):
 def test_native_cached_row_encoder_and_reader(self):
  import torch
  from student_pilot import carrier_c1_data as data,gf1_cache as C
  from tests.test_gf1_cache import model_for,settings
  from tests.test_r2_data_path import TinyProcessor
  class Processor(TinyProcessor):
   def __call__(self,text,videos,video_metadata,**kwargs):
    # Adapt only the pretrained processor boundary to the tiny LM raster.
    arrays=torch.from_numpy(videos[0].copy()).permute(0,3,1,2).float()
    arrays=torch.nn.functional.interpolate(arrays,(32,32),mode='bilinear',align_corners=False)
    videos=[arrays.permute(0,2,3,1).byte().numpy()]
    return super().__call__(text,videos,video_metadata,**kwargs)
  root,row=produced_cache([32,2,2])
  row['student_input'].update(question='Which colors occur in frame 1?',options=['A. red, green and blue','B. only black and white'])
  row['target']='<think>\nLocate: frame 1 contains red, green and blue pixels.\nRelate: the visible pixels match option A.\n</think>\n\nA'
  block=settings(dict(root=str(root/'bank'),dtype='float32'))
  batch,audit=data.encode_layout_row(Processor(),row,'duplicate',None,gf1=block['gf1'])
  self.assertEqual(audit['gf1_bank']['source'],'cached')
  model=model_for(block).eval()
  _,clips=C.rowbank_features(model,batch)
  self.assertTrue(torch.isfinite(clips[0][0]).all())
  self.assertEqual(model.gx_metrics['cached_rows'],1)
  (Path(os.environ['R2_PROOFS'])/'CACHE_ROW.json').write_text(json.dumps(dict(
   functions=['write_clip','encode_layout_row','row_bank','load_cached','rowbank_features'],
   stand_ins=['tiny pretrained tower and LM weights','tiny tokenizer and processor raster'],
   tensor_sha256=batch['aux_gf1_rowbanks'].entries[0].record['tensor']['sha256'])))

 def test_real_cached_read_hit_and_shape_refusals(self):
  import torch
  from student_pilot import gf1_cache as C,gf1
  from tests.test_gf1_cache import model_for,settings
  root,row=produced_cache()
  block=settings(dict(root=str(root/'bank'),dtype='float32'))
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
  (Path(os.environ['R2_PROOFS'])/'CACHE_READER.json').write_text(json.dumps(dict(
      tensor_sha256=entry.record['tensor']['sha256'],shape=list(entry.tensor.shape),cache_hit=True,
      real_functions=['load_cached','model_identity','rowbank_features'],
      stand_in='native tiny registered tower and language-model architecture; no answer generation'),indent=2)+'\n')

 def test_donor_count_and_key_refusals(self):
  from student_pilot import gf1_cache as C,gf1
  from tests.test_gf1_cache import settings
  from tests.test_gf1_cache import write_clip_frames
  row=write_clip_frames(fresh('donor_metadata'),'frames',17)
  block=settings();dense,anchors=gf1.dense_inputs(row,block['gf1'])
  donor=dict(schema=C.DONOR_SCHEMA,clip_key=C.clip_key(dense),geometry_dense=dense,
             anchor_slots=anchors,permutation_sha256='fixture')
  for update,pattern in (({'anchor_slots':[0]},'anchor count'),({},'own clip')):
   bad=copy.deepcopy(row);bad['student_input']['geometry_bank_donor']={**donor,**update}
   with self.assertRaisesRegex(ValueError,pattern):C.row_bank(bad,block['gf1'],dense,anchors,False)
