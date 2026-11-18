import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'tree_s1_admissionfix_168872'))
import student_pilot
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))
from student_pilot import carrier_c1_run as run


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


base = module('test_warm_start', ROOT / 'test_warm_start.py')
base.ROOT = ROOT
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))
review = module('reviewer_tests_original', ROOT / 'reviewer_tests_original.py')
from student_pilot import s1_warm_start as warm
import torch


class ReviewFixes(review.Boundary):
    def bound_cfg(self, step):
        cfg = super().bound_cfg(step)
        self.receipt['init_artifact'] = cfg['init_artifact']
        return cfg

    def test_finding_extra_head_keys_in_export_are_ignored(self):
        state = dict(self.model.auxiliary_heads.state_dict())
        state['unused_future_head.weight'] = torch.zeros(3)
        path = self.root / 'heads_extra_current.pt'
        torch.save(state, path)
        artifact = run.load(self.cfg['init_artifact']['artifact']['path'])
        artifact['heads'] = base.file_pin(path)
        base.write(self.root / 'artifact_extra_current.json', artifact)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = base.file_pin(self.root / 'artifact_extra_current.json')
        receipt = {**self.receipt, 'init_artifact': cfg['init_artifact']}
        receipt['warm_start'] = warm.bind(cfg, receipt)
        with self.assertRaisesRegex(ValueError, 'export key'):
            base.load_fixture(self.root, receipt, base.Tiny())

    def test_finding_non_stream_receipt_fields_are_not_bound(self):
        with self.assertRaisesRegex(ValueError, 'stream pins'):
            super().test_finding_non_stream_receipt_fields_are_not_bound()

    def test_preparation_model_camera_depth_and_division_are_also_bound(self):
        for key, value in (('camera', {'weight_focal': 99}), ('depth', {'num_points_per_frame': 1}),
                           ('model', {'path': '/other', 'sha256': 'a' * 64}),
                           ('division', {'path': '/other', 'sha256': 'b' * 64})):
            receipt = {**self.receipt, key: value}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(self.cfg, receipt)

    def test_dryrun_encodes_all_rank_post_export_rows_and_updates_at_s_plus_one(self):
        lineage = warm.bind(self.cfg, self.receipt)
        receipt = {**self.receipt, 'warm_start': lineage}
        self.model.model = torch.nn.Module()
        self.model.model.visual = torch.nn.Linear(2, 2).requires_grad_(False)
        self.model.probe = lambda *a: {}
        captured, encoded = [], []
        expected = list(base.data.mixed_indices(
            {name: value['count'] for name, value in receipt['streams'].items()}, 201,
            training_mode='final', mix=self.cfg['recipe']['mix'], world=4))[200]

        def get(stream, index):
            encoded.append((stream, index))
            return {'input_ids': torch.tensor([[1, 2]])}, None, {}

        def update(model, optimizer, rows, plan, rank, device, step):
            captured.append((step, plan))
            with torch.no_grad():
                model.embed.weight.add_(.01)
            return {'step': step, 'gradient_norms': {'llm': 1.}}, (None, None)

        with patch.object(run, 'prepared', return_value=(receipt, {})), \
             patch.object(run, 'processor_for_receipt', return_value=None), \
             patch.object(run, 'load_model', return_value=self.model), \
             patch.object(run, 'Rows', return_value=SimpleNamespace(get=get, close=lambda: None)), \
             patch.object(run, 'optimize_step', side_effect=update):
            report = run.dryrun(self.cfg, self.root / 'dryrun.json')
        self.assertEqual(captured, [(201, expected)])
        self.assertEqual(encoded, [(stream, indices[rank]) for rank in range(4) for stream, indices in expected])
        self.assertEqual(report['step']['step'], 201)

    def test_nonzero_scheduled_sampling_is_refused(self):
        run.validate(self.cfg)
        for key in ('max_own_probability', 'exposure_probability'):
            cfg = copy.deepcopy(self.cfg)
            cfg['scheduled_sampling'][key] = .1
            if key == 'exposure_probability':
                cfg['scheduled_sampling']['exposure_from_step'] = 100
                cfg['scheduled_sampling']['max_own_probability'] = .2
            cfg['recipe'] = run.recipe_for(cfg)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'own-value'):
                run.validate(cfg)

    def test_legitimate_warm_loader_and_unmodified_default_branch(self):
        lineage = warm.bind(self.cfg, self.receipt)
        loaded = base.load_fixture(self.root, {**self.receipt, 'warm_start': lineage}, base.Tiny())
        self.assertEqual(loaded.init_report['unselected_export_keys'], [])
        torch.testing.assert_close(loaded.embed.weight[5], self.model.embed.weight[5], rtol=0, atol=0)
        receipt = {key: value for key, value in self.receipt.items() if key != 'warm_start'}
        ordinary = base.load_fixture(self.root, receipt, base.Tiny())
        self.assertNotIn('unselected_export_keys', ordinary.init_report)
        expected = self.model.embed.weight[[1, 2]].to(torch.bfloat16).float().mean(0)
        torch.testing.assert_close(ordinary.embed.weight[5], expected, rtol=0, atol=0)

    def test_inconsistent_configuration_and_receipt_stream_pins_refuse(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['streams'] = {name: {'path': pin['path'] + '.new-run', 'sha256': 'd' * 64}
                          for name, pin in cfg['streams'].items()}
        with self.assertRaisesRegex(ValueError, 'stream pins'):
            warm.bind(cfg, self.receipt)


if __name__ == '__main__':
    unittest.main()
