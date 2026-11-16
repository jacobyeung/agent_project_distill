"""CPU authentication of native non-GX CTRL references with separate preparation."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from student_pilot import carrier_c1_run as run
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_gx_carrier import root, reference_pin
from tests.test_gx_s6 import metric_file, paired_cfg
from tests.test_gx_s7 import replace_json


class ProductionCtrlReference(unittest.TestCase):
    def fixture(self, world=8, full_config=False):
        reference = root()
        cfg = paired_cfg(root(), reference)
        cfg.update(world_size=world, row_start_step=800)
        cfg['geometry_online']['fail_fast']['reference_binding'] = reference_pin()
        cfg['recipe'] = run.recipe_for(cfg)
        source = dict(path='/fixture/source/receipt.json', sha256='1'*64)
        cfg['streams'] = dict(pose=source)
        ref = copy.deepcopy(cfg)
        ref.pop('geometry_online')
        ref.update(world_size=8, output=str(reference))
        ref['recipe'] = run.recipe_for(ref)
        stream = dict(receipt=source, database=dict(path='/fixture/rows.sqlite', sha256='2'*64),
                      count=283200, source_count=321152,
                      indices=dict(path='/fixture/ctrl/pose_indices.json', sha256='3'*64))
        ctrl = dict(schema='c1-preparation-v1', config_sha256=run.identity(ref),
                    trainer_commit='f2463e26c5786967d60f841daaa79c8f769c7a4e',
                    streams=dict(pose=stream), training_mode='pose_only', row_start_step=800,
                    frame_layout='duplicate', depth_enabled=False, recipe=ref['recipe'])
        own = copy.deepcopy(ctrl)
        own.update(config_sha256=run.identity(cfg), trainer_commit='GX',
                   geometry_online=cfg['geometry_online'], recipe=cfg['recipe'])
        # Native preparation writes its own indices file; equal inventory hashes
        # authenticate the same rows despite these different file locations.
        own['streams']['pose']['indices']['path'] = '/fixture/gx/pose_indices.json'
        write(reference/'receipt.json', ctrl)
        # Keep the own receipt in the run directory for pinned-read regressions.
        write(Path(cfg['output'])/'receipt.json', own)
        cfg['preparation'] = file_pin(Path(cfg['output'])/'receipt.json')
        ref['preparation'] = file_pin(reference/'receipt.json')
        bound = dict(config_sha256=run.identity(ref) if full_config else
                     'e42bbb822990030b8c9ab23cf91175e4a9a25480f22f3819ffc51090a9bb53ad',
                     preparation=ref['preparation'], trainer_commit=ctrl['trainer_commit'], world_size=8)
        write(reference/'binding.json', bound)
        self.repin_binding(cfg, reference)
        attempt = dict(binding=bound, resume=None, first_step=1, network=None, init=None, export_of=None)
        if full_config:
            attempt['config'] = ref
        write(reference/'attempt_119930.json', attempt)
        records = metric_file(reference, '119930', range(1, 4))
        write(reference/'run_119930.json', dict(schema='c1-run-v1', status='PASS', first_step=1,
              last_step=3, world_size=8, steps=[r['ranks'] for r in records], stopped_for_resume=False))
        return cfg, reference

    def repin_binding(self, cfg, reference):
        bound = load(reference/'binding.json')
        cfg['geometry_online']['fail_fast']['reference_binding'] = dict(
            sha256=file_pin(reference/'binding.json')['sha256'],
            config_sha256=bound['config_sha256'], trainer_commit=bound['trainer_commit'])

    def change_preparation(self, cfg, reference, side, change):
        path = reference/'receipt.json' if side == 'reference' else Path(cfg['preparation']['path'])
        receipt = load(path)
        change(receipt)
        replace_json(path, receipt)
        if side == 'own':
            cfg['preparation'] = file_pin(path)
        else:
            bound = load(reference/'binding.json')
            bound['preparation'] = file_pin(path)
            replace_json(reference/'binding.json', bound)
            attempt = load(reference/'attempt_119930.json')
            attempt['binding'] = bound
            replace_json(reference/'attempt_119930.json', attempt)
            self.repin_binding(cfg, reference)

    def refuse_before_cuda(self, cfg):
        with patch.object(run, 'validate'), patch.object(torch.cuda, 'is_available') as cuda:
            with self.assertRaises(ValueError):
                run.train(cfg)
            cuda.assert_not_called()

    def test_native_production_shape_at_gx_world_four_and_eight(self):
        for world in (4, 8):
            for full in (False, True):
                with self.subTest(world=world, full_config=full):
                    cfg, reference = self.fixture(world, full)
                    bound = load(reference/'binding.json')
                    self.assertNotEqual(cfg['preparation'], bound['preparation'])
                    self.assertNotIn('binding', load(reference/'run_119930.json'))
                    self.assertEqual('config' in load(reference/'attempt_119930.json'), full)
                    before = copy.deepcopy(cfg)
                    self.assertEqual(sorted(run.gx_reference(cfg, 3)), [1, 2, 3])
                    self.assertEqual(cfg, before)

    def test_each_row_determining_field_refuses_on_either_side(self):
        mutations = {
            'schema': lambda r: r.update(schema='foreign'),
            'stream_names': lambda r: r['streams'].update(vqa=copy.deepcopy(r['streams']['pose'])),
            'receipt_hash': lambda r: r['streams']['pose']['receipt'].update(sha256='a'*64),
            'database_hash': lambda r: r['streams']['pose']['database'].update(sha256='a'*64),
            'indices_hash': lambda r: r['streams']['pose']['indices'].update(sha256='a'*64),
            'count': lambda r: r['streams']['pose'].update(count=283199),
            'count_type': lambda r: r['streams']['pose'].update(count=283200.0),
            'source_count': lambda r: r['streams']['pose'].update(source_count=321151),
            'missing_indices': lambda r: r['streams']['pose'].pop('indices'),
            'frame_bundle': lambda r: r['streams']['pose'].update(
                frame_bundle=dict(path='/fixture/frames.tar', sha256='a'*64)),
            'training_mode': lambda r: r.update(training_mode='mixed'),
            'row_start_step': lambda r: r.update(row_start_step=0),
            'seed': lambda r: r['recipe'].update(seed=18),
            'seed_type': lambda r: r['recipe'].update(seed=float(r['recipe']['seed'])),
            'mix': lambda r: r['recipe'].update(mix=['vqa']*len(r['recipe']['mix'])),
            'global_batch': lambda r: r['recipe'].update(global_batch=16),
            'world_size': lambda r: r['recipe'].update(world_size=2),
            'frame_layout': lambda r: r.update(frame_layout='paired'),
            'frame_pair_gap_seconds': lambda r: r.update(frame_pair_gap_seconds=.5),
        }
        for side in ('own', 'reference'):
            for field, change in mutations.items():
                with self.subTest(side=side, field=field):
                    cfg, reference = self.fixture()
                    self.change_preparation(cfg, reference, side, change)
                    self.refuse_before_cuda(cfg)

    def test_both_preparation_files_are_sha_checked(self):
        for side in ('own', 'reference'):
            with self.subTest(side=side):
                cfg, reference = self.fixture()
                path = Path(cfg['preparation']['path']) if side == 'own' else reference/'receipt.json'
                with path.open('a') as handle:
                    handle.write(' ')
                self.refuse_before_cuda(cfg)

    def test_legacy_run_requires_matching_attempt_binding(self):
        for bad in ('missing', 'foreign', 'null'):
            with self.subTest(bad=bad):
                cfg, reference = self.fixture()
                path = reference/'attempt_119930.json'
                attempt = load(path)
                if bad == 'missing':
                    attempt.pop('binding')
                elif bad == 'null':
                    attempt['binding'] = None
                else:
                    attempt['binding']['trainer_commit'] = 'foreign'
                replace_json(path, attempt)
                self.refuse_before_cuda(cfg)

    def test_run_job_steps_and_complete_metrics_must_agree(self):
        for failure in ('job', 'attempt_job', 'orphan_job', 'first_step', 'last_step',
                        'attempt_first', 'attempt_last', 'steps', 'short_metrics',
                        'late_metrics', 'missing_metrics', 'null_binding', 'foreign_binding'):
            with self.subTest(failure=failure):
                cfg, reference = self.fixture()
                path = reference/'run_119930.json'
                report = load(path)
                if failure == 'job':
                    report['job_id'] = '119931'
                elif failure in ('attempt_job', 'attempt_first', 'attempt_last'):
                    ap = reference/'attempt_119930.json'
                    attempt = load(ap)
                    attempt[{'attempt_job': 'job_id', 'attempt_first': 'first_step',
                             'attempt_last': 'last_step'}[failure]] = 2
                    replace_json(ap, attempt)
                elif failure == 'orphan_job':
                    write(reference/'run_119931.json', report)
                elif failure in ('first_step', 'last_step'):
                    report[failure] = 2
                elif failure == 'steps':
                    report['steps'][0][0]['step'] = 2
                elif failure in ('short_metrics', 'late_metrics'):
                    metric_file(reference, '119930', [1, 2] if failure == 'short_metrics' else [2, 3])
                elif failure == 'missing_metrics':
                    # Retain the file outside the native metrics pattern, without deletion.
                    (reference/'metrics_119930.jsonl').rename(reference/'retained_metrics.jsonl')
                elif failure == 'null_binding':
                    report['binding'] = None
                else:
                    report['binding'] = {**load(reference/'binding.json'), 'trainer_commit': 'foreign'}
                replace_json(path, report)
                self.refuse_before_cuda(cfg)

    def test_stream_order_and_nested_bundle_hashes_are_compared(self):
        cfg, reference = self.fixture()
        receipt = load(reference/'receipt.json')
        other = copy.deepcopy(receipt)
        for value in (receipt, other):
            value['streams']['second'] = copy.deepcopy(value['streams']['pose'])
        other['streams'] = dict(reversed(list(other['streams'].items())))
        self.assertNotEqual(run.gx_preparation_rows(receipt), run.gx_preparation_rows(other))
        other = copy.deepcopy(receipt)
        for value in (receipt, other):
            value['streams']['pose']['frame_bundles'] = [dict(path='/fixture/frames.tar', sha256='a'*64)]
        other['streams']['pose']['frame_bundles'][0]['sha256'] = 'b'*64
        self.assertNotEqual(run.gx_preparation_rows(receipt), run.gx_preparation_rows(other))


if __name__ == '__main__':
    unittest.main()
