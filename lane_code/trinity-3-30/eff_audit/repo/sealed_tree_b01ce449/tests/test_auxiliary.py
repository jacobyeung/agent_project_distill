"""Training-only perception heads: config, disabled-path identity, gradients, convergence and sidecars."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch

from tests import auxiliary_baseline as baseline
from tests.auxiliary_toys import (ToyTokenizer, Toy, blank_query, category_query, encoded_row, install_runner)

runner = install_runner()
from student_pilot import auxiliary_config as config  # noqa: E402
from student_pilot import auxiliary_targets as targets  # noqa: E402
from student_pilot.auxiliary_losses import AuxiliaryHeads, attach, video_features  # noqa: E402
from student_pilot.ddp_core import backward_batch, collate_rows, row_losses  # noqa: E402

PIN = {'path': '/fixture/sidecar', 'sha256': '0' * 64}
QUESTION = 'How many chairs are next to the table?'


@contextmanager
def kept_directory():
    """Fixture files stay under TMPDIR; the tests never delete anything."""
    yield tempfile.mkdtemp(prefix='auxiliary-test-')


def cfg(pose=.1, depth=0., **extra):
    return config.normalize({'pose_weight': pose, 'depth_weight': depth, 'head_width': 16, 'supervision': PIN, **extra})


def plain_batch():
    ids = torch.tensor([[1] + [3] * 64 + [2, 5, 6]])
    labels = torch.full_like(ids, -100)
    labels[:, -2:] = ids[:, -2:]
    return {'input_ids': ids, 'labels': labels, 'attention_mask': torch.ones_like(ids), 'video_grid_thw': torch.tensor([[16, 4, 4]])}


def pose_record():
    p = np.repeat(np.eye(4)[None], 32, axis=0)
    p[:, 0, 3] = np.arange(32) * .02
    pose, mask = targets.pose_targets(p)
    return {'pose': pose.tolist(), 'pose_mask': mask.tolist(), 'depth': np.ones((16, 4, 4)).tolist(),
            'depth_mask': np.ones((16, 4, 4), bool).tolist()}


def queries():
    counts = [1 + (g % 3) for g in range(16)]
    entries = [category_query(QUESTION, 'chairs', counts=counts, scene=4, obj=[0.5, -0.2, 2.0, -0.7, -0.4, -1.2]),
               category_query(QUESTION, 'table', scene=1, obj=[1.0, 0.1, 3.0, 0.3, -0.3, -0.5])]
    return entries + [blank_query(), blank_query()]


def sidecar_batch(tokenizer, rows=1):
    record = {**pose_record(), 'queries': queries()}
    encoded = []
    for index in range(rows):
        row, batch, audit = encoded_row(tokenizer, QUESTION, 'There are 4 chairs.', qid=f'r{index}', record=record)
        encoded.append(targets.add_to_batch(batch, row, tokenizer, audit))
    return collate_rows(encoded, tokenizer.pad_token_id)


def all_heads(**weights):
    values = {'count_weight': .2, 'object_weight': .3, **weights}
    return cfg(.1, .05, **values)


class ConfigTests(unittest.TestCase):
    def test_v1_configs_keep_their_normalized_form_and_hash(self):
        legacy = {'pose_weight': .1, 'depth_weight': 0., 'warmup_ratio': .1, 'head_width': 128, 'depth_grid': 4,
                  'translation_unit_m': 1.0, 'temporal_patch_size': 2, 'frame_count': 32,
                  'representation': 'first_tubelet_camera_c2w_rotation_columns6_translation3_v1',
                  'feature_source': 'final_language_norm_video_tokens_v1', 'supervision': PIN}
        self.assertEqual(config.normalize({'pose_weight': .1, 'supervision': PIN}), legacy)
        self.assertEqual(targets.digest(config.normalize({'pose_weight': .1, 'supervision': PIN})), targets.digest(legacy))

    def test_new_keys_defaults_hash_and_validation(self):
        normalized = config.normalize({'count_weight': 0.})
        for key, value in config.PERCEPTION_DEFAULTS.items():
            self.assertEqual(normalized[key], value)
        self.assertEqual((normalized['reason_mix_prob'], normalized['reason_mix_start']), (.3, .3))
        base = targets.digest(cfg())
        for key, value in [('count_weight', .1), ('object_weight', .1), ('reason_weight', .1), ('reason_mix_prob', .5),
                           ('reason_mix_start', .5)]:
            self.assertNotEqual(targets.digest(cfg(**{key: value})), base, key)
        self.assertNotEqual(targets.digest(cfg(count_weight=.1)), targets.digest(cfg(count_weight=.2)))
        # Query-token heads need no sidecar; sidecar heads still do.
        self.assertTrue(config.reason_enabled(config.normalize({'reason_weight': .1})))
        self.assertFalse(config.sidecar_enabled(config.normalize({'reason_weight': .1})))
        for bad in [{'count_weight': .1}, {'object_weight': .1}, {'count_weight': -1, 'supervision': PIN},
                    {'reason_weight': float('nan')}, {'reason_mix_prob': 1.5}, {'reason_mix_start': -.1},
                    {'query_contract': 'other'}, {'category_source': 'other'}, {'unknown': 1}]:
            with self.assertRaises(ValueError, msg=str(bad)):
                config.normalize(bad)

    def test_ramp_and_mixing_schedule(self):
        settings = config.normalize({'reason_weight': .1})
        self.assertAlmostEqual(config.ramp(0, 366, settings), 1 / 37)
        self.assertEqual(config.ramp(36, 366, settings), 1)
        start = int(np.ceil(.3 * 100))
        self.assertFalse(config.mixing_active(start - 1, 100, settings))
        self.assertTrue(config.mixing_active(start, 100, settings))
        self.assertFalse(config.mixing_active(99, 100, config.normalize({'reason_weight': .1, 'reason_mix_prob': 0.})))
        self.assertFalse(config.mixing_active(99, 100, config.normalize({'count_weight': 0.})))

    def test_native_config_normalization_binds_each_flag(self):
        from student_pilot.ddp_config import normalize_training_config
        plain = normalize_training_config({}, 'qwen35')
        self.assertNotIn('auxiliary', plain)
        bound = normalize_training_config({'auxiliary': all_heads()}, 'qwen35')
        self.assertEqual(bound['auxiliary'], all_heads())
        for key, value in [('pose_weight', .2), ('depth_weight', .07), ('count_weight', .3), ('object_weight', .4),
                           ('reason_weight', .1), ('reason_mix_prob', .9), ('head_width', 32)]:
            other = normalize_training_config({'auxiliary': {**all_heads(), key: value}}, 'qwen35')
            self.assertNotEqual(targets.digest(bound), targets.digest(other), key)


class DisabledPathTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_off_logits_loss_gradients_and_rng_bit_identical(self):
        tokenizer = ToyTokenizer()
        for settings in (None, cfg(0., 0.), config.normalize({'count_weight': 0., 'reason_weight': 0.})):
            model = Toy()
            twin = copy.deepcopy(model)
            state = torch.random.get_rng_state().clone()
            if settings is not None:
                self.assertIsNone(attach(model, settings, tokenizer))
            self.assertTrue(torch.equal(state, torch.random.get_rng_state()))
            rows = [encoded_row(tokenizer, QUESTION, 'There are 4 chairs.')[1],
                    encoded_row(tokenizer, QUESTION + ' Count them.', 'Two.')[1]]
            new_batch, old_batch = collate_rows(rows, 0), baseline.collate_rows(rows, 0)
            self.assertEqual(new_batch.keys(), old_batch.keys())
            for key in new_batch:
                self.assertTrue(torch.equal(new_batch[key], old_batch[key]), key)
            positions = torch.where((new_batch['labels'][:, 1:] != -100).any(0))[0]
            self.assertTrue(torch.equal(runner.supervised_logits(model, new_batch, positions),
                                        baseline.supervised_logits(twin, old_batch, positions)))
            new = backward_batch(model, new_batch, [1, 0], 1, 2)
            old = baseline.backward_batch(twin, old_batch, [1, 0], 1, 2)
            self.assertTrue(torch.equal(new, old))
            for (name, p), q in zip(model.named_parameters(), twin.parameters()):
                self.assertTrue(torch.equal(p.grad, q.grad), name)
            self.assertTrue(torch.equal(state, torch.random.get_rng_state()))

    def test_enabled_training_refuses_missing_targets(self):
        model = Toy()
        attach(model, cfg())
        with self.assertRaisesRegex(ValueError, 'require targets'):
            row_losses(model, plain_batch())

    def test_enabled_head_init_preserves_rng(self):
        for settings in (cfg(), all_heads(), all_heads(reason_weight=.1)):
            model = Toy()
            state = torch.random.get_rng_state().clone()
            attach(model, settings, ToyTokenizer())
            self.assertTrue(torch.equal(state, torch.random.get_rng_state()))

    def test_pose_only_heads_match_the_pose_contract(self):
        torch.manual_seed(3)
        heads = AuxiliaryHeads(12, cfg())
        self.assertEqual(sorted(name for name, _ in heads.named_children()), ['pose'])
        self.assertEqual(sum(p.numel() for p in heads.parameters()), 36 * 16 + 16 + 16 * 9 + 9)


class HeadTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_real_loss_path_reaches_backbone_and_each_head(self):
        tokenizer = ToyTokenizer()
        for settings in (cfg(), cfg(0., .05), cfg(0., 0., count_weight=.2), cfg(0., 0., object_weight=.3), all_heads()):
            model = Toy()
            attach(model, settings, tokenizer)
            loss = row_losses(model, sidecar_batch(tokenizer))
            self.assertEqual(loss.shape, (1,))
            loss.sum().backward()
            self.assertGreater(model.embedding.weight.grad.norm().item(), 0)
            for name, p in model.auxiliary_heads.named_parameters():
                self.assertIsNotNone(p.grad, name)
                self.assertTrue(torch.isfinite(p.grad).all(), name)
            for child, module in model.auxiliary_heads.named_children():
                self.assertGreater(sum(p.grad.abs().sum().item() for p in module.parameters()), 0, child)
            self.assertEqual(set(model.auxiliary_heads.last_terms),
                             {name for name in ('pose', 'depth', 'count', 'object') if settings.get(name + '_weight')})

    def test_category_heads_converge_on_a_tiny_batch(self):
        tokenizer = ToyTokenizer()
        batch = sidecar_batch(tokenizer, rows=2)
        heads = AuxiliaryHeads(12, cfg(0., 0., count_weight=.2, object_weight=.3))
        hidden = torch.randn(*batch['input_ids'].shape, 12)
        features, tokens, mask = video_features(hidden, batch, 3, 2, tokens=True)

        def terms():
            return heads(features, batch, hidden=hidden, tokens=tokens, token_mask=mask)[1]
        initial = {k: v.mean().item() for k, v in terms().items()}
        optimizer = torch.optim.Adam(heads.parameters(), lr=1e-2)
        for _ in range(300):
            optimizer.zero_grad(set_to_none=True)
            sum(v.mean() for v in terms().values()).backward()
            optimizer.step()
        final = {k: v.mean().item() for k, v in terms().items()}
        for k in initial:
            self.assertLess(final[k], initial[k] * .2, (k, initial, final))
        print('category_toy_loss', json.dumps({'initial': initial, 'final': final}), flush=True)

    def test_pose_and_depth_converge_on_a_tiny_batch(self):
        heads = AuxiliaryHeads(12, cfg(.1, .05))
        x = torch.randn(2, 16, 4, 4, 12, requires_grad=True)
        record = pose_record()
        y = {'aux_' + k: torch.tensor(v, dtype=torch.bool if 'mask' in k else torch.float32)[None].expand(2, *np.shape(v))
             for k, v in record.items()}
        initial = {k: v.mean().item() for k, v in heads(x, y)[1].items()}
        for _ in range(160):
            heads.zero_grad(set_to_none=True)
            sum(v.mean() for v in heads(x, y)[1].values()).backward()
            with torch.no_grad():
                for parameter in heads.parameters():
                    parameter.add_(parameter.grad, alpha=-.2)
        final = {k: v.mean().item() for k, v in heads(x, y)[1].items()}
        for k in initial:
            self.assertLess(final[k], initial[k] * .5, (k, initial, final))
        self.assertGreater(x.grad.norm().item(), 0)

    def test_masked_targets_give_zero_loss_and_zero_gradients(self):
        tokenizer = ToyTokenizer()
        batch = sidecar_batch(tokenizer)
        for key in [k for k in batch if k.startswith('aux_') and k.endswith('_mask')]:
            batch[key] = torch.zeros_like(batch[key])
        batch['aux_pose'].fill_(float('nan'))
        batch['aux_depth'].fill_(float('nan'))
        heads = AuxiliaryHeads(12, all_heads())
        hidden = torch.randn(*batch['input_ids'].shape, 12, requires_grad=True)
        features, tokens, mask = video_features(hidden, batch, 3, 2, tokens=True)
        loss = heads(features, batch, hidden=hidden, tokens=tokens, token_mask=mask)[0]
        self.assertEqual(loss.item(), 0)
        loss.sum().backward()
        for name, p in heads.named_parameters():
            self.assertTrue(torch.equal(p.grad, torch.zeros_like(p.grad)), name)

    def test_padding_weights_zero_every_objective(self):
        tokenizer = ToyTokenizer()
        model = Toy()
        attach(model, all_heads(), tokenizer)
        backward_batch(model, sidecar_batch(tokenizer, rows=2), [0, 0], 1, 2)
        for name, p in model.named_parameters():
            self.assertTrue(torch.equal(p.grad, torch.zeros_like(p.grad)), name)

    def test_temporal_and_causal_alignment(self):
        b = plain_batch()
        h = torch.randn(1, b['input_ids'].shape[1], 12)
        self.assertEqual(video_features(h, b, 3, 2).shape, (1, 16, 4, 4, 12))
        features, tokens, mask = video_features(h, b, 3, 2, tokens=True)
        self.assertEqual((tokens.shape, int(mask.sum())), ((1, 64, 12), 64))
        bad = copy.deepcopy(b)
        bad['video_grid_thw'][0, 0] = 32
        with self.assertRaises(ValueError):
            video_features(h, bad, 3, 2)
        bad = copy.deepcopy(b)
        bad['labels'][0, 20] = 3
        with self.assertRaises(ValueError):
            video_features(h, bad, 3, 2)

    def test_checkpoint_head_roundtrip(self):
        tokenizer = ToyTokenizer()
        settings = all_heads(reason_weight=.1)
        model = Toy()
        attach(model, settings, tokenizer)
        batch = sidecar_batch(tokenizer)
        batch = {**batch, **reason_fields(batch)}
        reference = row_losses(model, batch)
        buffer = io.BytesIO()
        torch.save({name: value.detach().cpu() for name, value in model.auxiliary_heads.state_dict().items()}, buffer)
        buffer.seek(0)
        twin = Toy()
        twin.load_state_dict({k: v for k, v in model.state_dict().items() if not k.startswith('auxiliary_heads.')}, strict=False)
        attach(twin, json.loads(json.dumps(model.auxiliary_heads.manifest()))['settings'], tokenizer)
        twin.auxiliary_heads.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        self.assertTrue(torch.equal(reference, row_losses(twin, batch)))
        manifest = model.auxiliary_heads.manifest()
        self.assertTrue(manifest['inference_required'])
        self.assertEqual(manifest['query_tokens']['COUNT']['token'], '<|box_start|>')
        self.assertFalse(AuxiliaryHeads(12, cfg()).manifest()['inference_required'])


def reason_fields(batch):
    """Inert query fields: one padded slot per row and the displayed timestamps."""
    rows = batch['input_ids'].shape[0]
    return {'aux_reason_pos': torch.full((rows, 1), -1), 'aux_reason_kind': torch.full((rows, 1), -1),
            'aux_reason_value': torch.zeros(rows, 1), 'aux_reason_span': torch.zeros(rows, 1, dtype=torch.long),
            'aux_group_times': torch.arange(16.)[None].expand(rows, 16)}


class SidecarTests(unittest.TestCase):
    def test_pose_world_gauge_invariance_scale_and_first_pair(self):
        p = np.repeat(np.eye(4)[None], 32, 0)
        p[:, 0, 3] = np.arange(32)
        g = np.array([[0., -1, 0, 4], [1, 0, 0, -2], [0, 0, 1, 8], [0, 0, 0, 1]])
        a, m = targets.pose_targets(p)
        b, n = targets.pose_targets(g @ p)
        np.testing.assert_allclose(a, b, atol=1e-6)
        self.assertFalse(m[0])
        self.assertEqual(a[1, 6], 2)
        c, _ = targets.pose_targets(p, 2)
        np.testing.assert_allclose(c[:, 6:], a[:, 6:] / 2)
        p[0, 0, 0] = 2
        with self.assertRaises(ValueError):
            targets.pose_targets(p)

    def test_depth_log_metric_and_invalid_cells(self):
        z = np.ones((32, 8, 8)) * 4
        mask = np.ones_like(z, dtype=bool)
        mask[:, :2, :2] = False
        d, m = targets.depth_targets(z, mask)
        self.assertEqual(d.shape, (16, 4, 4))
        self.assertFalse(m[:, 0, 0].any())
        np.testing.assert_allclose(d[m], np.log(4))
        z[:] = np.nan
        d, m = targets.depth_targets(z, mask)
        self.assertFalse(m.any())

    def test_category_span_maps_to_prompt_tokens_by_offsets(self):
        tokenizer = ToyTokenizer()
        row, batch, audit = encoded_row(tokenizer, QUESTION, 'Four.', record={**pose_record(), 'queries': queries()},
                                        options=['A. 3', 'B. 4'])
        result = targets.add_to_batch(batch, row, tokenizer, audit)
        tokens = result['aux_category_tokens'][0]
        self.assertEqual(tokens.shape, (4, batch['input_ids'].shape[1]))
        ids = batch['input_ids'][0]
        self.assertEqual(tokenizer.decode(ids[tokens[0]]), 'chairs')
        self.assertEqual(tokenizer.decode(ids[tokens[1]]), 'table')
        self.assertFalse(tokens[2:].any())
        self.assertTrue(torch.all(batch['labels'][0][tokens.any(0)] == -100))
        self.assertEqual(result['aux_group_count'].shape, (1, 4, 16))
        self.assertEqual(result['aux_object'].shape, (1, 4, 6))
        self.assertEqual(result['aux_scene_count_mask'].tolist(), [[True, True, False, False]])
        moved = copy.deepcopy(row)
        moved['student_input']['question'] = 'Different text'
        with self.assertRaisesRegex(ValueError, 'verbatim'):
            targets.add_to_batch(batch, moved, tokenizer, audit)

    def test_v2_sidecar_load_validation_and_v1_compatibility(self):
        row = {'qid': 'fixture', 'dataset': 'scannet', 'scene': 'synthetic', 'target': 'Four.',
               'student_input': {'question': QUESTION, 'options': [], 'fps': 1., 'total_num_frames': 32,
                                 'frame_indices': list(range(32)), 'timestamps': list(range(32)),
                                 'frames': [{'path': f'/rgb/{i}.png', 'sha256': f'{i:064x}'} for i in range(32)]}}
        record = {'qid': 'fixture', 'input_sha256': targets.input_identity(row), **pose_record(),
                  'sources': {}, 'deferred': {}, 'queries': queries()}
        with kept_directory() as directory:
            def write(name, payload):
                path = Path(directory) / name
                path.write_text(json.dumps(payload))
                return targets.pin(path)
            v2 = write('v2.json', {'schema': targets.SCHEMA_V2, 'translation_unit_m': 1., 'rows': [record]})
            v1_record = {k: v for k, v in record.items() if k != 'queries'}
            v1 = write('v1.json', {'schema': targets.SCHEMA, 'translation_unit_m': 1., 'rows': [v1_record]})
            loaded = targets.load_for_rows([row], cfg(count_weight=.2, object_weight=.1, supervision=v2))
            self.assertEqual(loaded[0]['queries'], queries())
            # Pose-only configs accept v1 and drop v2 queries so no category work runs.
            self.assertEqual(targets.load_for_rows([row], cfg(supervision=v1)), [v1_record])
            self.assertNotIn('queries', targets.load_for_rows([row], cfg(supervision=v2))[0])
            with self.assertRaisesRegex(ValueError, 'schema'):
                targets.load_for_rows([row], cfg(count_weight=.2, supervision=v1))
            for mutate, message in [
                    (lambda r: r['queries'].pop(), 'exactly four'),
                    (lambda r: r['queries'][0].update(span=[0, 999]), 'span'),
                    (lambda r: r['queries'][0]['group_count'].__setitem__(0, -1), 'visible count'),
                    (lambda r: r['queries'][0].update(object=[0.] * 5), 'object'),
                    (lambda r: r['queries'][0].update(extra=1), 'fields')]:
                bad = copy.deepcopy(record)
                mutate(bad)
                pin = write('bad.json', {'schema': targets.SCHEMA_V2, 'translation_unit_m': 1., 'rows': [bad]})
                with self.assertRaisesRegex(ValueError, message):
                    targets.load_for_rows([row], cfg(count_weight=.2, supervision=pin))
            empty = copy.deepcopy(record)
            empty['queries'] = [blank_query() for _ in range(4)]
            pin = write('empty.json', {'schema': targets.SCHEMA_V2, 'translation_unit_m': 1., 'rows': [empty]})
            with self.assertRaisesRegex(ValueError, 'zero covered rows: object'):
                targets.load_for_rows([row], cfg(object_weight=.2, supervision=pin))
            self.assertIsNone(targets.load_for_rows([row], cfg(0, 0)))

    def test_v1_builder_and_load_preserve_rows(self):
        from unittest.mock import patch
        import sys
        with kept_directory() as directory:
            root = Path(directory)
            row = {'qid': 'fixture', 'dataset': 'scannetppv2', 'scene': 'synthetic',
                   'student_input': {'question': 'fixture only', 'options': [], 'fps': 1., 'total_num_frames': 32,
                                     'frame_indices': list(range(32)), 'timestamps': list(range(32)),
                                     'frames': [{'path': f'/rgb/{i}.png', 'sha256': f'{i:064x}'} for i in range(32)]}}
            p = np.repeat(np.eye(4)[None], 32, 0)
            p[:, 0, 3] = np.arange(32) * .01
            np.savez(root / 'calibration.npz', camera_poses=p, indices=np.arange(32))
            np.savez(root / 'dense.npz', depth_z=np.ones((32, 8, 8)) * 2, mask=np.ones((32, 8, 8), bool), indices=np.arange(32))
            alignment = {'estimated_geometry_used': False, 'validated_slots': 32, 'pose_field': 'aligned_pose',
                         'frames': [{'ordinal': i} for i in range(32)]}
            (root / 'alignment.json').write_text(json.dumps(alignment))
            (root / 'source.json').write_text('{}')
            receipt = {'dataset': row['dataset'], 'scene_name': row['scene'],
                       'coordinate_frame': 'source_world_meters_opencv_camera_to_world',
                       'geometry_source': 'official_aligned_pose_intrinsic_mesh_gt_valid_support',
                       'frames': [{'ordinal': i, 'timestamp_sec': i, 'sha256': f'{i:064x}'} for i in range(32)],
                       'calibration': targets.pin(root / 'calibration.npz'), 'dense': targets.pin(root / 'dense.npz'),
                       'alignment': targets.pin(root / 'alignment.json'), 'source_provenance': targets.pin(root / 'source.json')}
            (root / 'receipt.json').write_text(json.dumps(receipt))
            record = targets.build_row(row, targets.pin(root / 'receipt.json'), include_depth=True)
            self.assertFalse(record['deferred'])
            self.assertEqual(sum(record['pose_mask']), 15)
            second = copy.deepcopy(row)
            second['qid'] = 'missing'
            (root / 'training.json').write_text(json.dumps({'rows': [row, second]}))
            (root / 'map.json').write_text(json.dumps({row['qid']: targets.pin(root / 'receipt.json')}))
            (root / 'policy.json').write_text(json.dumps({'allowed_groups': ['train/scene'], 'excluded_groups': [],
                                                          'row_groups': {'fixture': 'train/scene', 'missing': 'train/scene'}}))
            argv = ['builder', '--training', str(root / 'training.json'), '--receipt-map', str(root / 'map.json'),
                    '--scene-policy', str(root / 'policy.json'), '--output', str(root / 'built.json'), '--depth']
            with patch.object(sys, 'argv', argv):
                targets.main()
            built = json.loads((root / 'built.json').read_text())
            self.assertEqual(len(built['rows']), 2)
            self.assertEqual(built['coverage'], {'pose': 1, 'depth': 1})
            (root / 'sidecar.json').write_text(json.dumps({'schema': targets.SCHEMA, 'translation_unit_m': 1., 'rows': [record]}))
            settings = cfg(supervision=targets.pin(root / 'sidecar.json'))
            self.assertEqual(targets.load_for_rows([row], settings), [record])
            moved = copy.deepcopy(row)
            moved['student_input']['frames'][0]['path'] = '/new/rgb.png'
            self.assertEqual(targets.input_identity(row), targets.input_identity(moved))
            moved['student_input']['frames'][0]['sha256'] = 'f' * 64
            with self.assertRaises(ValueError):
                targets.load_for_rows([moved], settings)


if __name__ == '__main__':
    unittest.main()
