"""Fourth-review defects exercised against either the snapshot or delivered kits."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get('SO_KIT_BUNDLE', ROOT/'out'))
TREE = ROOT/'work/b21_final/work/tree_r1'
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
    LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'), TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path[:0] = [str(BUNDLE/'kit_timing'), str(BUNDLE/'kit_profile'), str(TREE)]
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from tests.so_helpers import root, inputs, compact_processor, plan, reset_switches


class Round4Kits(unittest.TestCase):
    def setUp(self):
        reset_switches(self)

    def test_real_portrait_grids_and_observed_maximum(self):
        from audit import Coverage
        log = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look2.out')
        # These are the four real 72-row production shape records in the dispatch.
        # Count LF only; eight carriage returns are also split by str.splitlines().
        lines = log.read_bytes().decode().split("\n")
        coverage = Coverage(); seen = []; portraits = []
        for number,step in zip((694,698,702,706),(100,101,102,200)):
            self.assertTrue(lines[number-2].startswith(f'STEP {step} '))
            records = json.loads(lines[number-1].strip().removeprefix('shapes '))
            grids = [grid for _, _, values in records for grid in values]
            self.assertEqual(len(records), 72)
            portraits.append(grids.count([32,26,20])); seen.extend(grids)
            coverage.observe({'video_grid_thw':torch.tensor(grids)})
        self.assertEqual(portraits, [5,7,9,6])
        self.assertIn(coverage.max_grid, seen)
        self.assertEqual(coverage.max_grid, [32,20,26])  # Stable first-observed tie.
        self.assertEqual(coverage.grid_rows, 288)
        for grid in ([33,20,26], [32,20,30], [32,0,26]):
            with self.assertRaisesRegex(ValueError, 'grid cap'):
                coverage.observe({'video_grid_thw':torch.tensor([grid])})
        coverage.observe({'image_grid_thw':torch.tensor([[1,26,20],[1,20,26],[32,10,52]])})

    def test_replay_accepts_outside_interval_under_fixed_pooled_bound(self):
        from replay_compare import loss_acceptance
        decision = loss_acceptance([1.,2.], [1.125,2.], [1.1875,2.125])
        self.assertTrue(decision['accepted'])
        self.assertEqual(decision['off_max_abs'], .125)
        self.assertEqual(decision['threshold'], .25)
        self.assertEqual(decision['multiplier'], 2.)
        self.assertTrue(loss_acceptance([1.],[1.125],[1.25])['accepted'])
        self.assertFalse(loss_acceptance([1.],[1.125],[1.250001])['accepted'])
        self.assertTrue(loss_acceptance([1.],[1.],[1.])['accepted'])
        self.assertFalse(loss_acceptance([1.],[1.],[1.000001])['accepted'])
        self.assertFalse(loss_acceptance([0.],[0.],[-0.])['accepted'])
        self.assertFalse(loss_acceptance([1.],[1.125],[float('nan')])['accepted'])

    def test_grid_maximum_is_not_a_per_dimension_envelope(self):
        from audit import Coverage
        coverage=Coverage()
        coverage.observe({'video_grid_thw':torch.tensor([[1,20,26],[32,16,12]])})
        self.assertEqual(coverage.max_grid,[32,16,12])

    def test_plan_writes_trainer_prepared_receipt_and_encodes_pointing_weights(self):
        import write_plan
        directory = root(); raw = inputs(directory)
        (directory/'manifest.json').write_text('{}')
        raw['model'] = run.file_pin(directory/'manifest.json')
        cfg = dict(training_mode='final', align={'cam':{'layer':'final'}},
                   pointing_weights={'decision':5.,'row_mean':2.})
        for name, value in [('raw.json',raw), ('checkpoint.json',dict(schema='c1-checkpoint-v1',
                step=200,binding={'world_size':1}))]:
            (directory/name).write_text(json.dumps(value))
        cfg['preparation'] = run.file_pin(directory/'raw.json')
        (directory/'config.json').write_text(json.dumps(cfg))
        (directory/'pin.json').write_text(json.dumps(run.file_pin(directory/'checkpoint.json')))
        merged = dict(raw, align=cfg['align'], pointing_weights=cfg['pointing_weights'],
                      camera={'override_proof':7}, model_label='Qwen_fixture delta_rule gateddelta',
                      path_fixture='quoted_"_backslash_\\_control_\r_unicode_δ')
        args = ['write_plan.py','--tree',str(TREE),'--config',str(directory/'config.json'),
            '--receipt',str(directory/'raw.json'),'--resume-pin',str(directory/'pin.json'),
            '--steps','10','--out',str(directory/'plan.json')]
        recipe={'world_size':1,'reference_world_size':2,'mix':{'pointing':2}}
        row_plan=[('pointing',[0]),('pointing',[1])]
        with patch.object(sys,'argv',args), patch.object(run,'prepared',return_value=(merged,{})) as prepare, \
                patch.object(run,'recipe_for',return_value=recipe), \
                patch.object(run.data,'mixed_indices',return_value=iter([row_plan]*10)):
            write_plan.main()
        prepare.assert_called_once_with(cfg)
        receipt_path = directory/'prepared_receipt.json'
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt, merged)
        from privacy import WORDS
        self.assertFalse(WORDS.search(receipt_path.read_text()))
        self.assertEqual(json.loads((directory/'plan.json').read_text())['receipt_sha256'],
                         run.file_pin(receipt_path)['sha256'])
        from data_only import descriptor_for
        with patch.object(run,'recipe_for',return_value={}):
            self.assertEqual(descriptor_for(run,cfg,receipt).align_settings, cfg['align'])
        rows = run.Rows(receipt,compact_processor())
        try:
            batch, _, _ = rows.get('pointing',0)
            self.assertIn('aux_token_weights',batch)
            self.assertEqual(batch['aux_token_weights'].shape,batch['labels'].shape)
        finally:
            rows.close()
        import data_only
        import threading
        (directory/'manifest.json').write_text('{}')
        weights=run.data.pointing_token_weights; threads=[]
        def observe(*args,**kwargs):
            threads.append(threading.current_thread().name)
            return weights(*args,**kwargs)
        for arm in ('off','prefetch'):
            argv=['data_only.py','--tree',str(TREE),'--config',str(directory/'config.json'),
                '--receipt',str(receipt_path),'--manifest',str(directory/'manifest.json'),
                '--plan',str(directory/'plan.json'),'--steps','1','--arm',arm,
                '--out',str(directory/(arm+'.json'))]
            if arm=='prefetch': argv+=['--baseline',str(directory/'off.json')]
            with patch.object(sys,'argv',argv),patch.object(run,'recipe_for',return_value=recipe), \
                    patch.object(run,'processor_for_receipt',return_value=compact_processor()), \
                    patch.object(run.data,'pointing_token_weights',observe):
                data_only.main()
        self.assertEqual(threads.count('MainThread'),2)
        self.assertEqual(sum(n.startswith('c1-row-cpu') for n in threads),2)
        off=json.loads((directory/'off.json').read_text())
        on=json.loads((directory/'prefetch.json').read_text())
        self.assertEqual(off[0]['encoded_row_sha256'],on[0]['encoded_row_sha256'])
        self.assertEqual(off[0]['row_draws'],on[0]['row_draws'])

    def test_failed_coverage_cannot_publish_success_sidecar(self):
        import data_only
        directory = root(); receipt = inputs(directory)
        recipe = {'world_size':1,'reference_world_size':2}
        for name,value in [('receipt.json',receipt),('manifest.json',{}),
            ('config.json',dict(training_mode='final',r1_training={'fixture':True})),
            ('plan.json',dict(start_step=200,world_size=1,plans=[plan()]))]:
            (directory/name).write_text(json.dumps(value))
        receipt['model']=run.file_pin(directory/'manifest.json')
        (directory/'receipt.json').write_text(json.dumps(receipt))
        args=['data_only.py','--tree',str(TREE),'--receipt',str(directory/'receipt.json'),
            '--manifest',str(directory/'manifest.json'),'--config',str(directory/'config.json'),
            '--plan',str(directory/'plan.json'),'--steps','1','--require-coverage',
            '--out',str(directory/'off.json')]
        with patch.object(sys,'argv',args),patch.object(run,'recipe_for',return_value=recipe), \
                patch.object(run,'processor_for_receipt',return_value=compact_processor()):
            with self.assertRaisesRegex(ValueError,'augmented pose'):
                data_only.main()
        self.assertFalse((directory/'off.json.manifest.json').exists())

    def replay_fixture(self):
        from replay_compare import replay_order
        directory=root(); audits=directory/'audits';audits.mkdir()
        for rank in range(4):
            for name,arm in replay_order():
                folder=directory/name/f'rank{rank}';folder.mkdir(parents=True)
                switches=dict(C1_CPU_PREFETCH='1' if arm=='prefetch' else '0',
                              C1_BATCH_METRICS='0',C1_DECODED_CACHE_MIB='0')
                meta=dict(arm=arm,start_step=200,resume={},trainables=[],config_sha256='cfg',
                          binding={},threads={},switches=switches)
                record=dict(step=201,plan_sha256='plan',components={'x':1.},stream_means={'vqa':1.},
                            first_step_micro_losses=[1.],performance=switches)
                for file,value in [('manifest.json',meta),('steps.json',[record]),
                                   ('progress.json',{'stage':'complete'})]:
                    (folder/file).write_text(json.dumps(value))
            for arm in ('off','prefetch'):
                file=audits/f'data_{arm}_rank{rank}.json'
                file.write_text(json.dumps([dict(plan_sha256='plan',encoded_row_sha256=['same'],
                    row_draws=[['vqa',0,0]],global_rng_unchanged=True)]*10))
                meta=dict(start_step=200,resume={},config_sha256='cfg',rank=rank,world_size=4,
                    plans_checked=10,coverage_required=True,augmented_pose_rows=1,grid_rows=1,
                    augmentation_threads=['c1-row-cpu_0'] if arm=='prefetch' else ['MainThread'],
                    peak_group_tensor_bytes=10,group_budget_bytes=1024)
                Path(str(file)+'.manifest.json').write_text(json.dumps(meta))
        return directory,audits

    def test_replay_rejects_missing_grids_in_existing_sidecar(self):
        from replay_compare import compare
        directory,audits=self.replay_fixture()
        self.assertTrue(compare(directory,audits)['accepted'])
        path=audits/'data_prefetch_rank3.json.manifest.json'
        meta=json.loads(path.read_text());meta['grid_rows']=0;path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'CPU audit'):
            compare(directory,audits)

    def test_replay_rejects_main_thread_augmentation_in_existing_sidecar(self):
        from replay_compare import compare
        directory,audits=self.replay_fixture()
        path=audits/'data_prefetch_rank3.json.manifest.json'
        meta=json.loads(path.read_text());meta['augmentation_threads']=['MainThread']
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'CPU audit'):
            compare(directory,audits)

    def test_numeric_continuation_rules_are_operational(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        for text in ('start_step + 1', 'components', 'stream_means', 'off1', 'off2',
                     '2 ×', 'updates 2–21', 'last 20', 'strictly below', 'next checkpoint'):
            self.assertIn(text,note)

    def test_coordinator_pass_is_current(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        self.assertIn('31 tests',note); self.assertIn('880.158',note)
        meta=json.loads((BUNDLE/'ARTIFACTS.json').read_text())
        self.assertIn('12:55:19',meta['coordinator_gloo'])
        self.assertNotIn('requires lane execution',meta['coordinator_gloo'])

    def test_replay_variables_are_explicit(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        self.assertIn('REPLAY_OUT="$AUDIT_DIR/replay"',note)
        self.assertIn('REPLAY_METRICS=0',note)
        self.assertNotIn('REPLAY_METRICS="${C1_BATCH_METRICS:-0}"',note)

    def test_fallback_field_is_optional_when_off(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        self.assertIn('must not require `C1_CPU_PREFETCH_FALLBACK`',note)

    def test_runtime_respects_measured_startup_floor(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        self.assertIn('50–75 minutes',note)
        self.assertIn('8.7',note)
        self.assertNotIn('30–60 minutes',note)


if __name__ == '__main__':
    unittest.main(verbosity=2)
