"""Retained native hybrid-C1 stage-B, four-rank FSDP, and artifact regressions."""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
from torch import distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_run as run, stageb_mdg as sb, full_ft
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_data import mixed_indices, C1_A
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.mask_grounding_head import MaskGroundingHead, load_artifact, save_artifact
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_mdg_features import fixture as feature_fixture, small_layers, Tokenizer
from tests.test_mask_grounding_head import config as head_config, targets


def root():
    return Path(tempfile.mkdtemp(prefix='stageb_', dir=os.environ['LANE_TEST_OUTPUT']))


def block():
    return dict(clips_jsonl='/placeholder/clips.jsonl', frame_root='/placeholder/frames',
                rasters='/placeholder/rasters', confusers='/placeholder/confusers.json',
                vocab='/placeholder/vocab.json', exclude_scenes=[], stem_weights='/placeholder/stem.pth')


def fixture(frames=32, lora_rank=0):
    from transformers import Qwen3_5ForConditionalGeneration
    model, batch = feature_fixture(frames)
    # Native 16-pixel patches keep the decoder's RGB/ViT contract, with tiny channels and grids.
    model.config.vision_config.patch_size = 16
    native = Qwen3_5ForConditionalGeneration(model.config).float()
    model.model.visual = native.model.visual
    model.model.language_model.requires_grad_(True)
    model.lm_head.requires_grad_(True)
    model.auxiliary_heads.requires_grad_(True)
    model.model.visual.requires_grad_(False)
    batch['pixel_values_videos'] = torch.randn(frames * 8, 1536)
    head = MaskGroundingHead(head_config(lm_dim=32, vit_dim=32, phrase_max=8))
    model.auxiliary_heads.mdg = head
    model.mdg_settings = sb.settings(dict(block(), lora_rank=lora_rank))
    from student_pilot.mdg_lora import install
    install(model, lora_rank)
    model.mdg_tau, model.mdg_tau_info = .37, {'source': 'init_artifact'}
    from tests.test_e2e_ground_tokens import processor as atomic_processor
    from student_pilot import ground_tokens
    from student_pilot.carrier_c1_routing import add_routing_tokens
    proc = atomic_processor()
    add_routing_tokens(proc, include_ground=True)
    ground_tokens.add(proc)
    ground_tokens.initialize(model, proc)
    model.mdg_tokenizer = proc.tokenizer
    model.train()
    batch['aux_mdg_labels'] = ['chair', 'table']
    target = targets(frames=frames)
    return model, batch, target


class Rows:
    def __init__(self, batch, target):
        self.batch, self.target = batch, target

    def count(self, stream):
        return 12

    def get(self, stream, index):
        if stream == 'mdg':
            # Cross chunk boundaries on different ranks, exercising synchronized padding.
            q = 1 + index % 3
            batch = {**self.batch, 'aux_mdg_labels': ['chair', 'table', 'lamp'][:q]}
            return batch, targets(labels=q, frames=32), {'qid': str(index)}
        batch = {k: v for k, v in self.batch.items() if k != 'aux_mdg_labels'}
        batch['labels'] = torch.full_like(batch['input_ids'], -100)
        batch['labels'][0, -2:] = batch['input_ids'][0, -2:]
        return batch, None, {'qid': str(index)}


