from pathlib import Path
import inspect,sys
from transformers import Qwen3VLProcessor, Qwen2VLImageProcessor, Qwen3VLVideoProcessor
for obj in (Qwen3VLProcessor,Qwen2VLImageProcessor,Qwen3VLVideoProcessor):
    print(obj.__name__,inspect.signature(obj.__init__),inspect.getfile(obj))
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load
cfg=load(L/'work/build17/inputs/config.json')
print({k:cfg[k] for k in ('base_identity','carrier_placement','recipe','depth_enabled','r2_identity','init_artifact')})
