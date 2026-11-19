"""Frozen GXP on the CP1 final mix; retained, offline native-Qwen CPU fixtures."""
import copy
from contextlib import ExitStack, redirect_stdout
import io
import hashlib
import json
import os
from pathlib import Path
import tempfile
import subprocess
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_data as data, carrier_c1_run as run, g3t_online as gx
from student_pilot import carrier_c1_decode as decode, full_ft
from student_pilot.carrier_c1 import CarrierC1, parameter_groups
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import file_pin, load, write
from tests import test_carrier_c1_final as final
from tests.test_carrier_c1 import Tokenizer
from tests.test_carrier_c1_layout import raw_batch
from tests import test_carrier_c1_single_image as images
from tests.test_gx_carrier import TinyEncoder, settings, fusion_settings, collectives, architecture
from tests.test_fsdp import SOCKETS


def directory():
    return Path(tempfile.mkdtemp(prefix='gxp_mix_', dir=os.environ['LANE_TEST_OUTPUT']))


def configuration(world=4):
    cfg = dict(schema='carrier-c1-run-v1', training_mode='final', depth_enabled=True,
        depth_fov_source='pose_head', frame_layout='duplicate', frame_markers=True,
        init='base', parallel='fsdp', all_frames=True, carrier_placement=data.C1_C,
        streams={s: {} for s in ('pose', 'vqa', 'pointing', 'routing')},
        mix=['pose', 'pose', 'vqa', 'pointing', 'routing'], world_size=world,
        steps=52, milestones=[50, 52], pose_lr_scale=.6, lm_lr_scale=.6,
        weights=dict(pointing=1., depth=.25),
        scheduled_sampling=dict(seed=17, max_own_probability=0., pose_open_deg=20., pose_full_deg=10.,
            fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=None,
            exposure_from_step=None, exposure_probability=0.),
        init_artifact=dict(artifact=dict(path='/fixture/m800/artifact.json', sha256='a'*64),
                           lm='full', heads=['pose', 'depth']),
        geometry_online={**settings(), 'patch_fusion': fusion_settings(50)})
    cfg['geometry_online'].pop('fail_fast')
    cfg['recipe'] = recipe_for(cfg)
    return cfg


def fixture(geometry=True, placement=data.C1_C, geometry_settings=None):
    cfg = configuration()
    if geometry_settings is not None:
        cfg['geometry_online'] = copy.deepcopy(geometry_settings)
    def construct(*args, **kwargs):
        kwargs.update(frame_layout='duplicate')
        if geometry:
            kwargs.update(geometry_online=cfg['geometry_online'],
                          geometry_runtime=dict(image_mean=[.5]*3, image_std=[.25]*3))
        return CarrierC1(*args, **kwargs)
    with patch.object(final, 'CarrierC1', side_effect=construct), patch.object(gx, 'G3TEncoder', TinyEncoder):
        model, _, targets = final.final_fixture(placement)
    model.recipe = cfg['recipe']
    raw = raw_batch(32)
    # Ordinary text tokens stand for "Frame k:" before each native vision group.
    ids = torch.tensor([[2] + [v for g in range(32) for v in (20, 10+g%20, 62, 61, 63)] + [10, 11]])
    raw.update(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
               mm_token_type_ids=torch.where(ids == 61, 2, 0))
    batch = data.insert_frame_carriers(raw, Tokenizer(), carrier_placement=placement,
                                       frame_layout='duplicate')
    batch['labels'][0, -2:] = batch['input_ids'][0, -2:]
    return model, batch, targets


def image_batch():
    result = images.ImageProcessor()(text=['<|vision_start|><|image_pad|><|vision_end|>'])
    result['input_ids'] = torch.cat((result['input_ids'], torch.tensor([[10, 11]])), 1)
    result['attention_mask'] = torch.ones_like(result['input_ids'])
    result['mm_token_type_ids'] = torch.cat((result['mm_token_type_ids'], torch.zeros(1, 2, dtype=torch.long)), 1)
    result['labels'] = torch.full_like(result['input_ids'], -100)
    result['labels'][0, -2:] = result['input_ids'][0, -2:]
    return result


class MixRows:
    def __init__(self, batch, targets):
        self.batch, self.targets = batch, targets
        self.counts = dict(pose=37, vqa=41, pointing=43, routing=47)

    def count(self, stream):
        return self.counts[stream]

    def get(self, stream, index):
        batch = {k: v.clone() for k, v in self.batch.items()}
        if stream in ('vqa', 'pointing') and index % 2:
            batch = image_batch()
        pixel = 'pixel_values_videos' if 'video_grid_thw' in batch else 'pixel_values'
        batch[pixel] += index * .001
        if stream == 'routing':
            batch['input_ids'][0, -2:] = torch.tensor([40, 41])
            batch['labels'][0, -2:] = batch['input_ids'][0, -2:]
        return batch, self.targets if stream == 'pose' else None, {'qid': f'{stream}-{index}'}

    def close(self):
        pass


def plans(cfg, steps):
    r = cfg['recipe']
    return list(data.mixed_indices(MixRows(None, None).counts, steps, training_mode='final',
                                   seed=r['seed'], mix=r['mix'], world=r['world_size']))


def flattened(plan):
    return [(s, i) for s, indices in plan for i in indices]


