"""Frozen full-export initialization and attached-module freezing on tiny native CPU models."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from student_pilot import auxiliary_losses, camera_config, ddp_checkpoints, ddp_config, ddp_core, fsdp_training, full_ft
from student_pilot.camera_targets import insert_tokens
from student_pilot.common import canonical_bytes, sha256
from tests.fullft_toys import bf16_batch, source_rows, tiny_base
from tests.test_camera import PIN, SMALL, record_for
from tests.test_full_ft import CarrierTokenizer
from tools import heads_only_configs as builder


def directory():
    return Path(tempfile.mkdtemp(prefix='heads_only_', dir=os.environ['LANE_TEST_OUTPUT']))


def pin(path):
    return {'path': str(path), 'sha256': sha256(path)}


def export_fixture(root, model):
    state = model.state_dict()
    full_ft.save_export(full_ft.export_tensors(state, [name for name, _ in full_ft.base_parameters(model)]),
                        root / 'full_weights', {'base_sha256': 'b' * 64}, {'fixture': True})
    return pin(root / 'full_weights' / full_ft.EXPORT_MANIFEST)


def frozen_block(export, **extra):
    return full_ft.normalize({'train': {group: False for group in full_ft.TRAIN_GROUPS},
                              'init': {'kind': 'full_export', **export}, **extra})


def depth_camera(**extra):
    return camera_config.normalize({'weight': 1.0, **SMALL, 'supervision': PIN,
        'point_depth': {'weight': 0.5, 'd_proj': 16, 'mlp_hidden': 16, 'num_heads': 2,
                        'context_depth': 1, 'vit_layers': [1, 2, 3], 'num_points_per_frame': 2}, **extra})


class FrozenExportTests(unittest.TestCase):
    def test_normalize_accepts_only_the_new_frozen_export_combination(self):
        export = {'path': '/fixture/full_weights.json', 'sha256': 'a' * 64}
        block = frozen_block(export)
        self.assertTrue(full_ft.frozen_vlm(block))
        self.assertEqual(block, full_ft.normalize(block))
        for parallel in ('ddp', 'fsdp'):
            settings = ddp_config.normalize_training_config({'parallel': parallel, 'world_size': 2, 'full_ft': block}, 'qwen35')
            self.assertEqual(settings['full_ft'], block)
        for extra in ({'init': {'kind': 'base_merged_init_adapter'}},
                      {'train': {'llm': False, 'vision_blocks': True}},
                      {'learning_rates': {'llm': 1e-5}},
                      {'init': {'kind': 'full_export', **export, 'extra': True}},
                      {'init': {'kind': 'full_export', **export, 'sha256': 'A' * 64}}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                full_ft.normalize({**block, **extra})

    def test_bf16_export_is_exact_without_masters_and_retains_all_pin_checks(self):
        root = directory()
        reference = tiny_base(seed=5)
        export = export_fixture(root, reference)
        model = tiny_base(seed=99)
        block = frozen_block(export)
        evidence = full_ft.load_init_export(model, block, 'b' * 64)
        groups, report = full_ft.prepare_model(model, block)
        self.assertEqual(groups, {})
        self.assertIsNone(report['master_dtype'])
        self.assertEqual(evidence['manifest_sha256'], export['sha256'])
        for name, parameter in model.named_parameters():
            self.assertEqual(parameter.dtype, torch.bfloat16)
            self.assertFalse(parameter.requires_grad)
            self.assertTrue(torch.equal(parameter, reference.state_dict()[name]), name)
        with self.assertRaisesRegex(ValueError, 'another base snapshot'):
            full_ft.load_init_export(tiny_base(), block, 'c' * 64)
        with self.assertRaisesRegex(ValueError, 'BF16 base'):
            full_ft.load_init_export(tiny_base(dtype=torch.float32), block, 'b' * 64)
        with self.assertRaisesRegex(ValueError, 'manifest differs'):
            full_ft.load_init_export(tiny_base(), frozen_block({**export, 'sha256': '0' * 64}), 'b' * 64)
        manifest = json.loads(Path(export['path']).read_bytes())
        shard = root / 'full_weights' / manifest['files'][0]['name']
        with shard.open('ab') as handle:
            handle.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'differs from its manifest'):
            full_ft.load_init_export(tiny_base(), block, 'b' * 64)

    def test_one_native_step_updates_only_unfrozen_heads(self):
        root = directory()
        # Three tiny vision blocks provide the depth head's three native feature taps.
        model = tiny_base()
        config = copy.deepcopy(model.config)
        config.vision_config.depth = 3
        model = type(model)(config).to(torch.bfloat16)
        export = export_fixture(root, model)
        block = frozen_block(export)
        full_ft.load_init_export(model, block, 'b' * 64)
        full_ft.prepare_model(model, block)
        heads = auxiliary_losses.attach(model, None, CarrierTokenizer(), depth_camera(freeze_modules=['point_depth']))
        path = root / 'auxiliary_heads.pt'
        # Give the init weights a distinct identity and exercise the strict native module loader.
        state = {name: value.detach().clone() + 0.001 for name, value in heads.state_dict().items()}
        torch.save(state, path)
        block = frozen_block(export, init_modules={'heads': pin(path)})
        full_ft.load_init_modules(block, heads=heads)
        self.assertTrue(all(torch.equal(value, state[name]) for name, value in heads.state_dict().items()))
        settings = ddp_config.normalize_training_config({'world_size': 2, 'full_ft': block}, 'qwen35')
        for opt in (full_ft.build_optimizer({}, {}, heads, block, settings),
                    ddp_core.build_optimizer({}, heads, settings),
                    ddp_core.build_optimizer({}, heads, {**settings, 'head_learning_rate': 1e-4})):
            self.assertEqual({id(p) for group in opt.param_groups for p in group['params']},
                             {id(p) for p in heads.parameters() if p.requires_grad})
        optimizer = full_ft.build_optimizer({}, {}, heads, block, settings)
        before = {name: value.detach().clone() for name, value in model.named_parameters()}
        record = {**record_for(0), 'point_depth': {'uv': [[[250., 750.], [500., 500.]]] * 16,
                                                  'depth': [[2., 3.]] * 16, 'mask': [[True, True]] * 16}}
        batch = insert_tokens(source_rows()[0], record, CarrierTokenizer())
        model.train()
        ddp_core.row_losses(model, bf16_batch(batch)).sum().backward()
        optimizer.step()
        changed = set()
        for name, parameter in model.named_parameters():
            if not torch.equal(parameter, before[name]):
                changed.add(name)
            if not parameter.requires_grad:
                self.assertIsNone(parameter.grad, name)
                self.assertTrue(torch.equal(parameter, before[name]), name)
                self.assertNotIn(parameter, optimizer.state)
        self.assertTrue(changed)
        self.assertTrue(all(name.startswith('auxiliary_heads.') and '.point_depth.' not in name for name in changed))
        self.assertTrue(any('camera.head.' in name for name in changed))
        self.assertTrue(any('camera.tokens' in name for name in changed))

    def test_schedule_caps_only_the_new_mode_and_resume_counters_agree(self):
        export = {'path': '/fixture/full_weights.json', 'sha256': 'a' * 64}
        block = frozen_block(export)
        self.assertEqual(full_ft.scheduler_steps(block, 1800, 1600), 1600)
        self.assertEqual(full_ft.scheduler_steps(block, 1800, None), 1800)
        for old in (full_ft.normalize({}), full_ft.normalize({'train': {'llm': False}}),
                    full_ft.normalize({'init': {'kind': 'full_export', **export}})):
            self.assertEqual(full_ft.scheduler_steps(old, 1800, 1600), 1800)
        settings = ddp_config.normalize_training_config({'world_size': 2, 'full_ft': block,
            'epochs': 3, 'max_steps': 1600, 'effective_batch_size': 64}, 'qwen35')
        state = {'row_count': 38400, 'microbatch_size': 1, 'planned_steps': 1600, 'realized': {'optimizer_steps': 400}}
        checkpoint = {'step': 400, 'state': state, 'metrics_line_count': 400,
                      'batch_plan_position': {'epoch': 0, 'batch_index': 400}, 'epoch': 0}
        self.assertEqual(ddp_checkpoints.validate_progress(checkpoint, settings), 600)
        self.assertEqual(ddp_core.schedule_lr(1599, 1600, settings), 0.0)


class FreezeConfigTests(unittest.TestCase):
    def test_frozen_attachments_require_pins_and_remain_replicated_outside_fsdp(self):
        from safetensors.torch import save_file
        root = directory()
        model = tiny_base()
        camera = depth_camera(freeze_modules=['point_depth', 'geometry'])
        heads = auxiliary_losses.attach(model, None, CarrierTokenizer(), camera)
        geometry = torch.nn.Module()
        geometry.projector = torch.nn.Linear(16, 16)
        model.add_module('geometry_input', geometry)
        geometry_path = root / 'geometry.safetensors'
        save_file(geometry.projector.state_dict(), str(geometry_path))
        heads_path = root / 'heads.pt'
        torch.save(heads.state_dict(), heads_path)
        block = full_ft.normalize({'train': {'llm': False},
                                  'init_modules': {'heads': pin(heads_path), 'geometry': pin(geometry_path)}})
        with self.assertRaisesRegex(ValueError, 'init_modules.heads'):
            full_ft.frozen_attached_parameters(None, camera, heads, geometry)
        with self.assertRaisesRegex(ValueError, 'init_modules.geometry'):
            full_ft.frozen_attached_parameters({**block, 'init_modules': {'heads': pin(heads_path)}}, camera, heads, geometry)
        with self.assertRaisesRegex(ValueError, 'attached projector'):
            full_ft.frozen_attached_parameters(block, camera, heads)
        frozen = full_ft.frozen_attached_parameters(block, camera, heads, geometry)
        self.assertEqual({id(p) for p in frozen},
                         {id(p) for p in heads.camera.point_depth.parameters()} | {id(p) for p in geometry.parameters()})
        full_ft.load_init_modules(block, geometry=geometry, heads=heads)
        parameters = [p for p in model.parameters() if p.requires_grad]
        with patch.object(fsdp_training, 'FSDP', return_value=model) as wrap, patch.object(fsdp_training.dist, 'broadcast'):
            fsdp_training.wrap_model(model, parameters, object(), torch.device('cpu'), frozen_adapters=frozen)
        self.assertEqual({id(p) for p in wrap.call_args.kwargs['ignored_states']},
                         {id(p) for p in heads.parameters()} | {id(p) for p in geometry.parameters()})
        for _, p in full_ft.base_parameters(model):
            p.data = p.data.float()
        with patch('torch.distributed.fsdp.FullyShardedDataParallel', return_value=model) as wrap, \
                patch.object(full_ft.dist, 'broadcast'):
            full_ft.wrap_full_model(model, [*parameters, *frozen], object(), torch.device('cpu'))
        self.assertEqual({id(p) for p in wrap.call_args.kwargs['ignored_states']},
                         {id(p) for p in heads.parameters()} | {id(p) for p in geometry.parameters()})
        settings = ddp_config.normalize_training_config({'world_size': 2}, 'qwen35')
        optimizer = full_ft.build_optimizer({}, {}, heads, block, settings)
        before = {name: p.detach().clone() for name, p in geometry.named_parameters()}
        # The frozen projector can feed a trainable head without owning gradients or AdamW state.
        hidden = geometry.projector(torch.randn(1, 16, 16))
        target = {'aux_camera_positions': torch.arange(16)[None],
                  'aux_camera_target': torch.tensor([record_for(0)['camera']], dtype=torch.float32),
                  'aux_camera_mask': torch.ones(1, 16, dtype=torch.bool), 'aux_camera_scale': torch.ones(1),
                  'aux_point_depth_uv': torch.zeros(1, 16, 2, 2), 'aux_point_depth_gt': torch.ones(1, 16, 2),
                  'aux_point_depth_mask': torch.zeros(1, 16, 2, dtype=torch.bool)}
        heads.camera.loss(hidden, target).sum().backward()
        optimizer.step()
        for name, p in geometry.named_parameters():
            self.assertTrue(torch.equal(p, before[name]))
            self.assertIsNone(p.grad)
            self.assertNotIn(p, optimizer.state)

    def test_absent_key_keeps_canonical_config_and_initialization(self):
        raw = {'weight': 1.0, **SMALL, 'supervision': PIN}
        cfg = camera_config.normalize(raw)
        self.assertNotIn('freeze_modules', cfg)
        self.assertEqual(canonical_bytes(cfg), canonical_bytes(camera_config.normalize(cfg)))
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(7)
            plain = auxiliary_losses.AuxiliaryHeads(16, {}, depth_camera(), vit_dim=16)
            torch.manual_seed(7)
            frozen = auxiliary_losses.AuxiliaryHeads(16, {}, depth_camera(freeze_modules=['point_depth']), vit_dim=16)
        self.assertTrue(all(torch.equal(v, frozen.state_dict()[n]) for n, v in plain.state_dict().items()))
        self.assertTrue(all(p.requires_grad for p in plain.parameters()))
        self.assertTrue(all(not p.requires_grad for p in frozen.camera.point_depth.parameters()))

    def test_module_names_are_validated(self):
        for value in ('point_depth', [None], ['point_depth', 'point_depth'], ['unknown'], ['tokens']):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'freeze_modules'):
                depth_camera(freeze_modules=value)
        from student_pilot.camera_head import CameraSupervision
        with self.assertRaisesRegex(ValueError, 'not attached'):
            CameraSupervision(16, {'weight': 1.0, **SMALL, 'supervision': PIN, 'freeze_modules': ['point_depth']})

    def test_optional_milestones_preserve_default_and_pick_exact_steps(self):
        self.assertEqual(ddp_config.normalize_run_control({}), {'checkpoint_every_steps': 25})
        control = ddp_config.normalize_run_control({'checkpoint_milestones': builder.MILESTONES})
        self.assertEqual([s for s in range(1, 1601) if ddp_checkpoints.milestone_due(s, control)], builder.MILESTONES)
        self.assertFalse(ddp_checkpoints.due(600, 0, 700, 1600, control))
        self.assertEqual(ddp_checkpoints.checkpoint_kind(400, 1600, control, True, False), 'milestone')
        self.assertEqual(ddp_checkpoints.checkpoint_kind(1600, 1600, control, True, False), 'final')
        for steps in ([], [True], [0], [400, 200], [200, 200]):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                ddp_config.normalize_run_control({'checkpoint_milestones': steps})


class BuilderTests(unittest.TestCase):
    def request(self):
        from tests.test_geometry_training import geometry_settings
        root = directory()
        def save(name, value):
            path = root / name
            path.write_bytes(canonical_bytes(value))
            return pin(path)
        bank = save('bank.json', {'synthetic': True})
        cpdm = {'world_size': 8, 'parallel': 'fsdp', 'camera': depth_camera(supervision=bank)}
        export = export_fixture(root, tiny_base())
        features = save('features.jsonl', {'synthetic': True})
        geometry = geometry_settings(root / 'features.jsonl')
        geometry['store'].update(manifest_sha256=features['sha256'],
                                 camera_manifest=str(root / 'cameras.jsonl'),
                                 camera_manifest_sha256=save('cameras.jsonl', {'camera': True})['sha256'])
        return root, {'schema': 'heads-only-build-v1', 'cpdm_config': save('cpdm.json', cpdm),
            'f17': {'full_weights': export, 'heads': save('auxiliary_heads.pt', {'synthetic': 'heads'})},
            'rows': {'A0': {'name': 'POSE32_V2', 'count': 1280, 'source': save('a0.json', {'rows': 'a0'})},
                     'A1': {'name': 'SECOND_SOURCE', 'count': 2560, 'source': save('a1.json', {'rows': 'a1'})}},
            'freeze_modules': ['point_depth'],
            'run2': {'geometry_config': save('geometry.json', geometry),
                     'geometry_weights': save('projector.safetensors', {'synthetic': 'geometry'}),
                     'heads': save('prior_heads.pt', {'synthetic': 'migrated heads'})}}

    def test_builder_emits_normalized_pinned_arms_and_prior_variants_without_loading_weights(self):
        root, request = self.request()
        request_path = root / 'request.json'
        request_path.write_bytes(canonical_bytes(request))
        with patch.object(torch, 'load', side_effect=AssertionError('builder must not deserialize weights')):
            builder.main(['--request', str(request_path), '--output', str(root / 'built')])
        spec = json.loads((root / 'built/BUILD.json').read_bytes())
        self.assertEqual(set(spec['configs']), {'A0_RUN1', 'A1_RUN1', 'A0_RUN2', 'A1_RUN2'})
        self.assertEqual(spec['inputs'], request)
        for name, item in spec['configs'].items():
            path = root / 'built' / item['path']
            self.assertEqual(sha256(path), item['sha256'])
            cfg = json.loads(path.read_bytes())
            settings = ddp_config.normalize_training_config(cfg, 'qwen35')
            self.assertTrue(full_ft.frozen_vlm(settings['full_ft']))
            self.assertEqual(settings['effective_batch_size'], 64)
            self.assertEqual(settings['warmup_ratio'], .03)
            self.assertEqual(settings['full_ft']['learning_rates']['heads'], 1e-4)
            self.assertEqual(cfg['checkpoint_milestones'], builder.MILESTONES)
            self.assertEqual(cfg['full_ft']['init']['sha256'], request['f17']['full_weights']['sha256'])
            prior = name.endswith('RUN2')
            self.assertEqual(camera_config.g3t_prior_enabled(cfg['camera']), prior)
            if prior:
                self.assertIn('geometry', cfg['camera']['freeze_modules'])
                self.assertEqual(cfg['full_ft']['init_modules']['heads'], request['run2']['heads'])
            else:
                self.assertEqual(cfg['full_ft']['init_modules']['heads'], request['f17']['heads'])
                self.assertNotIn('geometry', cfg)
        bad = copy.deepcopy(request)
        bad['f17']['heads']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'differs from its SHA-256'):
            builder.build(bad)
        bad = copy.deepcopy(request)
        bad['rows']['A1']['source'] = bad['rows']['A0']['source']
        with self.assertRaisesRegex(ValueError, 'second row source'):
            builder.build(bad)


if __name__ == '__main__':
    unittest.main()
