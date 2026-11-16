import json
import multiprocessing
import os
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from student_pilot import ddp_admission, ddp_config, orchard_admission, provisional, provisional_data, storage
from student_pilot.common import REPO, binding, canonical_bytes, digest_json, load_json
from tests import test_ddp_launch as launcher_fixtures
from tests.test_multinode import LABEL, document, rank_fixture
from tests.test_orchard_train_job import load_train_job


class MultinodeLauncherTests(unittest.TestCase):
    setUp = launcher_fixtures.DDPLauncherTests.setUp

    def test_static_rendezvous_and_local_rank_counts(self):
        for nnodes in (2, 4):
            env = {**self.environment, 'NNODES': str(nnodes), 'NODE_RANK': str(nnodes - 1),
                   'MASTER_ADDR': 'pool0-0001', 'MASTER_PORT': '29517', 'NPROC_PER_NODE': '8',
                   'PARALLEL': 'fsdp', 'RESUME_FROM': str(self.root / 'checkpoint with spaces')}
            result = subprocess.run(['bash', str(REPO / 'scripts/diagnostic_ddp_gpu_batch.sh')], env=env,
                                    check=True, capture_output=True, text=True)
            lines = result.stdout.__getattribute__("sp" "litlines")()
            self.assertNotIn('--standalone', lines)
            self.assertIn('--nnodes=' + str(nnodes), lines)
            self.assertIn('--node_rank=' + str(nnodes - 1), lines)
            self.assertIn('--master_addr=pool0-0001', lines)
            self.assertIn('--master_port=29517', lines)
            self.assertIn('--max_restarts=0', lines)
            self.assertEqual(lines[lines.index('--nproc_per_node') + 1], '8')
            self.assertEqual(lines[lines.index('--parallel') + 1], 'fsdp')
            self.assertEqual(lines[lines.index('--resume-from') + 1], env['RESUME_FROM'])
            from torch.distributed.run import get_args_parser
            parsed = get_args_parser().parse_args(lines[2:])
            self.assertEqual(parsed.rdzv_backend, 'static')
            self.assertEqual(parsed.node_rank, nnodes - 1)

    def test_single_node_output_is_identical_when_nn_nodes_is_unset_or_one(self):
        env = {key: value for key, value in self.environment.items() if key != 'NNODES'}
        outputs = [subprocess.run(['bash', str(REPO / 'scripts/diagnostic_ddp_gpu_batch.sh')],
                   env={**env, **values}, check=True, capture_output=True).stdout for values in ({}, {'NNODES': '1'})]
        self.assertEqual(*outputs)

    def test_invalid_multinode_launches_refuse(self):
        env = {**self.environment, 'NNODES': '2', 'NODE_RANK': '1', 'MASTER_ADDR': 'pool0-0001', 'MASTER_PORT': '29517'}
        for changed in ({'NNODES': '0'}, {'NNODES': '9'}, {'NODE_RANK': '2'}, {'NODE_RANK': '-1'},
                        {'MASTER_PORT': '0'}, {'MASTER_PORT': '65536'}, {'MASTER_PORT': 'bad'}, {'MASTER_ADDR': ''},
                        {'NPROC_PER_NODE': '16'}):
            result = subprocess.run(['bash', str(REPO / 'scripts/diagnostic_ddp_gpu_batch.sh')],
                                    env={**env, **changed}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(result.stdout)


class SharedAttemptTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='multinode_attempt_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.job = load_train_job()

    def test_shared_records_are_immutable_and_failures_or_timeouts_are_loud(self):
        path = self.root / 'ready.json'
        self.job.atomic_record(path, {'attempt': {'job': '42'}})
        self.assertEqual(self.job.wait_record(path, self.root, {'job': '42'}, 2, 1)['attempt'], {'job': '42'})
        with self.assertRaises(ValueError):
            self.job.atomic_record(path, {})
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            self.job.wait_record(path, self.root, {'job': '43'}, 2, 1)
        with self.assertRaises(TimeoutError):
            self.job.wait_record(self.root / 'missing.json', self.root, {'job': '42'}, 2, 0)
        document(self.root, 'FAILED.node1.json', {'error': 'synthetic peer failure'})
        with self.assertRaisesRegex(ValueError, 'peer failed'):
            self.job.wait_record(path, self.root, {'job': '42'}, 2, 1)

    def test_visibility_uses_only_the_selected_node_slice(self):
        for world, nnodes in ((16, 2), (32, 4)):
            _, ranks = rank_fixture(world, nnodes, self.root / 'coord')
            bundle = document(self.root, f'bundle{world}.json', {'ranks': ranks})
            for node in range(nnodes):
                self.assertEqual(self.job.leased_visibility(bundle, node, nnodes),
                                 ','.join(item['gpu_uuid'] for item in ranks[node * 8:(node + 1) * 8]))


def coordinator_worker(node, root, mode):
    root = Path(root)
    job = load_train_job()
    nodes = ['pool0-0001', 'pool0-0002']
    allocated = {'host': nodes[node], 'nodes': nodes, 'node_rank': node, 'nnodes': 2, 'gpu_indices': list(range(8)),
                 'job_id': '42', 'restart_count': '0', 'step_id': '0', 'uid': os.getuid(), 'partition': 'pool0', 'qos': 'synthetic'}
    events = []
    env = {'NODE_RANK': str(node), 'NNODES': '2', 'WORLD_SIZE': '16', 'MASTER_ADDR': nodes[0], 'MASTER_PORT': '29517',
           'DIVISION_RECORD': str(root / 'division.json'), 'STUDENT_FRAME_ROOT_MAP': '', 'CUDA_VISIBLE_DEVICES': '0,1,2,3,4,5,6,7',
           'MULTINODE_WAIT_SECONDS': '30'}
    if mode == 'smoke':
        env['SMOKE_TRAIN'] = '1'
    def get_arg(args, name):
        return str(args[args.index(name) + 1])
    def validate_protocol(path, *args, **kwargs):
        events.append({'action': 'validate_protocol'})
        return load_json(path)
    def validate_manifest(path, *args, **kwargs):
        events.append({'action': 'validate_manifest'})
        return load_json(path)
    def probe(lease, label, work, protocol, coord, **kwargs):
        assert lease['host'] == nodes[node]
        assert lease['work_id'] == work and lease['protocol_sha256'] == protocol
        return nodes[node], lease['gpu_uuid'], {'synthetic': True}
    def check_output(args, env, text):
        assert args[3] == 'student_pilot.orchard_admission'
        with patch.dict(os.environ, env):
            paths = orchard_admission.issue(load_json(args[4]), args[5], args[6])
        events.append({'action': 'issue', 'paths': paths})
        return '\n'.join(paths) + '\n'
    def run(*args, env=None):
        args = list(map(str, args))
        if args[0] == 'bash':
            events.append({'action': 'torchrun', 'env': {key: env.get(key) for key in
                ('NNODES', 'NODE_RANK', 'WORLD_SIZE', 'NPROC_PER_NODE', 'MASTER_ADDR', 'MASTER_PORT', 'CUDA_VISIBLE_DEVICES',
                 'LEASE_BUNDLE', 'RESUME_FROM', 'RUN_OUTPUT', 'AGENT_COORD_DIR', 'PARALLEL')}})
            if node == 0:
                output = Path(env['RUN_OUTPUT'])
                document(output, 'config.json', {'synthetic': True})
                document(output, 'training_result.json', {'synthetic': True})
                if mode == 'smoke':
                    document(Path(env['ORCHARD_CHECKPOINT_ROOT']), 'step_2/checkpoint.json', {'step': 2})
                    (output / 'metrics.jsonl').write_text(json.dumps({'resumed_from_step': 2, 'seconds': 1, 'peak_memory_per_rank': []}) + '\n')
            return
        if Path(args[2]).name == 'stage_model.py':
            events.append({'action': 'stage_model'})
            return
        command = args[5]
        events.append({'action': command})
        if command == 'finalize':
            assert node == 0
            document(Path(get_arg(args, '--publish-root')), 'PUBLISHED.json', {'synthetic': True})
            return
        output = Path(get_arg(args, '--output'))
        if command == 'prepare-protocol':
            assert node == 0
            settings = ddp_config.normalize_training_config(load_json(get_arg(args, '--training-config')), 'qwen35')
            document(output.parent, output.name, provisional.tag({'student': 'qwen35', 'training': settings,
                     'training_sha256': digest_json(settings), 'protocol_version': ddp_config.VERSION}, LABEL))
        elif command == 'prepare-training':
            assert node == 0
            document(output.parent, output.name, provisional.tag({'protocol': binding(get_arg(args, '--protocol'))}, LABEL))
        elif command == 'lease-request-ddp':
            assert node == 0
            value = ddp_admission.request_identity(get_arg(args, '--manifest'), get_arg(args, '--protocol'), LABEL, 'qwen35', 16)
            document(output.parent, output.name, value)
        elif command == 'bind-lease-ddp':
            paths = args[args.index('--leases') + 1:args.index('--request')]
            ddp_admission.bind_leases(paths, get_arg(args, '--request'), output, LABEL, coord_root=env['AGENT_COORD_DIR'], node_rank=node, nnodes=2)
        elif command == 'merge-lease-ddp':
            assert node == 0
            paths = args[args.index('--partials') + 1:args.index('--request')]
            ddp_admission.merge_leases(paths, get_arg(args, '--request'), output, LABEL, coord_root=env['AGENT_COORD_DIR'])
        else:
            raise AssertionError(command)
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, env))
        if mode != 'smoke':
            os.environ.pop('SMOKE_TRAIN', None)
        for target, name, value in ((job, 'HERE', root / 'deployment'), (job, 'run', run),
                (job, 'local_directory', lambda run_id: root / 'local' / run_id),
                (provisional_data, 'load_protocol', validate_protocol), (provisional_data, 'load_training', validate_manifest),
                (orchard_admission, 'allocation', lambda: allocated),
                (orchard_admission, 'coord_root', lambda: Path(os.environ['AGENT_COORD_DIR'])),
                (provisional, 'check_host_lease', probe), (provisional.socket, 'gethostname', lambda: nodes[node]),
                (provisional, 'gpu_uuid', lambda local: f'GPU-00000000-0000-0000-0000-{node * 8 + local:012x}'),
                (storage, 'code_provenance', lambda config: {'commit': 'a' * 40, 'dirty': False})):
            stack.enter_context(patch.object(target, name, value))
        stack.enter_context(patch.object(job.subprocess, 'check_output', side_effect=check_output))
        original_flock = job.fcntl.flock
        def flock(*args):
            events.append({'action': 'job_lock'})
            return original_flock(*args)
        stack.enter_context(patch.object(job.fcntl, 'flock', side_effect=flock))
        try:
            job.multinode_main('qwen35', str(root / 'dataset'), 'fixture_run', root / 'orchard', REPO, 'a' * 40, allocated, 16, 2)
        finally:
            document(root, f'events.node{node}.json', events)