class Contract(unittest.TestCase):
    def test_final_mode_is_frozen_explicit_and_preserves_legacy_blocks(self):
        cfg = configuration()
        run.validate(cfg)
        self.assertNotIn('fail_fast', gx.normalize(cfg['geometry_online']))
        for change in ({'mode': 'finetune'}, {'input': gx.NATIVE_INPUT}, {'patch_fusion': None}):
            bad = copy.deepcopy(cfg)
            bad['geometry_online'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                run.validate(bad)
        bad = copy.deepcopy(cfg); bad['geometry_online'].pop('patch_fusion')
        run.validate(bad)
        for world in (1, 2, 3, 5, 6, 12, True):
            with self.subTest(world=world), self.assertRaises(ValueError):
                recipe_for({**cfg, 'world_size': world})
        for reference in (4, 8, 16, 48, True):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                recipe_for({**cfg, 'reference_world_size': reference})
        legacy = settings()
        self.assertEqual(gx.normalize(legacy), legacy)

    def test_optional_fail_fast_survives_authenticated_code_rebinding(self):
        old = configuration()
        old.update(code=dict(path='/fixture/old', sha256='a'*64), preparation={'fixture': True})
        current = copy.deepcopy(old)
        current['code'] = dict(path='/fixture/new', sha256='b'*64)
        bound = lambda c, commit: dict(config_sha256=run.identity(c), preparation=c['preparation'],
                                       trainer_commit=commit, world_size=4)
        self.assertEqual(run.gx_rule_rebind(bound(old, 'old'), bound(current, 'new'), current, old),
                         'gx-code-rebind-v1')

    def test_world_four_and_eight_preserve_cp1_updates_across_epochs_and_resume(self):
        base = configuration(32); base.pop('geometry_online'); base['recipe'] = recipe_for(base)
        reference = plans(base, 9)
        for world in (4, 8):
            cfg = configuration(world)
            self.assertEqual(cfg['recipe']['global_batch'], 160)
            self.assertEqual(len(cfg['recipe']['mix']), 160//world)
            actual = plans(cfg, 9)
            self.assertEqual([flattened(p) for p in actual], [flattened(p) for p in reference])
            resumed = list(data.mixed_indices(MixRows(None, None).counts, 9, start_step=4,
                training_mode='final', mix=cfg['recipe']['mix'], world=world))
            self.assertEqual(resumed, actual[4:])
            ctrl = {k: v for k, v in cfg.items() if k != 'geometry_online'}
            ctrl['reference_world_size'] = 32
            self.assertEqual(recipe_for(ctrl), cfg['recipe'])

    def test_common_parameters_and_rng_equal_cp1_without_copying_weights(self):
        for placement in data.PLACEMENTS:
            donor, _, _ = fixture(False, placement)
            # final_fixture resets the construction seed on both paths.
            model, _, _ = fixture(True, placement)
            current = model.state_dict()
            for name, value in donor.state_dict().items():
                self.assertTrue(torch.equal(value, current[name]), name)


class NativeForward(unittest.TestCase):
    def test_zero_start_hidden_loss_pose_depth_and_vqa_readouts_on_every_stream(self):
        donor, _, _ = fixture(False)
        model, batch, targets = fixture()
        donor.eval(); model.eval()
        with torch.no_grad():
            for stream in ('pose', 'vqa', 'pointing', 'routing'):
                for image in ((False, True) if stream in ('vqa', 'pointing') else (False,)):
                    with self.subTest(stream=stream, image=image):
                        row = image_batch() if image else batch
                        carriers = not image
                        self.assertTrue(torch.equal(model.hidden(row, carriers), donor.hidden(row, carriers)))
                        target = targets if stream == 'pose' else None
                        left, right = model(row, target, stream=stream), donor(row, target, stream=stream)
                        self.assertTrue(torch.equal(left['loss'], right['loss']))
                        for key in left['components']:
                            self.assertTrue(torch.equal(left['components'][key], right['components'][key]), key)
                        if image:
                            self.assertEqual(model.gx_metrics, dict(single_image_fusion_skipped=True))
                        if stream == 'vqa':
                            options = dict(max_new_tokens=2, do_sample=False, pad_token_id=0, eos_token_id=1)
                            self.assertTrue(torch.equal(model.generate(row, **options), donor.generate(row, **options)))
            uv = torch.full((32, 2, 2), 500.)
            a = model(batch, {'uv': uv}, stream='readout')
            b = donor(batch, {'uv': uv}, stream='readout')
            for key in a:
                self.assertTrue(torch.equal(a[key], b[key]), key)
            self.assertEqual(model.readout(batch, uv.tolist()), donor.readout(batch, uv.tolist()))

    def test_each_video_stream_uses_its_own_student_patches_and_image_rows_skip(self):
        model, batch, targets = fixture()
        model.eval()
        calls = []
        encoder = model.auxiliary_heads.geometry_encoder
        original = encoder.forward
        def capture(images, coords=None):
            calls.append(images.detach().clone())
            return original(images, coords)
        with patch.object(encoder, 'forward', side_effect=capture), torch.no_grad():
            for index, stream in enumerate(('pose', 'vqa', 'pointing', 'routing')):
                row = {**batch, 'pixel_values_videos': batch['pixel_values_videos'] + index * .2}
                model(row, targets if stream == 'pose' else None, stream=stream)
                expected = gx.student_frames(row['pixel_values_videos'], row['video_grid_thw'],
                    model.config.vision_config, **model.geometry_runtime)[0]
                expected, _ = gx.square_518(expected, encoder.image_size)
                self.assertTrue(torch.equal(calls[-1], expected))
                self.assertEqual(len(calls[-1]), 32)
            self.assertEqual(len(calls), 4)
            for stream in ('vqa', 'pointing'):
                model(image_batch(), stream=stream)
            self.assertEqual(len(calls), 4)
        self.assertFalse(torch.equal(calls[0], calls[-1]))

    def test_alignment_keeps_cp1_rates_and_changes_only_the_two_grafts(self):
        donor, _, _ = fixture(False)
        model, batch, targets = fixture()
        options = dict(pose_lr_scale=.6, lm_lr_scale=.6)
        old = {id(p): g['initial_lr'] for g in parameter_groups(donor, donor.recipe, **options) for p in g['params']}
        old_names = {n: old[id(p)] for n, p in donor.named_parameters() if id(p) in old}
        groups = parameter_groups(model, model.recipe, **options)
        by_id = {id(p): g for g in groups for p in g['params']}
        for name, p in model.named_parameters():
            if name in old_names:
                self.assertEqual(by_id[id(p)]['initial_lr'], old_names[name], name)
            if id(p) in by_id:
                aligned = name.startswith(('auxiliary_heads.patch_fusion.', 'auxiliary_heads.pose.cam_token_connector.'))
                self.assertEqual(by_id[id(p)]['gx_alignment'], aligned, name)
        optimizer = torch.optim.AdamW(groups, weight_decay=.01)
        # This four-row unit probe uses one physical rank without reference expansion.
        model.recipe = {k: v for k, v in model.recipe.items() if k != 'reference_world_size'}
        rows = MixRows(batch, targets)
        plan = [('pose', [0]), ('vqa', [0]), ('pointing', [1]), ('routing', [0])]
        encoder = model.auxiliary_heads.geometry_encoder
        frozen = {n: p.clone() for n, p in encoder.named_parameters()}
        for step in (1, 50, 51):
            before = {n: p.clone() for n, p in model.named_parameters() if p.requires_grad}
            run.optimize_step(model, optimizer, rows, plan, 0, torch.device('cpu'), step)
            for group in groups:
                expected = run.learning_rate(step, {**model.recipe, 'learning_rate': group['initial_lr']})
                if step <= 50 and not group['gx_alignment']:
                    expected = 0.
                self.assertEqual(group['lr'], expected)
            for name, p in model.named_parameters():
                if p.requires_grad and step <= 50 and not by_id[id(p)]['gx_alignment']:
                    self.assertTrue(torch.equal(before[name], p), name)
            self.assertTrue(all(p.grad is None and not p.requires_grad and p not in optimizer.state
                                and torch.equal(p, frozen[n]) for n, p in encoder.named_parameters()))
        self.assertTrue(any(not torch.equal(before[n], p) for n, p in model.named_parameters()
                            if n.startswith('model.language_model.') and p.requires_grad))
        self.assertTrue(any(not torch.equal(before[n], p) for n, p in model.named_parameters()
                            if n.startswith('auxiliary_heads.depth.') and p.requires_grad))

    def test_all_world_four_first_batches_through_the_native_check_tool(self):
        cfg = configuration(); cfg['preparation'] = {'fixture': True}
        model, batch, targets = fixture()
        rows = MixRows(batch, targets)
        receipt = dict(streams={s: {'count': n} for s, n in rows.counts.items()})
        out = directory()/'first_batch.json'
        with patch.object(run, 'prepared', return_value=(receipt, {})), \
             patch.object(run, 'processor_for_receipt', return_value=None), \
             patch.object(run, 'load_model', return_value=model), patch.object(run, 'Rows', return_value=rows):
            records = run.first_batch_check(cfg, list(range(4)), out)
        self.assertEqual(len(records), 160)
        self.assertTrue(all(r['finite'] and 'error' not in r for r in records),
                        [r for r in records if not r['finite']])
        self.assertEqual({r['rank'] for r in records}, set(range(4)))
        self.assertEqual(load(out)['schema'], 'c1-first-batch-check-v1')
        self.assertTrue(all(p.grad is None for p in model.parameters()))

    def test_export_has_only_encoder_pins_and_reloads_strictly(self):
        model, batch, targets = fixture()
        with torch.no_grad():
            model.auxiliary_heads.patch_fusion.fc2.weight.normal_(std=.01)
            model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.normal_(std=.01)
        directory_ = directory()
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(directory_/'m0', model, model, {'base_identity': 'fixture'}, 0)
        heads = torch.load(directory_/'m0/heads.pt', weights_only=True)
        self.assertFalse(any(k.startswith('geometry_encoder.') for k in heads))
        self.assertEqual(heads['_gx_geometry_online'], model.geometry_online)
        self.assertTrue(any(k.startswith('patch_fusion.') for k in heads))
        self.assertTrue(any(k.startswith('pose.cam_token_connector.') for k in heads))
        with torch.no_grad():
            model.auxiliary_heads.patch_fusion.fc2.weight.zero_()
            model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.zero_()
        with patch.object(full_ft, 'load_export'):
            run.load_artifact(model, file_pin(directory_/'m0/artifact.json'))
            for name, value in model.auxiliary_heads.state_dict().items():
                if not name.startswith('geometry_encoder.'):
                    self.assertTrue(torch.equal(value, heads[name]), name)
            for name in ('patch_fusion.fc2.weight', 'pose.cam_token_connector.mlp.2.weight', '_gx_geometry_online'):
                bad = {k: v for k, v in heads.items() if k != name}
                root = directory(); torch.save(bad, root/'heads.pt')
                artifact = load(directory_/'m0/artifact.json'); artifact['heads'] = file_pin(root/'heads.pt')
                write(root/'artifact.json', artifact)
                with self.assertRaises((ValueError, RuntimeError)):
                    run.load_artifact(model, file_pin(root/'artifact.json'))

    def test_frozen_checkpoint_contains_no_encoder_tensors_or_optimizer_state(self):
        model, batch, targets = fixture()
        model.recipe = {k: v for k, v in model.recipe.items() if k != 'reference_world_size'}
        groups = parameter_groups(model, model.recipe, pose_lr_scale=.6, lm_lr_scale=.6)
        optimizer = torch.optim.AdamW(groups)
        run.optimize_step(model, optimizer, MixRows(batch, targets), [('pose', [0]), ('vqa', [1])],
                          0, torch.device('cpu'), 1)
        root = directory()
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=lambda out, value: out.__setitem__(0, value)):
            pin = run.checkpoint(root/'checkpoint', model, optimizer, {}, 1)
        manifest = load(pin['path'])
        self.assertEqual(manifest['geometry_encoder'], model.geometry_online['encoder'])
        self.assertNotIn('geometry_encoder_dtype', manifest)
        for relative in manifest['files']:
            if relative.endswith('.pt') and not relative.startswith('rng'):
                payload = torch.load(root/'checkpoint'/relative, weights_only=True)
                self.assertFalse(any('geometry_encoder' in n for n in payload.get('tensors', {})))
        self.assertFalse(any(n.startswith('auxiliary_heads.geometry_encoder.') for n, _ in full_ft.named_trainable(model)))
        self.assertTrue(all(p not in optimizer.state for p in model.auxiliary_heads.geometry_encoder.parameters()))
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=lambda out, value: out.__setitem__(0, value)):
            self.assertEqual(run.restore(pin, model, optimizer, {}), 1)
            bad = copy.deepcopy(manifest); bad['geometry_encoder']['weights']['sha256'] = 'f'*64
            write(root/'changed.json', bad)
            with self.assertRaisesRegex(ValueError, 'encoder pins'):
                run.restore(file_pin(root/'changed.json'), model, optimizer, {})

    def test_cp1_m800_pose_and_depth_warm_start_keeps_step_zero_exact(self):
        donor, _, _ = fixture(False)
        # Full export stores BF16 base tensors, as in the native training kit.
        for _, p in full_ft.base_parameters(donor):
            p.data = p.bfloat16().float()
        root = directory()
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=donor.state_dict()):
            run.export(root/'m800', donor, donor, {'base_identity': 'fixture'}, 800)
        model, batch, targets = fixture()
        spec = dict(artifact=file_pin(root/'m800/artifact.json'), lm='full', heads=['pose', 'depth'])
        run.init_from_artifact(model, spec, part='lm')
        report = run.init_from_artifact(model, spec, part='heads')
        self.assertTrue(any(k.startswith('pose.cam_token_connector.') for k in report['planned_init']))
        self.assertTrue(any(k.startswith('patch_fusion.') for k in report['planned_init']))
        model.eval(); donor.eval()
        with torch.no_grad():
            self.assertTrue(torch.equal(model.hidden(batch), donor.hidden(batch)))
            self.assertTrue(torch.equal(model(batch, targets)['loss'], donor(batch, targets)['loss']))

    def test_routed_prefill_uses_gx_and_matches_cp1_at_zero(self):
        donor, _, _ = fixture(False); donor.eval()
        model, batch, _ = fixture(); model.eval()
        processor = SimpleNamespace(tokenizer=final.FakeTokenizer(),
            _routing_tokens=dict(ids={'<depth_at': 40, '<move': 45, '<pose': 39, '<turn': 47, '<box_3d': 38}))
        def force(ids, logits):
            output = torch.full_like(logits, -1e9); output[:, 1] = 0.
            return output
        with patch.object(model, 'geometry_features', wraps=model.geometry_features) as features:
            a = decode.generate(model, processor, batch, logits_processor=force)
            b = decode.generate(donor, processor, batch, logits_processor=force)
        self.assertEqual(features.call_count, 1)
        self.assertEqual(a, b)
        self.assertEqual(model.gx_metrics['patch_delta_ratio'], 0.)
        with torch.no_grad():
            model.auxiliary_heads.patch_fusion.fc2.bias.fill_(.1)
        decode.generate(model, processor, batch, logits_processor=force)
        self.assertGreater(model.gx_metrics['patch_delta_ratio'], 0.)
        self.assertEqual(len(model.model.visual._forward_hooks), 0)

    def test_single_image_vqa_admission_and_prompt_readout(self):
        root, rows = images.SingleImageTests().fixture()
        row = copy.deepcopy(rows[0]); row.pop('pointing'); row['target'] = '{"point_2d": null}'
        source = root/'vqa.jsonl'
        source.write_text(json.dumps(row) + '\n')
        cfg = configuration()
        receipt = data.build_stream(file_pin(source), file_pin(root/'division.json'), root/'vqa', 'vqa',
                                    training_mode='final', geometry_online=cfg['geometry_online'])
        self.assertEqual(receipt['count'], 1)
        processor = images.ImageProcessor()
        cfg = configuration()
        for target in (row['target'], data.READOUT_TARGET):
            batch, targets, audit = data.encode(processor, {**row, 'target': target}, {}, 'vqa',
                training_mode='final', frame_layout='duplicate', geometry_online=cfg['geometry_online'])
            self.assertIn('image_grid_thw', batch)
            self.assertNotIn('aux_g3t_images', batch)
            model, _, _ = fixture()
            run.check_row(batch, targets, 'vqa', model)
            self.assertTrue(torch.isfinite(model(batch, stream='vqa')['loss']))


