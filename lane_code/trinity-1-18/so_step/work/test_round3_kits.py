"""Bounded continuation audit and ordered replay regressions; CPU only."""
import importlib
import json
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'), TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path[:0] = [str(ROOT/'out/kit_timing'), str(ROOT/'out/kit_profile'),
               os.environ.get('SO_TEST_TREE', str(ROOT/'work/b21_final/work/tree_r1'))]
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from tests.so_helpers import root, inputs, compact_processor, plan, native


class KitRound3(unittest.TestCase):
    def test_plan_writer_matches_continuation_sampler_call(self):
        from write_plan import build_plan
        cfg = dict(row_start_step=17, training_mode='final', r2_sampling={'fixture':True}, r2_identity={})
        receipt = dict(streams={s:dict(count=33) for s in ('pose','vqa','routing','pointing')})
        recipe = dict(mix={'pose':1}, world_size=4)
        plans = [plan(world=4)] * 10
        with patch.object(run, 'recipe_for', return_value=recipe), \
                patch.object(run.data, 'mixed_indices', return_value=iter(plans)) as sample:
            result = build_plan(run, cfg, receipt, 200, 10)
        sample.assert_called_once_with({s:33 for s in receipt['streams']}, 227, start_step=217,
            training_mode='final', mix=recipe['mix'], world=4, r2_sampling=cfg['r2_sampling'], require_r2=True)
        self.assertEqual(result['start_step'],200)
        self.assertEqual(result['plans'],plans)
        self.assertEqual(result['world_size'],4)

    def test_alignment_descriptor_enforces_real_pose_check(self):
        from data_only import descriptor_for
        cfg = dict(training_mode='final', align={'cam':{'layer':'final'}})
        with patch.object(run,'recipe_for',return_value=native().recipe):
            descriptor = descriptor_for(run, cfg, {'align':cfg['align']})
        model = native(); directory=root(); rows=run.Rows(inputs(directory),compact_processor())
        try:
            batch, targets, _ = rows.get('pose',0)
        finally:
            rows.close()
        with self.assertRaisesRegex(ValueError, 'Teacher-aligned'):
            run.check_row(batch,targets,'pose',descriptor)
        self.assertEqual(descriptor.align_settings,cfg['align'])
        with patch.object(run,'recipe_for',return_value=model.recipe):
            self.assertFalse(hasattr(descriptor_for(run,{'training_mode':'final'},{}),'align_settings'))

    def test_grid_cap_and_actual_augmentation_coverage(self):
        from audit import Coverage
        from student_pilot import pose_samples
        coverage = Coverage()
        with patch.object(pose_samples,'augment',return_value='encoded'):
            with coverage.augmentation(pose_samples):
                self.assertEqual(pose_samples.augment(None,dict(seed=1,brightness=.3)), 'encoded')
                pose_samples.augment(None,dict(seed=1,brightness=0))
        coverage.observe({'video_grid_thw':torch.tensor([[32,20,26]])})
        self.assertEqual(coverage.augmented_pose_rows,1)
        self.assertEqual(coverage.max_grid,[32,20,26])
        with self.assertRaisesRegex(ValueError,'grid cap'):
            coverage.observe({'video_grid_thw':torch.tensor([[32,22,26]])})
        with self.assertRaisesRegex(ValueError,'augmented pose'):
            Coverage().require()
        coverage.require()

    def test_data_audit_records_process_peak_rss_and_continuation_step(self):
        import data_only
        directory = root(); recipe=native().recipe
        values = [('receipt.json',inputs(directory)),('manifest.json',{}),
                  ('config.json',dict(training_mode='final',r1_training={'fixture':True})),
                  ('plan.json',dict(start_step=200,world_size=1,plans=[plan()]))]
        for name,value in values:
            (directory/name).write_text(json.dumps(value))
        args = ['data_only.py','--tree',os.environ.get('SO_TEST_TREE',str(ROOT/'work/b21_final/work/tree_r1')),
            '--receipt',str(directory/'receipt.json'),'--manifest',str(directory/'manifest.json'),
            '--config',str(directory/'config.json'),'--plan',str(directory/'plan.json'),
            '--out',str(directory/'off.json'),'--arm','off','--steps','1']
        with patch.object(sys,'argv',args), patch.object(run,'recipe_for',return_value=recipe), \
                patch.object(run,'processor_for_receipt',return_value=compact_processor()):
            data_only.main()
        meta=json.loads((directory/'off.json.manifest.json').read_text())
        self.assertGreater(meta['peak_rss_bytes'], 0)
        self.assertEqual(meta['start_step'],200)
        self.assertEqual(json.loads((directory/'off.json').read_text())[0]['step'],201)

    def test_replay_accepts_only_bitwise_or_bounded_off_spread(self):
        from replay_compare import loss_acceptance
        self.assertTrue(loss_acceptance([1.,2.],[1.,2.],[1.,2.])['accepted'])
        self.assertFalse(loss_acceptance([1.,2.],[1.,2.],[1.,2.000000001])['accepted'])
        self.assertTrue(loss_acceptance([1.,2.],[1.2,2.2],[1.1,2.1])['accepted'])
        self.assertFalse(loss_acceptance([1.,2.],[1.2,2.2],[1.3,2.1])['accepted'])
        self.assertFalse(loss_acceptance([1.],[1.1],[float('nan')])['accepted'])
        self.assertFalse(loss_acceptance([0.],[0.],[-0.])['accepted'])

    def test_full_replay_gate_binds_audit_plan_and_on_provenance(self):
        from replay_compare import compare, replay_order
        directory = root(); audit_dir = directory/'audit'; audit_dir.mkdir()
        for rank in range(4):
            for name,arm in replay_order():
                path=directory/name/f'rank{rank}'; path.mkdir(parents=True)
                values={'C1_CPU_PREFETCH':'1' if arm == 'prefetch' else '0',
                        'C1_BATCH_METRICS':'0','C1_DECODED_CACHE_MIB':'0','C1_CPU_PREFETCH_FALLBACK':'0'}
                meta=dict(arm=arm,start_step=200,resume={'pin':'same'},trainables=['same'],
                          config_sha256='cfg',binding={},threads={},switches=values)
                record=dict(step=201,plan_sha256='same',components={'a':1.},stream_means={'vqa':1.},
                            first_step_micro_losses=[1.])
                if arm == 'prefetch':
                    record['performance']=values
                (path/'manifest.json').write_text(json.dumps(meta))
                (path/'steps.json').write_text(json.dumps([record]))
                (path/'progress.json').write_text(json.dumps({'stage':'complete'}))
            for arm in ('off','prefetch'):
                path=audit_dir/f'data_{arm}_rank{rank}.json'
                record=dict(plan_sha256='same',row_draws=[['pose',0,0]],encoded_row_sha256=['same'],global_rng_unchanged=True)
                path.write_text(json.dumps([record]*10))
                meta=dict(start_step=200,resume={'pin':'same'},config_sha256='cfg',rank=rank,world_size=4,
                          plans_checked=10,coverage_required=True,augmented_pose_rows=1,
                          peak_group_tensor_bytes=100,group_budget_bytes=1024)
                Path(str(path)+'.manifest.json').write_text(json.dumps(meta))
        self.assertTrue(compare(directory,audit_dir)['accepted'])
        path=directory/'on/rank3/steps.json'
        good=path.read_text(); records=json.loads(good); records[0].pop('performance')
        path.write_text(json.dumps(records))
        with self.assertRaisesRegex(ValueError,'provenance'):
            compare(directory,audit_dir)
        path.write_text(good)
        path=audit_dir/'data_prefetch_rank3.json'; records=json.loads(path.read_text())
        records[0]['plan_sha256']='wrong'; path.write_text(json.dumps(records))
        with self.assertRaisesRegex(ValueError,'CPU audit'):
            compare(directory,audit_dir)

    def test_replay_mode_is_one_step_and_wrapper_is_off_off_on(self):
        from replay_compare import replay_order
        self.assertEqual(replay_order(), [('off1','off'),('off2','off'),('on','prefetch')])
        # Exercise argument parsing without CUDA, model load or filesystem outputs.
        import launch
        with patch.object(sys,'argv',['launch.py','--help']), self.assertRaises(SystemExit) as caught:
            launch.main()
        self.assertEqual(caught.exception.code,0)
        self.assertIn("'replay'", (ROOT/'out/kit_profile/launch.py').read_text())
        wrapper=(ROOT/'out/kit_profile/replay.sh').read_text()
        self.assertIn('off1:off off2:off on:prefetch',wrapper)
        self.assertIn('--mode replay',wrapper)
        self.assertIn('RESUME_PIN',wrapper)
        self.assertNotIn('895s',wrapper)

if __name__ == '__main__':
    unittest.main(verbosity=2)
