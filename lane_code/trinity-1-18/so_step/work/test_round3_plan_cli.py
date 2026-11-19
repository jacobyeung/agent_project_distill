"""Real plan-writer CLI pin and artifact-filter regression."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'),TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0,range(8))
sys.path[:0]=[str(ROOT/'out/kit_timing'),str(ROOT/'out/kit_profile'),str(ROOT/'work/b21_final/work/tree_r1')]
import torch
torch.set_num_threads(8)
from tests.so_helpers import root,plan
from student_pilot import carrier_c1_run as run
from privacy import WORDS,scrub
import write_plan

class PlanCLI(unittest.TestCase):
    def test_real_pin_start_step_and_scrubbed_metadata(self):
        directory=root()
        cfg={'training_mode':'final','row_start_step':3}
        receipt={'streams':{'pose':{'count':32}}}
        checkpoint={'schema':'c1-checkpoint-v1','step':200,'binding':{'world_size':4}}
        source=directory/'qwen_checkpoint.json';source.write_text(json.dumps(checkpoint))
        pin=run.file_pin(source)
        for name,value in (('config.json',cfg),('receipt.json',receipt),('pin.json',pin)):
            (directory/name).write_text(json.dumps(value))
        cfg['preparation']=run.file_pin(directory/'receipt.json')
        (directory/'config.json').write_text(json.dumps(cfg))
        args=['write_plan.py','--tree',str(ROOT/'work/b21_final/work/tree_r1'),
              '--config',str(directory/'config.json'),'--receipt',str(directory/'receipt.json'),
              '--resume-pin',str(directory/'pin.json'),'--steps','10','--out',str(directory/'plan.json')]
        with patch.object(sys,'argv',args),patch.object(run,'prepared',return_value=(receipt,{})),patch.object(run,'recipe_for',return_value={'world_size':4,'mix':{'pose':1}}),patch.object(run.data,'mixed_indices',return_value=iter([plan(4)]*10)) as sample:
            write_plan.main()
        actual=json.loads((directory/'plan.json').read_text())
        self.assertEqual(actual['start_step'],200)
        self.assertEqual(sample.call_args.kwargs['start_step'],203)
        self.assertEqual(actual['resume'],scrub(pin))
        self.assertFalse(WORDS.search((directory/'plan.json').read_text()))
        self.assertEqual(actual['receipt_sha256'],run.file_pin(directory/'prepared_receipt.json')['sha256'])

if __name__=='__main__': unittest.main(verbosity=2)