class ConnectorOnly(unittest.TestCase):
    @staticmethod
    def config(world=32, bf16=False):
        cfg = configuration(world)
        cfg['geometry_online'].pop('patch_fusion')
        if bf16:
            cfg['geometry_online']['encoder_dtype'] = 'bf16'
        cfg['recipe'] = recipe_for(cfg)
        return cfg

    def test_zero_start_matches_cp1_on_every_stream_and_storage_dtype(self):
        for bf16 in (False, True):
            cfg = self.config(bf16=bf16)
            run.validate(cfg)
            donor, _, _ = fixture(False)
            model, batch, targets = fixture(geometry_settings=cfg['geometry_online'])
            donor.eval(); model.eval()
            self.assertFalse(hasattr(model.auxiliary_heads, 'patch_fusion'))
            self.assertTrue(all(torch.equal(v, model.state_dict()[k]) for k, v in donor.state_dict().items()))
            with torch.no_grad():
                for stream in ('pose', 'vqa', 'pointing', 'routing'):
                    variants = [batch]
                    if stream != 'pose':
                        empty = {**batch, 'aux_camera_positions': torch.full_like(batch['aux_camera_positions'], -1)}
                        variants.append(empty)
                    if stream in ('vqa', 'pointing'):
                        variants.append(image_batch())
                    for row in variants:
                        with self.subTest(bf16=bf16, stream=stream, carriers=int((row.get('aux_camera_positions', torch.tensor([-1])) >= 0).sum())):
                            carriers = 'video_grid_thw' in row
                            self.assertTrue(torch.equal(model.hidden(row, carriers), donor.hidden(row, carriers)))
                            target = targets if stream == 'pose' else None
                            left, right = model(row, target, stream=stream), donor(row, target, stream=stream)
                            self.assertTrue(torch.equal(left['loss'], right['loss']))
                            for key in left['components']:
                                self.assertTrue(torch.equal(left['components'][key], right['components'][key]), key)
                options = dict(max_new_tokens=2, do_sample=False, pad_token_id=0, eos_token_id=1)
                for row in (batch, empty, image_batch()):
                    self.assertTrue(torch.equal(model.generate(row, **options), donor.generate(row, **options)))
                uv = torch.full((32, 2, 2), 500.)
                self.assertEqual(model.readout(batch, uv.tolist()), donor.readout(batch, uv.tolist()))

    def test_only_rows_with_carriers_call_g3t(self):
        model, batch, targets = fixture(geometry_settings=self.config()['geometry_online'])
        model.eval()
        encoder = model.auxiliary_heads.geometry_encoder
        with patch.object(encoder, 'forward', wraps=encoder.forward) as forward, torch.no_grad():
            for stream in ('pose', 'vqa', 'pointing', 'routing'):
                forward.reset_mock()
                model(batch, targets if stream == 'pose' else None, stream=stream)
                self.assertEqual(forward.call_count, 1, stream)
                if stream != 'pose':
                    empty = {**batch, 'aux_camera_positions': torch.full_like(batch['aux_camera_positions'], -1)}
                    forward.reset_mock()
                    model(empty, stream=stream)
                    forward.assert_not_called()
                    self.assertEqual(model.gx_metrics, dict(no_carriers_geometry_skipped=True))
            for row in (image_batch(), {k: v for k, v in batch.items() if k != 'aux_camera_positions'}):
                forward.reset_mock()
                self.assertIsNone(model.geometry_features(row))
                forward.assert_not_called()
            forward.reset_mock()
            model.generate(empty, max_new_tokens=1, do_sample=False, pad_token_id=0, eos_token_id=1)
            forward.assert_not_called()

    def test_mixed_batch_skips_empty_rows_and_preserves_feature_indices(self):
        model, batch, _ = fixture(geometry_settings=self.config()['geometry_online'])
        positions = torch.cat((torch.full_like(batch['aux_camera_positions'], -1), batch['aux_camera_positions']))
        mixed = {**batch, 'input_ids': batch['input_ids'].expand(2, -1), 'aux_camera_positions': positions}
        frames = [torch.zeros(32, 3, 4, 4), torch.ones(32, 3, 4, 4)]
        value = torch.ones(32, 2058)
        with patch.object(gx, 'student_frames', return_value=frames), \
             patch.object(gx, 'features', return_value=value) as features:
            result = model.geometry_features(mixed)
        self.assertEqual(features.call_count, 1)
        self.assertTrue(torch.equal(result[0], torch.zeros_like(value)))
        self.assertTrue(torch.equal(result[1], value))

    def test_first_batches_world_32_four_and_eight_both_dtypes(self):
        for bf16 in (False, True):
            for world in (32, 4, 8):
                with self.subTest(world=world, bf16=bf16):
                    cfg = self.config(world, bf16); cfg['preparation'] = {'fixture': True}
                    model, batch, targets = fixture(geometry_settings=cfg['geometry_online'])
                    model.recipe = cfg['recipe']
                    rows = MixRows(batch, targets)
                    receipt = dict(streams={s: {'count': n} for s, n in rows.counts.items()})
                    out = directory()/'gxc_first_batch.json'
                    with patch.object(run, 'prepared', return_value=(receipt, {})), \
                         patch.object(run, 'processor_for_receipt', return_value=None), \
                         patch.object(run, 'load_model', return_value=model), patch.object(run, 'Rows', return_value=rows):
                        records = run.first_batch_check(cfg, list(range(world)), out)
                    self.assertEqual(len(records), 160)
                    self.assertTrue(all(r['finite'] and 'error' not in r for r in records), [r for r in records if not r['finite']])
                    self.assertEqual({r['rank'] for r in records}, set(range(world)))
                    self.assertTrue(all(p.grad is None for p in model.parameters()))
                    if world == 32:
                        self.assertEqual(len(cfg['recipe']['mix']), 5)

    def test_step_one_cp1_groups_rates_and_frozen_invariants(self):
        for bf16 in (False, True):
            donor, _, _ = fixture(False)
            cfg = self.config(bf16=bf16)
            model, batch, targets = fixture(geometry_settings=cfg['geometry_online'])
            model.recipe = cfg['recipe']
            options = dict(pose_lr_scale=.6, lm_lr_scale=.6, inherited=['pose_branch.fc2.weight'])
            old = {id(p): g for g in parameter_groups(donor, donor.recipe, **options) for p in g['params']}
            old_names = {n: old[id(p)] for n, p in donor.named_parameters() if id(p) in old}
            groups = parameter_groups(model, model.recipe, **options)
            by_id = {id(p): g for g in groups for p in g['params']}
            for name, p in model.named_parameters():
                if name in old_names:
                    self.assertEqual(by_id[id(p)]['name'], old_names[name]['name'], name)
                    self.assertEqual(by_id[id(p)]['initial_lr'], old_names[name]['initial_lr'], name)
                if 'pose.cam_token_connector.' in name and p.requires_grad:
                    self.assertEqual(by_id[id(p)]['initial_lr'], 6e-5)
                    self.assertEqual(by_id[id(p)]['name'], 'pose')
            self.assertTrue(all('gx_alignment' not in g for g in groups))
            optimizer = torch.optim.AdamW(groups, weight_decay=.01)
            frozen = {n: p.clone() for n, p in model.named_parameters() if not p.requires_grad}
            before = {n: p.clone() for n, p in model.named_parameters() if p.requires_grad}
            rows = MixRows(batch, targets)
            plan = [('pose', [0]), ('vqa', [0]), ('pointing', [1]), ('routing', [0])]
            info, _ = run.optimize_step(model, optimizer, rows, plan, 0, torch.device('cpu'), 1)
            for group in groups:
                self.assertEqual(group['lr'], run.learning_rate(1, {**model.recipe, 'learning_rate': group['initial_lr']}))
                self.assertGreater(group['lr'], 0.)
            for name, p in model.named_parameters():
                if name in frozen:
                    self.assertTrue(torch.equal(p, frozen[name]), name)
                    self.assertIsNone(p.grad, name)
                    self.assertNotIn(p, optimizer.state, name)
            for prefix in ('model.language_model.', 'auxiliary_heads.pose.cam_token_connector.', 'auxiliary_heads.depth.'):
                self.assertTrue(any(not torch.equal(before[n], p) for n, p in model.named_parameters() if n in before and n.startswith(prefix)), prefix)
            self.assertGreater(model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.grad.norm(), 0.)
            self.assertTrue(all(not p.requires_grad for p in model.model.visual.parameters()))
            self.assertFalse(model.auxiliary_heads.geometry_encoder.training)

    def test_fail_fast_ignores_explicit_no_carrier_skips(self):
        history = [[dict(step=1, stream_means=dict(pose=1.), shapes=[
            dict(gx=dict(delta_ratio=.2)), dict(gx=dict(no_carriers_geometry_skipped=True)),
            dict(gx=dict(single_image_fusion_skipped=True))])]]
        result = run.gx_fail_fast(history, dict(step=1, min_delta_ratio=.1, max_loss_ratio=2.))
        self.assertEqual(result['verdict'], 'CONTINUE')
        self.assertEqual(result['median_delta_ratio'], .2)


