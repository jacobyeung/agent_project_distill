"""Second-review kit gates; no GPU or production files are accessed."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'), TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path[:0] = [str(ROOT/'out/kit_timing'), str(ROOT/'out/kit_profile'),
               os.environ.get('SO_TEST_TREE', str(ROOT/'work/tree'))]
import torch
torch.set_num_threads(8)
from tests.so_helpers import root, inputs, compact_processor, plan, native
from student_pilot import carrier_c1_run as run


class KitRound2(unittest.TestCase):
    def test_full_plan_memory_includes_every_group_and_targets(self):
        import data_only
        directory = root()
        recipe = native().recipe
        values = [('receipt.json',inputs(directory)), ('manifest.json',{}),
                  ('config.json',dict(training_mode='final',r1_training=True)),
                  ('plan.json',dict(world_size=1,plans=[plan()]*101))]
        for name, value in values:
            (directory/name).write_text(json.dumps(value))
        args = ['data_only.py','--tree',os.environ.get('SO_TEST_TREE',str(ROOT/'work/tree')),
                '--receipt',str(directory/'receipt.json'),'--manifest',str(directory/'manifest.json'),
                '--config',str(directory/'config.json'),'--plan',str(directory/'plan.json'),
                '--out',str(directory/'off.json'),'--arm','off','--full-plan']
        # Small synthetic tensors retain the real grouping, row hash and RNG paths.
        def get(rows, stream, index):
            return {'pixels':torch.zeros(3)}, {'target':torch.zeros(5)}, {}
        with patch.object(sys,'argv',args), patch.object(run,'recipe_for',return_value=recipe), \
                patch.object(run,'processor_for_receipt',return_value=compact_processor()), \
                patch.object(run.Rows,'get',get), patch.object(run,'check_row'):
            data_only.main()
        records = json.loads((directory/'off.json').read_text())
        self.assertEqual(len(records),101)
        self.assertTrue(all(r['max_group_tensor_bytes'] == 64 for r in records))
        meta = json.loads((directory/'off.json.manifest.json').read_text())
        self.assertTrue(meta['full_plan'])
        self.assertEqual(meta['plans_checked'],101)
        self.assertEqual(meta['peak_group_tensor_bytes'],64)

    def test_gpu_guard_refuses_busy_low_memory_and_unreadable_probe(self):
        from gpu_guard import check
        from subprocess import CompletedProcess, CalledProcessError
        def probe(gpus, apps):
            return [CompletedProcess([],0,gpus,''), CompletedProcess([],0,apps,'')]
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='0,1'):
            with patch('gpu_guard.subprocess.run',side_effect=probe('0, GPU-a, 80000\n1, GPU-b, 80000\n','GPU-b, 999999\n')):
                with self.assertRaisesRegex(ValueError,'compute process'):
                    check()
            with patch('gpu_guard.subprocess.run',side_effect=probe('0, GPU-a, 76000\n1, GPU-b, 80000\n','')):
                with self.assertRaisesRegex(ValueError,'free memory'):
                    check()
            with patch('gpu_guard.subprocess.run',side_effect=probe('0, GPU-a, 80000\n1, GPU-b, 80000\n','')):
                self.assertEqual(len(check()),2)
            with patch('gpu_guard.subprocess.run',side_effect=CalledProcessError(1,['nvidia-smi'])):
                with self.assertRaises(CalledProcessError):
                    check()

    def test_t_power_and_off_drift_persist_comparison_before_refusal(self):
        import summarize
        self.assertAlmostEqual(summarize.precision([0,1,2])['minimum_detectable_difference_s'],
                               (4.303+1.061)/(3**.5))
        directory = root()
        manifest = dict(trainables=[],config_sha256='cfg',start_step=0,resume=None,
                        binding={},threads={},warmup=10,measured_steps=10)
        for leg,arm in enumerate(('off','prefetch','off')):
            for rank in range(4):
                path=directory/f'r0_l{leg}_{arm}'/f'rank{rank}'
                path.mkdir(parents=True)
                (path/'manifest.json').write_text(json.dumps(manifest))
                records=[dict(plan_sha256=str(i),wall_seconds=10.,data_seconds=2.,
                    first_step_micro_losses=[.2 if leg == 0 else .3],
                    microstep_host={'forward_total':[1.], 'backward_including_recompute_and_fsdp':[2.]})
                    for i in range(20)]
                (path/'steps.json').write_text(json.dumps(records))
        with self.assertRaisesRegex(SystemExit,'OFF brackets'):
            summarize.summarize(directory)
        result=json.loads((directory/'comparison.json').read_text())
        self.assertFalse(result['_parity']['off_brackets_bitwise'])
        self.assertFalse(result['prefetch']['first_step_loss_bitwise'])
        self.assertIn('wall',result['prefetch'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
