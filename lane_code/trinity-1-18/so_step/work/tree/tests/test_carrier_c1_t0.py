"""T0 trainer guards: rank-synced row errors, shared startup errors, rank-aligned depth,
C1-r teacher alignment with uncovered rows, and the warm-start head graft."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_run as run
from student_pilot import c1r_align
from tests.test_carrier_c1_final import final_fixture
from tests.test_fsdp import SOCKETS

ALIGN = {'cam': {'layer': 'final', 'weight': 0.5}, 'clip': {'weight': 0.5}, 'loss': 'centered_cosine',
         'patch': None, 'projector': {'depth': 2, 'width': '2H'}, 'schedule': {'kind': 'constant'}, 'targets': ['cam']}


def good_batch(slots=32):
    ids = torch.zeros(1, 8, dtype=torch.long)
    return dict(input_ids=ids, labels=torch.tensor([[-100]*4 + [1]*4]),
                aux_camera_positions=torch.tensor([list(range(slots)) + [-1]*(32-slots)]))


class StubRows:
    def __init__(self, bad):
        self.bad = bad
    def count(self, stream):
        return 10
    def get(self, stream, index):
        if index in self.bad:
            raise ValueError('Complete routing row exceeds 16384 tokens')
        return good_batch(), None, {'qid': index}


def _fetch_worker(rank, world, path, results):
    dist.init_process_group('gloo', init_method='file://'+path, rank=rank, world_size=world)
    try:
        model = type('M', (), {'training_mode': 'final'})()
        # Rank 1 cannot encode row 0: both ranks must move to row 1 together.
        out = run.fetch(StubRows({0} if rank == 1 else set()), 'routing', 0, model, device='cpu', distributed=True)
        results[rank] = out[2]['index']
        # Every candidate fails on rank 0: both ranks skip together.
        out = run.fetch(StubRows(set(range(10)) if rank == 0 else set()), 'routing', 0, model, tries=3,
                        device='cpu', distributed=True)
        results[rank + world] = out is None
        try:
            run.agree(dist.group.WORLD, 'bind refused' if rank == 0 else None)
            results[rank + 2*world] = False
        except ValueError as exc:
            results[rank + 2*world] = 'rank 0' in str(exc)
    finally:
        dist.destroy_process_group()


class T0Guards(unittest.TestCase):
    def test_fetch_substitutes_then_skips_and_checks_rows(self):
        model, _, _ = final_fixture()
        batch, _, audit = run.fetch(StubRows({0, 1}), 'routing', 0, model)
        self.assertEqual((audit['qid'], audit['index'], audit['substituted_from'], len(audit['row_errors'])), (2, 2, 0, 2))
        self.assertIsNone(run.fetch(StubRows({0, 1}), 'routing', 0, model, tries=2))
        targets = dict(aux_camera_mask=torch.ones(1, 32, dtype=torch.bool),
                       aux_point_depth_mask=torch.zeros(1, 32, 64, dtype=torch.bool),
                       aux_point_depth_uv=torch.zeros(1, 32, 64, 2))
        run.check_row(good_batch(), targets, 'pose', model)
        with self.assertRaises(ValueError):
            run.check_row(good_batch(16), targets, 'pose', model)  # the 16-carrier step-1 row
        with self.assertRaises(ValueError):
            run.skip_guard(2, 100)

    @unittest.skipUnless(SOCKETS, 'Local gloo sockets required')
    def test_rank_synced_decisions_over_gloo(self):
        root = tempfile.mkdtemp(prefix='t0_gloo_', dir=os.environ.get('TMPDIR'))
        results = mp.Manager().dict()
        mp.spawn(_fetch_worker, args=(2, str(Path(root)/'rdzv'), results), nprocs=2, join=True)
        self.assertEqual([results[i] for i in range(6)], [1, 1, True, True, True, True])

    def test_final_mode_runs_depth_on_unlabelled_pose_rows_with_a_zero_term(self):
        model, batch, targets = final_fixture()
        targets = {**targets, 'aux_point_depth_mask': torch.zeros_like(targets['aux_point_depth_mask'])}
        calls = []
        original = model.auxiliary_heads.depth.forward
        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)
        with mock.patch.object(model.auxiliary_heads.depth, 'forward', spy):
            result = model(batch, targets)
        result['loss'].backward()
        self.assertEqual((len(calls), float(result['components']['depth'])), (1, 0.))
        self.assertTrue(torch.isfinite(result['loss']))


class T0Segments(unittest.TestCase):
    def test_pointing_and_vqa_segment_tags_and_logged_ce(self):
        from student_pilot.carrier_c1_data import STREAM_SEGMENTS, segment_tags
        vocab = {1: '<think>', 2: '</think>', 3: '{"point_2d": [', 4: '722', 5: ', ', 6: '453', 7: ']}', 8: 'null', 9: 'B', 10: 'trace'}
        decode = lambda i: vocab[i]
        visible = torch.tensor([[-100, 1, 2, 3, 4, 5, 6, 7]])
        names = [STREAM_SEGMENTS[t] if t >= 0 else None for t in segment_tags(visible, 'pointing', decode)[0].tolist()]
        self.assertEqual(names, [None, 'pointing_format', 'pointing_format', 'pointing_format', 'pointing_coord',
                                 'pointing_format', 'pointing_coord', 'pointing_format'])
        null = segment_tags(torch.tensor([[-100, 1, 2, 3, 8, 7]]), 'pointing', decode)[0].tolist()
        self.assertEqual({STREAM_SEGMENTS[t] for t in null if t >= 0}, {'pointing_null'})
        vqa = segment_tags(torch.tensor([[-100, 1, 10, 10, 2, 9]]), 'vqa', decode)[0].tolist()
        self.assertEqual([STREAM_SEGMENTS[t] if t >= 0 else None for t in vqa],
                         [None, 'vqa_trace', 'vqa_trace', 'vqa_trace', 'vqa_trace', 'vqa_answer'])
        model, batch, _ = final_fixture()
        labels = batch['labels']
        tags = torch.full_like(labels, -1)
        supervised = (labels[:, 1:] != -100).nonzero()[:, 1] + 1
        tags[0, supervised[0]] = STREAM_SEGMENTS.index('vqa_trace')
        tags[0, supervised[-1]] = STREAM_SEGMENTS.index('vqa_answer')
        result = model({**batch, 'aux_segments': tags}, stream='vqa')
        segments = result['metrics']['segments']
        self.assertEqual({k: v[1] for k, v in segments.items()}, {'vqa_trace': 1, 'vqa_answer': 1})
        self.assertAlmostEqual(sum(v[0] for v in segments.values()) / 2, float(result['components']['vqa']), places=4)


class T0FrameMarkers(unittest.TestCase):
    def test_markers_precede_each_group_and_carriers_still_follow_it(self):
        from student_pilot.carrier_c1_data import insert_frame_carriers
        class Tok:
            _c1_frame_markers = True
            def encode(self, text, **kwargs):
                if not text.startswith('Frame '):
                    return [5]  # the carrier token
                return [40, 41 + int(text.split()[1].rstrip(':'))]
            def convert_tokens_to_ids(self, token):
                return {'<|fim_middle|>': 5, '<|vision_start|>': 62}.get(token, 61)
        groups = 4
        ids = torch.tensor([[2] + [v for _ in range(groups) for v in (62, 61, 63)] + [10, 11, 12]])
        batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                     mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[groups, 2, 2]]))
        batch['labels'][0, -2:] = ids[0, -2:]
        out = insert_frame_carriers(batch, Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                    frame_layout='duplicate')
        seq = out['input_ids'][0].tolist()
        self.assertEqual(seq, [2] + [v for k in range(1, groups + 1) for v in (40, 41 + k, 62, 61, 5, 63)] + [10, 11, 12])
        positions = out['aux_camera_positions'][0]
        self.assertTrue(all(seq[p] == 5 and seq[p - 1] == 61 for p in positions[:groups].tolist()))
        self.assertEqual(out['labels'][0, -2:].tolist(), [11, 12])
        self.assertEqual(int((out['labels'] != -100).sum()), 2)
        self.assertEqual(out['mm_token_type_ids'][0].tolist().count(2), groups)


class T0Teacher(unittest.TestCase):
    def test_depth_graft_preserves_frozen_encoder_and_requires_grad(self):
        donor, _, _ = final_fixture()
        receiver, _, _ = final_fixture()
        with torch.no_grad():
            for parameter in donor.auxiliary_heads.depth.parameters():
                parameter.add_(.125)
        for parameter in receiver.auxiliary_heads.depth.model.visual.parameters():
            parameter.requires_grad_(False)
        flags = {k: p.requires_grad for k, p in receiver.named_parameters()}
        before = {k: v.clone() for k, v in receiver.auxiliary_heads.depth.state_dict().items()}
        root = Path(tempfile.mkdtemp(dir=os.environ.get('TMPDIR')))
        heads = {k: v.detach().clone() for k, v in donor.auxiliary_heads.state_dict().items()}
        torch.save(heads, root/'heads.pt')
        artifact = dict(schema='carrier-c1-artifact-v1', step=400, pose_backing='lm_final_norm',
                        placement=receiver.carrier_placement, frame_layout=receiver.frame_layout,
                        carrier_position_policy=receiver.carrier_position_policy, heads=run.file_pin(root/'heads.pt'))
        (root/'artifact.json').write_text(json.dumps(artifact))
        spec = dict(artifact=run.file_pin(root/'artifact.json'), lm='base', heads=['pose'])
        run.init_from_artifact(receiver, spec)
        for name, value in receiver.auxiliary_heads.depth.state_dict().items():
            torch.testing.assert_close(value, before[name], rtol=0, atol=0)
        spec['heads'] = ['pose', 'depth']
        report = run.init_from_artifact(receiver, spec)
        self.assertNotIn('depth', report['kept'])
        for name, value in receiver.auxiliary_heads.depth.state_dict().items():
            torch.testing.assert_close(value, donor.auxiliary_heads.depth.state_dict()[name], rtol=0, atol=0)
        self.assertEqual(flags, {k: p.requires_grad for k, p in receiver.named_parameters()})
        heads.pop(next(k for k in heads if k.startswith('depth.')))
        torch.save(heads, root/'heads.pt')
        artifact['heads'] = run.file_pin(root/'heads.pt')
        (root/'artifact.json').write_text(json.dumps(artifact))
        spec['artifact'] = run.file_pin(root/'artifact.json')
        with self.assertRaisesRegex(ValueError, 'init heads differ'):
            run.init_from_artifact(receiver, spec)

    def model(self, seed):
        torch.manual_seed(seed)
        model, batch, targets = final_fixture()
        # The C1-r head reads 2048-wide teacher-space states; rebuild the pose head at that width.
        from student_pilot.camera_head import CameraSupervision
        settings = dict(model.auxiliary_heads.pose.settings, embed_dim=2048, num_heads=4, trunk_depth=1)
        model.auxiliary_heads.pose = CameraSupervision(model.config.text_config.hidden_size, settings).float()
        c1r_align.attach(model, ALIGN, training=True)
        return model, batch, targets

    def test_uncovered_rows_add_no_teacher_term_and_keep_the_pose_loss(self):
        model, batch, targets = self.model(7)
        teacher = torch.randn(1, 32, 2048)
        covered = model(batch, {**targets, 'aux_g3t_cam': teacher, 'aux_g3t_valid': torch.ones(1, dtype=torch.bool)})
        uncovered = model(batch, {**targets, 'aux_g3t_cam': torch.zeros(1, 32, 2048),
                                  'aux_g3t_valid': torch.zeros(1, dtype=torch.bool)})
        self.assertGreater(float(covered['components']['align_cam']), 0.)
        self.assertEqual(float(uncovered['components']['align_cam']), 0.)
        self.assertEqual(float(uncovered['components']['align_clip']), 0.)
        torch.testing.assert_close(covered['components']['pose'], uncovered['components']['pose'])
        uncovered['loss'].backward()
        self.assertTrue(torch.isfinite(uncovered['loss']))

    def test_pre_teacher_init_keeps_the_planned_projector(self):
        from student_pilot.camera_head import CameraSupervision
        torch.manual_seed(21)
        donor, _, _ = final_fixture()
        settings = dict(donor.auxiliary_heads.pose.settings, embed_dim=2048, num_heads=4, trunk_depth=1)
        donor.auxiliary_heads.pose = CameraSupervision(donor.config.text_config.hidden_size, settings).float()
        receiver, _, _ = self.model(22)
        planned = {k: v.clone() for k, v in receiver.auxiliary_heads.pose.projector.state_dict().items()}
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            root = Path(root)
            torch.save({k: v.detach().clone() for k, v in donor.auxiliary_heads.state_dict().items()}, root/'heads.pt')
            artifact = dict(schema='carrier-c1-artifact-v1', step=800, pose_backing='lm_final_norm',
                            placement=receiver.carrier_placement, frame_layout=receiver.frame_layout,
                            carrier_position_policy=receiver.carrier_position_policy,
                            heads={'path': str(root/'heads.pt'), 'sha256': run.sha256(root/'heads.pt')})
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec = dict(artifact={'path': str(root/'artifact.json'), 'sha256': run.sha256(root/'artifact.json')}, lm='base', heads=['pose'])
            report = run.init_from_artifact(receiver, spec, part='heads')
        self.assertEqual(report['projector'], 'planned_init')
        for name, value in receiver.auxiliary_heads.pose.projector.state_dict().items():
            self.assertTrue(torch.equal(value, planned[name]), name)
        torch.testing.assert_close(receiver.auxiliary_heads.pose.head.state_dict()['token_norm.weight'],
                                   donor.auxiliary_heads.pose.head.state_dict()['token_norm.weight'])

    def test_pose_only_donor_grafts_and_final_branches_keep_planned_init(self):
        from student_pilot.camera_head import CameraSupervision
        torch.manual_seed(31)
        donor, _, _ = final_fixture()
        receiver, _, _ = final_fixture()
        base = dict(donor.auxiliary_heads.pose.settings, embed_dim=2048, num_heads=4, trunk_depth=1)
        hidden = donor.config.text_config.hidden_size
        donor.auxiliary_heads.pose = CameraSupervision(hidden, dict(base, weight_gravity=0., weight_scale=0.)).float()
        receiver.auxiliary_heads.pose = CameraSupervision(hidden, dict(base, weight_gravity=1., weight_scale=0.04)).float()
        planned = {k: v.clone() for k, v in receiver.auxiliary_heads.pose.state_dict().items()}
        fresh = sorted(k for k in planned if k.startswith(('head.gravity_branch.', 'head.scale_branch.', 'head.scale_token')))
        self.assertTrue(fresh)
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            root = Path(root)
            torch.save({k: v.detach().clone() for k, v in donor.auxiliary_heads.state_dict().items()}, root/'heads.pt')
            artifact = dict(schema='carrier-c1-artifact-v1', step=400, pose_backing='lm_final_norm', training_mode='pose_only',
                            placement=receiver.carrier_placement, frame_layout=receiver.frame_layout,
                            carrier_position_policy=receiver.carrier_position_policy,
                            heads={'path': str(root/'heads.pt'), 'sha256': run.sha256(root/'heads.pt')})
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec = dict(artifact={'path': str(root/'artifact.json'), 'sha256': run.sha256(root/'artifact.json')}, lm='base', heads=['pose'])
            report = run.init_from_artifact(receiver, spec, part='heads')
            self.assertEqual(report['planned_init'], ['pose.' + k for k in fresh])
            live = receiver.auxiliary_heads.pose.state_dict()
            for name, value in donor.auxiliary_heads.pose.state_dict().items():
                torch.testing.assert_close(live[name], value)
            for name in fresh:
                self.assertTrue(torch.equal(live[name], planned[name]), name)
            # A donor from any other mode must carry every receiver tensor.
            artifact['training_mode'] = 'final'
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec['artifact']['sha256'] = run.sha256(root/'artifact.json')
            with self.assertRaisesRegex(ValueError, 'init heads differ'):
                run.init_from_artifact(receiver, spec, part='heads')

    def test_head_graft_loads_pose_only_and_refuses_key_or_placement_drift(self):
        donor, _, _ = self.model(11)
        receiver, _, _ = self.model(12)
        depth_before = {k: v.clone() for k, v in receiver.auxiliary_heads.depth.state_dict().items()}
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            root = Path(root)
            heads = {k: v.detach().clone() for k, v in donor.auxiliary_heads.state_dict().items()}
            torch.save(heads, root/'heads.pt')
            artifact = dict(schema='carrier-c1-artifact-v1', step=600, pose_backing='lm_final_norm',
                            placement=receiver.carrier_placement, frame_layout=receiver.frame_layout,
                            carrier_position_policy=receiver.carrier_position_policy, pose_projector='teacher_space_mlp_v1',
                            heads={'path': str(root/'heads.pt'), 'sha256': run.sha256(root/'heads.pt')},
                            head_init=dict(prefix='global_camera_head.', copied=['trunk.0.ls1', 'token_norm.weight'], derived=['embed_pose.bias']))
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec = dict(artifact={'path': str(root/'artifact.json'), 'sha256': run.sha256(root/'artifact.json')}, lm='base', heads=['pose'])
            report = run.init_from_artifact(receiver, spec, part='heads')
            for name, value in donor.auxiliary_heads.pose.state_dict().items():
                torch.testing.assert_close(receiver.auxiliary_heads.pose.state_dict()[name], value)
            for name, value in receiver.auxiliary_heads.depth.state_dict().items():
                self.assertTrue(torch.equal(value, depth_before[name]), name)
            self.assertEqual((report['kept'], receiver.inherited_head_params),
                             (['depth'], ['embed_pose.bias', 'token_norm.weight', 'trunk.0.ls1']))
            del heads['pose.tokens']
            torch.save(heads, root/'heads.pt')
            artifact['heads']['sha256'] = run.sha256(root/'heads.pt')
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec['artifact']['sha256'] = run.sha256(root/'artifact.json')
            with self.assertRaises(ValueError):
                run.init_from_artifact(receiver, spec, part='heads')
            artifact['placement'] = 'other'
            (root/'artifact.json').write_text(json.dumps(artifact))
            spec['artifact']['sha256'] = run.sha256(root/'artifact.json')
            with self.assertRaises(ValueError):
                run.init_from_artifact(receiver, spec, part='heads')


if __name__ == '__main__':
    unittest.main()


class ExportLeg(unittest.TestCase):
    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

    """The 'x' leg restores a run's newest resume state under that run's binding and exports m<step>."""
    BOUND = dict(config_sha256='a'*64, preparation={'path': '/p/receipt.json', 'sha256': 'b'*64},
                 trainer_commit='c'*40, world_size=32)

    def test_export_binding_must_match_world_and_preparation(self):
        other = dict(self.BOUND, config_sha256='d'*64, trainer_commit='e'*40)
        self.assertIs(run.check_export_binding(other, self.BOUND), other)
        for bad in (dict(other, world_size=8), dict(other, preparation={'path': '/q', 'sha256': 'f'*64}),
                    {k: v for k, v in other.items() if k != 'trainer_commit'}, None):
            with self.assertRaisesRegex(ValueError, 'Export binding'):
                run.check_export_binding(bad, self.BOUND)

    def test_export_leg_needs_a_resume_pin_and_no_smoke(self):
        from unittest import mock
        with mock.patch.object(run, 'validate'):
            for kwargs in (dict(resume_pin=None), dict(resume_pin=None, smoke_steps=3)):
                with self.assertRaisesRegex(ValueError, 'export leg'):
                    run.train({}, export_binding=self.BOUND, **kwargs)

    def test_export_resume_state_reuses_an_existing_export(self):
        from unittest import mock
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            with mock.patch.object(run, 'existing_export', return_value=True) as existing, \
                    mock.patch.object(run, 'export') as export:
                directory, reused = run.export_resume_state(root, 'wrapped', 'model', {'c': 1}, 1234, 0, distributed=False)
            self.assertEqual((directory, reused), (Path(root)/'m1234', True))
            existing.assert_called_once_with(Path(root)/'m1234', {'c': 1}, 1234)
            export.assert_not_called()
            with mock.patch.object(run, 'existing_export', return_value=False), \
                    mock.patch.object(run, 'export') as export:
                directory, reused = run.export_resume_state(root, 'wrapped', 'model', {'c': 1}, 1234, 0, distributed=False)
            export.assert_called_once_with(Path(root)/'m1234', 'wrapped', 'model', {'c': 1}, 1234)
            self.assertFalse(reused)


class Cp1Prepare(unittest.TestCase):
    """CP1 prepare levers: a child division under the pose division, and the per-type route table."""

    def pin(self, root, name, value):
        path = Path(root)/name
        path.write_text(json.dumps(value))
        return {'path': str(path), 'sha256': run.sha256(path)}

    def test_child_division_admitted_only_with_superset_heldout_and_clean_train(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            parent = self.pin(root, 'a1.json', {'train_scenes': ['s1', 's2'], 'heldout_scenes': ['h1']})
            good = self.pin(root, 'a3.json', {'parent_division': parent, 'train_scenes': ['s1', 's2', 's3'],
                                              'heldout_scenes': ['h1', 'h2']})
            leaky = self.pin(root, 'leak.json', {'parent_division': parent, 'train_scenes': ['s1', 'h1'],
                                                 'heldout_scenes': ['h2']})
            orphan = self.pin(root, 'orphan.json', {'train_scenes': ['s1'], 'heldout_scenes': ['h1']})
            self.assertTrue(run.division_admits(parent, parent))
            self.assertTrue(run.division_admits(good, parent))
            self.assertFalse(run.division_admits(leaky, parent))
            self.assertFalse(run.division_admits(orphan, parent))

    def test_route_table_drops_only_direct_rows_of_routed_types(self):
        cfg = {'route_table': {'object_abs_distance': 'route', 'object_rel_direction_easy': 'direct'}}
        self.assertTrue(run.routed_type({'question_type': 'object_abs_distance'}, cfg))
        self.assertFalse(run.routed_type({'question_type': 'object_rel_direction_easy'}, cfg))
        self.assertFalse(run.routed_type({'question_type': 'object_counting'}, cfg))
        self.assertFalse(run.routed_type({'question_type': 'object_abs_distance'}, {}))

    def test_route_table_must_map_types_to_route_or_direct(self):
        self.assertEqual(run.validate_route_table({'object_abs_distance': 'route'}), {'object_abs_distance': 'route'})
        for bad in ({'object_abs_distance': 'maybe'}, ['object_abs_distance'], {1: 'route'}):
            with self.assertRaisesRegex(ValueError, 'route_table'):
                run.validate_route_table(bad)


class Cp1HeldRows(unittest.TestCase):
    """CP1 holds rows by qid list or source tag (e.g. V-SD) without rebuilding a receipt."""

    def test_held_row_matches_listed_qids_or_source_tags_per_stream(self):
        qids, sources = {'vqa': {'q1'}}, {'vqa': ['vsd'], 'pointing': ['pa3b']}
        self.assertTrue(run.held_row({'qid': 'q1'}, 'vqa', qids, sources))
        self.assertTrue(run.held_row({'qid': 'q2', 'source': '/x/vsd_k8/rows'}, 'vqa', qids, sources))
        self.assertTrue(run.held_row({'qid': 'q3', 'provenance': {'source': 'ap/pa3b_out'}}, 'pointing', qids, sources))
        self.assertFalse(run.held_row({'qid': 'q1'}, 'pointing', qids, sources))
        self.assertFalse(run.held_row({'qid': 'q4', 'source': '/x/weak_data/out/a'}, 'vqa', qids, sources))
        self.assertFalse(run.held_row({'qid': 'q4'}, 'vqa', {}, {}))


class PoseLrToggle(unittest.TestCase):
    """CP1 pose lever: pose_lr_scale gives the pose head and carriers their own group at a fraction of the head rate."""

    def test_pose_group_only_when_scaled(self):
        from student_pilot.carrier_c1 import parameter_groups, RECIPE
        model, _, _ = final_fixture()
        default = {g['name']: g for g in parameter_groups(model)}
        self.assertNotIn('pose', default)
        scaled = {g['name']: g for g in parameter_groups(model, pose_lr_scale=0.3)}
        self.assertAlmostEqual(scaled['pose']['lr'], 0.3 * RECIPE['learning_rate'])
        self.assertEqual(scaled['pose']['initial_lr'], scaled['pose']['lr'])
        pose_ids = {id(p) for p in model.auxiliary_heads.pose.parameters() if p.requires_grad}
        self.assertEqual({id(p) for p in scaled['pose']['params']}, pose_ids)
        moved = sum(len(g['params']) for g in default.values()) - sum(len(g['params']) for g in scaled.values() if g['name'] != 'pose')
        self.assertEqual(moved, len(pose_ids))
        self.assertEqual(scaled['heads']['lr'], RECIPE['learning_rate'])


class PointingDecisionWeight(unittest.TestCase):
    """CP1 pointing_weights: the null-or-point decision token weighs `decision`, the row mean stays `row_mean`."""

    def run_row(self, pieces):
        from student_pilot.carrier_c1_data import pointing_token_weights
        vocab = {i: p for i, p in enumerate(pieces)}
        labels = torch.tensor([[-100, -100] + list(range(len(pieces)))])
        return pointing_token_weights(labels, lambda i: vocab[i], decision=5.0, row_mean=2.0)[0]

    def test_null_and_point_rows(self):
        for pieces, decision in ((['{"', 'point_2d', '":', ' null', '}'], 3), (['{"', 'point_2d', '":', ' [', '1', '2', ',', '3', ']}'], 3)):
            w = self.run_row(pieces)
            self.assertEqual(float(w[:2].sum()), 0.)
            sup = w[2:]
            self.assertAlmostEqual(float(sup.mean()), 2.0, places=5)
            others = [float(x) for j, x in enumerate(sup) if j != decision]
            self.assertAlmostEqual(float(sup[decision]) / others[0], 5.0, places=5)
            self.assertTrue(all(abs(o - others[0]) < 1e-6 for o in others))


class FirstBatchCheck(unittest.TestCase):
    """CPU first-batch check: every listed rank's planned rows run fetch and the full no-grad forward."""

    def test_records_finite_rows_substitutions_and_failures(self):
        model, batch, targets = final_fixture()
        model.eval()

        class FakeRows:
            def __init__(self, bad):
                self.bad = bad

            def count(self, stream):
                return 2

            def get(self, stream, index):
                if index in self.bad:
                    raise ValueError('fixture row fails to encode')
                return batch, targets, {'qid': f'q{index}'}

        records = run.check_plan_rows(model, FakeRows(bad={1}), [[('pose', [0, 1])]], [0, 1])
        self.assertEqual([r['rank'] for r in records], [0, 1])
        self.assertTrue(all(r['finite'] for r in records))
        self.assertEqual(records[1]['substituted_from'], 1)
        self.assertEqual(records[1]['qid'], 'q0')
        failed = run.check_plan_rows(model, FakeRows(bad={0, 1}), [[('pose', [0, 1])]], [0])
        self.assertFalse(failed[0]['finite'])
        self.assertIn('every candidate row failed', failed[0]['error'])