class R6Regressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Read-only Git references are the actual CP1 implementation, not a replica.
        cls.baseline = {}
        for name in ('carrier_c1_data', 'carrier_c1_sweep', 'carrier_c1_run'):
            source = subprocess.run(['git', 'show', f'e6456bc:student_pilot/{name}.py'],
                cwd=Path(__file__).resolve().parents[1], check=True, capture_output=True, text=True).stdout
            module = ModuleType('student_pilot._s11_cp1_' + name)
            module.__package__ = 'student_pilot'
            exec(compile(source, f'e6456bc:student_pilot/{name}.py', 'exec'), module.__dict__)
            cls.baseline[name] = module
        cls.cp1 = cls.baseline['carrier_c1_run']
        cls.cp1.data = cls.baseline['carrier_c1_data']
        cls.cp1.recipe_for = cls.baseline['carrier_c1_sweep'].recipe_for

    def test_step400_final_gx_matches_actual_cp1_loop(self):
        for gate in (None, False, True):
            for smoke in (None, 2):
                reports = []
                for module, geometry in ((self.cp1, False), (run, False), (run, True)):
                    cfg = configuration(32)
                    cfg.update(steps=401, milestones=[])
                    if not geometry:
                        cfg.pop('geometry_online')
                    if gate is not None:
                        cfg['gate_stop'] = gate
                    cfg['output'] = str(directory())
                    with ExitStack() as stack:
                        for name in ('checkpoint', 'gx_validate_history', 'gx_reference'):
                            if hasattr(module, name):
                                stack.enter_context(patch.object(module, name))
                        stack.enter_context(patch.object(module, 'gx_step_history', return_value=[])) if geometry else None
                        stack.enter_context(patch.object(module, 'optimize_step', side_effect=lambda *a:
                            (dict(wall_seconds=0., head_metrics={}), None)))
                        reports.append(module.run_steps(None, None, None, None, MixRows(None, None).counts,
                            cfg['output'], cfg, {}, torch.device('cpu'), start_step=399,
                            smoke_steps=smoke, distributed=False))
                with self.subTest(gate=gate, smoke=smoke):
                    expected = [(r['last_step'], r['stop_reason']) for r in reports]
                    self.assertEqual(expected, [expected[0]] * 3)
                    self.assertEqual(expected[0][0], 400 if gate is not False and not smoke else 401)
        self.assertFalse(run.step400_gate_enabled(dict(training_mode='pose_only', geometry_online=settings())))
        # Both the live loop and the resume review must consult the same policy.
        import inspect
        self.assertIn('step400_gate_enabled(cfg)', inspect.getsource(run.train))

    def test_retries_and_exhausted_skips_match_actual_world32_fetch(self):
        _, batch, targets = fixture(False)
        model = SimpleNamespace(training_mode='final')
        reference_cfg = configuration(32)
        counts = dict.fromkeys(reference_cfg['mix'], 257)
        reference = [[(stream, list(range(32 * step, 32 * (step + 1))))
                      for stream in reference_cfg['mix']] for step in range(2)]
        for rejected in ({0}, {3}, {7}, {15}, {31}, {35}, {0, 2, 5}, set(range(8))):
            class RejectedRows:
                def count(self, stream):
                    return counts[stream]

                def get(self, stream, index):
                    if stream == 'vqa' and index in rejected:
                        raise ValueError(f'rejected row {index}')
                    return batch, targets if stream == 'pose' else None, dict(qid=f'{stream}-{index}')

            rows = RejectedRows()
            expected = []
            outcomes = []
            with redirect_stdout(io.StringIO()):
                for plan in reference:
                    update, decisions = [], []
                    for stream, indices in plan:
                        flags = [int(not any(stream == 'vqa' and (i + off) % counts[stream] in rejected
                                             for i in indices)) for off in range(8)]
                        end = flags.index(1) + 1 if 1 in flags else 8
                        flags = flags[:end]
                        decisions.append(flags)
                        group = []
                        for index in indices:
                            replies = iter(flags)
                            def reduce(flag, **kw):
                                flag.fill_(next(replies))
                            with patch.object(dist, 'all_reduce', side_effect=reduce):
                                result = self.cp1.fetch(rows, stream, index, model, distributed=True)
                            group.append(None if result is None else result[2]['index'])
                        update.append((stream, group))
                    expected.append(update)
                    outcomes.append(decisions)
                for world in (4, 8):
                    cfg = configuration(world)
                    model.recipe = cfg['recipe']
                    for step, nominal in enumerate(reference):
                        plan = [(stream, indices[start:start + world]) for stream, indices in nominal
                                for start in range(0, 32, world)]
                        factor = run.nominal_slices(cfg['recipe'], plan)
                        per_rank = []
                        for rank in range(world):
                            replies = iter(flag for group in outcomes[step] for flag in group)
                            def reduce(flag, **kw):
                                flag.fill_(next(replies))
                            with patch.object(dist, 'all_reduce', side_effect=reduce):
                                per_rank.append(list(run.fetch_plan(rows, model, plan, rank, distributed=True)))
                            self.assertEqual(list(replies), [])
                        actual = []
                        for start in range(0, len(plan), factor):
                            stream = plan[start][0]
                            slices = [[None if per_rank[rank][slot] is None else per_rank[rank][slot][2]['index']
                                       for rank in range(world)] for slot in range(start, start + factor)]
                            actual.append((stream, [i for part in slices for i in part]))
                        with self.subTest(world=world, step=step, rejected=rejected):
                            self.assertEqual(actual, expected[step])
            if rejected == set(range(8)):
                self.assertTrue(any(None in indices for plan in expected for _, indices in plan))
            if rejected in ({0}, {3}, {0, 2, 5}):
                offset = max(rejected) + 1
                self.assertEqual(expected[0][2], ('vqa', list(range(offset, 32 + offset))))
            if rejected == {35}:
                self.assertEqual(expected[1][2], ('vqa', list(range(36, 68))))

    def test_non_gx_image_vqa_admission_matches_actual_cp1(self):
        old = self.baseline['carrier_c1_data']
        root, source_rows = images.SingleImageTests().fixture()
        row = copy.deepcopy(source_rows[0]); row.pop('pointing'); row['target'] = '{"point_2d": null}'
        source = root/'vqa.jsonl'; source.write_text(json.dumps(row) + '\n')
        for module in (old, data):
            self.assertFalse(module.single_image_row(row, 'vqa'))
            with self.assertRaisesRegex(ValueError, '32 pinned native frames'):
                module.build_stream(file_pin(source), file_pin(root/'division.json'),
                                    root/('baseline' if module is old else 'current'), 'vqa')
        for mode in ('mixed', 'pose_only'):
            self.assertFalse(data.single_image_row(row, 'vqa', training_mode=mode, geometry_online=settings()))
        cfg = configuration(32); cfg.pop('geometry_online'); cfg['recipe'] = recipe_for(cfg)
        cfg['preparation'] = {'fixture': True}
        receipt = dict(streams={s: {'count': n} for s, n in MixRows(None, None).counts.items()})
        model, batch, targets = fixture(False)
        class ImageVqaRows(MixRows):
            def get(self, stream, index):
                if stream == 'vqa':
                    return image_batch(), None, dict(qid='image-vqa')
                # Keep other streams on valid video rows in this CP1 fixture.
                return self.batch, self.targets if stream == 'pose' else None, dict(qid=f'{stream}-{index}')
        records = []
        with redirect_stdout(io.StringIO()) as captured:
            for module in (self.cp1, run):
                with ExitStack() as stack:
                    for name, result in (('prepared', (receipt, {})), ('processor_for_receipt', None),
                                         ('load_model', model), ('Rows', ImageVqaRows(batch, targets))):
                        stack.enter_context(patch.object(module, name, return_value=result))
                    records.append(module.first_batch_check(cfg, [0], root/(module.__name__.split('.')[-1]+'.json')))
                with self.assertRaisesRegex(KeyError, 'aux_camera_positions'):
                    module.check_row(image_batch(), None, 'vqa', model)
        self.assertIn('aux_camera_positions', captured.getvalue())
        verdict = lambda rs: [(r['stream'], r['finite'], r.get('error'), r.get('qid')) for r in rs]
        self.assertEqual(verdict(records[0]), verdict(records[1]))
        self.assertEqual([r['stream'] for r in records[1] if not r['finite']], ['vqa'])


