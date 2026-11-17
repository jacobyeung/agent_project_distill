"""Move native cache proofs into the sealed test tree with independent products."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
source=(B/'coverage_final.py').read_text().split('class NativeCache(unittest.TestCase):',1)[1]
source='class NativeCache(unittest.TestCase):'+source
start=source.index(' def row(self):');end=source.index('\n def test_cli_',start)
source=source[:start]+''' def row(self):
  from tests.test_gf1_cache import write_clip_frames
  return write_clip_frames(self.root,'frames',17)

 def setUp(self):
  self.root=fresh('native_cache')

 def folder(self,name):
  p=self.root/name;p.mkdir(parents=True,exist_ok=True);return p
'''+source[end:]
source=source.replace("folder('cache')","self.root").replace("folder('invalid_cache')","self.folder('invalid_cache')")
source=source.replace('Tiny,settings,small_square','Tiny,settings,SIDE')
source=source.replace('torch.manual_seed(17);encoder=Tiny(block).eval();loaded=[]','''# Raster adaptation is inside the tiny tower boundary. The real frame
  # loader and native resize execute without replacement.
  class BoundaryTower(Tiny):
   def forward(self,images,coords=None):
    images=torch.nn.functional.interpolate(images.float(),(SIDE,SIDE),mode='bilinear',align_corners=False).half()
    return super().forward(images,coords)
  torch.manual_seed(17);encoder=BoundaryTower(block).eval();loaded=[]''')
source=source.replace("patch.object(G,'native_square_518',small_square),",'')
source=source.replace("'small_square resize to tiny raster'","'raster adaptation inside the tiny tower boundary; native frame loader/resize unchanged'")
tail=(B/'coverage_finish.py').read_text().split('class CacheRead(unittest.TestCase):',1)[1]
tail='class CacheRead(unittest.TestCase):'+tail
tail=tail.replace("root=L/'work/build8/proofs/coverage_final/cache'\n  row=json.loads((root/'row.json').read_text());block=settings(dict(root=str(root/'bank'),dtype='float32'))",'''root,row=produced_cache()
  block=settings(dict(root=str(root/'bank'),dtype='float32'))''')
tail=tail.replace("(folder('cache_read')/'RESULT.json')","(Path(os.environ['R2_PROOFS'])/'CACHE_READER.json')")
tail=tail.replace("row=json.loads((L/'work/build8/proofs/coverage_final/cache/row.json').read_text())",'''from tests.test_gf1_cache import write_clip_frames
  row=write_clip_frames(fresh('donor_metadata'),'frames',17)''')
header='''"""Native cache CLI/writer/reader proofs; only the tiny tower boundary stands in."""
import copy,hashlib,io,json,os,runpy,sys,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tests.test_r2_build8 import folder as fresh

def produced_cache():
 import torch
 from student_pilot import gf1_cache as C,g3t_online as G
 from tests.test_gf1_cache import Tiny,settings,SIDE,write_clip_frames
 class BoundaryTower(Tiny):
  def forward(self,images,coords=None):
   images=torch.nn.functional.interpolate(images.float(),(SIDE,SIDE),mode='bilinear',align_corners=False).half()
   return super().forward(images,coords)
 root=fresh('cache_reader');row=write_clip_frames(root,'frames',17)
 torch.manual_seed(17);encoder=BoundaryTower(settings()).eval()
 C.write_clip(encoder,row,root/'bank',grid=C.frame_grid(row),dtype='float32')
 return root,row

'''
# Keep the CLI proof's summary outside temporary products compacted by the harness.
source=source.replace("(p/'PROOF.json')","(Path(os.environ['R2_PROOFS'])/'CACHE_CLI.json')")
target=L/'work/tree_r1/tests/test_r2_build8_cache.py'
target.write_text(header+source+'\n'+tail)
compile(target.read_bytes(),str(target),'exec')
print(target)
