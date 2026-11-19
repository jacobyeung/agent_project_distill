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
