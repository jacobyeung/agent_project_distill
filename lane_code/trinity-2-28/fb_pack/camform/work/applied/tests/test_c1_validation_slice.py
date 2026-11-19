"""Held-out CP1 pose admission, collective reads and the best-pose pointer."""
import copy
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1_sweep import recipe_for
from tests.test_c1_pose_mix_division import dense, database, dump
from tests.test_carrier_c1_final import final_fixture
from tests.test_fsdp import SOCKETS


def directory():
    return Path(tempfile.mkdtemp(prefix='cp1_validation_', dir=os.environ.get('LANE_TEST_OUTPUT')))


class ValidationRows:
    def __init__(self, batch, targets):
        self.batch, self.targets, self.calls, self.bad = batch, targets, [], None

    def validation_count(self):
        return 3

    def validation_get(self, index):
        self.calls.append(index)
        if index == self.bad:
            raise ValueError('bad row')
        return self.batch, self.targets, dict(dataset='d3', scene=f's{index//2}')


def artifacts(root, steps):
    for step in steps:
        run.write(root/f'm{step}'/'artifact.json', dict(step=step))


def _validation_worker(rank, root):
    torch.set_num_threads(1)
    root = Path(root)
    dist.init_process_group('gloo', init_method='file://' + str(root/'rendezvous'), rank=rank, world_size=2)
    try:
        model, batch, targets = final_fixture()
        rows = ValidationRows(batch, targets)
        wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
        modes = []
        hook = wrapped.register_forward_pre_hook(lambda module, args: modes.append((module.training, torch.is_grad_enabled())))
        first = run.validation_read(wrapped, rows, rank, torch.device('cpu'), 10, root, True)
        for key in ('weight_trans', 'weight_rot', 'weight_focal', 'weight_gravity', 'weight_scale'):
            model.auxiliary_heads.pose.settings[key] *= .5
        second = run.validation_read(wrapped, rows, rank, torch.device('cpu'), 20, root, True)
        calls = list(rows.calls)
        reused = run.validation_read(wrapped, rows, rank, torch.device('cpu'), 20, root, True)
        assert rows.calls == calls
        tied = run.validation_read(wrapped, rows, rank, torch.device('cpu'), 30, root, True)
        rows.bad = 1 if rank == 1 else None
        skipped = run.validation_read(wrapped, rows, rank, torch.device('cpu'), 40, root, True)
        hook.remove()
        run.write(root/f'rank{rank}.json', dict(first=first, second=second, reused=reused, tied=tied,
                  skipped=skipped, calls=calls, training=wrapped.training, modes=modes))
    finally:
        dist.destroy_process_group()


