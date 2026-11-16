"""Native C1 CPU trainer checks with local MDG interface fakes."""
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock
import weakref

import numpy as np
import torch
from torch import distributed as dist, nn
from torch.nn import functional as F
import torch.multiprocessing as mp

from student_pilot import grounding_features, mdg_train as train
from student_pilot.p3_provenance import load, write
from tests.test_grounding_train import fixture as gh_fixture, runtime as gh_runtime, prompt


def runtime():
    # T0 loaders (load_artifact, mdg_runtime) hold the base in bf16; freeze_runtime keeps loaded dtypes.
    from student_pilot import full_ft
    rt, batch = gh_runtime()
    for _, parameter in full_ft.base_parameters(rt[0]):
        parameter.data = parameter.data.to(torch.bfloat16)
    return rt, batch


@dataclass
class PrefixFeatures:
    taps: list
    vit: list
    pixels: torch.Tensor
    grid: tuple
    hidden: torch.Tensor
    cache: object
    prefix_len: int


@dataclass
class SuffixStates:
    query: torch.Tensor
    phrase: torch.Tensor
    phrase_mask: torch.Tensor


@dataclass
class MDGUnits:
    scene: str
    qid: str
    labels: list
    kind: list
    frame_presence: np.ndarray
    clip_present: np.ndarray
    unique: np.ndarray
    masks: np.ndarray
    used: np.ndarray


@dataclass
class MDGConfig:
    lm_dim: int = 32
    vit_dim: int = 32
    dim: int = 8
    stem_pretrained: bool = False
    stem_weights: str = ''


class Cache:
    pass


class Tokenizer:
    pad_token_id = 0

    def encode(self, text, **kwargs):
        return [6 + ord(c) % 32 for c in text]

    def __call__(self, text, **kwargs):
        return dict(input_ids=self.encode(text), offset_mapping=[(i, i + 1) for i in range(len(text))])


def fake_capture(model, batch):
    assert not torch.is_grad_enabled()
    assert not model.training
    assert next(model.parameters()).dtype == torch.bfloat16
    features = grounding_features.capture(model, batch)
    frames = features.taps[0].shape[0]
    gh, gw = features.grid
    return PrefixFeatures(features.taps, [features.vit] * 3,
        torch.zeros(frames, 3, 32 * gh, 32 * gw, device=features.hidden.device),
        features.grid, features.hidden, Cache(), features.hidden.shape[1])


def fake_suffix(model, prefix, names, *, chunk=8):
    assert not torch.is_grad_enabled()
    assert chunk > 0
    q = prefix.hidden[:, -1].float().expand(len(names), -1)
    query = torch.stack([q, q], 1).clone()
    phrase = query[:, None].expand(-1, 8, -1, -1).clone()
    return SuffixStates(query, phrase, torch.ones(len(names), 8, dtype=torch.bool, device=q.device))


def fake_units(npz_or_row, vocab, confusers, *, max_visible=24, absent_share=.30,
               confuser_share=.5, seed_key):
    assert max_visible == 24 and absent_share == .30 and confuser_share == .5
    assert confusers == {'chair': ['table']}
    row = npz_or_row
    with np.load(row['path'], allow_pickle=False) as z:
        mask = z['inst'] == 1
        used = z['used']
    presence = np.stack([mask.any((-2, -1)), np.zeros(32, bool)]).astype(np.float32)
    presence[:, ~used] = np.nan
    return MDGUnits(row['scene'], row['qid'], ['chair', 'table'], ['visible', 'confuser'],
        presence, np.array([1., 0.], np.float32), np.array([True, False]),
        np.stack([mask, np.zeros_like(mask)]), used)


def fake_tensors(units):
    return dict(frame_presence=torch.from_numpy(np.nan_to_num(units.frame_presence)),
        frame_valid=torch.from_numpy(np.isfinite(units.frame_presence) & (units.clip_present[:, None] == 1)),
        clip_present=torch.from_numpy(units.clip_present), masks=torch.from_numpy(units.masks),
        mask_valid=torch.from_numpy(units.frame_presence == 1))


