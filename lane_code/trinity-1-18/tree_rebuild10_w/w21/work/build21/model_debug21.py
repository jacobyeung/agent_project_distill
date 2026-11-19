from pathlib import Path
import sys,json,traceback
B=Path(__file__).resolve().parent;sys.path[:0]=[str(B),str(B.parent/'tree_r1')]
import torch,numpy as np
from native_assets21 import PatchGridProcessor
from transformers import Qwen3_5Config,Qwen3_5ForConditionalGeneration
root=B/'proofs/capacity/model';cfg=Qwen3_5Config.from_pretrained(root,local_files_only=True)
for obj in (cfg,cfg.text_config,cfg.vision_config):obj._attn_implementation='sdpa'
if '--one-head' in sys.argv:cfg.vision_config.num_heads=1
model=Qwen3_5ForConditionalGeneration(cfg)
p=PatchGridProcessor(root);batch=p(text=['<video>Is the red square left?'],videos=[np.zeros((32,32,32,3),dtype=np.uint8)])
try:
 with torch.no_grad():out=model(**batch)
 print('PASS',out.logits.shape,torch.isfinite(out.logits).all().item())
except Exception:traceback.print_exc()