def worker(rank, directory):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method='file://' + directory + '/rendezvous', rank=rank, world_size=4)
    try:
        model, batch, target = fixture(lora_rank=4)
        # Tiny run retains the production optimize/checkpoint/export paths, without pose supervision.
        model.mdg_settings['label_chunk'] = 2
        wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
        optimizer = torch.optim.AdamW(parameter_groups(wrapped), weight_decay=.01)
        rows = Rows(batch, target)
        plans = list(mixed_indices(dict(vqa=12, mdg=12), 3, training_mode='final', mix=['vqa', 'mdg'], world=4))
        with small_layers():
            wrapped(batch, target, stream='mdg')['loss'].backward()
            assert all(p.grad is None for _, p in full_ft.named_trainable(wrapped)
                       if all(p is not q for q in model.auxiliary_heads.parameters()))
            for name, parameter in model.auxiliary_heads.mdg_lora.named_parameters():
                assert parameter.dtype == torch.float32
                assert parameter.grad is not None and torch.isfinite(parameter.grad).all()
                if name.endswith('.B'):
                    assert parameter.grad.norm() > 0, name
            optimizer.zero_grad(set_to_none=True)
            for step in range(3):
                info, _ = run.optimize_step(wrapped, optimizer, rows, plans[step], rank, torch.device('cpu'), step+1, True)
                assert all(torch.isfinite(torch.tensor(v)) for v in info['components'].values())
                assert info['gradient_norms']['mdg_lora'] > 0
                if step == 0:
                    checkpoint = run.checkpoint(Path(directory)/'checkpoint', wrapped, optimizer, {'stageb': True}, 1)
            expected = {n: p.detach().clone() for n, p in full_ft.named_trainable(wrapped)}
            assert run.restore(checkpoint, wrapped, optimizer, {'stageb': True}) == 1
            for step in (1, 2):
                run.optimize_step(wrapped, optimizer, rows, plans[step], rank, torch.device('cpu'), step+1, True)
            for name, parameter in full_ft.named_trainable(wrapped):
                torch.testing.assert_close(parameter, expected[name], rtol=0, atol=0)
            cfg = dict(base_identity='fixture', mdg=dict(block(), lora_rank=4), code=file_pin(Path(directory)/'code.json'))
            run.export(Path(directory)/'m3', wrapped, model, cfg, 3)
        if rank == 0:
            head, meta = load_artifact(Path(directory)/'m3/mdg')
            assert meta['base_artifact'] == file_pin(Path(directory)/'m3/artifact.json')
            assert meta['tau'] == .37
            assert (Path(directory)/'m3/mdg/lora.pt').is_file()
            write(Path(directory)/'result.json', dict(world=4, steps=3, resume_exact=True, export=True))
    finally:
        dist.destroy_process_group()
    if rank == 0:
        check_lora_export(Path(directory)/'m3')


def check_lora_export(directory):
    import numpy as np
    from student_pilot import mdg_eval, mdg_lora
    model, batch, _ = fixture(lora_rank=4)
    run.load_artifact(model, file_pin(directory/'artifact.json'))
    head, meta = load_artifact(directory/'mdg')
    expected = {n: p.clone() for n, p in model.auxiliary_heads.mdg_lora.state_dict().items()}
    mdg_lora.load(model, directory/'mdg', meta)
    for name, value in model.auxiliary_heads.mdg_lora.state_dict().items():
        assert torch.equal(value, expected[name]), name
    model.eval()
    model.mdg_head = head
    from tests.test_e2e_ground_tokens import processor as atomic_processor
    proc = atomic_processor()
    from student_pilot.carrier_c1_routing import add_routing_tokens
    add_routing_tokens(proc, include_ground=True)
    model.mdg_tokenizer = proc.tokenizer
    with small_layers(), torch.no_grad():
        out = model(batch, stream='mdg')[-1]
        reference = head.decode(out)
        reference.update(clip_prob=out['clip_logit'].sigmoid(), frame_prob=out['frame_logit'].sigmoid())
        with mock.patch.object(mdg_eval, 'trainer_row', return_value=({}, {})), \
                mock.patch.object(mdg_eval, 'selection_id', return_value='fixture'), \
                mock.patch('student_pilot.carrier_c1_canary.prompt_batch', return_value=batch):
            predicted, _ = mdg_eval.predict(model, None, {}, {}, batch['aux_mdg_labels'],
                                           directory, torch.device('cpu'), 2)
    for key, value in reference.items():
        if key == 'present':
            continue
        value = value.cpu().numpy() if torch.is_tensor(value) else np.asarray(value)
        if key == 'area':
            value = value.astype(np.float64) / np.prod(reference['mask'].shape[-2:])
        np.testing.assert_array_equal(value, predicted[key], err_msg=key)


