"""Exercise real CPU row replay and timing-summary validation without GPU access."""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'),TMPDIR=str(ROOT/'work/test_runs'))
if hasattr(os,'sched_getaffinity'):
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:8])
sys.path.insert(0,os.environ.get('SO_TEST_TREE',str(ROOT/'work/verified_release/combined')))
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from tests.so_helpers import root,inputs,compact_processor,plan,native


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class Utilities(unittest.TestCase):
    def test_real_cpu_rows_all_data_arms_and_rng(self):
        directory=root()
        recipe=native().recipe
        for filename,value in [('receipt.json',inputs(directory)),('manifest.json',{}),
                               ('config.json',dict(training_mode='final',r1_training=True)),
                               ('plan.json',dict(world_size=1,plans=[plan()]*10))]:
            (directory/filename).write_text(json.dumps(value))
        replay=module('so_data_only',ROOT/'out/kit_timing/data_only.py')
        for arm in ('off','prefetch','cache'):
            destination=directory/(arm+'.json')
            args=['data_only.py','--tree',str(ROOT/'work/verified_release/combined'),
                  '--receipt',str(directory/'receipt.json'),'--manifest',str(directory/'manifest.json'),
                  '--config',str(directory/'config.json'),'--plan',str(directory/'plan.json'),
                  '--out',str(destination),'--arm',arm]
            with patch.object(sys,'argv',args),patch.object(run,'recipe_for',return_value=recipe),\
                    patch.object(run,'processor_for_receipt',side_effect=lambda *a:compact_processor()):
                replay.main()
            records=json.loads(destination.read_text())
            self.assertEqual(len(records),10)
            self.assertTrue(all(r['global_rng_unchanged'] and r['copy_seconds']==0 for r in records))
        print('SO_DATA_KIT: ten real SQLite/RGB/encoding plans per arm; OFF/prefetch/cache RNG unchanged; CPU only',flush=True)

    def test_summary_slowest_rank_and_parity_failures(self):
        summary=module('so_summary',ROOT/'out/kit_timing/summarize.py')
        directory=root()
        manifest=dict(trainables=[['weight',4,'float32']],config_sha256='cfg',start_step=2,
                      resume={'path':'checkpoint','sha256':'pin'},binding={'world_size':4})
        for arm in ('off','prefetch','cache','metrics'):
            for rank in range(4):
                path=directory/arm/f'rank{rank}'
                path.mkdir(parents=True)
                (path/'manifest.json').write_text(json.dumps(manifest))
                records=[dict(plan_sha256=str(step),wall_seconds=10+rank,data_seconds=1+rank,
                              first_step_micro_losses=[.25,.5]) for step in range(10)]
                (path/'steps.json').write_text(json.dumps(records))
        result=summary.summarize(directory)
        self.assertEqual(result['off']['median_wall_all'],13)
        self.assertEqual(result['off']['median_data'],4)
        path=directory/'metrics/rank3/steps.json'
        original=json.loads(path.read_text())
        broken=json.loads(path.read_text());broken[0]['plan_sha256']='wrong'
        path.write_text(json.dumps(broken))
        with self.assertRaisesRegex(ValueError,'Row plan mismatch'):
            summary.summarize(directory)
        broken=json.loads(json.dumps(original));broken[0]['first_step_micro_losses'][0]=.3
        path.write_text(json.dumps(broken))
        with self.assertRaisesRegex(SystemExit,'loss differed'):
            summary.summarize(directory)
        broken=json.loads(json.dumps(original));broken[0]['first_step_micro_losses'][0]=float('nan')
        path.write_text(json.dumps(broken))
        with self.assertRaisesRegex(ValueError,'finite scalar'):
            summary.summarize(directory)
        path.write_text(json.dumps(original))
        broken=dict(manifest,trainables=[])
        (directory/'metrics/rank3/manifest.json').write_text(json.dumps(broken))
        with self.assertRaisesRegex(ValueError,'Manifest parity failed: trainables'):
            summary.summarize(directory)
        print('SO_SUMMARY_KIT: slowest-rank reduction verified; changed rows/trainables/losses and NaN rejected',flush=True)


if __name__=='__main__':
    unittest.main(verbosity=2)
