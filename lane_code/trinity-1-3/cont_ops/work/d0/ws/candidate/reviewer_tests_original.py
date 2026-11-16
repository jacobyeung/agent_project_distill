import copy
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import test_warm_start as base  # noqa: E402  (sets up the sealed tree plus private overlay)
import torch  # noqa: E402

run, data = base.run, base.data
from student_pilot import s1_warm_start as warm  # noqa: E402
from student_pilot.p3_provenance import file_pin, write  # noqa: E402


def sealed_lr(step, recipe, lr):
    # Independent restatement of decoupled_v.learning_rate (sealed b01ce449).
    w = math.ceil(recipe['steps'] * recipe['warmup_ratio'])
    if step <= w:
        return lr * step / w
    return lr * .5 * (1 + math.cos(math.pi * (step - w) / (recipe['steps'] - w)))


class Boundary(unittest.TestCase):
    def setUp(self):
        self.root, self.cfg, self.donor, self.receipt, self.model = base.fixture()

    def bound_cfg(self, step):
        art = run.load(self.cfg['init_artifact']['artifact']['path'])
        art['step'] = step
        path = self.root / f'artifact_s{step}.json'
        write(path, art)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = file_pin(path)
        return cfg

    def first_loop_step(self, cfg, start):
        captured = []
        stop = [False]

        def update(model, optimizer, rows, plan, rank, device, step, distributed, gates):
            captured.append((step, plan))
            stop[0] = True
            return {'wall_seconds': .001, 'head_metrics': {}}, None

        counts = {n: v['count'] for n, v in self.receipt['streams'].items()}
        out = self.root / f'loop_{start}'
        out.mkdir()
        with patch.object(run, 'optimize_step', side_effect=update), \
             patch.object(run, 'checkpoint'), patch.object(run, 'export'), \
             patch.object(run, 'existing_export', return_value=False), \
             patch.object(run.rehearsal, 'enabled', return_value=False):
            run.run_steps(self.model, self.model, None, None, counts, out, cfg, {},
                          torch.device('cpu'), start_step=start, stop=stop, distributed=False)
        return captured[0], counts

    def test_lr_and_rows_at_boundary_for_two_exports(self):
        for s in (200, 650):
            with self.subTest(s=s):
                cfg = self.bound_cfg(s)
                lineage = warm.bind(cfg, self.receipt)
                start = warm.start_step({'warm_start': lineage})
                self.assertEqual(start, s)
                (step, plan), counts = self.first_loop_step(cfg, start)
                self.assertEqual(step, s + 1)
                recipe = run.recipe_for(cfg)
                self.assertEqual(recipe, run.recipe_for(self.donor))
                groups = run.parameter_groups(self.model)
                for g in groups:
                    got = run.learning_rate(step, {**recipe, 'learning_rate': g['initial_lr']})
                    self.assertEqual(got, sealed_lr(s + 1, recipe, g['initial_lr']))
                    self.assertNotEqual(got, sealed_lr(1, recipe, g['initial_lr']))
                # Original uninterrupted plan, exactly as the donor's run_steps(start_step=0) enumerates it.
                original = list(data.mixed_indices(counts, recipe['steps'], training_mode='final',
                                                   mix=recipe['mix'], world=recipe['world_size']))
                self.assertEqual(plan, original[s])
                self.assertNotEqual(plan, original[s - 1])
                rows = run.Rows(self.receipt, None)
                try:
                    got_ids = [(st, r, rows.row(st, ix[r])[0]['qid']) for st, ix in plan for r in range(4)]
                    exp_ids = [(st, r, rows.row(st, ix[r])[0]['qid']) for st, ix in original[s] for r in range(4)]
                finally:
                    rows.close()
                self.assertEqual(got_ids, exp_ids)

    def test_finding_extra_head_keys_in_export_are_ignored(self):
        # heads.pt with an extra top-level module not in the live model: loads without error.
        state = dict(self.model.auxiliary_heads.state_dict())
        state['stray_head.weight'] = torch.zeros(3)
        path = self.root / 'heads_extra.pt'
        torch.save(state, path)
        art = run.load(self.cfg['init_artifact']['artifact']['path'])
        art['heads'] = file_pin(path)
        apath = self.root / 'artifact_extra.json'
        write(apath, art)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = file_pin(apath)
        lineage = warm.bind(cfg, self.receipt)
        loaded = base.load_fixture(self.root, {**self.receipt, 'init_artifact': cfg['init_artifact'],
                                               'warm_start': lineage}, base.Tiny())
        self.assertTrue(hasattr(loaded, 'warm_start_lineage'))  # accepted silently

    def test_finding_non_stream_receipt_fields_are_not_bound(self):
        # Stream receipt pins are in REBIND and row_identity strips them, so a rebuilt preparation
        # whose camera/depth/model settings differ from the donor's still binds.
        receipt = copy.deepcopy(self.receipt)
        receipt['camera'] = {'weight_focal': 99.0}
        receipt['depth'] = {'num_points_per_frame': 1}
        receipt['division'] = {'path': '/elsewhere', 'sha256': 'c' * 64}
        cfg = copy.deepcopy(self.cfg)
        cfg['streams'] = {k: {'path': v['path'] + '.other', 'sha256': 'd' * 64} for k, v in cfg['streams'].items()}
        warm.bind(cfg, receipt)  # no refusal


if __name__ == '__main__':
    unittest.main()