class ValidationPreparation(unittest.TestCase):
    def setUp(self):
        self.root = directory()
        self.division = dump(self.root/'division.json', dict(train_scenes=['d3/train'], heldout_scenes=['d3/a', 'd3/b']))
        self.rows = dump(self.root/'rows.json', dict(schema='pose-stream-a3-v1', count=4,
            database=database(self.root/'rows.sqlite', [dense('d3', 'b'), dense('d3', 'train'),
                                                       dense('d3', 'a'), dense('d3', 'b')])))
        self.slice = dump(self.root/'slice.json', dict(schema='cp1-pose-validation-slice-v1',
                                                       scenes=['d3/a', 'd3/b'], count=2))
        self.cfg = dict(preparation_output=str(self.root/'prep'), validation=dict(rows=self.rows, slice=self.slice))

    def prepare(self):
        with mock.patch.object(run, 'pose_row_check') as check:
            result = run.prepare_validation(self.cfg, self.division)
        return result, check

    def test_selects_in_database_order_with_pinned_receipts(self):
        result, check = self.prepare()
        self.assertEqual(result, dict(rows=self.rows, slice=self.slice, database=run.load(self.rows['path'])['database'],
                                     count=3, scenes=2, indices=run.file_pin(self.root/'prep'/'validation_indices.json')))
        self.assertEqual(run.load(run.pinned(result['indices'])), [0, 2, 3])
        self.assertEqual(check.call_count, 3)

    def test_train_unknown_and_empty_scenes_are_refused(self):
        for scene, message in (('d3/train', 'heldout_scenes'), ('d3/unknown', 'heldout_scenes'),
                               ('d3/empty', 'no selected row')):
            with self.subTest(scene=scene):
                self.cfg['validation']['slice'] = dump(self.root/f'{scene.split("/")[-1]}.json',
                    dict(schema='cp1-pose-validation-slice-v1', scenes=[scene], count=1))
                division = dump(self.root/f'div_{scene.split("/")[-1]}.json',
                    dict(train_scenes=['d3/train'], heldout_scenes=['d3/a', 'd3/b', 'd3/empty']))
                with self.assertRaisesRegex(ValueError, message):
                    run.prepare_validation(self.cfg, division)

    def test_selected_row_failure_is_not_filtered_away(self):
        with mock.patch.object(run, 'pose_row_check', side_effect=ValueError('invalid pose')):
            with self.assertRaisesRegex(ValueError, 'Validation row 0.*invalid pose'):
                run.prepare_validation(self.cfg, self.division)
        with self.assertRaises(ValueError):
            run.prepare_validation(self.cfg, self.division)

    def test_sparse_rows_do_not_admit_a_scene(self):
        row, target = dense('d3', 'a')
        target['camera_mask'][0] = False
        self.cfg['validation']['rows'] = dump(self.root/'sparse.json', dict(schema='pose-stream-a3-v1', count=2,
            database=database(self.root/'sparse.sqlite', [(row, target), dense('d3', 'b')])))
        with self.assertRaisesRegex(ValueError, 'no selected row'):
            self.prepare()

    def preparation_fixture(self):
        spec = dump(self.root/'mix.json', dict(schema='c1-pose-mix-v1'))
        model = dump(self.root/'model.json', dict(kind='base', base_identity='fixture', root='/fixture/snapshot',
                                                files={'config.json': 'config'}))
        order = dump(self.root/'order.json', [])
        entry = dict(kind='mix', receipt=spec, count=5, order=order, sources=[])
        pose = dict(count=5, model=model, inputs=dict(division=self.division),
                    settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                                  camera=dict(point_depth={})))
        cfg = {**self.cfg, 'training_mode': 'final', 'base_identity': 'fixture', 'streams': {'pose': spec},
               'carrier_placement': run.data.C1_A, 'recipe': {}, 'exclusions': {}}
        with mock.patch.object(run, 'validate'), mock.patch.object(run, 'authenticate', return_value='commit'), \
                mock.patch.object(run.routing, 'load_exclusions', return_value={'d0/test'}), \
                mock.patch('student_pilot.c1_pose_mix.prepare', return_value=(entry, pose)), \
                mock.patch('student_pilot.students.get_student', return_value=dict(snapshot=Path('/fixture/snapshot'), config_sha256='config')), \
                mock.patch.object(run, 'pose_row_check'):
            receipt = run.prepare(cfg)
        cfg['preparation'] = run.file_pin(self.root/'prep'/'receipt.json')
        return cfg, receipt

    def test_prepare_keeps_validation_out_of_training_counts(self):
        cfg, receipt = self.preparation_fixture()
        self.assertEqual(receipt['division'], self.division)
        self.assertEqual(set(receipt['streams']), {'pose'})
        self.assertEqual(receipt['streams']['pose']['count'], 5)
        self.assertEqual(receipt['validation']['count'], 3)
        self.assertEqual(receipt['validation']['slice'], cfg['validation']['slice'])

    def test_prepared_refuses_changed_pins_and_authenticates_validation_files(self):
        cfg, receipt = self.preparation_fixture()
        with mock.patch.object(run, 'validate'), mock.patch.object(run, 'authenticate', return_value='commit'), \
                mock.patch('student_pilot.c1_pose_mix.validate_spec'):
            self.assertEqual(run.prepared(cfg)[0]['validation'], receipt['validation'])
            for name in ('rows', 'slice'):
                changed = copy.deepcopy(cfg)
                changed['validation'][name]['sha256'] = '0'*64
                with self.assertRaisesRegex(ValueError, 'validation pins differ'):
                    run.prepared(changed)
            for name in ('database', 'indices'):
                pin = receipt['validation'][name]
                path = Path(pin['path'])
                with path.open('ab') as handle:
                    handle.write(b'\n')
                with self.assertRaisesRegex(ValueError, 'changed pinned input'):
                    run.prepared(cfg)
                pin['sha256'] = run.sha256(path)
                source = run.load(cfg['validation']['rows']['path'])
                if name == 'database':
                    source['database'] = pin
                    self.cfg['validation']['rows'] = dump(self.root/'repinned.json', source)
                    cfg['validation']['rows'] = self.cfg['validation']['rows']
                    receipt['validation']['rows'] = cfg['validation']['rows']
                    receipt['config_sha256'] = run.identity(cfg)
                cfg['preparation'] = dump(self.root/f'prep_{name}.json', receipt)

    def test_validation_config_is_optional_and_requires_exact_pins(self):
        cfg = dict(schema='carrier-c1-run-v1', init='base', parallel='fsdp', all_frames=True,
                   carrier_placement=run.data.C1_A, streams=dict(pose={}, vqa={}, pointing={}))
        cfg['recipe'] = recipe_for(cfg)
        raw_before = run.digest(cfg)
        before = run.identity(cfg)
        run.validate(cfg)
        self.assertEqual(raw_before, run.digest(cfg))
        from trace_format.contracts import HEADING_PLANE_MIN_DEFAULT
        self.assertEqual(before, run.digest({**cfg, 'heading_plane_min':HEADING_PLANE_MIN_DEFAULT}))
        run.validate({**cfg, 'validation': self.cfg['validation']})
        self.assertEqual(before, run.identity(cfg))
        for bad in (None, {}, {'rows': self.rows}, {**self.cfg['validation'], 'other': {}},
                    {'rows': {'path': 'relative', 'sha256': 'x'}, 'slice': self.slice}):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'validation needs'):
                run.validate({**cfg, 'validation': bad})

    def test_rows_use_the_mix_row_encoder_and_selected_indices(self):
        value, _ = self.prepare()
        receipt = dict(streams={}, validation=value, training_mode='final', frame_layout='duplicate')
        model, batch, targets = final_fixture()
        with mock.patch.object(run.data, 'encode', return_value=(batch, targets, {})) as encode:
            rows = run.Rows(receipt, object())
            try:
                self.assertEqual(rows.validation_count(), 3)
                encoded, labels, audit = rows.validation_get(1)
                self.assertIs(encoded, batch)
                self.assertIn('aux_g3t_valid', labels)
                self.assertFalse(bool(labels['aux_g3t_valid'].any()))
                self.assertEqual((audit['dataset'], audit['scene']), ('d3', 'a'))
                self.assertEqual(encode.call_args.args[1]['scene'], 'a')
                self.assertEqual(encode.call_args.kwargs['frame_layout'], 'duplicate')
            finally:
                rows.close()
        empty = run.Rows(dict(streams={}), None)
        self.assertEqual(empty.validation_count(), 0)
        empty.close()