def gloo_worker(rank, root):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method='file://'+root+'/rendezvous', rank=rank, world_size=4)
    try:
        model, batch, targets = fixture()
        wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
        wrapped.eval()
        rows = MixRows(batch, targets)
        records = run.check_plan_rows(wrapped, rows, plans(configuration(), 1), [rank])
        assert len(records) == 40 and all(r['finite'] for r in records), records
        write(Path(root)/f'rank{rank}.json', records)
    finally:
        dist.destroy_process_group()


class MemoryFallback(unittest.TestCase):
    def test_absent_keys_preserve_normalized_identity_and_fp32_output_bytes(self):
        # Captured on the pinned S10 input checkout with the supplied CPU wrapper.
        previous_threads = torch.get_num_threads()
        self.addCleanup(torch.set_num_threads, previous_threads)
        torch.set_num_threads(1)
        expected = ['657308f57b5a02d3a14add15e07a6e41c374198304a37d016df1ab34ac27ac69',
                    '82668c672c6df471df1f81390b9c025961842e5a7f0d83e46c46d38b72131cbc',
                    'd5213e36cf4ca7c2b4e0a4df2361e2a02e13490817a4b6a517a851034386530f']
        for fusion, config_sha in ((False, 'a81d0d327710a6ef8512aa0ffec6dfbd11469aafbfcf74c5822ca10b94c19539'),
                                   (True, 'ed9836870dc6da0d3198e49a7ab0868744e160fa3ad48df0c01aa97ead52638a')):
            block = settings()
            if fusion:
                block['patch_fusion'] = fusion_settings(50)
            normalized = gx.normalize(block)
            self.assertNotIn('encoder_dtype', normalized)
            self.assertEqual(hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest(), config_sha)
            torch.manual_seed(1109)
            encoder = gx.G3TEncoder(block, architecture(), image_size=28)
            result = encoder(torch.rand(4, 3, 28, 28))
            hashes = [hashlib.sha256(x.numpy().tobytes()).hexdigest() for x in result]
            self.assertEqual(hashes, expected + (['522e752c60b3f4eb1807285d985e443bd48e9492288f853a99681312161ebad8'] if fusion else []))
        cfg = configuration()
        self.assertEqual(run.digest(cfg), '67e65629e78c3cf5f39511b549c3e345d92cf73fb98ce6ea7753d9cc3d6d6aae')
        from trace_format.contracts import HEADING_PLANE_MIN_DEFAULT
        self.assertEqual(run.identity(cfg), run.digest({**cfg, 'heading_plane_min':HEADING_PLANE_MIN_DEFAULT}))
        off = {**cfg, 'contract_epoch':False}
        self.assertEqual(run.identity(off), run.digest(off))
        self.assertEqual(run.identity({**off, 'heading_plane_min':HEADING_PLANE_MIN_DEFAULT}), run.digest(off))

    def test_frozen_only_strict_options_and_identity_binding(self):
        original = configuration()
        for dtype in (None, 'fp32', 'float16', True, {}):
            with self.subTest(dtype=dtype), self.assertRaises(ValueError):
                gx.normalize({**settings(), 'encoder_dtype': dtype})
        with self.assertRaises(ValueError):
            gx.normalize({**settings('finetune'), 'encoder_dtype': 'bf16'})
        for value in (None, 1, 'true'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gx.normalize({**settings(), 'patch_fusion': {**fusion_settings(50), 'checkpointing': value}})
        with self.assertRaises(ValueError):
            gx.normalize({**settings('finetune'), 'patch_fusion': {**fusion_settings(50), 'checkpointing': True}})
        for change in ({'encoder_dtype': 'bf16'},
                       {'patch_fusion': {**fusion_settings(50), 'checkpointing': True}}):
            cfg = copy.deepcopy(original); cfg['geometry_online'].update(change)
            run.validate(cfg)
            self.assertNotEqual(run.identity(cfg), run.identity(original))

    def test_bf16_storage_fp32_heads_parity_no_saved_activations_and_pinned_load(self):
        from safetensors.torch import save_file
        torch.manual_seed(1109)
        block = {**settings(), 'patch_fusion': fusion_settings(50)}
        fp32 = gx.G3TEncoder(block, architecture(), image_size=28)
        bf16 = gx.G3TEncoder({**block, 'encoder_dtype': 'bf16'}, architecture(), image_size=28)
        root = directory(); weights = root/'frozen.safetensors'
        save_file(fp32.state_dict(), weights)
        bf16.settings['encoder']['weights'] = file_pin(weights)
        report = bf16.load_pinned(weights)
        self.assertEqual(report['encoder_dtype'], 'bf16')
        self.assertTrue(all(p.dtype == torch.bfloat16 and not p.requires_grad for p in bf16.parameters()))
        self.assertEqual(sum(p.numel()*p.element_size() for p in fp32.parameters()),
                         2*sum(p.numel()*p.element_size() for p in bf16.parameters()))
        for name, value in fp32.state_dict().items():
            other = bf16.state_dict()[name]
            self.assertTrue(torch.equal(other, value.to(other.dtype)), name)
        x = torch.rand(32, 3, 28, 28, requires_grad=True)
        heads = []
        def record(head, inputs):
            heads.append(([p.dtype for p in head.parameters()], inputs[0][-1].dtype))
        handles = [head.register_forward_pre_hook(record) for head in
                   (bf16.local_camera_head, bf16.global_camera_head)]
        saved = []
        try:
            with torch.autograd.graph.saved_tensors_hooks(lambda t: saved.append(t) or t, lambda t: t):
                left, right = fp32(x), bf16(x)
                bf16(x)  # The steady-state path must also remain under no_grad.
        finally:
            for handle in handles:
                handle.remove()
        self.assertEqual(saved, [])
        self.assertTrue(all(not t.requires_grad and t.grad_fn is None for t in left+right))
        self.assertTrue(all(set(dtypes) == {torch.float32} and dtype == torch.float32 for dtypes, dtype in heads))
        self.assertTrue(all(p.dtype == torch.bfloat16 for p in bf16.parameters()))
        diffs = [float((a-b).abs().max()) for a,b in zip(left, right)]
        # A fixture bound for storage quantization, separate from native/lean parity.
        for a, b in zip(left, right):
            self.assertLessEqual(float((a-b).abs().max()), .03*max(1., float(a.abs().max())))
        self.assertTrue(bf16.verified)
        self.assertTrue(bf16.parity['bitwise'])
        write(root/'bf16_evidence.json', dict(max_abs_diff=diffs, relative_to_max_tolerance=.03,
            parity=bf16.parity, fp32_parameter_bytes=sum(p.numel()*p.element_size() for p in fp32.parameters()),
            bf16_parameter_bytes=sum(p.numel()*p.element_size() for p in bf16.parameters())))
        bf16.verified = False
        original = bf16._lean
        def corrupted(images):
            cam, patches = original(images)
            return cam + .1, patches
        with patch.object(bf16, '_lean', side_effect=corrupted), self.assertRaisesRegex(ValueError, 'differs from native'):
            bf16(x)

    def test_bf16_all_world_four_first_batches_with_and_without_checkpointing(self):
        for checkpointing in (False, True):
            cfg = configuration(); cfg['preparation'] = {'fixture': True}
            cfg['geometry_online']['encoder_dtype'] = 'bf16'
            if checkpointing:
                cfg['geometry_online']['patch_fusion']['checkpointing'] = True
            model, batch, targets = fixture(geometry_settings=cfg['geometry_online'])
            rows = MixRows(batch, targets)
            receipt = dict(streams={s: {'count': n} for s, n in rows.counts.items()})
            root = directory()
            with patch.object(run, 'prepared', return_value=(receipt, {})), \
                 patch.object(run, 'processor_for_receipt', return_value=None), \
                 patch.object(run, 'load_model', return_value=model), patch.object(run, 'Rows', return_value=rows):
                records = run.first_batch_check(cfg, list(range(4)), root/'bf16_first_batch.json')
            self.assertEqual(len(records), 160)
            self.assertTrue(all(r['finite'] and 'error' not in r for r in records),
                            [r for r in records if not r['finite']])
            self.assertEqual({r['rank'] for r in records}, set(range(4)))
            self.assertTrue(all(p.grad is None for p in model.parameters()))

    def test_bf16_native_dino_patch_embed_and_full_meta_storage_accounting(self):
        block = {**settings(), 'patch_fusion': fusion_settings(50), 'encoder_dtype': 'bf16'}
        encoder = gx.G3TEncoder(block, architecture(dino=True), image_size=28)
        result = encoder(torch.rand(2, 3, 28, 28, requires_grad=True))
        self.assertTrue(encoder.parity['bitwise'])
        self.assertTrue(all(torch.isfinite(t).all() and not t.requires_grad for t in result))
        with torch.device('meta'):
            production = gx.G3TEncoder(block)
        count = sum(p.numel() for p in production.parameters())
        stored = sum(p.numel()*p.element_size() for p in production.parameters())
        self.assertEqual(count, 1341440022)
        self.assertEqual(stored, count*2)
        head_bytes = {name: sum(p.numel()*4 for p in head.parameters()) for name, head in
                      (('local_camera_head', production.local_camera_head),
                       ('global_camera_head', production.global_camera_head))}
        write(directory()/'production_memory.json', dict(parameters=count, fp32_parameter_bytes=count*4,
            bf16_parameter_bytes=stored, transient_fp32_head_bytes=head_bytes))

    def test_checkpointed_pooling_projector_outputs_and_gradients_are_exact(self):
        block = {**configuration()['geometry_online'], 'encoder_dtype': 'bf16'}
        model, batch, targets = fixture(geometry_settings=block)
        fusion = model.auxiliary_heads.patch_fusion
        with torch.no_grad():
            fusion.fc2.weight.normal_(std=.01)
            model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.normal_(std=.01)
        model.eval()
        def forward(checkpointing):
            model.zero_grad(set_to_none=True)
            if checkpointing:
                model.geometry_online['patch_fusion']['checkpointing'] = True
            result = model(batch, targets, stream='pose')
            result['loss'].backward()
            grads = {n: p.grad.clone() for n,p in fusion.named_parameters()}
            return result['loss'].detach(), grads
        left, grads = forward(False)
        with patch.object(fusion, 'pool_project', wraps=fusion.pool_project) as recompute:
            right, checked = forward(True)
            self.assertGreaterEqual(recompute.call_count, 2)
        self.assertTrue(torch.equal(left, right))
        for name in grads:
            self.assertTrue(torch.equal(grads[name], checked[name]), name)
        self.assertGreater(float(checked['fc1.weight'].norm()), 0.)
        self.assertTrue(all(p.grad is None for p in model.auxiliary_heads.geometry_encoder.parameters()))
        self.assertEqual(len(model.model.visual._forward_hooks), 0)
        model.gx_zero_feature = True
        with torch.no_grad():
            self.assertTrue(torch.isfinite(model(batch, targets)['loss']))

    def test_bf16_exports_checkpoints_record_dtype_and_reject_mismatch(self):
        model, batch, targets = fixture(geometry_settings={**configuration()['geometry_online'], 'encoder_dtype': 'bf16'})
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe))
        root = directory()
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()), \
             patch.object(dist, 'all_gather_object', side_effect=lambda out, value: out.__setitem__(0, value)):
            run.export(root/'export', model, model, {'base_identity': 'fixture'}, 0)
            pin = run.checkpoint(root/'checkpoint', model, optimizer, {}, 0)
            self.assertEqual(load(pin['path'])['geometry_encoder_dtype'], 'bf16')
            self.assertEqual(run.restore(pin, model, optimizer, {}), 0)
            for value in ('fp32', None):
                manifest = load(pin['path'])
                if value is None:
                    manifest.pop('geometry_encoder_dtype')
                else:
                    manifest['geometry_encoder_dtype'] = value
                write(root/f'checkpoint_{value}.json', manifest)
                with self.assertRaisesRegex(ValueError, 'encoder dtype'):
                    run.restore(file_pin(root/f'checkpoint_{value}.json'), model, optimizer, {})
        artifact = load(root/'export/artifact.json')
        self.assertEqual(artifact['geometry_online']['encoder_dtype'], 'bf16')
        heads = torch.load(root/'export/heads.pt', weights_only=True)
        self.assertEqual(heads['_gx_geometry_online']['encoder_dtype'], 'bf16')
        with patch.object(full_ft, 'load_export'):
            run.load_artifact(model, file_pin(root/'export/artifact.json'))
            heads['_gx_geometry_online'].pop('encoder_dtype')
            torch.save(heads, root/'changed_heads.pt')
            changed = {**artifact, 'heads': file_pin(root/'changed_heads.pt')}
            write(root/'changed_artifact.json', changed)
            with self.assertRaisesRegex(ValueError, 'heads.pt geometry_online'):
                run.load_artifact(model, file_pin(root/'changed_artifact.json'))
            model.geometry_online.pop('encoder_dtype')
            with self.assertRaisesRegex(ValueError, 'geometry_online'):
                run.load_artifact(model, file_pin(root/'export/artifact.json'))
            with collectives(), self.assertRaisesRegex(ValueError, 'encoder dtype'):
                run.restore(pin, model, optimizer, {})