class StageB(unittest.TestCase):
    def test_lora_prefix_init_and_non_mdg_streams_are_bitwise_equal(self):
        from student_pilot import mdg_lora, mdg_features
        from tests.test_mdg_features import cache_tensors
        from tests.test_carrier_c1_final import final_fixture
        model, batch, target = fixture(frames=2)
        reference = copy.deepcopy(model)
        model.mdg_settings['lora_rank'] = 4
        mdg_lora.install(model, 4)
        with small_layers():
            with sb.capture_mode(model), sb.capture_mode(reference):
                a, b = mdg_features.capture_prefix(model, batch), mdg_features.capture_prefix(reference, batch)
                self.assertTrue(torch.equal(a.hidden, b.hidden))
                for key, value in cache_tensors(a.cache).items():
                    self.assertTrue(torch.equal(value, cache_tensors(b.cache)[key]))
                sa = mdg_features.suffix_states(model, a, ['chair', 'long table'], train_adapters=True)
                sb_ = mdg_features.suffix_states(reference, b, ['chair', 'long table'])
                self.assertTrue(torch.equal(sa.query, sb_.query))
                self.assertTrue(torch.equal(sa.phrase, sb_.phrase))
            for a, b in zip(model(batch, stream='mdg'), reference(batch, stream='mdg')):
                for key in a:
                    self.assertTrue(torch.equal(a[key], b[key]), key)
        model, batch, target = final_fixture()
        reference = copy.deepcopy(model)
        mdg_lora.install(model, 4)
        with torch.no_grad():
            for adapter in model.auxiliary_heads.mdg_lora.values():
                adapter.B.normal_()
        model.eval(); reference.eval()
        def equal(a, b):
            if torch.is_tensor(a):
                self.assertTrue(torch.equal(a, b))
            elif isinstance(a, dict):
                for key in a:
                    equal(a[key], b[key])
            elif isinstance(a, (tuple, list)):
                for x, y in zip(a, b):
                    equal(x, y)
            else:
                self.assertEqual(a, b)
        with torch.no_grad():
            for stream in ('pose', 'vqa', 'pointing', 'routing', 'readout'):
                with self.subTest(stream=stream):
                    supplied = target if stream == 'pose' else None
                    equal(model(batch, supplied, stream=stream), reference(batch, supplied, stream=stream))
        from student_pilot.carrier_c1_decode import generate
        from tests.test_carrier_c1_final import FakeTokenizer
        processor = SimpleNamespace(tokenizer=FakeTokenizer(), _routing_tokens={'ids': {'<pose': 39}})
        def eos(ids, logits):
            result = torch.full_like(logits, -1e9)
            result[:, 1] = 0
            return result
        equal(generate(model, processor, batch, logits_processor=eos),
              generate(reference, processor, batch, logits_processor=eos))

    def test_lora_gradients_cache_and_optimizer_isolation(self):
        from student_pilot import mdg_features
        from tests.test_mdg_features import cache_tensors
        model, batch, target = fixture(frames=2, lora_rank=4)
        groups = parameter_groups(model)
        group = next(g for g in groups if g['name'] == 'mdg_lora')
        self.assertEqual(group['lr'], 1e-4)
        self.assertEqual(group['weight_decay'], 0.)
        optimizer = torch.optim.AdamW(groups, weight_decay=.01)
        before = {n: p.detach().clone() for n, p in model.named_parameters()}
        flags = {n: p.requires_grad for n, p in model.named_parameters()}
        with small_layers():
            with sb.capture_mode(model):
                prefix = mdg_features.capture_prefix(model, batch)
                saved = cache_tensors(prefix.cache)
                states = mdg_features.suffix_states(model, prefix, ['a', 'long table'], chunk=2, train_adapters=True)
                with torch.enable_grad():
                    (states.query.square().sum() + states.phrase.square().sum()).backward()
                for key, value in saved.items():
                    self.assertTrue(torch.equal(value, cache_tensors(prefix.cache)[key]))
                self.assertFalse(prefix.hidden.requires_grad)
            optimizer.zero_grad(set_to_none=True)
            model(batch, target, stream='mdg')['loss'].backward()
            self.assertTrue(all(p.grad is None for _, p in full_ft.base_parameters(model)))
            for name, p in model.auxiliary_heads.mdg_lora.named_parameters():
                self.assertIsNotNone(p.grad, name)
                self.assertTrue(torch.isfinite(p.grad).all(), name)
                if name.endswith('.B'):
                    self.assertGreater(float(p.grad.norm()), 0, name)
            optimizer.step()
            changed = {n for n, p in model.named_parameters() if not torch.equal(p, before[n])}
            self.assertTrue(any(n.startswith('auxiliary_heads.mdg_lora.') for n in changed))
            self.assertTrue(any(n.startswith('auxiliary_heads.mdg.') for n in changed))
            self.assertTrue(all(n.startswith(('auxiliary_heads.mdg_lora.', 'auxiliary_heads.mdg.')) for n in changed))
            self.assertEqual(flags, {n: p.requires_grad for n, p in model.named_parameters()})
            with sb.capture_mode(model):
                self.assertTrue(torch.equal(prefix.hidden, mdg_features.capture_prefix(model, batch).hidden))
            optimizer.zero_grad(set_to_none=True)
            model(batch, target, stream='mdg')['loss'].backward()
            self.assertTrue(all(float(p.grad.norm()) > 0 for p in model.auxiliary_heads.mdg_lora.parameters()))

    def test_lora_gate_skips_prefix_and_padding_and_restores_after_error(self):
        from student_pilot import mdg_lora
        model, _, _ = fixture(frames=2, lora_rank=4)
        projection = model.model.language_model.layers[1].self_attn.q_proj
        adapter = projection._mdg_adapter
        with torch.no_grad():
            adapter.B.normal_()
        x = torch.randn(2, 5, 32, requires_grad=True)
        mask = torch.tensor([[False, False, True, True, False], [False, False, True, False, False]])
        seen = []
        handle = adapter.register_forward_pre_hook(lambda m, args: seen.append(args[0].shape[0]))
        try:
            plain = projection(x)
            self.assertEqual(seen, [])
            with mdg_lora.suffix_mask(model, mask):
                out = projection(x)
                changed = x.detach().clone()
                changed[~mask] += 1000
                perturbed = projection(changed)
            self.assertTrue(torch.equal(out[mask], perturbed[mask]))
            self.assertTrue(torch.equal(out[~mask], plain[~mask]))
            out[mask].sum().backward()
            self.assertEqual(float(x.grad[~mask].abs().sum()), 0.)
            self.assertEqual(seen, [3, 3])
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                with mdg_lora.suffix_mask(model, mask):
                    raise RuntimeError('fixture')
            self.assertTrue(torch.equal(projection(x), plain))
            self.assertEqual(seen, [3, 3])
            with mdg_lora.suffix_mask(model, torch.zeros_like(mask)):
                self.assertTrue(torch.equal(projection(x), plain))
            self.assertEqual(seen, [3, 3])
            weight = projection.weight
            with mock.patch.object(projection, 'forward', side_effect=RuntimeError('fixture')):
                with self.assertRaisesRegex(RuntimeError, 'fixture'), mdg_lora.suffix_mask(model, mask):
                    projection(x)
            self.assertIs(projection.weight, weight)
        finally:
            handle.remove()

    def test_lora_artifact_pins_and_rank_mismatch(self):
        from student_pilot import mdg_lora
        model, _, _ = fixture(frames=2, lora_rank=4)
        directory = root()
        metadata = mdg_lora.export(directory, model, model.state_dict())
        mdg_lora.load(model, directory, metadata)
        changed = copy.deepcopy(metadata)
        changed['lora_config']['rank'] = 8
        changed['lora_config']['alpha'] = 16
        with self.assertRaisesRegex(ValueError, 'rank differs'):
            mdg_lora.load(model, directory, changed)
        with self.assertRaisesRegex(ValueError, 'matching artifact metadata'):
            mdg_lora.load(model, directory, {})
        with (directory/'lora.pt').open('ab') as handle:
            handle.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed pinned'):
            mdg_lora.load(model, directory, metadata)

    def test_lora_fsdp_mixed_precision_keeps_fp32_adapters(self):
        import torch.testing._internal.distributed.fake_pg
        directory = root()
        dist.init_process_group('fake', init_method='file://' + str(directory/'rendezvous'), rank=0, world_size=4)
        try:
            model, batch, target = fixture(frames=2, lora_rank=4)
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=True)
            with small_layers():
                loss = wrapped(batch, target, stream='mdg')['loss']
                loss.backward()
            for name, parameter in full_ft.named_trainable(wrapped):
                if not name.startswith('auxiliary_heads.'):
                    self.assertIsNone(parameter.grad, name)
            for name, parameter in model.auxiliary_heads.mdg_lora.named_parameters():
                self.assertEqual(parameter.dtype, torch.float32)
                self.assertEqual(parameter.grad.dtype, torch.float32)
                if name.endswith('.B'):
                    self.assertGreater(float(parameter.grad.norm()), 0., name)
        finally:
            dist.destroy_process_group()

    def test_absent_recipe_and_config_unchanged_and_lora_validated(self):
        from student_pilot.carrier_c1 import RECIPE
        cfg = dict(schema='carrier-c1-run-v1', recipe=RECIPE, init='base', parallel='fsdp', all_frames=True,
                   streams=dict(pose={}, vqa={}, pointing={}), carrier_placement=C1_A)
        before = json.dumps(cfg, sort_keys=True)
        run.validate(cfg)
        self.assertEqual(json.dumps(cfg, sort_keys=True), before)
        self.assertEqual(recipe_for(cfg), RECIPE)
        self.assertEqual(sb.settings(block())['lora_rank'], 0)
        self.assertEqual(sb.settings({**block(), 'lora_rank': 2})['lora_rank'], 2)
        for rank in (-1, True, 1.5):
            with self.assertRaisesRegex(ValueError, 'nonnegative integer'):
                sb.settings({**block(), 'lora_rank': rank})
        final = dict(cfg, training_mode='final', frame_layout='duplicate', frame_markers=True,
                     depth_fov_source='pose_head', world_size=4, reference_world_size=32,
                     mix=['pose', 'vqa', 'vqa', 'mdg', 'routing', 'pose', 'vqa', 'vqa', 'pointing', 'routing'],
                     mdg=block(), streams=dict(pose={}, vqa={}, pointing={}, routing={}, mdg=block()['clips_jsonl']))
        final['scheduled_sampling'] = dict(seed=17, max_own_probability=1., pose_open_deg=45.,
            pose_full_deg=25., fov_open_deg=2., depth_open_absrel=.25, ema_steps=100,
            force_from_step=None, exposure_from_step=None, exposure_probability=0.)
        final['recipe'] = recipe_for(final)
        run.validate(final)
        self.assertEqual(final['recipe']['global_batch'], 320)
        self.assertEqual(final['recipe']['mix'].count('mdg'), 8)
        for changed in (dict(final, training_mode='mixed'), dict(final, frame_markers=False)):
            with self.assertRaises(ValueError):
                run.validate(changed)

    def test_absent_preparation_receipt_bytes_and_streams(self):
        from student_pilot.carrier_c1 import RECIPE
        from student_pilot.p3_provenance import encoded
        directory = root()
        pins = {name: {'path': '/fixture/' + name, 'sha256': 'a'*64}
                for name in ('pose', 'vqa', 'pointing', 'model', 'division')}
        databases = {name: {'path': '/fixture/' + name + '.sqlite', 'sha256': 'b'*64}
                     for name in ('pose', 'vqa', 'pointing')}
        camera = {'point_depth': {'fixture': True}}
        source = dict(schema='decoupled-v-preparation-v1', count=321152,
                      settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames', camera=camera),
                      inputs={'division': pins['division']}, model=pins['model'], database=databases['pose'])
        values = {'/fixture/pose': source, '/fixture/model': dict(kind='base', base_identity='base',
                  root='/fixture/snapshot', files={'config.json': 'c'*64})}
        for name in ('vqa', 'pointing'):
            values['/fixture/' + name] = dict(schema='c1-stream-v1', stream=name, division=pins['division'],
                heldout_overlap=0, gt_masks_only=True, count=1, database=databases[name])
        cfg = dict(schema='carrier-c1-run-v1', recipe=RECIPE, init='base', parallel='fsdp', all_frames=True,
                   streams={k: pins[k] for k in ('pose', 'vqa', 'pointing')}, carrier_placement=C1_A,
                   base_identity='base', preparation_output=str(directory/'prepared'))
        def connection(pin):
            result = mock.MagicMock()
            count = 321152 if pin == databases['pose'] else 1
            result.__enter__.return_value.execute.return_value.fetchone.return_value = (count, 0, count-1)
            return result
        with mock.patch.object(run, 'authenticate', return_value='d'*40), \
                mock.patch.object(run, 'pinned', side_effect=lambda p: Path(p['path'])), \
                mock.patch.object(run, 'load', side_effect=lambda p: values[str(p)]), \
                mock.patch.object(run, 'connect', side_effect=connection), \
                mock.patch('student_pilot.students.get_student', return_value=dict(snapshot=Path('/fixture/snapshot'),
                                                                                  config_sha256='c'*64)):
            receipt = run.prepare(cfg)
        expected = dict(schema='c1-preparation-v1', config_sha256=run.identity(cfg), trainer_commit='d'*40,
            streams={k: dict(receipt=pins[k], database=databases[k], count=321152 if k == 'pose' else 1,
                             source_count=321152 if k == 'pose' else 1) for k in ('pose', 'vqa', 'pointing')},
            model=pins['model'], division=pins['division'], camera=camera, depth=camera['point_depth'],
            carrier_placement=C1_A, training_mode='mixed', depth_enabled=True, recipe=RECIPE)
        self.assertEqual(receipt, expected)
        self.assertEqual((directory/'prepared/receipt.json').read_bytes(), (encoded(expected)+'\n').encode())

    def test_native_forward_backward_modes_and_base_isolation(self):
        model, batch, target = fixture()
        modes = [(m, m.training) for m in model.modules()]
        with small_layers():
            result = model(batch, target, stream='mdg')
        result['loss'].backward()
        self.assertTrue(torch.isfinite(result['loss']))
        self.assertTrue(all(m.training == flag for m, flag in modes))
        for name, parameter in model.auxiliary_heads.mdg.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
            self.assertTrue(torch.isfinite(parameter.grad).all(), name)
        self.assertTrue(all(p.grad is None for _, p in full_ft.base_parameters(model)))
        groups = parameter_groups(model)
        self.assertEqual(next(g['lr'] for g in groups if g['name'] == 'heads_mdg'), model.recipe['learning_rate'])
        model.mdg_settings['lr_scale'] = .25
        self.assertEqual(next(g['lr'] for g in parameter_groups(model) if g['name'] == 'heads_mdg'),
                         model.recipe['learning_rate'] * .25)

    def test_rank_zero_prefix_and_other_stream_bitwise_equal(self):
        from student_pilot.mdg_features import capture_prefix
        model, batch, target = fixture()
        plain = copy.deepcopy(model)
        plain.auxiliary_heads.mdg = None
        modes = [(m, m.training) for m in model.modules()]
        with small_layers():
            with sb.capture_mode(model):
                before = capture_prefix(model, batch).hidden.clone()
            model(batch, target, stream='mdg')['loss'].backward()
            with sb.capture_mode(model):
                after = capture_prefix(model, batch).hidden
            with sb.capture_mode(plain):
                reference = capture_prefix(plain, batch).hidden
        self.assertTrue(torch.equal(before, after))
        self.assertTrue(torch.equal(before, reference))
        self.assertTrue(all(m.training == flag for m, flag in modes))
        vqa, _, _ = Rows(batch, target).get('vqa', 0)
        a, b = model(vqa, stream='vqa'), plain(vqa, stream='vqa')
        self.assertTrue(torch.equal(a['loss'], b['loss']))

    def test_first_batch_ranks(self):
        model, batch, target = fixture()
        for _, parameter in full_ft.base_parameters(model):
            parameter.data = parameter.data.bfloat16()
        model.eval()
        plans = list(mixed_indices(dict(mdg=12), 1, training_mode='final', mix=['mdg'], world=4))
        with small_layers():
            records = run.check_plan_rows(model, Rows(batch, target), plans, [0, 1, 2, 3])
        self.assertEqual(len(records), 4)
        for rank, record in enumerate(records):
            self.assertEqual(record['rank'], rank)
            self.assertTrue(record['finite'], record)
            self.assertGreater(record['Q'], 0)
            self.assertGreater(record['prompt_tokens'], 0)
            self.assertGreater(record['peak_rss_bytes'], 0)
            self.assertEqual(set(record['loss_parts']), {'total', 'bce', 'dice', 'frame', 'clip', 'iou'})

    def test_prepare_pins_rows_exclusions_splits_and_source_mutation(self):
        from tests.test_grounding_train import fixture as data_fixture
        directory = root()
        _, index = data_fixture(directory/'rasters')
        clips = [dict(row, dataset='d1') for row in index['train'] + index['val']]
        path = directory/'clips.jsonl'
        path.write_text(''.join(json.dumps(row) + '\n' for row in clips))
        write(directory/'vocab.json', ['chair', 'table'])
        write(directory/'confusers.json', {'chair': ['table']})
        (directory/'stem.pth').write_bytes(b'fixture pin only')
        config = dict(block(), clips_jsonl=str(path), rasters=str(directory/'rasters'),
                      vocab=str(directory/'vocab.json'), confusers=str(directory/'confusers.json'),
                      stem_weights=str(directory/'stem.pth'))
        cfg = dict(mdg=config, streams={'mdg': str(path)}, preparation_output=str(directory/'prepared'))
        value = sb.prepare(cfg, {'d1/heldout'}, set())
        self.assertEqual(value['count'], 3)
        admitted = sb.verify(cfg, value)
        groups = [{r['scene'] for r in admitted[k]} for k in ('train', 'tau', 'val')]
        self.assertTrue(all(not a & b for i, a in enumerate(groups) for b in groups[i+1:]))
        self.assertEqual(value['inputs']['clips_jsonl'], file_pin(path))
        with self.assertRaisesRegex(ValueError, 'benchmark-scene'):
            sb.prepare(dict(cfg, preparation_output=str(directory/'refused')), {'d1/scene_0'}, set())
        with self.assertRaisesRegex(ValueError, 'configuration/source'):
            sb.verify(dict(cfg, mdg=dict(config, weight=2)), value)
        (directory/'confusers.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'configuration/source'):
            sb.verify(cfg, value)

    def test_attach_init_artifact_and_export_identity(self):
        directory = root()
        model, batch, target = fixture()
        saved = {k: v.clone() for k, v in model.auxiliary_heads.mdg.state_dict().items()}
        metadata = dict(base_artifact={'path': '/fixture/base.json', 'sha256': 'a'*64},
                        tau=.41, trainer_commit='1'*40, step=8, metrics={})
        save_artifact(directory/'init', model.auxiliary_heads.mdg, metadata)
        sb.attach(model, dict(block(), init_artifact=str(directory/'init')),
                  SimpleNamespace(tokenizer=Tokenizer()))
        self.assertEqual(model.mdg_tau, .41)
        for name, tensor in model.auxiliary_heads.mdg.state_dict().items():
            self.assertTrue(torch.equal(tensor, saved[name]))
        write(directory/'artifact.json', {'milestone': 5})
        write(directory/'code.json', {'commit': '2'*40})
        sb.export(directory, model, model.state_dict(), {'code': file_pin(directory/'code.json')},
                  5, model.mdg_tau, model.mdg_tau_info)
        head, meta = load_artifact(directory/'mdg')
        self.assertEqual(meta['base_artifact'], file_pin(directory/'artifact.json'))
        self.assertEqual(meta['tau'], .41)
        for name, tensor in head.state_dict().items():
            self.assertTrue(torch.equal(tensor, saved[name]))

    def test_standalone_stageb_bundle_loads_without_training_inputs(self):
        from tests.test_mdg_runtime import Runtime, processor
        from student_pilot import mdg_runtime, mdg_eval
        from tests.test_carrier_c1_run import RunnerTests
        Runtime.setUpClass()
        directory = root()
        model = copy.deepcopy(Runtime.official)
        model.auxiliary_heads.mdg = MaskGroundingHead(head_config(lm_dim=32, vit_dim=32, phrase_max=8))
        model.mdg_tau, model.mdg_tau_info = .37, {'source': 'init_artifact'}
        from student_pilot.mdg_lora import install
        install(model, 4)
        with torch.no_grad():
            for adapter in model.auxiliary_heads.mdg_lora.values():
                adapter.B.normal_(std=.01)
        receipt = dict(Runtime.receipt, mdg=dict(block(), lora_rank=4))
        write(directory/'receipt.json', receipt)
        write(directory/'code.json', {'commit': '1'*40})
        cfg = dict(Runtime.native, mdg=receipt['mdg'], preparation=file_pin(directory/'receipt.json'),
                   code=file_pin(directory/'code.json'))
        write(directory/'config.json', cfg)
        with RunnerTests().local_collectives(), \
                mock.patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(directory/'milestone', model, model, cfg, 4)
        bundle = mdg_runtime.make_bundle(directory/'bundle', config=directory/'config.json',
            receipt=directory/'receipt.json', model_manifest=Runtime.sources['model_manifest'],
            base_dir=Runtime.sources['base_dir'], artifact_dir=directory/'milestone')
        with mock.patch.object(run, 'processor_for', side_effect=processor), \
                mock.patch.object(run, 'prepared', side_effect=AssertionError('training inputs opened')), \
                mock.patch.object(run, 'load_model', side_effect=AssertionError('base shards opened')):
            loaded, _, native = mdg_eval.load_runtime(file_pin(directory/'config.json'),
                file_pin(directory/'milestone/artifact.json'), directory/'milestone/mdg',
                torch.device('cpu'), file_pin(bundle))
        self.assertEqual(native, cfg)
        for name, tensor in model.auxiliary_heads.mdg_lora.state_dict().items():
            self.assertTrue(torch.equal(tensor, loaded.auxiliary_heads.mdg_lora.state_dict()[name]), name)
        for name, tensor in model.auxiliary_heads.mdg.state_dict().items():
            self.assertTrue(torch.equal(tensor, loaded.mdg_head.state_dict()[name]), name)
            self.assertTrue(torch.equal(tensor, loaded.auxiliary_heads.mdg.state_dict()[name]), name)

    def test_suffix_call_count_is_equal_across_label_counts(self):
        model, batch, _ = fixture()
        model.mdg_settings['label_chunk'] = 2
        calls = []
        hook = model.model.language_model.register_forward_hook(lambda *args: calls.append(1))
        try:
            with small_layers(), mock.patch.object(dist, 'is_initialized', return_value=True), \
                    mock.patch.object(dist, 'all_reduce', side_effect=lambda value, **kwargs: value.fill_(3)):
                for q in (1, 2, 3, 1):
                    start = len(calls)
                    row = dict(batch, aux_mdg_labels=['chair', 'table', 'lamp'][:q])
                    result = model(row, targets(labels=q, frames=32), stream='mdg')
                    self.assertEqual(len(calls) - start, 3)  # One prefill, two suffix chunks.
                    self.assertEqual(result['metrics']['mdg']['Q'], q)
                    self.assertEqual(result['metrics']['mdg']['padded_Q'], 3)
        finally:
            hook.remove()

    def test_fsdp_lifecycle_with_fake_group_is_not_gloo_proof(self):
        import torch.testing._internal.distributed.fake_pg
        directory = root()
        dist.init_process_group('fake', init_method='file://' + str(directory/'rendezvous'), rank=0, world_size=4)
        try:
            model, batch, target = fixture(lora_rank=4)
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
            with small_layers():
                for _ in range(3):
                    wrapped(batch, target, stream='mdg')['loss'].backward()
                    vqa, _, _ = Rows(batch, target).get('vqa', 0)
                    wrapped(vqa, stream='vqa')['loss'].backward()
        finally:
            dist.destroy_process_group()

    def test_no_init_calibrates_only_the_reserved_training_slice(self):
        from tests.test_grounding_train import fixture as data_fixture
        from student_pilot.mdg_train import ClipDataset
        directory = root()
        config, index = data_fixture(directory/'data')
        write(directory/'confusers.json', {'chair': ['table']})
        config['confusers'] = str(directory/'confusers.json')
        model, batch, _ = fixture()
        model.mdg_tau = None
        model.mdg_receipt, model.mdg_processor = {}, SimpleNamespace(tokenizer=Tokenizer())
        data = ClipDataset(index['train'][:1], ['chair', 'table'], model.mdg_processor, {}, config)
        prompt = {k: v for k, v in batch.items() if k != 'aux_mdg_labels'}
        modes = [(m, m.training) for m in model.modules()]
        with small_layers(), mock.patch.object(sb, 'dataset', return_value=data) as selected, \
                mock.patch('student_pilot.carrier_c1_canary.prompt_batch', return_value=prompt):
            tau, report = sb.calibrate(model, model)
        selected.assert_called_once_with(model.mdg_receipt, model.mdg_processor, 'tau')
        self.assertTrue(0 <= tau <= 1)
        self.assertFalse(report['val_used'])
        self.assertFalse(report['sampler_used'])
        self.assertEqual(report['n_clips'], 1)
        self.assertTrue(all(m.training == flag for m, flag in modes))

    def test_serial_native_optimizer_checkpoint_resume_and_milestone(self, lora_rank=0):
        from tests.test_carrier_c1_run import RunnerTests
        directory = root()
        write(directory/'code.json', dict(commit='1'*40))
        model, batch, target = fixture(lora_rank=lora_rank)
        model.mdg_settings['label_chunk'] = 2
        optimizer = torch.optim.AdamW(parameter_groups(model), weight_decay=.01)
        rows = Rows(batch, target)
        plans = list(mixed_indices(dict(vqa=12, mdg=12), 3, training_mode='final', mix=['vqa', 'mdg'], world=4))
        with small_layers(), RunnerTests().local_collectives():
            for step in range(3):
                run.optimize_step(model, optimizer, rows, plans[step], 0, torch.device('cpu'), step+1)
                if step == 0:
                    saved = run.checkpoint(directory/'checkpoint', model, optimizer, {'stageb': True}, 1)
            expected = {n: p.detach().clone() for n, p in full_ft.named_trainable(model)}
            self.assertEqual(run.restore(saved, model, optimizer, {'stageb': True}), 1)
            for step in (1, 2):
                run.optimize_step(model, optimizer, rows, plans[step], 0, torch.device('cpu'), step+1)
            for name, parameter in full_ft.named_trainable(model):
                torch.testing.assert_close(parameter, expected[name], rtol=0, atol=0, msg=name)
            cfg = dict(base_identity='fixture', mdg=dict(block(), lora_rank=lora_rank), code=file_pin(directory/'code.json'))
            with mock.patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
                run.export(directory/'m3', model, model, cfg, 3)
            head, meta = load_artifact(directory/'m3/mdg')
            self.assertEqual(meta['base_artifact'], file_pin(directory/'m3/artifact.json'))
            self.assertTrue(run.existing_export(directory/'m3', cfg, 3))
            fresh, _, _ = fixture(lora_rank=lora_rank)
            run.load_artifact(fresh, file_pin(directory/'m3/artifact.json'))
            for name, tensor in model.auxiliary_heads.mdg.state_dict().items():
                self.assertTrue(torch.equal(tensor, fresh.auxiliary_heads.mdg.state_dict()[name]), name)
        if lora_rank:
            check_lora_export(directory/'m3')

    def test_lora_serial_resume_export_and_predict(self):
        self.test_serial_native_optimizer_checkpoint_resume_and_milestone(lora_rank=4)

    @unittest.skipUnless(__import__('tests.test_fsdp', fromlist=['SOCKETS']).SOCKETS,
                         'sandbox blocks local sockets required by world-4 Gloo')
    def test_world_four_checkpoint_resume_export(self):
        directory = root()
        write(directory/'code.json', dict(commit='1'*40))
        # Native models are imported before forking; no per-rank environment/model downloads.
        fixture()
        mp.start_processes(worker, args=(str(directory),), nprocs=4, join=True, start_method='fork')
        self.assertTrue(load(directory/'result.json')['resume_exact'])
