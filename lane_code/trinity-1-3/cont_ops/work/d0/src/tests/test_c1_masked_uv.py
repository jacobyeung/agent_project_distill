"""A3 pose rows keep off-frame uv on masked-out depth points (T1's step-1 deadlock on ranks 10 and 14).

The private depth head must train such rows exactly like rows with zero uv there, the shared row check
must refuse off-frame uv on labelled points, and a rank that raises mid-step must exit at once instead
of waiting in process-group teardown while its peers wait in a collective."""
import math
import os
import tempfile
import time
import unittest

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_data import mixed_indices
from tests.test_carrier_c1_final import final_fixture
from tests.test_carrier_c1_t0 import good_batch


def a1_targets(targets):
    """A1 pose rows: zero-mask depth placeholders (uv 0, depth 0, mask False)."""
    return {**targets, 'aux_point_depth_uv': torch.zeros_like(targets['aux_point_depth_uv']),
            'aux_point_depth_gt': torch.zeros_like(targets['aux_point_depth_gt']),
            'aux_point_depth_mask': torch.zeros_like(targets['aux_point_depth_mask'])}


def a3_targets(targets):
    """A3 d1 rows: labelled points plus masked-out points whose uv lies just off the frame."""
    uv, mask = targets['aux_point_depth_uv'].clone(), targets['aux_point_depth_mask'].clone()
    mask[0, :, 1] = False
    uv[0, ::2, 1] = torch.tensor([1001., 300.])
    uv[0, 1::2, 1] = torch.tensor([-1.2783203125, 1001.])
    return {**targets, 'aux_point_depth_uv': uv, 'aux_point_depth_mask': mask}


class PoseRows:
    def __init__(self, batch, targets):
        self.batch, self.targets = batch, targets

    def count(self, stream):
        return 9

    def get(self, stream, index):
        return self.batch, self.targets if stream == 'pose' else None, {}


def _two_rank_worker(rank, root, results):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method='file://' + root + '/rendezvous', rank=rank, world_size=2)
    try:
        model, batch, targets = final_fixture()
        rows = PoseRows(batch, a1_targets(targets) if rank == 0 else a3_targets(targets))
        wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
        optimizer = torch.optim.AdamW(parameter_groups(wrapped), weight_decay=.01)
        plans = list(mixed_indices(dict(pose=9, vqa=9), 2, training_mode='final', mix=['pose', 'pose', 'vqa'], world=2))
        infos = [run.optimize_step(wrapped, optimizer, rows, plan, rank, torch.device('cpu'), step, True)[0]
                 for step, plan in enumerate(plans, 1)]
        heads = torch.cat([p.detach().reshape(-1) for p in wrapped.module.auxiliary_heads.parameters()])
        gathered = [torch.zeros_like(heads) for _ in range(2)]
        dist.all_gather(gathered, heads)
        results[rank] = dict(steps=[i['step'] for i in infos], skipped=[i['skip_totals']['skipped'] for i in infos],
                             depth=[i['components']['depth'] for i in infos],
                             finite=all(math.isfinite(v) for i in infos for v in i['components'].values()),
                             same_heads=bool(torch.equal(gathered[0], gathered[1])))
    finally:
        dist.destroy_process_group()


def _fail_fast_worker(rank, root):
    dist.init_process_group('gloo', init_method='file://' + root + '/rendezvous', rank=rank, world_size=2)

    def step():
        if rank == 1:
            raise ValueError('Point queries must lie in [0, 1000] x [0, 1000]')
        dist.all_reduce(torch.ones(1))

    try:
        run.run_or_exit(step)
    finally:
        dist.destroy_process_group()


class MaskedOffFrameUv(unittest.TestCase):
    def test_masked_out_off_frame_uv_trains_exactly_like_zero_uv(self):
        model, batch, targets = final_fixture()
        raw = a3_targets(targets)
        zeroed = {**raw, 'aux_point_depth_uv': torch.where(raw['aux_point_depth_mask'][..., None],
                                                           raw['aux_point_depth_uv'], 0.)}
        results = []
        for case in (raw, zeroed):
            model.zero_grad(set_to_none=True)
            torch.manual_seed(0)
            result = model(batch, case)
            result['loss'].backward()
            results.append((result['loss'].detach(), float(result['components']['depth']),
                            {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}))
        torch.testing.assert_close(results[0][0], results[1][0], rtol=0, atol=0)
        self.assertGreater(results[0][1], 0.)
        self.assertEqual(results[0][2].keys(), results[1][2].keys())
        for name, grad in results[0][2].items():
            torch.testing.assert_close(grad, results[1][2][name], rtol=0, atol=0)
        head = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        with self.assertRaisesRegex(ValueError, r'\[0, 1000\]'):
            head.query(torch.zeros(32, 1, 2, 2), raw['aux_point_depth_uv'][0])

    def test_shared_row_check_refuses_off_frame_uv_only_on_labelled_points(self):
        model, _, targets = final_fixture()
        run.check_row(good_batch(), a3_targets(targets), 'pose', model)
        run.check_row(good_batch(), a1_targets(targets), 'pose', model)
        for value in (1000.5, -0.5, float('nan')):
            bad = a3_targets(targets)
            bad['aux_point_depth_uv'][0, 5, 0, 0] = value
            with self.assertRaisesRegex(ValueError, r'\[0, 1000\]'):
                run.check_row(good_batch(), bad, 'pose', model)
        short = {**targets, 'aux_point_depth_uv': targets['aux_point_depth_uv'][..., :1, :]}
        with self.assertRaisesRegex(ValueError, 'uv pair'):
            run.check_row(good_batch(), short, 'pose', model)

    def test_two_ranks_train_two_steps_on_a1_only_and_a3_batches(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            results = mp.Manager().dict()
            mp.spawn(_two_rank_worker, args=(root, results), nprocs=2, join=True)
            a1, a3 = results[0], results[1]
        self.assertEqual((a1['steps'], a3['steps'], a1['skipped'], a3['skipped']), ([1, 2], [1, 2], [0, 0], [0, 0]))
        self.assertTrue(a1['finite'] and a3['finite'] and a1['same_heads'] and a3['same_heads'])
        self.assertEqual(a1['depth'], [0., 0.])
        self.assertTrue(all(value > 0 for value in a3['depth']))

    def test_a_rank_that_raises_mid_step_exits_without_teardown(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            started = time.monotonic()
            with self.assertRaises(mp.ProcessExitedException) as caught:
                mp.spawn(_fail_fast_worker, args=(root,), nprocs=2, join=True)
            self.assertEqual((caught.exception.error_index, caught.exception.exit_code), (1, 1))
            self.assertLess(time.monotonic() - started, 120)


if __name__ == '__main__':
    unittest.main()
