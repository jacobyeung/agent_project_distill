from pathlib import Path
import unittest,json
import torch,numpy as np
from native_assets21 import PatchGridProcessor
from transformers import Qwen3_5Config,Qwen3_5ForConditionalGeneration
B=Path(__file__).resolve().parent
class Model21(unittest.TestCase):
 def test_tiny_rgb_forward_dimensions_and_bad_head_mutation(self):
  root=B/'proofs/capacity/model';cfg=Qwen3_5Config.from_pretrained(root,local_files_only=True)
  self.assertEqual((cfg.text_config.hidden_size,cfg.vision_config.hidden_size),(4,4))
  for obj in (cfg,cfg.text_config,cfg.vision_config):obj._attn_implementation='sdpa'
  p=PatchGridProcessor(root);batch=p(text=['<video>Which square is left?'],videos=[np.zeros((2,32,32,3),dtype=np.uint8)])
  cfg.vision_config.num_heads=2
  with torch.no_grad(),self.assertRaisesRegex(RuntimeError,'size of tensor'):Qwen3_5ForConditionalGeneration(cfg)(**batch)
  cfg.vision_config.num_heads=1
  with torch.no_grad():result=Qwen3_5ForConditionalGeneration(cfg)(**batch)
  self.assertTrue(torch.isfinite(result.logits).all())