class MaskGroundingHead(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.video = nn.Linear(cfg.lm_dim, cfg.dim)
        self.query = nn.Linear(2 * cfg.lm_dim, cfg.dim)
        self.output = nn.Linear(cfg.dim, 4)

    def encode_video(self, taps, vit, pixels, grid, geo=None):
        return dict(memory=self.video(torch.stack(taps).mean((0, 2)).float()), grid=grid)

    def forward(self, video, query, phrase, phrase_mask):
        q = self.query(query.flatten(1).float())
        q = F.dropout(q, .2, self.training)
        result = self.output(torch.tanh(q[:, None] + video['memory'][None]))
        q_count, frames = result.shape[:2]
        gh, gw = video['grid']
        horizontal = torch.linspace(-1, 1, 8 * gw, device=result.device)
        mask = result[..., 0, None, None] - horizontal
        mask = mask.expand(q_count, frames, 8 * gh, 8 * gw)
        return [dict(mask_logit=mask, frame_logit=result[..., 1], clip_logit=result[..., 2].mean(1),
                     iou=result[..., 3])]

    def loss(self, outs, targets):
        out = outs[-1]
        indices = torch.randperm(out['mask_logit'].shape[-1], device=out['mask_logit'].device)[:4]
        mask = out['mask_logit'][..., indices]
        truth = F.interpolate(targets['masks'].flatten(0, 1)[:, None].float(),
                              size=out['mask_logit'].shape[-2:], mode='nearest')[:, 0]
        truth = truth.reshape_as(out['mask_logit'])[..., indices]
        bce = F.binary_cross_entropy_with_logits(mask, truth)
        dice = (mask.sigmoid() - truth).square().mean()
        frame_loss = F.binary_cross_entropy_with_logits(out['frame_logit'], targets['frame_presence'])
        clip = F.binary_cross_entropy_with_logits(out['clip_logit'], targets['clip_present'])
        iou = out['iou'].sigmoid().square().mean()
        return dict(total=bce + dice + frame_loss + clip + iou, bce=bce, dice=dice,
                    frame=frame_loss, clip=clip, iou=iou)

    @staticmethod
    def decode(out, tau=None):
        probability = out['clip_logit'].sigmoid()[:, None] * out['frame_logit'].sigmoid()
        uv = torch.tensor([250, 500], device=probability.device).expand(*probability.shape, 2)
        masks = out['mask_logit'] > 0
        return dict(prob=probability, mask=masks, uv=uv, iou=out['iou'], area=masks.sum((-2, -1)))


def save_artifact(directory, head, meta):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / 'mdg.pt').open('xb') as stream:
        torch.save(head.state_dict(), stream)
    write(directory / 'mdg.json', meta)


def load_artifact(directory):
    meta = load(Path(directory) / 'mdg.json')
    head = MaskGroundingHead(MDGConfig(**meta['config']))
    head.load_state_dict(torch.load(Path(directory) / 'mdg.pt', weights_only=True))
    return head, meta


@contextmanager
def interfaces(batch):
    modules = {}
    for name, members in (
            ('mdg_features', dict(capture_prefix=fake_capture, suffix_states=fake_suffix)),
            ('mdg_targets', dict(mdg_units_for_clip=fake_units, to_tensors=fake_tensors)),
            ('mask_grounding_head', dict(MDGConfig=MDGConfig, MaskGroundingHead=MaskGroundingHead,
                                         save_artifact=save_artifact, load_artifact=load_artifact))):
        module = ModuleType('student_pilot.' + name)
        module.__dict__.update(members)
        modules[module.__name__] = module
    with ExitStack() as stack:
        stack.enter_context(mock.patch.dict(sys.modules, modules))
        stack.enter_context(mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)))
        stack.enter_context(mock.patch('student_pilot.carrier_c1_canary.prompt_batch', side_effect=prompt(batch)))
        yield modules


def fixture(root):
    cfg, index = gh_fixture(root)
    write(Path(root) / 'confusers.json', {'chair': ['table']})
    cfg.update(head=dict(dim=8, stem_pretrained=False), confusers=str(Path(root) / 'confusers.json'),
               warmup=1, checkpoint_minutes=100, wall_budget_minutes=180, tau_clips=1, val_items=2,
               failfast_step=600, label_chunk=2)
    return cfg, index


