"""CPU-only model-sized cache-hit overhead, with identical zero-work forwards."""
import gc,importlib.util,json,os,resource,statistics,sys,time
from pathlib import Path
import torch
torch.set_num_threads(8)
L=Path('/scratch/jjyeung/orch_n30/so_read')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
before=load('cache_before',L/'work/round3-before-u0/a0.py');after=load('cache_after',L/'work/src/u0/a0.py')
class Config:
 def to_dict(self):return {}
class Qwen3_5VisionModel(torch.nn.Module):
 def __init__(self,blocks):
  super().__init__();self.config=Config();self.layers=torch.nn.ModuleList()
  for i in range(blocks):
   layer=torch.nn.Module();layer.register_parameter('weight',torch.nn.Parameter(torch.full((2048,1024),.5,dtype=torch.bfloat16),requires_grad=False))
   layer.register_buffer('offset',torch.zeros(1024,dtype=torch.bfloat16));self.layers.append(layer)
 def forward(self,x):return x+1
class Parent:
 def __init__(self,v):self.model=type('Holder',(),{'visual':v})()
def timing(fn,count):
 values=[]
 for _ in range(count):
  start=time.perf_counter();fn();values.append(time.perf_counter()-start)
 return {'seconds':values,'median_seconds':statistics.median(values),'min_seconds':min(values),'max_seconds':max(values)}
receipt={'kind':'measured CPU stub cache-hit overhead, not GPU speedup','torch':torch.__version__,
 'threads':torch.get_num_threads(),'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),'nice':os.getpriority(os.PRIO_PROCESS,0),'cases':[]}
with torch.no_grad():
 for blocks in (128,256):
  case={'blocks':blocks,'parameter_tensors':blocks,'parameter_shape':[2048,1024],
        'buffer_tensors':blocks,'buffer_shape':[1024],'dtype':'bfloat16',
        'parameter_count':blocks*2048*1024,'weight_and_buffer_bytes':blocks*(2048*1024+1024)*2}
  for label,impl in (('before',before),('after',after)):
   v=Qwen3_5VisionModel(blocks).eval();store=impl.ReadCache(1000000);x=torch.ones(32,dtype=torch.bfloat16)
   start=time.perf_counter();impl.install_vision_cache(Parent(v),store);case[label+'_install_seconds']=time.perf_counter()-start
   v(x);v(x) # miss then warm hit, excluded
   case[label+'_per_call']=timing(lambda:v(x),7)
   if label=='after':case['boundary']=timing(store.weight_boundary,3)
   assert store.stats['vision']['hits']==8
   del v,store,x;gc.collect()
  case['median_speed_ratio']=case['before_per_call']['median_seconds']/case['after_per_call']['median_seconds']
  receipt['cases'].append(case)
receipt['max_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
assert receipt['max_rss_bytes']<30*1024**3
(L/'out/checks/CACHE_COST3.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2,sort_keys=True))
