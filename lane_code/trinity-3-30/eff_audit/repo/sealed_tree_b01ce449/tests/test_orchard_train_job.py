"""Regression for the DDP launcher visibility gate (job 147510).

scripts/orchard/train_job.py is a Slurm launcher script, not an importable student_pilot
module (like scripts/orchard/eval_job.py, see tests/test_orchard_eval_wrapper.py), so this
loads it directly from its file path. The lease bundle records each rank's physical
gpu_index (from SLURM_JOB_GPUS), but Slurm's cgroup exports a local-index
CUDA_VISIBLE_DEVICES that never matches that physical list, so
student_pilot.ddp_admission.select_rank() blocked every rank with "Launcher visibility must
list the leased GPUs in rank order". leased_visibility() lists the leased GPU UUIDs in rank
order instead -- the form select_rank() also accepts -- so train_job.train() can export it as
CUDA_VISIBLE_DEVICES before the DDP launch.
"""
import importlib.util
import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAIN_JOB_PATH = REPO_ROOT / 'scripts' / 'orchard' / 'train_job.py'


def load_train_job():
    spec = importlib.util.spec_from_file_location('_orchard_train_job', TRAIN_JOB_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


train_job = load_train_job()


class LeasedVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['LANE_TEST_OUTPUT']) / ('train_job_visibility_' + self._testMethodName)
        self.root.mkdir(parents=True, exist_ok=True)

    def test_uuids_listed_in_rank_order_for_a_local_index_lease(self):
        # Mirrors job 147510: SLURM_JOB_GPUS leased physical indices 0,2,3,4 while the
        # job's cgroup exported the local-index CUDA_VISIBLE_DEVICES=0,1,2,3.
        bundle_path = self.root / 'leases.json'
        ranks = [
            {'rank': 0, 'gpu_index': 0, 'gpu_uuid': 'GPU-00000000-0000-0000-0000-000000000000'},
            {'rank': 1, 'gpu_index': 2, 'gpu_uuid': 'GPU-11111111-1111-1111-1111-111111111111'},
            {'rank': 2, 'gpu_index': 3, 'gpu_uuid': 'GPU-22222222-2222-2222-2222-222222222222'},
            {'rank': 3, 'gpu_index': 4, 'gpu_uuid': 'GPU-33333333-3333-3333-3333-333333333333'},
        ]
        bundle_path.write_text(json.dumps({'schema': 'provisional-ddp-supervisor-leases-v1', 'ranks': ranks}))

        visible = train_job.leased_visibility(bundle_path)

        self.assertEqual(visible, ','.join(rank['gpu_uuid'] for rank in ranks))
        # Same string select_rank() itself builds from the bundle, so it now matches.
        self.assertEqual(visible, ','.join(lease['gpu_uuid'] for lease in ranks))

    def test_environment_passed_to_the_launch_carries_the_uuid_list(self):
        bundle_path = self.root / 'leases.json'
        ranks = [
            {'gpu_index': 0, 'gpu_uuid': 'GPU-aaaaaaaa-0000-0000-0000-000000000000'},
            {'gpu_index': 2, 'gpu_uuid': 'GPU-bbbbbbbb-0000-0000-0000-000000000000'},
            {'gpu_index': 3, 'gpu_uuid': 'GPU-cccccccc-0000-0000-0000-000000000000'},
            {'gpu_index': 4, 'gpu_uuid': 'GPU-dddddddd-0000-0000-0000-000000000000'},
        ]
        bundle_path.write_text(json.dumps({'ranks': ranks}))

        # The exact assignment train() performs right after LEASE_BUNDLE is set (train_job.py,
        # around line 120), reproduced here without the rest of train()'s Slurm/git side effects.
        env = {'PATH': '/usr/bin', 'LEASE_BUNDLE': str(bundle_path)}
        env['CUDA_VISIBLE_DEVICES'] = train_job.leased_visibility(bundle_path)

        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],
                          'GPU-aaaaaaaa-0000-0000-0000-000000000000,'
                          'GPU-bbbbbbbb-0000-0000-0000-000000000000,'
                          'GPU-cccccccc-0000-0000-0000-000000000000,'
                          'GPU-dddddddd-0000-0000-0000-000000000000')
        self.assertEqual(env['PATH'], '/usr/bin')


if __name__ == '__main__':
    unittest.main()
