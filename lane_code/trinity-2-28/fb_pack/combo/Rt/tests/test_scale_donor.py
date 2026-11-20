"""Native tiny C1 donor regressions; all retained files stay in the test output."""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

from student_pilot import scale_donor as D
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.tower_read import apply_tower
from tests.test_carrier_c1_final import final_fixture
from tests.test_tower_read import tower_state, tower_batch


def fixture():
    model, batch, targets = final_fixture()
    model.auxiliary_heads.depth.model.visual.requires_grad_(False).eval()
    # A trained FiLM must respond to FoV; zero initialization hides live-FoV leaks.
    film = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.fov_film[-1]
    with torch.no_grad():
        film.weight.copy_(torch.randn(film.weight.shape, generator=torch.Generator().manual_seed(5)) * .5)
    batch.update(tower_batch())
    return model, batch, targets


def source(model, root):
    root.mkdir(parents=True, exist_ok=True)
    torch.save(model.auxiliary_heads.state_dict(), root/'heads.pt')
    artifact = dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=400,
                    fixture=True, heads=file_pin(root/'heads.pt'))
    (root/'artifact.json').write_text(json.dumps(artifact, sort_keys=True)+'\n')
    return file_pin(root/'artifact.json')


def settings(model, pin, variant):
    depth = model.auxiliary_heads.depth
    return dict(schema=D.SCHEMA, checkpoint=pin, fov_source=variant,
                visual_sha256=D.visual_identity(depth.model.visual),
                feature_contract_sha256=digest(D.feature_contract(depth)))


def train_two(model, batch, targets):
    class Rows:
        def count(self, stream):return 1
        def get(self, stream, index):
            return {k:v for k,v in batch.items() if isinstance(v, torch.Tensor)}, targets, {}
    model.train()
    optimizer = torch.optim.AdamW(parameter_groups(model), weight_decay=.01)
    donor = model.auxiliary_heads.scale_donor
    frozen = {id(p) for p in donor.parameters()} | {id(p) for p in donor.visual.parameters()}
    assert not frozen.intersection(id(p) for g in optimizer.param_groups for p in g['params'])
    results = []
    for step in (1, 2):
        # Native optimizer logic and loss; only distributed transport is absent.
        results.append(run.optimize_step(model, optimizer, Rows(), [('pose', [0])], 0,
                                         torch.device('cpu'), step, distributed=False)[0])
    return optimizer, results


def native_export(model, root):
    with ExitStack() as stack:
        stack.enter_context(mock.patch('student_pilot.fsdp_training.publication_state',
                                       side_effect=lambda wrapped: wrapped.state_dict()))
        for name, value in (('get_rank', 0), ('get_world_size', 1)):
            stack.enter_context(mock.patch.object(run.dist, name, return_value=value))
        stack.enter_context(mock.patch.object(run.dist, 'barrier'))
        run.export(root, model, model, dict(base_identity='fixture', trace_program_version='3.13'), 2)
    return file_pin(root/'artifact.json')