def distributed_run(rank, root, cfg, index):
    torch.set_num_threads(1)
    os.environ['RANK'], os.environ['WORLD_SIZE'] = str(rank), '2'
    os.environ['GLOO_SOCKET_IFNAME'] = 'lo'
    dist.init_process_group('gloo', init_method='file://' + str(Path(root) / 'rendezvous'), rank=rank, world_size=2)
    try:
        rt, batch = runtime()
        with interfaces(batch):
            full = {**cfg, 'output': str(Path(root) / 'full')}
            resumed = {**cfg, 'output': str(Path(root) / 'resumed')}
            train.train(full, runtime=rt, index=index)
            train.train(resumed, runtime=rt, index=index, stop_after_steps=4)
            train.train(resumed, runtime=rt, index=index)
    finally:
        dist.destroy_process_group()


class Trainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        runtime()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='mdg_train_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.cfg, self.index = fixture(self.root)

    def test_two_rank_gloo_checkpoint_replays_exact_losses(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except PermissionError as exc:
            self.skipTest(f'The execution sandbox prohibits gloo sockets: {exc}')
        mp.start_processes(distributed_run, args=(str(self.root), self.cfg, self.index),
                           nprocs=2, join=True, start_method='fork')
        journal = lambda name: list(map(json.loads, (self.root / name / 'metrics.jsonl').read_text().splitlines()))
        full, resumed = journal('full'), journal('resumed')
        self.assertEqual([r['step'] for r in resumed], list(range(1, 7)))
        for a, b in zip(full, resumed):
            for key in ('loss', 'bce', 'dice', 'frame', 'clip', 'iou'):
                self.assertEqual(a[key], b[key], (a['step'], key))
            for key in ('seconds_prefill', 'seconds_suffix', 'seconds_head', 'peak_memory'):
                self.assertGreaterEqual(a[key], 0)
        state = lambda name: torch.load(self.root / name / 'checkpoints/step_00000006/state.pt', weights_only=False)
        a, b = state('full'), state('resumed')
        self.assertEqual(b['sampler_position'], 6)
        self.assertEqual(len(b['rng']), 2)
        self.assertEqual(a['scheduler'], b['scheduler'])
        for key in a['head']:
            self.assertTrue(torch.equal(a['head'][key], b['head'][key]), key)
        self.assertTrue((self.root / 'resumed/checkpoints/step_00000004/complete.json').is_file())
        meta = load(self.root / 'resumed/final/step_00000006/mdg.json')
        self.assertEqual(meta['schema'], 'mdg-head-v1')
        self.assertFalse(meta['tau_slice']['val_used'])
        self.assertFalse(meta['tau_slice']['sampler_used'])

    def test_first_batch_loads_once_checks_two_real_sampler_ranks(self):
        rt, batch = runtime()
        with interfaces(batch), mock.patch.object(train, 'load_runtime', return_value=rt) as loader, mock.patch.object(
                train, 'make_index', return_value=self.index), mock.patch.object(
                train, 'capture_clip', wraps=train.capture_clip) as capture:
            result = train.first_batch(self.cfg)
        self.assertEqual(loader.call_count, 1)
        self.assertTrue(result['ok'], result)
        self.assertEqual([r['rank'] for r in result['ranks']], [0, 1])
        self.assertTrue(all(r['Q'] == 2 and r['peak_rss'] > 0 for r in result['ranks']))
        split = train.split_index(self.index, self.cfg)
        for rank, call in enumerate(capture.call_args_list):
            expected = next(iter(train.EpochSampler(len(split['train']), rank, 2)))
            self.assertEqual(call.args[1]['clip'], split['train'][expected])
        self.assertEqual(load(self.root / 'run/FIRST_BATCH.json'), result)
        self.assertTrue(all(p.grad is None for p in rt[0].parameters()))

    def test_prefix_cache_released_before_head_forward(self):
        rt, batch = runtime()
        refs = []
        def suffix(model, prefix, names, *, chunk=8):
            refs.append(weakref.ref(prefix.cache))
            return fake_suffix(model, prefix, names, chunk=chunk)
        original = MaskGroundingHead.encode_video
        def encode(head, taps, vit, pixels, grid, geo=None):
            self.assertTrue(refs and all(ref() is None for ref in refs))
            return original(head, taps, vit, pixels, grid, geo)
        with interfaces(batch) as modules, mock.patch.object(MaskGroundingHead, 'encode_video', encode):
            modules['student_pilot.mdg_features'].suffix_states = suffix
            result = train.first_batch(self.cfg, runtime=rt, index=self.index)
        self.assertTrue(result['ok'], result)

    def test_first_batch_reports_each_failure(self):
        rt, batch = runtime()
        with interfaces(batch), mock.patch.object(train, 'capture_clip', side_effect=ValueError('forced')):
            result = train.first_batch(self.cfg, runtime=rt, index=self.index)
        self.assertFalse(result['ok'])
        self.assertEqual(len(result['ranks']), 2)
        self.assertTrue(all('forced' in r['error'] for r in result['ranks']))

    def test_tau_scene_slice_disjoint_and_sha_ordered(self):
        split = train.split_index(self.index, self.cfg)
        scenes = [{r['scene'] for r in split[k]} for k in ('train', 'tau', 'val')]
        self.assertTrue(all(scenes))
        self.assertFalse(scenes[0] & scenes[1] or scenes[0] & scenes[2] or scenes[1] & scenes[2])
        first = min({r['scene'] for r in self.index['train']}, key=lambda s: hashlib.sha256(s.encode()).hexdigest())
        self.assertEqual(scenes[1], {first})
        self.assertEqual(train.split_index(split, self.cfg), split)
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            train.split_index({**split, 'tau': split['val']}, self.cfg)
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            train.split_index(self.index, {**self.cfg, 'exclude_scenes': [first]})

    def test_tau_optimizes_in_mask_and_null_on_101_grid(self):
        records = dict(labels=[True, True, False], scores=[.9, .6, .2], point_hits=[True, False, False],
            null_scores=[.2, .5], mask_ious=[.7], clip_labels=[True, False], clip_scores=[.8, .2], items=2)
        tau, objective = train.choose_tau(records)
        self.assertEqual(tau, .21)
        self.assertEqual(objective, .5)
        metrics = train.metrics_at(records, tau)
        self.assertEqual(metrics['in_mask'], .5)
        self.assertEqual(metrics['null_on_absent'], .5)
        self.assertEqual(metrics['mask_iou'], .7)
        self.assertEqual(metrics['clip_presence_auroc'], 1.)

    def test_metrics_use_union_masks_ignore_band_and_fixed_item_limit(self):
        rt, batch = runtime()
        cfg, index = train.prepare(self.cfg, self.index)
        with interfaces(batch):
            dataset = train.ClipDataset(index['val'], index['vocab'], rt[1], {}, cfg, cache=True)
            item = dataset[0]
            item['units'].frame_presence[0, 0] = np.nan
            truth = item['units'].frame_presence == 1
            probability = torch.from_numpy(np.where(truth, .9, .1))
            masks = F.interpolate(torch.from_numpy(item['units'].masks).flatten(0, 1)[:, None].float(),
                                  size=(8, 8), mode='nearest')[:, 0].reshape(2, 32, 8, 8).bool()
            decoded = dict(prob=probability, uv=torch.tensor([250, 500]).expand(2, 32, 2), mask=masks)
            outs = [dict(clip_logit=torch.tensor([3., -3.]))]
            head = train.new_head(rt[0], cfg)
            with mock.patch.object(train, 'forward_clip', return_value=(outs, {})), mock.patch.object(
                    head, 'decode', return_value=decoded):
                records = train.collect_outputs(rt[0], head, dataset, torch.device('cpu'), cfg, limit=2)
                limited = train.collect_outputs(rt[0], head, dataset, torch.device('cpu'), cfg, limit=1)
        result = train.metrics_at(records, .5)
        self.assertEqual(result['visible_frames'], 15)
        self.assertEqual(result['absent_frames'], 48)
        self.assertEqual(limited['items'], 1)
        for key in ('in_mask', 'null_on_absent', 'presence_recall', 'presence_auroc',
                    'clip_presence_auroc', 'mask_iou'):
            self.assertEqual(result[key], 1., key)

    def test_failfast_stops_at_first_due_eval_and_retains_checkpoint(self):
        rt, batch = runtime()
        cfg = {**self.cfg, 'eval_every': 2, 'failfast_step': 3}
        def bad(*args):
            step = args[-1]
            return .5, dict(in_mask=.1, presence_auroc=.2, mask_iou=.05, step=step, tau=.5)
        with interfaces(batch), mock.patch.object(train, 'evaluate_weights', side_effect=bad), mock.patch.object(
                train, 'export_artifact'):
            result = train.train(cfg, runtime=rt, index=self.index)
        self.assertEqual(result, dict(step=4, failfast=True))
        self.assertEqual(load(self.root / 'run/FAILFAST.json')['step'], 4)
        self.assertTrue((self.root / 'run/checkpoints/step_00000004/complete.json').is_file())
        for metrics in (dict(in_mask=.59, presence_auroc=.9, mask_iou=.5),
                        dict(in_mask=.8, presence_auroc=None, mask_iou=.5),
                        dict(in_mask=.8, presence_auroc=.9, mask_iou=.34)):
            self.assertTrue(train.fail_fast(metrics, {}))
        self.assertFalse(train.fail_fast(dict(in_mask=.6, presence_auroc=.85, mask_iou=.35), {}))

    def test_calibrate_writes_tau_and_never_fits_validation(self):
        rt, batch = runtime()
        with interfaces(batch), mock.patch.object(train, 'load_runtime', return_value=rt), mock.patch.object(
                train, 'make_index', return_value=self.index):
            train.train(self.cfg, runtime=rt, index=self.index, stop_after_steps=1)
            with mock.patch.object(train, 'calibrate_training', wraps=train.calibrate_training) as calibration:
                tau = train.calibrate_export(self.cfg, output=self.root / 'calibrated')
            dataset = calibration.call_args.args[2]
        self.assertEqual(dataset.entries, train.split_index(self.index, self.cfg)['tau'])
        meta = load(self.root / 'calibrated/mdg.json')
        self.assertEqual(meta['tau'], tau)
        self.assertEqual(meta['metrics']['tau'], tau)
        self.assertEqual(meta['metrics']['step'], meta['step'])
        self.assertEqual(meta['split_identity']['tau']['scenes'], meta['tau_slice']['scenes'])

    def test_fork_workers_prepare_cpu_inputs_and_cache_eval_inputs(self):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except PermissionError as exc:
            self.skipTest(f'The execution sandbox prohibits DataLoader sharing sockets: {exc}')
        rt, batch = runtime()
        cfg, index = train.prepare(self.cfg, self.index)
        with interfaces(batch):
            dataset = train.ClipDataset(index['train'], index['vocab'], rt[1], {}, cfg)
            loader = train.make_loader(dataset, 0, 1, 0, 1)
            self.assertEqual(loader.multiprocessing_context.get_start_method(), 'fork')
            item = next(iter(loader))
            self.assertTrue(all(value.device.type == 'cpu' for value in item['batch'].values()))
            cached = train.ClipDataset(index['tau'], index['vocab'], rt[1], {}, cfg, cache=True)
            self.assertIs(cached[0], cached[0])

    def test_resume_restores_journal_and_rejects_changed_inputs(self):
        rt, batch = runtime()
        with interfaces(batch):
            train.train(self.cfg, runtime=rt, index=self.index, stop_after_steps=1)
            train.append_metric(self.root / 'run/metrics.jsonl', dict(step=2, loss=-999.))
            train.train(self.cfg, runtime=rt, index=self.index, stop_after_steps=2)
            rows = list(map(json.loads, (self.root / 'run/metrics.jsonl').read_text().splitlines()))
            self.assertEqual([r['step'] for r in rows], [1, 2])
            self.assertTrue(list((self.root / 'run').glob('metrics.jsonl.superseded-*')))
            with self.assertRaisesRegex(ValueError, 'configuration'):
                train.train({**self.cfg, 'lr': .1}, runtime=rt, index=self.index)

    def test_serial_checkpoint_replays_stochastic_losses_and_weights(self):
        rt, batch = runtime()
        full = {**self.cfg, 'output': str(self.root / 'serial_full')}
        resumed = {**self.cfg, 'output': str(self.root / 'serial_resumed')}
        with interfaces(batch):
            train.train(full, runtime=rt, index=self.index)
            train.train(resumed, runtime=rt, index=self.index, stop_after_steps=4)
            train.train(resumed, runtime=rt, index=self.index)
        journal = lambda name: list(map(json.loads, (self.root / name / 'metrics.jsonl').read_text().splitlines()))
        a, b = journal('serial_full'), journal('serial_resumed')
        self.assertEqual([r['loss'] for r in a], [r['loss'] for r in b])
        state = lambda name: torch.load(self.root / name / 'checkpoints/step_00000006/state.pt', weights_only=False)
        a, b = state('serial_full'), state('serial_resumed')
        for key in a['head']:
            self.assertTrue(torch.equal(a['head'][key], b['head'][key]), key)

    def test_native_feature_contract_binds_tokenizer_and_processor(self):
        try:
            features = importlib.import_module('student_pilot.mdg_features')
        except ModuleNotFoundError:
            self.skipTest('The parallel feature module has not landed')
        rt, batch = runtime()
        model, processor, _ = rt
        processor.tokenizer = Tokenizer()
        processor.video_processor = SimpleNamespace(image_mean=[.1, .2, .3], image_std=[.2, .2, .2])
        train.freeze_runtime(model, processor, torch.device('cpu'))
        with mock.patch.object(grounding_features, 'TAP_LAYERS', (1, 1)), mock.patch.object(
                features, 'TAP_LAYERS', (1, 1)), mock.patch.object(
                features, 'VIT_BLOCKS', (1, 2, 3)), mock.patch.object(features, 'QUERY_LAYER', 1):
            inputs, info = train.capture_clip(model, dict(batch=batch, labels=['chair', 'table']),
                                              torch.device('cpu'), 2)
        self.assertIs(model.mdg_tokenizer, processor.tokenizer)
        self.assertIs(model.mdg_video_processor, processor.video_processor)
        self.assertEqual(tuple(inputs[4].shape), (2, 2, model.config.text_config.hidden_size))
        self.assertEqual(info['prompt_tokens'], batch['input_ids'].shape[1])
        self.assertFalse(any(v.requires_grad for v in [*inputs[0], *inputs[1], inputs[2], inputs[4], inputs[5]]))

    def test_real_head_targets_training_and_artifact_contract(self):
        try:
            head_api = importlib.import_module('student_pilot.mask_grounding_head')
            target_api = importlib.import_module('student_pilot.mdg_targets')
        except ModuleNotFoundError:
            self.skipTest('The parallel head or target module has not landed')
        rt, batch = runtime()
        cfg = {**self.cfg, 'steps': 1, 'head': dict(dim=16, heads=4, mlp=32, pixel_dim=8,
                                                  blocks=1, points=8, stem_pretrained=False)}
        with interfaces(batch), mock.patch.dict(sys.modules, {
                'student_pilot.mask_grounding_head': head_api, 'student_pilot.mdg_targets': target_api}):
            result = train.first_batch(cfg, runtime=rt, index=self.index)
            self.assertTrue(result['ok'], result)
            train.train(cfg, runtime=rt, index=self.index)
        head, meta = head_api.load_artifact(self.root / 'run/final/step_00000001')
        self.assertEqual(meta['schema'], 'mdg-head-v1')
        self.assertEqual(meta['step'], 1)
        self.assertFalse(meta['tau_slice']['val_used'])
        self.assertTrue(all(p.dtype == torch.float32 for p in head.parameters()))


if __name__ == '__main__':
    unittest.main()
