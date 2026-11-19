"""CPU fixture: unchanged own/_prepare_decode/HeadState; small random model primitives."""
import os,sys
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='8'
import resource,time,types,argparse
import numpy as np
from core import *
from runtime import code,boundary_method
from worker import run,binding
from types import SimpleNamespace as NS

def fixture(src,out):
 import torch,transformers
 torch.set_num_threads(8);torch.manual_seed(17)
 from torch import nn
 from student_pilot import carrier_c1_canary,decoupled_v,carrier_c1_decode
 class Pose(nn.Module):
  def __init__(self):super().__init__();self.linear=nn.Linear(8,9)
  def carrier_states(self,hidden,positions):return hidden[:,positions[0]]
  def predict_all(self,h,key_mask):
   p=self.linear(h);p=p.clone();p[...,3:7]=torch.tensor([0.,0.,0.,1.]);p[...,7:9]=1.
   return [p],[torch.tensor([[0.,-1.,0.]])],None
 class Depth(nn.Module):
  def __init__(self):super().__init__();self.linear=nn.Linear(5,4)
  def encode(self,grid,vit,fov):return self.linear(torch.cat([vit,fov],-1))
  def query(self,depth,uv):
   xy=uv/1000.;return torch.nn.functional.softplus(depth[:,None,0]+depth[:,None,1]*xy[...,0]+depth[:,None,2]*xy[...,1])+1.
 class Language(nn.Module):
  def __init__(self):super().__init__();self.norm=nn.LayerNorm(8)
  def forward(self,inputs_embeds,**kw):return self.norm(inputs_embeds)
 class Body(nn.Module):
  def __init__(self):super().__init__();self.embedding=nn.Embedding(64,8);self.language_model=Language()
  def forward(self,input_ids,**kw):return self.language_model(inputs_embeds=self.embedding(input_ids))
 class Model(nn.Module):
  def __init__(self):
   super().__init__();self.model=Body();self.lm_head=nn.Linear(8,64);self.auxiliary_heads=nn.Module();self.auxiliary_heads.pose=Pose()
   self.auxiliary_heads.depth=nn.Module();self.auxiliary_heads.depth.auxiliary_heads=nn.Module();self.auxiliary_heads.depth.auxiliary_heads.camera=nn.Module();self.auxiliary_heads.depth.auxiliary_heads.camera.point_depth=Depth()
   self.config=NS(text_config=NS(max_position_embeddings=32768));self.carrier_placement='fixture';self.depth_fov_source='pose_head'
  def check_placement(self,b):assert b['aux_camera_positions'].shape==(1,32)
  def get_input_embeddings(self):return self.model.embedding
  def geometry_features(self,b):return None
  def patch_injection(self,stack,b,g):return None
  def carrier_embeddings(self,h,p,g):return h
 class Native(nn.Module):
  def __init__(self,config):super().__init__();self.config=config
  def forward(self,**kw):
   h=self.model(**kw);return NS(logits=self.lm_head(h[:,-1:]),past_key_values=None)
 def prompt(processor,row,cfg):
  from PIL import Image
  colors=[]
  for f in row['student_input']['frames']:
   with Image.open(f['path']) as im:colors.append(np.asarray(im.convert('RGB').resize((8,8)),dtype=np.float32).mean((0,1))/255.)
  return {'input_ids':torch.arange(32)[None,:],'attention_mask':torch.ones((1,32),dtype=torch.long),'aux_camera_positions':torch.arange(32)[None,:],'fixture_rgb':torch.tensor(np.array(colors))}
 originals=(transformers.Qwen3_5ForConditionalGeneration,carrier_c1_canary.prompt_batch,decoupled_v.features)
 proxy=types.ModuleType('transformers');proxy.__getattr__=lambda name:getattr(transformers,name);proxy.Qwen3_5ForConditionalGeneration=Native;sys.modules['transformers']=proxy;carrier_c1_canary.prompt_batch=prompt
 decoupled_v.features=lambda depth,batch,allow_short:NS(grids=[None],vits=[batch['fixture_rgb']])
 model=Model().eval();torch.save(model.state_dict(),out/'random_small_weights.pt')
 p=out/'FIXTURE_CONFIG.json';atomic(p,{'input_sha256':{str(pathlib.Path(__file__)):sha(__file__)},'synthetic':True,'seed':17,'fixture':'small random CPU primitives; RGB mean preprocessing'})
 class Boundary:own=boundary_method()
 b=Boundary();b.model=model;b.processor=NS(tokenizer=NS(),_routing_tokens={'ids':{'open':1}});b.device='cpu';b.settings={'config':{'path':str(p),'sha256':sha(p)}}
 def restore():
  sys.modules['transformers']=transformers
  transformers.Qwen3_5ForConditionalGeneration,carrier_c1_canary.prompt_batch,decoupled_v.features=originals
 return b,restore

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'out/cpu_stub_verified'));a=ap.parse_args()
 out=fresh(a.out);write_guard(out)
 for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TORCH_HOME','torch')]:
  q=out/name;q.mkdir(exist_ok=True);os.environ[var]=str(q)
 src=code(out);begin=time.monotonic()
 b,restore=fixture(src,out);cs=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][:1]
 pins={str(p):sha(p) for p in [pathlib.Path(__file__),KIT/'core.py',KIT/'worker.py',KIT/'runtime.py',KIT/'inputs/TRAIN_CAPTURES.json',KIT/'vendor/native_kit/boundaries.py',KIT/'inputs/A10b_code.tgz',out/'random_small_weights.pt',out/'FIXTURE_CONFIG.json']}
 try:
  count=run(cs,b,out,pins,True)
  dest=out/'captures'/digest(cs[0]['canonical'])[:16];before=sha(dest/'PHASE_COMPLETE.json')
  # A resumed fixture must not call the model.
  b.own=lambda *a:(_ for _ in ()).throw(AssertionError('forward called on completed capture'))
  count2=run(cs,b,out,pins,True);assert before==sha(dest/'PHASE_COMPLETE.json')
 finally:restore()
 pins[str(dest/'PHASE_COMPLETE.json')]=sha(dest/'PHASE_COMPLETE.json')
 for name in ('torch','numpy','PIL','transformers'):
  module=sys.modules[name];pins[str(pathlib.Path(module.__file__))]=sha(module.__file__)
 pins[sys.executable]=sha(sys.executable)
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;assert rss<40_000_000_000
 atomic(out/'CPU_CHECK.json',{'input_sha256':pins,'status':'STUB PASS; real weights MISSING','capture':cs[0]['canonical'],'shape':[32,51,51],'first_run_captures':count,'resume_captures':count2,'skip_receipt_unchanged':True,'peak_rss_bytes':rss,'seconds':time.monotonic()-begin,'median_ratio_vs544':'MISSING: synthetic weights cannot measure checkpoint parity','OwnDepthScale_ratio_vs544':'MISSING','real_functions':['GPU.own','runtime.prompt_batch','_prepare_decode','closed_adapters','HeadState','depth_head.query invocation'],'stubbed_primitives':['trainer prompt preprocessing (RGB mean)','native backbone','pose and depth weights','private-ViT feature extraction'],'command':'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B '+' '.join(sys.argv)})
 print('CPU stub PASS',rss,'bytes peak RSS',flush=True)
if __name__=='__main__':main()
