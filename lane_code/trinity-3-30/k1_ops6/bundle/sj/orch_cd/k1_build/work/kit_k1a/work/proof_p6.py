import os,sys,json,copy,tempfile
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(Path(__file__).parent))
import gate,prooflib,parity_live as P
def proof():
 import torch
 from PIL import Image
 from tests.test_sam3_tower import StubBackend
 torch.set_num_threads(1)
 root=Path(tempfile.mkdtemp(prefix='p6_',dir=prooflib.LANE/'work'));path=root/'frame.png';Image.new('RGB',(24,16),(32,64,96)).save(path)
 tower=P.Sam3Tower(dict(device='cpu'),backend=StubBackend())
 with Image.open(path) as im:d=P.detect(tower,[im.convert('RGB')],'chair')[0]
 entry=dict(frame_sha256=gate.sha(path),phrase='chair',prediction=P.prediction(d),fixture_only=True)
 recorded=root/'cache.json';recorded.write_text(json.dumps(entry))
 entry=json.loads(recorded.read_text())
 with Image.open(path) as im:fresh=P.detect(tower,[im.convert('RGB')],'chair')[0]
 identical=P.check(entry,path,'chair',fresh);assert identical['ok']
 shifted=root/'shifted.png';Image.new('RGB',(24,16),(33,64,96)).save(shifted)
 rejected=[]
 for frame,phrase,tag in [(shifted,'chair','shifted_frame'),(path,'table','swapped_phrase')]:
  try:P.check(entry,frame,phrase,fresh)
  except ValueError:rejected.append(tag)
  else:raise AssertionError(tag+' passed')
 bad=copy.deepcopy(entry);bad['prediction']['all_instance_scores'][0]-=.05
 drift=P.check(bad,path,'chair',fresh);assert not drift['ok'];rejected.append('0.05_score_drift')
 return dict(recorded_cache=str(recorded),identical=identical,mutations_refused=rejected,fixture_only=True,real_gpu_parity=False,noise_rule=P.RULE)
if __name__=='__main__':raise SystemExit(not prooflib.run('P6',proof))
