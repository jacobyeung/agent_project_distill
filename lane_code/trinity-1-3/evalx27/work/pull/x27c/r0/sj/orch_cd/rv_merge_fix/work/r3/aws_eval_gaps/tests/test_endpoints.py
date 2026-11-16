"""Canonical first/last task plumbing with explicitly synthetic video fixtures."""
import json,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'evaluator'))
from test_frames import video
from test_eval_gaps import pin,full_spec
from data import tasks_for
from media import decode
from evalpath.official import build_prompt_context
class Endpoints(unittest.TestCase):
 def test_first_last_canonical_items_through_decoder(self):
  p=ROOT/'checks/endpoint_source.mp4';video(p,200,10)
  entries=[]
  for spec,frames in [(full_spec(),32),(dict(benchmark='devrows',rows=pin('DEV_ITEMS.jsonl')),96),
                      (dict(benchmark='devrows',rows=pin('DEV_ITEMS.jsonl')),128),
                      (dict(benchmark='official5130',rows=pin('meta_5130.jsonl')),32)]:
   rows=tasks_for(spec,dict(video_root='/scratch/unavailable',vsti_video_root='/scratch/unavailable'))
   for t in (rows[0],rows[-1]):
    task={**t,'video_path':str(p),'video_sha256':''}
    arrays,audit=decode(task,'spread',frames,'uniform' if frames==96 else 'nested' if frames>32 else None)
    self.assertEqual(len(arrays),frames);self.assertTrue(build_prompt_context(t,'ours'))
    entries.append(dict(benchmark=t['benchmark'],id=t['example_id'],frames=frames,shape=list(arrays.shape)))
  (ROOT/'checks/SYNTHETIC_ENDPOINTS.json').write_text(json.dumps(dict(media='synthetic; not evidence of run-node media availability',entries=entries),indent=2)+'\n')
if __name__=='__main__':unittest.main()