class Distributed(unittest.TestCase):
    def test_native_fsdp_no_grad_forward_without_socket_transport(self):
        # This exercises native FSDP hooks; a size-one fake group proves no
        # cross-rank communication or sharding equivalence.
        import torch.testing._internal.distributed.fake_pg
        from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
        dist.init_process_group('fake', store=dist.HashStore(), rank=0, world_size=1)
        try:
            model, batch, targets = fixture()
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=True).eval()
            encoder = model.auxiliary_heads.geometry_encoder
            wrapped_modules = FSDP.fsdp_modules(wrapped)
            self.assertTrue(all(unit.module is not encoder for unit in wrapped_modules))
            rows = MixRows(batch, targets)
            records = run.check_plan_rows(wrapped, rows,
                [[('pose', [0]), ('vqa', [1]), ('pointing', [2]), ('routing', [3])]], [0])
            self.assertTrue(all(r['finite'] for r in records), records)
            self.assertTrue(all(p.grad is None for p in model.parameters()))
            groups = parameter_groups(wrapped, model.recipe, pose_lr_scale=.6, lm_lr_scale=.6)
            self.assertNotIn('geometry_encoder', {g['name'] for g in groups})
        finally:
            dist.destroy_process_group()

    @unittest.skipUnless(SOCKETS, 'Local gloo sockets required')
    def test_world_four_full_no_grad_forward(self):
        root = directory()
        mp.spawn(gloo_worker, args=(str(root),), nprocs=4, join=True)
        for rank in range(4):
            self.assertTrue(all(r['finite'] for r in load(root/f'rank{rank}.json')))