class ValidationHeldout(unittest.TestCase):
    """A child-division slice (A3 held-out scenes) validates an A1-division run."""

    def test_child_heldout_scenes_count_for_the_parent_run(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            def pin(name, value):
                path = Path(root)/name; path.write_text(json.dumps(value))
                return {'path': str(path), 'sha256': run.sha256(path)}
            parent = pin('a1.json', {'train_scenes': ['s1'], 'heldout_scenes': ['h1']})
            child = pin('a3.json', {'parent_division': parent, 'train_scenes': ['s1', 's2'], 'heldout_scenes': ['h1', 'v1', 'v2']})
            other = pin('x.json', {'train_scenes': ['s9'], 'heldout_scenes': ['v1']})
            self.assertEqual(run.validation_heldout(parent), {'h1'})
            self.assertEqual(run.validation_heldout(parent, dict(child, field='heldout_scenes')), {'h1', 'v1', 'v2'})
            self.assertEqual(run.validation_heldout(parent, other), {'h1'})
            self.assertEqual(run.validation_heldout(parent, None), {'h1'})


class PoseExclusions(unittest.TestCase):
    """cfg pose_exclusions (posedata2's x4 list) drops pose rows only; other streams keep the shared list."""

    def test_pose_mix_receives_the_union_and_other_streams_do_not(self):
        lists = {'shared': {'d1/a'}, 'pose': {'d3/b'}, 'report': set()}
        captured = {}

        class Stop(Exception):
            pass

        def fake_prepare(spec, output, benchmark, reported, excluded, check=None):
            captured['benchmark'] = set(benchmark)
            raise Stop()
        cfg = {'training_mode': 'final', 'exclusions': 'shared', 'pose_exclusions': 'pose', 'report_exclusions': 'report',
               'streams': {'pose': {'path': '/p', 'sha256': 'a'*64}}, 'preparation_output': '/o'}
        from student_pilot import c1_pose_mix
        with mock.patch.object(run, 'validate'), mock.patch.object(run, 'authenticate', return_value='c'*40), \
                mock.patch.object(run, 'load', return_value={'schema': 'c1-pose-mix-v1'}), \
                mock.patch.object(run, 'pinned', side_effect=lambda pin: pin), \
                mock.patch.object(run.routing, 'load_exclusions', side_effect=lambda pin: lists.get(pin, set())), \
                mock.patch.object(c1_pose_mix, 'prepare', side_effect=fake_prepare):
            with self.assertRaises(Stop):
                run.prepare(cfg)
        self.assertEqual(captured['benchmark'], {'d1/a', 'd3/b'})


class CheckProgressFile(unittest.TestCase):
    def test_rewrite_replaces_the_progress_file(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            path = Path(root)/'job.c0.json'
            run.rewrite(path, {'records': [1]})
            run.rewrite(path, {'records': [1, 2]})
            self.assertEqual(json.loads(path.read_text()), {'records': [1, 2]})
            self.assertFalse((Path(root)/'job.c0.json.part').exists())


class LmLrToggle(unittest.TestCase):
    def test_lm_group_rate_scales_only_the_lm(self):
        from student_pilot.carrier_c1 import parameter_groups, RECIPE
        model, _, _ = final_fixture()
        default = {g['name']: g for g in parameter_groups(model)}
        scaled = {g['name']: g for g in parameter_groups(model, lm_lr_scale=0.6)}
        self.assertAlmostEqual(scaled['llm']['lr'], 0.6 * RECIPE['lm_learning_rate'])
        self.assertEqual(scaled['llm']['initial_lr'], scaled['llm']['lr'])
        self.assertEqual(scaled['heads']['lr'], default['heads']['lr'])
        self.assertEqual(len(scaled['llm']['params']), len(default['llm']['params']))