class ScaleDonorTests(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix='scale_donor_', dir=os.environ['LANE_TEST_OUTPUT']))

    def test_requires_explicit_source_and_fov_and_frozen_visual(self):
        model, batch, targets = fixture(); root = self.root()
        cfg = settings(model, source(model, root), 'V1')
        for key in cfg:
            bad = dict(cfg); bad.pop(key)
            with self.assertRaises(ValueError):D.validate(bad)
        with self.assertRaises(ValueError):D.validate(dict(cfg, fov_source='pose_head'))
        model.auxiliary_heads.depth.model.visual.requires_grad_(True)
        with self.assertRaisesRegex(ValueError, 'already frozen'):D.attach(model, cfg)

    def test_both_variants_are_frozen_and_use_pinned_checkpoint(self):
        for variant in ('V1', 'V2'):
            with self.subTest(variant=variant):
                model, batch, targets = fixture(); root = self.root()
                pin = source(model, root)
                cfg = settings(model, pin, variant)
                # Prove the donor loads its source, not the currently live head.
                with torch.no_grad():
                    next(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.parameters()).add_(.1)
                donor = D.attach(model, cfg)
                self.assertIs(donor.visual, model.auxiliary_heads.depth.model.visual)
                self.assertFalse(any('visual' in n for n in donor.state_dict()))
                before = D.tensor_pins(donor.state_dict()); grid = donor(batch, tower_state()).clone()
                live = D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
                optimizer, steps = train_two(model, batch, targets)
                self.assertEqual(before, D.tensor_pins(donor.state_dict()))
                self.assertNotEqual(live, D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict()))
                self.assertTrue(torch.equal(grid, donor(batch, tower_state())))
                self.assertFalse(donor.training); self.assertFalse(donor.visual.training)
                self.assertFalse(any(p.grad is not None for p in donor.parameters()))
                self.assertEqual(donor.metadata()['tensors'], before)
                # A trainable live private FoV/query cannot leak into V1.
                with torch.no_grad():
                    model.auxiliary_heads.depth.fov.weight.add_(1)
                    model.auxiliary_heads.depth.auxiliary_heads.frame_queries.add_(1)
                self.assertTrue(torch.equal(grid, donor(batch, tower_state())))
                donor.requires_grad_(True)
                with self.assertRaisesRegex(ValueError, 'made trainable'):parameter_groups(model)

    def test_export_pins_reject_changed_donor_and_shared_visual(self):
        model, batch, targets = fixture(); root = self.root()
        cfg = settings(model, source(model, root/'source'), 'V1')
        donor = D.attach(model, cfg)
        pin = native_export(model, root/'export')
        fresh, _, _ = fixture(); D.attach(fresh, cfg)
        run.load_artifact(fresh, pin)
        self.assertEqual(donor.initial_pins, D.tensor_pins(fresh.auxiliary_heads.scale_donor.state_dict()))
        artifact = json.loads((root/'export/artifact.json').read_text())
        state = torch.load(root/'export/heads.pt', weights_only=True)
        for prefix in ('scale_donor.point_depth.', 'depth.model.visual.'):
            changed = copy.deepcopy(state)
            key = next(k for k in changed if k.startswith(prefix))
            changed[key].reshape(-1)[0] += 1
            with self.assertRaisesRegex(ValueError, 'changed since initialization'):
                D.verify_export(model, changed, artifact['scale_donor'])
        fresh, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'pins differ|explicit reader'):
            D.verify_export(fresh, state, artifact['scale_donor'])

    def test_v2_requires_tower_and_matches_exact_native_fov(self):
        model, batch, targets = fixture(); root = self.root()
        donor = D.attach(model, settings(model, source(model, root), 'V2'))
        with self.assertRaisesRegex(ValueError, 'requires the frozen'):donor(batch)
        seen = []
        encode = donor.point_depth.encode
        def spy(grid, vits, fov):
            seen.append(fov.clone()); return encode(grid, vits, fov)
        with mock.patch.object(donor.point_depth, 'encode', side_effect=spy):donor(batch, tower_state())
        self.assertTrue(torch.equal(seen[0], torch.tensor(tower_state().raw_pose9[::2, 7:9], dtype=torch.float32)))

    def test_tower_scales_once_and_own_depth_stays_live(self):
        from student_pilot.carrier_c1_decode import HeadState
        model, batch, targets = fixture(); root = self.root()
        donor = D.attach(model, settings(model, source(model, root), 'V1'))
        model.eval()
        with torch.no_grad():
            hidden = model.hidden(batch)
            own = HeadState(model, batch, hidden)
            tower = HeadState(model, batch, hidden, pose_source='tower', tower_state=tower_state())
        with torch.no_grad():
            own_depth = own.depth(1, [[200,300]])
            # The own readout still uses the original live head.
            self.assertIs(own.depth_head, model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth)
            self.assertNotEqual(float(own_depth[0]), float(tower.depth(1, [[200,300]])[0]))
        expected, scale = tower_state().scaled_pose9(donor(batch).double().numpy())
        np.testing.assert_array_equal(tower.pose9, expected)
        self.assertEqual(tower.tower_scale, scale)

        np.testing.assert_array_equal(tower.depth_map[:, 0].numpy(), tower_state().depth_grid * scale)
        with torch.no_grad():
            lifted = tower.read_depth(1, [500,500], tower.pose9[0,7:9])
        self.assertEqual(lifted['depth_p30'], scale)
        self.assertEqual(float(lifted['camera_point'][2]), round(scale, 8))


    def test_handover_preserves_native_optimizer_and_rejects_binding_drift(self):
        from student_pilot.r1_handover import compare_configs, trainable_group_table
        model, _, _ = fixture(); root = self.root()
        cfg = settings(model, source(model, root), 'V1')
        before = trainable_group_table({}, model)
        D.attach(model, cfg)
        self.assertEqual(before, trainable_group_table({}, model))
        compare_configs({}, {'scale_donor': cfg})
        compare_configs({'scale_donor': cfg}, {'scale_donor': cfg})
        with self.assertRaises(ValueError):compare_configs({'scale_donor': cfg}, {})
        with self.assertRaises(ValueError):
            compare_configs({'scale_donor': cfg}, {'scale_donor': dict(cfg, fov_source='V2')})

    def test_source_and_feature_pins_refuse_corruption(self):
        model, _, _ = fixture(); root = self.root()
        cfg = settings(model, source(model, root), 'V1')
        for field in ('visual_sha256', 'feature_contract_sha256'):
            with self.assertRaises(ValueError):D.attach(model, dict(cfg, **{field:'0'*64}))
        with self.assertRaises(ValueError):
            D.attach(model, dict(cfg, checkpoint={**cfg['checkpoint'], 'sha256':'0'*64}))

    def test_live_fov_negative_control_fails_invariance(self):
        model, batch, _ = fixture(); root = self.root()
        donor = D.attach(model, settings(model, source(model, root), 'V1'))
        depth = model.auxiliary_heads.depth
        def require_invariance():
            before = donor(batch, tower_state()).clone()
            with torch.no_grad():depth.fov.bias.sub_(.5)
            self.assertTrue(torch.equal(before, donor(batch, tower_state())), 'live FoV leak')
        require_invariance()
        encode = donor.point_depth.encode
        probe = torch.zeros(1, 32, depth.fov.in_features)
        def leaky(grid, vits, fov):
            live = (1e-4 + (np.pi-2e-4)*depth.fov(probe).sigmoid())[0].detach()
            return encode(grid, vits, live)
        with mock.patch.object(donor.point_depth, 'encode', side_effect=leaky):
            with self.assertRaisesRegex(AssertionError, 'live FoV leak'):require_invariance()

    def test_verified_rank_and_follower_use_identical_donor_with_relocated_heads(self):
        from student_pilot import p3_provenance as P, r1_persisted
        model, _, _ = fixture(); root = self.root()
        cfg = settings(model, source(model, root/'source'), 'V1')
        heads = root/'source/heads.pt'
        replica = root/'replica.pt'; replica.write_bytes(heads.read_bytes())
        h = P.sha256(heads)
        with r1_persisted.scope({h: str(replica)}):
            with mock.patch.object(P, 'sha256', wraps=P.sha256) as hashes:
                first = D.attach(model, cfg)
                self.assertEqual(sum(Path(c.args[0]) == replica for c in hashes.call_args_list), 1)
            fresh, _, _ = fixture()
            with mock.patch.object(P, 'sha256', wraps=P.sha256) as hashes, \
                 mock.patch.object(D.torch, 'load', wraps=torch.load) as loads:
                follower = D.attach(fresh, cfg, verify_assets=False)
                self.assertFalse(any(Path(c.args[0]) == replica for c in hashes.call_args_list))
                self.assertTrue(loads.call_args.kwargs['mmap'])
            self.assertEqual(first.initial_pins, follower.initial_pins)
        # The default path still authenticates bytes even if tensors deserialize.
        with heads.open('ab') as f:f.write(b'tamper')
        fresh, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'changed pinned'):D.attach(fresh, cfg)
        # Followers still reject feature-contract and visual corruption.
        with self.assertRaisesRegex(ValueError, 'architecture pin'):
            D.attach(fresh, dict(cfg, feature_contract_sha256='0'*64), verify_assets=False)

    def test_mdg_runtime_strict_load_requires_reader_metadata_steps(self):
        import inspect
        from types import SimpleNamespace
        from transformers import Qwen3_5ForConditionalGeneration
        from student_pilot import mdg_runtime as runtime, full_ft
        from student_pilot.carrier_c1 import CarrierC1
        model, batch, targets = fixture(); root = self.root()
        cfg = settings(model, source(model, root/'source'), 'V1')
        D.attach(model, cfg)
        train_two(model, batch, targets)
        pin = native_export(model, root/'export')
        artifact = json.loads(Path(pin['path']).read_text())
        raw = torch.load(root/'export/heads.pt', weights_only=True)
        receipt = dict(camera=model.auxiliary_heads.pose.settings,
                       depth=model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.settings,
                       carrier_placement=model.carrier_placement, training_mode='final',
                       depth_enabled=True, recipe=model.recipe, depth_fov_source='pose_head',
                       depth_init={'path': '/unused-depth-init', 'sha256': '0'*64})
        processor = SimpleNamespace(tokenizer=None, _routing_tokens={})
        # Exercise a proposed reader adapter at the exact strict-load site. The
        # shipped runtime stays guarded; its real CarrierC1 constructor and
        # full_ft.load_export run unchanged. Only bundle/processor boundaries
        # and the tiny, deliberately different empty base are substituted.
        original = '    model.auxiliary_heads.load_state_dict(heads, strict=True)'
        runtime_source = inspect.getsource(runtime.load_runtime)
        self.assertEqual(runtime_source.count(original), 1)
        reader_steps = '''
visual = model.auxiliary_heads.depth.model.visual
prefix = "depth.model.visual."
visual.load_state_dict({key[len(prefix):]: value for key, value in heads.items()
                        if key.startswith(prefix)}, strict=True)
visual.requires_grad_(False)
scale_donor.attach(model, binding)
metadata = heads.pop("_scale_donor", None)
if metadata != artifact.get("scale_donor"):
    raise ValueError("Scale donor artifact/head metadata differs")
scale_donor.verify_export(model, heads, metadata)
model.auxiliary_heads.load_state_dict(heads, strict=True)
'''
        def execute(mode='documented'):
            checked = []
            def empty_base(_):
                torch.manual_seed(1234)
                return Qwen3_5ForConditionalGeneration(copy.deepcopy(model.config)).float()
            def reader_load(fresh, heads, header):
                self.assertIs(type(fresh), CarrierC1)
                self.assertFalse(hasattr(fresh.auxiliary_heads, 'scale_donor'))
                visual = fresh.auxiliary_heads.depth.model.visual
                self.assertTrue(any(p.requires_grad for p in visual.parameters()))
                self.assertNotEqual(D.visual_identity(visual), cfg['visual_sha256'])
                steps = reader_steps
                if mode == 'old_order':
                    D.attach(fresh, cfg)
                elif mode == 'freeze_only':
                    visual.requires_grad_(False)
                    D.attach(fresh, cfg)
                elif mode == 'load_only':
                    steps = steps.replace('visual.requires_grad_(False)\n', '')
                elif mode == 'no_metadata_pop':
                    steps = steps.replace('metadata = heads.pop("_scale_donor", None)',
                                          'metadata = heads.get("_scale_donor")')
                elif mode in ('tampered_visual', 'missing_visual'):
                    key = next(k for k in heads if k.startswith('depth.model.visual.'))
                    if mode == 'tampered_visual':
                        heads[key].reshape(-1)[0] += 1
                    else:
                        heads.pop(key)
                elif mode == 'bad_metadata':
                    heads['_scale_donor'] = {}
                elif mode == 'tampered_donor':
                    key = next(k for k in heads if k.startswith('scale_donor.point_depth.'))
                    heads[key].reshape(-1)[0] += 1
                exec(compile(steps, '<documented-reader-sequence>', 'exec'),
                     dict(model=fresh, heads=heads, artifact=header, binding=cfg, scale_donor=D))
                self.assertFalse(any(p.requires_grad for p in visual.parameters()))
                self.assertEqual(D.visual_identity(visual), cfg['visual_sha256'])
                checked.append(True)
            namespace = dict(runtime.__dict__, _reader_load=reader_load)
            exec(compile(runtime_source.replace(original, '    _reader_load(model, heads, artifact)'),
                         '<runtime-with-reader-adapter>', 'exec'), namespace)
            with ExitStack() as stack:
                stack.enter_context(mock.patch('student_pilot.r2_policy.unsupported_entry'))
                stack.enter_context(mock.patch.object(runtime, '_bundle', return_value=(root,root/'export',{},receipt,{},artifact,'fixture')))
                stack.enter_context(mock.patch.object(runtime, '_empty_base', side_effect=empty_base))
                # The copied function globals must use these boundary substitutes.
                namespace.update(_bundle=runtime._bundle, _empty_base=runtime._empty_base)
                stack.enter_context(mock.patch.object(run, 'processor_for_receipt', return_value=processor))
                stack.enter_context(mock.patch('student_pilot.camera_targets.carrier_id', return_value=5))
                stack.enter_context(mock.patch.object(run.routing, 'init_routing_embeddings'))
                load_base = stack.enter_context(mock.patch.object(full_ft, 'load_export', wraps=full_ft.load_export))
                loaded, _, _ = namespace['load_runtime']({'bundle': 'fixture'}, torch.device('cpu'))
                self.assertEqual(load_base.call_count, 1)
            self.assertEqual(checked, [True])
            expected = {k:v for k,v in raw.items() if isinstance(v, torch.Tensor)}
            self.assertEqual(D.tensor_pins(loaded.auxiliary_heads.state_dict()), D.tensor_pins(expected))
            self.assertEqual(loaded.auxiliary_heads.scale_donor.initial_pins,
                             model.auxiliary_heads.scale_donor.initial_pins)
            self.assertIn('depth_init', loaded.mdg_runtime_report['skipped'])
        execute()
        for mode, error, message in (
                ('old_order', ValueError, 'already frozen'),
                ('freeze_only', ValueError, 'shared visual pin differs'),
                ('load_only', ValueError, 'already frozen'),
                ('tampered_visual', ValueError, 'shared visual pin differs'),
                ('missing_visual', RuntimeError, 'Missing key'),
                ('no_metadata_pop', RuntimeError, '_scale_donor'),
                ('bad_metadata', ValueError, 'metadata differs'),
                ('tampered_donor', ValueError, 'changed since initialization')):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(error, message):execute(mode)

    def test_pre_donor_resume_binding_stays_fail_closed(self):
        from tests.test_carrier_c1_run import RunnerTests
        model, _, _ = fixture(); root = self.root()
        cfg = settings(model, source(model, root/'source'), 'V1')
        old = dict(config_sha256=run.identity({}), preparation={'fixture': True},
                   trainer_commit='fixture', world_size=1)
        new = dict(old, config_sha256=run.identity({'scale_donor': cfg}))
        self.assertNotEqual(old, new)
        model.trace_program_version = '3.13'
        optimizer = torch.optim.AdamW(parameter_groups(model))
        with RunnerTests().local_collectives():
            pin = run.checkpoint(root/'checkpoint', model, optimizer, old, 1)
            D.attach(model, cfg)
            with self.assertRaisesRegex(ValueError, 'C1 resume binding differs'):
                run.restore(pin, model, optimizer, new)
            self.assertEqual(run.restore(pin, model, optimizer, old), 1)
        # The donor itself adds no trainable shard or optimizer-layout change.
        self.assertEqual(model.auxiliary_heads.scale_donor.initial_pins,
                         D.tensor_pins(model.auxiliary_heads.scale_donor.state_dict()))
