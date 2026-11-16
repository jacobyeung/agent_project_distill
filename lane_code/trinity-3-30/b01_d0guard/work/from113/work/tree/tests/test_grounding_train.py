"""Retained native-model CPU training, two-rank replay and calibration fixtures."""
import itertools
import json
import os
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch
from torch import distributed as dist
import torch.multiprocessing as mp

from student_pilot import grounding_features, grounding_train as train
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_grounding_features import tiny_clip


def fake_units(path, grid, vocab, **kwargs):
    rgb_wh = path['rgb_wh'] if isinstance(path, dict) else [320, 240]
    path = path['path'] if isinstance(path, dict) else path
    with np.load(path, allow_pickle=False) as data:
        inst = data['inst']
        present = (inst == 1).any((1, 2))
        scene, qid = str(data['scene']), str(data['qid'])
    h, w = 2 * grid[0], 2 * grid[1]
    presence = np.stack([present, np.zeros(32, bool)]).astype(np.float32)
    mass = np.zeros((2, 32, h, w), np.float32)
    mass[0, present, :, :max(1, w // 2)] = 1 / (h * max(1, w // 2))
    point = np.full((2, 32, 2), np.nan, np.float32)
    point[0, present] = [250, 500]
    largest = np.full((2, 32), -1, np.int32); largest[0, present] = 1
    return SimpleNamespace(scene=scene, qid=qid, labels=['chair', 'table'], kind=['visible', 'clip_absent'],
                           presence=presence, mass=mass, point=point, largest=largest,
                           _inst=inst, _label_ids={'chair': [1]}, _rgb_wh=rgb_wh)


def runtime():
    model, batch = tiny_clip(h=2, w=2)
    processor = SimpleNamespace(tokenizer=SimpleNamespace(encode=lambda text, **kwargs: [8, 9] if text == 'chair' else [10]))
    return (model, processor, {}), batch


def prompt(batch):
    def make(processor, row, native):
        copied = dict(batch)
        copied['pixel_values_videos'] = batch['pixel_values_videos'] + int(row['qid'].split('_')[-1]) * .01
        return copied
    return make


def fixture(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    entries = []
    for i in range(5):
        path = root / f'clip_{i}.npz'
        inst = np.full((32, 240, 320), -1, np.int16)
        inst[:16, :, :160] = 1
        with path.open('xb') as stream:
            np.savez_compressed(stream, inst=inst, used=np.ones(32, bool), ids=np.array([1], np.int32),
                                labels=np.array(['chair']), scene=f'scene_{i}', qid=f'clip_{i}')
        entries.append(dict(path=str(path), sha256=file_pin(path)['sha256'], scene=f'scene_{i}', qid=f'clip_{i}',
                            frame_indices=list(range(32)), frame_sha256=['a' * 64] * 32, rgb_wh=[320, 240]))
    write(root / 'artifact.json', {'schema': 'synthetic-base-fixture'})
    cfg = dict(output=str(root / 'run'), steps=6, world_size=2, device='cpu', num_workers=0,
               wall_minutes=180, checkpoint_minutes=100, eval_every=0, fail_fast_minutes=1000,
               calibration_clips=1, base_artifact=file_pin(root / 'artifact.json'), trainer_commit='synthetic-fixture',
               head=dict(dim=16, heads=4, blocks=1, text_layers=1, dropout=.1))
    return cfg, dict(train=entries[:4], val=entries[4:], vocab=['table'])


def distributed_run(rank, root, cfg, index):
    torch.set_num_threads(1)
    os.environ['RANK'], os.environ['WORLD_SIZE'] = str(rank), '2'
    os.environ['GLOO_SOCKET_IFNAME'] = 'lo'
    dist.init_process_group('gloo', init_method='file://' + str(Path(root) / 'rendezvous'), rank=rank, world_size=2)
    try:
        rt, batch = runtime()
        with mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)), mock.patch(
                'student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)), mock.patch(
                'student_pilot.grounding_targets.units_for_clip', side_effect=fake_units):
            uninterrupted = {**cfg, 'output': str(Path(root) / 'uninterrupted')}
            interrupted = {**cfg, 'output': str(Path(root) / 'interrupted')}
            train.train(uninterrupted, runtime=rt, index=index)
            train.train(interrupted, runtime=rt, index=index, stop_after_steps=4)
            train.train(interrupted, runtime=rt, index=index)
    finally:
        dist.destroy_process_group()


class Trainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        runtime()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='gh_train_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.cfg, self.index = fixture(self.root)

    def contexts(self, batch):
        return (mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)),
                mock.patch('student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)),
                mock.patch('student_pilot.grounding_targets.units_for_clip', side_effect=fake_units))

    def test_two_rank_train_checkpoint_resume_matches_uninterrupted(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except PermissionError as exc:
            self.skipTest(f'The execution sandbox prohibits gloo sockets: {exc}')
        self.add_ignored_clip(n_used=0)
        mp.start_processes(distributed_run, args=(str(self.root), self.cfg, self.index), nprocs=2,
                           join=True, start_method='fork')
        expected = [load_line for load_line in map(json.loads, (self.root / 'uninterrupted/metrics.jsonl').read_text().splitlines())]
        actual = list(map(json.loads, (self.root / 'interrupted/metrics.jsonl').read_text().splitlines()))
        self.assertEqual([r['step'] for r in actual], list(range(1, 7)))
        for a, b in zip(actual, expected):
            self.assertEqual([a[k] for k in ('loss', 'presence', 'heat', 'point')],
                             [b[k] for k in ('loss', 'presence', 'heat', 'point')])
        state = lambda name: torch.load(self.root / name / 'checkpoints/step_00000006/state.pt', weights_only=False)
        full, resumed = state('uninterrupted'), state('interrupted')
        self.assertEqual(resumed['sampler_position'], 6)
        self.assertEqual(len(resumed['rng']), 2)
        self.assertEqual(full['scheduler'], resumed['scheduler'])
        for name in full['head']:
            self.assertTrue(torch.equal(full['head'][name], resumed['head'][name]), name)
        self.assertTrue((self.root / 'interrupted/checkpoints/step_00000004/complete.json').is_file())
        meta = load(self.root / 'interrupted/final/step_00000006/gh.json')
        self.assertEqual(meta['metrics']['calibration']['split'], 'train')
        self.assertEqual(meta['step'], meta['metrics']['step'])

    def add_ignored_clip(self, n_used=32, structural=False):
        path = self.root / f'ignored_{n_used}_{structural}.npz'
        inst = np.full((32, 240, 320), -2, np.int16)
        inst[:n_used] = -1
        if structural and n_used:
            inst[0, :20, :20] = 1
        with path.open('xb') as stream:
            np.savez_compressed(stream, inst=inst, used=np.arange(32) < n_used, ids=np.array([1]),
                                labels=np.array(['wall' if structural else 'chair']), scene='ignored', qid='clip_99')
        entry = {**self.index['train'][0], 'path': str(path), 'sha256': file_pin(path)['sha256'],
                 'scene': 'ignored', 'qid': 'clip_99'}
        self.index['train'].insert(0, entry)
        return entry

    def test_first_batch_loads_once_and_checks_every_rank(self):
        rt, batch = runtime()
        a, b, c = self.contexts(batch)
        cfg = self.cfg
        with a, b, c, mock.patch.object(train, 'load_runtime', return_value=rt) as loader, mock.patch.object(
                train, 'make_index', return_value=self.index):
            result = train.first_batch(cfg)
        self.assertEqual(loader.call_count, 1)
        self.assertTrue(result['ok'], result)
        self.assertEqual([r['rank'] for r in result['ranks']], [0, 1])
        self.assertTrue(all(r['labels'] == 2 for r in result['ranks']))
        self.assertEqual(load(self.root / 'run/FIRST_BATCH.json'), result)

    def test_serial_native_checkpoint_resume_matches_uninterrupted(self):
        rt, batch = runtime()
        a, b, c = self.contexts(batch)
        with a, b, c:
            full = {**self.cfg, 'output': str(self.root / 'serial_full')}
            resumed = {**self.cfg, 'output': str(self.root / 'serial_resume')}
            train.train(full, runtime=rt, index=self.index)
            train.train(resumed, runtime=rt, index=self.index, stop_after_steps=4)
            train.append_metric(self.root / 'serial_resume/metrics.jsonl', dict(step=5, loss=-999.))
            train.train(resumed, runtime=rt, index=self.index)
        records = lambda name: list(map(json.loads, (self.root / name / 'metrics.jsonl').read_text().splitlines()))
        self.assertEqual([r['loss'] for r in records('serial_full')], [r['loss'] for r in records('serial_resume')])
        state = lambda name: torch.load(self.root / name / 'checkpoints/step_00000006/state.pt', weights_only=False)
        full_state, resumed_state = state('serial_full'), state('serial_resume')
        for name in full_state['head']:
            self.assertTrue(torch.equal(full_state['head'][name], resumed_state['head'][name]), name)
        tails = list((self.root / 'serial_resume').glob('metrics.jsonl.superseded-*'))
        self.assertEqual(len(tails), 1)
        self.assertIn('-999.0', tails[0].read_text())
        with a, b, c, mock.patch.object(train, 'load_runtime', return_value=rt), mock.patch.object(
                train, 'make_index', return_value=self.index):
            train.calibrate_export(resumed, output=self.root / 'checkpoint_export')
        self.assertEqual(load(self.root / 'checkpoint_export/gh.json')['step'], 6)

    def test_first_batch_reports_failure_and_tries_later_rank(self):
        rt, batch = runtime()
        a, b, c = self.contexts(batch)
        with a, b, c, mock.patch.object(train, 'forward_clip', side_effect=ValueError('forced batch error')) as forward:
            result = train.first_batch(self.cfg, runtime=rt, index=self.index)
        self.assertFalse(result['ok'])
        self.assertEqual(forward.call_count, 2)
        self.assertTrue(all('forced batch error' in r['error'] for r in result['ranks']))

    def test_failfast_stops_after_calibrating_before_heldout(self):
        rt, batch = runtime()
        cfg = {**self.cfg, 'eval_every': 1, 'fail_fast_minutes': 0}
        events = []
        original = train.calibrate_training
        def calibration(*args):
            self.assertEqual(args[3].entries, self.index['train'])
            events.append('calibration')
            return original(*args)
        def validation(*args):
            self.assertEqual(events, ['calibration'])
            self.assertEqual(args[3].entries, self.index['val'])
            events.append('heldout')
            return dict(in_mask=0., presence_auroc=.1)
        a, b, c = self.contexts(batch)
        with a, b, c, mock.patch.object(train, 'calibrate_training', side_effect=calibration), mock.patch.object(
                train, 'validate', side_effect=validation):
            result = train.train(cfg, runtime=rt, index=self.index)
        self.assertEqual(result, dict(step=1, failfast=True))
        self.assertEqual(load(self.root / 'run/FAILFAST.json')['step'], 1)
        self.assertTrue((self.root / 'run/checkpoints/step_00000001/complete.json').is_file())

    def test_calibrate_command_revalidates_with_training_only_tau(self):
        from student_pilot.grounding_head import load_artifact
        rt, batch = runtime()
        head = train.new_head(rt[0], self.cfg)
        a, b, c = self.contexts(batch)
        training = train.ClipDataset(self.index['train'], self.index['vocab'], rt[1], {}, self.cfg)
        heldout = train.ClipDataset(self.index['val'], self.index['vocab'], rt[1], {}, self.cfg)
        with a, b, c:
            tau, metrics = train.evaluate_weights(*rt[:2], head, training, heldout, torch.device('cpu'), self.cfg, 3)
            train.export_artifact(self.root / 'source', head, {**self.cfg, 'data_identity': train.digest(self.index)},
                                  3, tau, metrics)
        with a, b, c, mock.patch.object(train, 'load_runtime', return_value=rt), mock.patch.object(
                train, 'make_index', return_value=self.index), mock.patch.object(
                train, 'validate', wraps=train.validate) as validation:
            tau = train.calibrate_export(self.cfg, artifact=self.root / 'source', output=self.root / 'calibrated')
        self.assertEqual(validation.call_count, 1)
        self.assertEqual(validation.call_args.args[5], tau)
        _, meta = load_artifact(self.root / 'calibrated')
        self.assertEqual(meta['tau'], tau)
        self.assertEqual(meta['metrics']['calibration']['split'], 'train')
        self.assertEqual(meta['step'], 3)
        self.assertEqual(meta['metrics']['step'], 3)
        self.assertEqual(meta['metrics']['tau'], tau)
        self.assertFalse(meta['tau_val_used'])
        with a, b, c, mock.patch.object(train, 'load_runtime', return_value=rt), mock.patch.object(
                train, 'make_index', return_value={**self.index, 'val': self.index['val'][:0]}):
            with self.assertRaisesRegex(ValueError, 'another train/val split'):
                train.calibrate_export(self.cfg, artifact=self.root / 'source', output=self.root / 'calibrated2')
        self.assertFalse(meta['tau_slice']['val_used'])
        self.assertEqual(meta['tau_slice']['n_frames'], 32)

    def test_final_step_validates_and_exports_best_and_final(self):
        rt, batch = runtime()
        cfg = {**self.cfg, 'steps': 2, 'eval_every': 100}
        a, b, c = self.contexts(batch)
        with a, b, c:
            result = train.train(cfg, runtime=rt, index=self.index)
        self.assertEqual(result['step'], 2)
        for part in ('best', 'final'):
            meta = load(self.root / 'run' / part / 'step_00000002/gh.json')
            self.assertEqual(meta['metrics']['calibration']['split'], 'train')
            self.assertGreaterEqual(meta['tau'], 0.)
            self.assertLessEqual(meta['tau'], 1.)
            self.assertEqual(meta['step'], meta['metrics']['step'])
            self.assertEqual(meta['tau'], meta['metrics']['tau'])

    def test_wall_stop_exports_fresh_metrics_for_each_weight_and_step(self):
        rt, batch = runtime()
        cfg = {**self.cfg, 'steps': 6, 'eval_every': 2, 'wall_minutes': 3}
        events, snapshots = [], []
        clock = [0.]
        append = train.append_metric
        def record(path, value):
            append(path, value)
            if Path(path).name == 'metrics.jsonl':
                clock[0] = value['step'] * 60.
        original = train.calibrate_training
        def calibration(*args):
            self.assertEqual(args[3].entries, self.index['train'])
            events.append('calibrate')
            _, audit = original(*args)
            return (.6 if len(snapshots) == 0 else .8), audit
        def validation(model, processor, head, dataset, device, tau):
            self.assertEqual(events[-1], 'calibrate')
            self.assertEqual(dataset.entries, self.index['val'])
            events.append('validate')
            snapshots.append({key: value.clone() for key, value in head.state_dict().items()})
            return dict(tau=tau, in_mask=.9 if len(snapshots) == 1 else .2, presence_auroc=1.)
        a, b, c = self.contexts(batch)
        with a, b, c, mock.patch.object(train, 'calibrate_training', side_effect=calibration), mock.patch.object(
                train, 'validate', side_effect=validation), mock.patch.object(
                train, 'append_metric', side_effect=record), mock.patch.object(train.time, 'monotonic', side_effect=lambda: clock[0]):
            result = train.train(cfg, runtime=rt, index=self.index)
        self.assertEqual(result['step'], 3)
        self.assertEqual(events, ['calibrate', 'validate', 'calibrate', 'validate'])
        for part, step, tau, hit, snapshot in [('best', 2, .6, .9, snapshots[0]), ('final', 3, .8, .2, snapshots[1])]:
            path = self.root / 'run' / part / f'step_{step:08d}'
            meta = load(path / 'gh.json')
            weights = torch.load(path / 'gh.pt', weights_only=True)
            self.assertEqual((meta['step'], meta['metrics']['step']), (step, step))
            self.assertEqual((meta['tau'], meta['metrics']['tau'], meta['metrics']['in_mask']), (tau, tau, hit))
            self.assertFalse(meta['tau_slice']['val_used'])
            for key in snapshot:
                self.assertTrue(torch.equal(weights[key], snapshot[key]), key)

    def test_export_rejects_stale_metric_step_or_tau(self):
        rt, _ = runtime()
        head = train.new_head(rt[0], self.cfg)
        with self.assertRaisesRegex(AssertionError, 'own step'):
            train.export_artifact(self.root / 'stale_step', head, self.cfg, 3, .8, dict(step=2, tau=.8))
        with self.assertRaisesRegex(ValueError, 'tau differ'):
            train.export_artifact(self.root / 'stale_tau', head, self.cfg, 3, .8, dict(step=3, tau=.6))

    def test_validation_values_cannot_change_training_slice_tau(self):
        rt, batch = runtime()
        head = train.new_head(rt[0], self.cfg)
        training = train.ClipDataset(self.index['train'], self.index['vocab'], rt[1], {}, self.cfg)
        heldout = train.ClipDataset(self.index['val'], self.index['vocab'], rt[1], {}, self.cfg)
        a, b, c = self.contexts(batch)
        results = []
        with a, b, c:
            for heldout_tau in (.01, .99):
                with mock.patch.object(train, 'validate', return_value=dict(tau=heldout_tau)):
                    results.append(train.evaluate_weights(*rt[:2], head, training, heldout, torch.device('cpu'), self.cfg, 3))
        self.assertEqual(results[0], results[1])
        tau, metrics = results[0]
        self.assertEqual(metrics['tau'], tau)
        self.assertNotIn(tau, (.01, .99))

    def test_dataset_substitutes_ignored_samples_in_each_ranks_deterministic_order(self):
        self.add_ignored_clip(n_used=0)
        self.add_ignored_clip(n_used=7)
        self.add_ignored_clip(structural=True)
        self.add_ignored_clip()  # Used frames, but no visible object.
        rt, batch = runtime()
        dataset = train.ClipDataset(self.index['train'], self.index['vocab'], rt[1], {}, self.cfg)
        # Use real target eligibility for this test rather than the training fixture renderer.
        with mock.patch('student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)):
            self.assertNotEqual(dataset[0]['clip']['scene'], 'ignored')
            for rank in range(2):
                keys = list(itertools.islice(train.EpochSampler(len(dataset), rank, 2, with_fallback=True), 8))
                for primary, position, owner, world in keys:
                    order = train.EpochSampler(len(dataset), owner, world, position)
                    expected = next(i for i in order if dataset.entries[i]['scene'] != 'ignored')
                    item = dataset[(primary, position, owner, world)]
                    self.assertEqual(item['clip'], dataset.entries[expected])
                    self.assertGreaterEqual(item['n_used'], 8)

    def test_validation_erodes_rgb_union_and_failfast_rejects_boundary_hits(self):
        rt, batch = runtime()
        head = train.new_head(rt[0], self.cfg)
        path = self.root / 'boundary.npz'
        inst = np.full((32, 240, 320), -1, np.int16)
        inst[0, :20, :20] = 1
        inst[0, 100:114, 100:114] = 2
        with path.open('xb') as stream:
            np.savez_compressed(stream, inst=inst, used=np.ones(32, bool), ids=np.array([1, 2]),
                                labels=np.array(['chair', 'chair']))
        row = {**self.index['val'][0], 'path': str(path), 'rgb_wh': [320, 240], 'sha256': file_pin(path)['sha256']}
        dataset = train.ClipDataset([row], [], rt[1], {}, self.cfg)
        probability = torch.tensor([[.9] + [.1] * 31])
        with mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)), mock.patch(
                'student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)), mock.patch.object(
                head, 'decode', return_value=dict(prob=probability, uv=torch.tensor([[[2, 40]] * 32]))):
            metrics = train.validate(*rt[:2], head, dataset, torch.device('cpu'), .5)
        self.assertEqual(metrics['in_mask'], 0.)
        self.assertEqual(metrics['null_on_absent'], 1.)
        self.assertEqual(metrics['presence_auroc'], 1.)
        self.assertTrue(train.fail_fast(metrics, self.cfg))
        with mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)), mock.patch(
                'student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)), mock.patch.object(
                head, 'decode', return_value=dict(prob=probability, uv=torch.tensor([[[330, 440]] * 32]))):
            metrics = train.validate(*rt[:2], head, dataset, torch.device('cpu'), .5)
        self.assertEqual(metrics['in_mask'], 1.)  # Hit lies in the smaller instance.

    def test_frame_root_uses_the_existing_guarded_resolver(self):
        from student_pilot import orchard_paths
        root = self.root / 'data2root'
        root.mkdir()
        with mock.patch.object(orchard_paths, 'PROJECT', self.root), mock.patch.dict(
                os.environ, {'STUDENT_ORCHARD': '1', 'STUDENT_FRAME_ROOT_MAP': '{}'}):
            train.bind_frames({'frame_root': str(root)})
            self.assertEqual(orchard_paths.resolve_read('/data2/k8pd/aa/frame.png'), root / 'k8pd/aa/frame.png')
            with self.assertRaisesRegex(ValueError, 'differs'):
                train.bind_frames({'frame_root': str(self.root / 'other')})

    def test_validation_uses_current_tau_eroded_union_and_fixed_200_items(self):
        rt, batch = runtime()
        head = train.new_head(rt[0], self.cfg)
        dataset = train.ClipDataset(self.index['val'], self.index['vocab'], rt[1], {}, self.cfg)
        probability = torch.tensor([[.9] * 16 + [.1] * 16, [.1] * 32])
        uv = torch.tensor([[[250, 500]] * 32] * 2)
        a, b, c = self.contexts(batch)
        with a, b, c, mock.patch.object(head, 'decode', return_value=dict(prob=probability, uv=uv)):
            good = train.validate(rt[0], rt[1], head, dataset, torch.device('cpu'), .5)
            null = train.validate(rt[0], rt[1], head, dataset, torch.device('cpu'), .99)
        self.assertEqual((good['items'], good['visible_frames'], good['absent_frames']), (2, 16, 48))
        self.assertEqual([good[k] for k in ('in_mask', 'presence_auroc', 'null_on_absent', 'presence_recall')], [1.] * 4)
        self.assertEqual(null['in_mask'], 0.)
        self.assertEqual(null['presence_recall'], 0.)

    def test_sampler_replays_each_rank_and_epoch_from_position(self):
        sequences = [list(itertools.islice(iter(train.EpochSampler(5, rank, 2)), 12)) for rank in range(2)]
        self.assertNotEqual(sequences[0], sequences[1])
        for rank in range(2):
            resumed = list(itertools.islice(iter(train.EpochSampler(5, rank, 2, 4)), 8))
            self.assertEqual(resumed, sequences[rank][4:])
        row = train.clip_row(self.index['train'][0])
        self.assertEqual(row['student_input']['timestamps'], [i / 24 for i in range(32)])
        self.assertTrue(row['student_input']['frames'][0]['path'].startswith('/data2/k8pd/aa/'))

    def test_tau_balanced_accuracy_and_tied_auroc(self):
        tau, balanced = train.choose_tau([0, 0, 1, 1], [.1, .4, .6, .8])
        self.assertEqual((tau, balanced), (.6, 1.))
        self.assertEqual(train.presence_auroc([0, 1], [.5, .5]), .5)
        self.assertIsNone(train.presence_auroc([1], [.5]))
        with self.assertRaises(ValueError): train.choose_tau([0], [.5])

    def test_routed_loading_refuses_identity_drift(self):
        rt, _ = runtime()
        native = dict(frame_layout='duplicate', frame_markers=True, training_mode='final', depth_enabled=True,
                      carrier_placement='append_after_temporal_group_video_tokens_v1', base_identity='base')
        write(self.root / 'c1.json', native)
        cfg = {**self.cfg, 'c1_config': str(self.root / 'c1.json')}
        artifact = dict(base_identity='base', config_sha256='correct')
        from student_pilot import carrier_c1_run as c1
        for mismatch in ({}, {'base_identity': 'other'}, {'config_sha256': 'other'}):
            with mock.patch.object(c1, 'prepared', return_value=({}, {})) as prep, mock.patch.object(
                    c1, 'processor_for_receipt', return_value=rt[1]), mock.patch.object(
                    c1, 'load_model', return_value=rt[0]), mock.patch.object(
                    c1, 'load_artifact', return_value={**artifact, **mismatch}), mock.patch.object(c1, 'identity', return_value='correct'):
                if mismatch:
                    with self.assertRaisesRegex(ValueError, 'identity'): train.load_runtime(cfg, torch.device('cpu'))
                else:
                    train.load_runtime(cfg, torch.device('cpu'))
                prep.assert_called_once_with(native, admission=True)


if __name__ == '__main__':
    unittest.main()