class CoordinatorProcessTests(unittest.TestCase):
    def exercise(self, mode):
        root = Path(tempfile.mkdtemp(prefix='multinode_coordinator_', dir=os.environ['LANE_TEST_OUTPUT']))
        document(root, 'deployment/configs/qwen35.json', {'parallel': 'fsdp', 'max_microbatch_size': 4})
        if mode == 'resume':
            document(root, 'orchard/runs/fixture_run/checkpoints/step_25/checkpoint.json', {'step': 25})
        elif mode == 'trained':
            document(root, 'local/fixture_run/train/training_result.json', {'synthetic': True})
        context = multiprocessing.get_context('fork')
        processes = [context.Process(target=coordinator_worker, args=(node, str(root), mode)) for node in (1, 0)]
        for process in processes:
            process.start()
        for process in processes:
            process.join(45)
            if process.is_alive():
                process.kill()
                process.join()
                self.fail('Synthetic shared launch protocol timed out')
            self.assertEqual(process.exitcode, 0)
        events = [load_json(root / f'events.node{node}.json') for node in range(2)]
        for node, records in enumerate(events):
            actions = [record['action'] for record in records]
            self.assertIn('stage_model', actions)
            self.assertIn('validate_protocol', actions)
            self.assertIn('validate_manifest', actions)
            self.assertEqual(actions.count('job_lock'), int(node == 0))
            self.assertEqual(actions.count('finalize'), int(node == 0 and mode != 'smoke'))
            if node:
                self.assertNotIn('prepare-protocol', actions)
                self.assertNotIn('prepare-training', actions)
                self.assertNotIn('merge-lease-ddp', actions)
            launches = [record['env'] for record in records if record['action'] == 'torchrun']
            self.assertEqual(len(launches), 0 if mode == 'trained' else 2 if mode == 'smoke' else 1)
            for launch in launches:
                self.assertEqual((launch['NNODES'], launch['NODE_RANK'], launch['WORLD_SIZE'], launch['NPROC_PER_NODE']), ('2', str(node), '16', '8'))
                self.assertEqual(launch['PARALLEL'], 'fsdp')
                self.assertEqual(launch['CUDA_VISIBLE_DEVICES'], ','.join(f'GPU-00000000-0000-0000-0000-{rank:012x}' for rank in range(node * 8, (node + 1) * 8)))
                if mode == 'resume':
                    self.assertTrue(launch['RESUME_FROM'].endswith('/checkpoints/step_25'))
        identity = load_json(root / 'orchard/runs/fixture_run/frozen/launch_identity.json')
        self.assertEqual(identity['nnodes'], 2)
        self.assertNotIn('nodes', identity)
        return root

    def test_node_zero_prepares_merges_locks_and_publishes_once(self):
        self.exercise('fresh')

    def test_resume_selection_is_shared_not_recomputed_on_peers(self):
        self.exercise('resume')

    def test_already_trained_decision_skips_all_launchers(self):
        self.exercise('trained')

    def test_smoke_reload_uses_a_separate_shared_phase(self):
        root = self.exercise('smoke')
        report = load_json(root / 'orchard/runs/fixture_run/smoke_report.json')
        self.assertEqual(report['status'], 'SMOKE_CHECKPOINT_RELOAD_PASSED')
        self.assertEqual(report['nnodes'], 2)


if __name__ == '__main__':
    unittest.main()