class ValidationRead(unittest.TestCase):
    @unittest.skipUnless(SOCKETS, 'requires local sockets: sandbox denies 127.0.0.1 bind')
    def test_two_rank_fsdp_padding_best_tie_reuse_and_shared_skip(self):
        root = directory()
        artifacts(root, (10, 20, 30, 40))
        mp.spawn(_validation_worker, args=(str(root),), nprocs=2, join=True)
        ranks = [run.load(root/f'rank{rank}.json') for rank in range(2)]
        for rank, result in enumerate(ranks):
            self.assertEqual(result['calls'], ([0, 2]*2 if rank == 0 else [1, 0]*2))
            self.assertTrue(result['training'] and result['reused']['reused'])
            self.assertTrue(all(mode == [False, False] for mode in result['modes']))
            self.assertEqual(result['skipped']['skips'], 1)
        for step in (10, 20, 30):
            summary = run.load(root/f'validation_m{step}.json')
            self.assertEqual((summary['n'], summary['scenes'], summary['skips']), (3, 2, 0))
            self.assertTrue(all(math.isfinite(summary[k]) for k in ('slice_pose_loss', 'rotation_deg', 'fov_deg', 'depth_absrel')))
            self.assertTrue(all(math.isfinite(v) for v in summary['pose_parts'].values()))
            self.assertEqual(summary['pose_metrics']['all']['rot_deg']['n'], 96)
        best = run.load(root/'best_pose.json')
        self.assertLess(ranks[0]['second']['slice_pose_loss'], ranks[0]['first']['slice_pose_loss'])
        self.assertEqual((best['schema'], best['step'], best['criterion']), ('cp1-best-pose-v1', 20, 'slice_pose_loss'))
        self.assertEqual(best['artifact'], run.file_pin(root/'m20'/'artifact.json'))
        self.assertEqual([h['step'] for h in best['history']], [10, 20])

    def test_single_rank_restores_eval_mode_and_keeps_best_on_worse_read(self):
        root = directory()
        artifacts(root, (1, 2, 3, 4))
        model, batch, targets = final_fixture()
        model.eval()
        rows = ValidationRows(batch, targets)
        first = run.validation_read(model, rows, 0, torch.device('cpu'), 1, root, False)
        best_pin = run.file_pin(root/'best_pose.json')
        for key in ('weight_trans', 'weight_rot', 'weight_focal', 'weight_gravity', 'weight_scale'):
            model.auxiliary_heads.pose.settings[key] *= 2
        second = run.validation_read(model, rows, 0, torch.device('cpu'), 2, root, False)
        self.assertEqual(first['n'], 3)
        self.assertGreater(second['slice_pose_loss'], first['slice_pose_loss'])
        self.assertFalse(model.training)
        self.assertEqual(best_pin, run.file_pin(root/'best_pose.json'))
        for key in ('weight_trans', 'weight_rot', 'weight_focal', 'weight_gravity', 'weight_scale'):
            model.auxiliary_heads.pose.settings[key] *= .25
        improved = run.validation_read(model, rows, 0, torch.device('cpu'), 3, root, False)
        best = run.load(root/'best_pose.json')
        self.assertLess(improved['slice_pose_loss'], first['slice_pose_loss'])
        self.assertEqual((best['step'], best['artifact']), (3, run.file_pin(root/'m3'/'artifact.json')))
        self.assertEqual([h['step'] for h in best['history']], [1, 3])
        best_pin = run.file_pin(root/'best_pose.json')
        run.validation_read(model, rows, 0, torch.device('cpu'), 4, root, False)
        self.assertEqual(best_pin, run.file_pin(root/'best_pose.json'))
        calls = list(rows.calls)
        reused = run.validation_read(model, rows, 0, torch.device('cpu'), 4, root, False)
        self.assertTrue(reused['reused'])
        self.assertEqual(rows.calls, calls)
        self.assertIsNone(run.validation_read(model, object(), 0, torch.device('cpu'), 5, root, False))

    def test_corrupt_summary_is_reread_and_reuse_repairs_the_best_pointer(self):
        root = directory()
        artifacts(root, (1, 2))
        model, batch, targets = final_fixture()
        rows = ValidationRows(batch, targets)
        (root/'validation_m1.json').write_text('{"schema": "cp1-pose')
        first = run.validation_read(model, rows, 0, torch.device('cpu'), 1, root, False)
        self.assertEqual((first['n'], run.load(root/'validation_m1.json')['n']), (3, 3))
        self.assertEqual(run.load(root/'best_pose.json')['step'], 1)
        (root/'best_pose.json').rename(root/'best_pose_moved.json')
        calls = list(rows.calls)
        reused = run.validation_read(model, rows, 0, torch.device('cpu'), 1, root, False)
        self.assertTrue(reused['reused'])
        self.assertEqual(rows.calls, calls)
        self.assertEqual(run.load(root/'best_pose.json')['step'], 1)
        self.assertEqual(sorted(p.name for p in root.iterdir() if p.name.startswith('.')), [])
        (root/'validation_m2.json').write_text('[]')
        (root/'best_pose.json').write_text('{"schema": "cp1-best')
        second = run.validation_read(model, rows, 0, torch.device('cpu'), 2, root, False)
        self.assertEqual((second['n'], run.load(root/'validation_m2.json')['step']), (3, 2))
        self.assertEqual(run.load(root/'best_pose.json')['step'], 2)

    def test_gate_replay_skips_a_truncated_metrics_line(self):
        root = directory()
        line = lambda step: run.json.dumps(dict(step=step, ranks=[dict(head_metrics=dict(rotation_deg=float(step)))]))
        (root/'metrics_1.jsonl').write_text(line(1) + '\n' + line(2) + '\n' + line(3)[:17])
        seen = []
        run.replay_gates(root, 5, mock.Mock(update=seen.append))
        self.assertEqual(seen, [dict(rotation_deg=1.), dict(rotation_deg=2.)])

    def test_forward_error_restores_training_mode(self):
        model, batch, targets = final_fixture()
        with mock.patch.object(model, 'forward', side_effect=RuntimeError('read failed')):
            with self.assertRaisesRegex(RuntimeError, 'read failed'):
                run.validation_read(model, ValidationRows(batch, targets), 0, torch.device('cpu'), 1, directory(), False)
        self.assertTrue(model.training)

    def test_bad_rows_skip_without_forward_or_best_pointer(self):
        root = directory()
        model, batch, targets = final_fixture()
        rows = ValidationRows(batch, {**targets, 'aux_camera_mask': torch.zeros_like(targets['aux_camera_mask'])})
        with mock.patch.object(model, 'forward', side_effect=AssertionError('must skip')):
            summary = run.validation_read(model, rows, 0, torch.device('cpu'), 1, root, False)
        self.assertEqual((summary['n'], summary['skips'], summary['slice_pose_loss']), (0, 3, None))
        self.assertFalse((root/'best_pose.json').exists())
        self.assertTrue(model.training)

    def test_native_loop_reads_after_export_and_smoke_never_reads(self):
        events = []
        cfg = dict(recipe={**run.RECIPE, 'milestones': [800]})
        rows = mock.Mock()
        rows.validation_count.return_value = 3
        with mock.patch.object(run, 'optimize_step', return_value=({'wall_seconds': 0.}, None)), \
                mock.patch.object(run, 'checkpoint'), mock.patch.object(run, 'existing_export', return_value=False), \
                mock.patch.object(run, 'export', side_effect=lambda *a: events.append('export')), \
                mock.patch.object(run, 'validation_read', side_effect=lambda *a: events.append('validation') or {'n': 3}) as read:
            report = run.run_steps(None, None, None, rows, dict(pose=9, vqa=9, pointing=9), directory(), cfg, {},
                                   torch.device('cpu'), start_step=799, distributed=False)
            self.assertEqual(events, ['export', 'validation'])
            info = report['steps'][0][0]
            self.assertEqual(info['validation'], {'n': 3})
            self.assertGreaterEqual(info['validation_seconds'], 0.)
            read.reset_mock()
            run.run_steps(None, None, None, rows, dict(pose=9, vqa=9, pointing=9), directory(), cfg, {},
                          torch.device('cpu'), start_step=799, smoke_steps=1, distributed=False)
            read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
