"""Use the direct read's exact exported scorer; never substitute a numeric rule."""
from common import *
class Scorer:
 def __init__(self):
  cfg=js(ROOT/'inputs/DIRECT_SCORER.json');assert sha(cfg['module_path'])==cfg['module_sha256']
  self.fn=getattr(module(cfg['module_path'],'direct_read_scorer'),cfg['callable']);self.kwargs=cfg.get('kwargs',{})
  if cfg['score_range']!=[0,1]:raise ValueError('Scorer adapter must return [0,1]')
 def __call__(self,item,prediction):
  if prediction is None:return 0.
  result=float(self.fn(item,prediction,**self.kwargs))
  if not 0<=result<=1:raise ValueError('Invalid item score')
  return result
