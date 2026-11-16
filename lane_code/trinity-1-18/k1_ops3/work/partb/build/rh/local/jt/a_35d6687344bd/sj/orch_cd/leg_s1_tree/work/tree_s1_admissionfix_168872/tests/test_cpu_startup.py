import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.orchard import cpu_startup


class CpuStartupTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='cpu_startup_train_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.frozen = self.root / 'frozen'
        self.frozen.mkdir()
        for name in ('protocol.json', 'training.json', 'config.json', 'launch_identity.json'):
            (self.frozen / name).write_text('{}\n')
        self.env = patch.dict(os.environ, {'TRAINER_COMMIT': 'a' * 40, 'CUDA_VISIBLE_DEVICES': '0,1'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_seals_before_request_and_never_issues_a_gpu_lease(self):
        calls = []

        def run(command, env):
            calls.append(command)
            self.assertEqual(env['CUDA_VISIBLE_DEVICES'], '')
            output = Path(command[command.index('--output') + 1])
            output.write_text(json.dumps({'synthetic_cpu_fixture': True}))

        with patch.object(cpu_startup, 'require_clean_checkout'), patch.object(cpu_startup, 'run', side_effect=run):
            result = cpu_startup.prepare(self.frozen, 'qwen36_27b', 8)
        self.assertEqual([command[5] for command in calls], ['seal-source', 'lease-request-ddp'])
        self.assertEqual(result['status'], 'CPU_STARTUP_PREPARED')
        self.assertEqual(len(result['inputs']), 6)
        self.assertFalse(any('bind-lease' in ' '.join(command) or 'sbatch' in command for command in calls))
        self.assertTrue((self.frozen / 'cpu_startup.json').is_file())

    def test_shared_frame_preparation_exports_a_byte_pinned_gpu_receipt(self):
        from student_pilot.common import binding
        from student_pilot import startup_receipt

        def run(command, env):
            Path(command[command.index('--output') + 1]).write_text('{}')

        def prepare(*args):
            for name in ('startup_receipt.json', 'shared_frames.json'):
                (self.frozen / name).write_text('{}')
            return binding(self.frozen / 'startup_receipt.json')

        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}), \
                patch.object(cpu_startup, 'require_clean_checkout'), patch.object(cpu_startup, 'run', side_effect=run), \
                patch.object(startup_receipt, 'prepare', side_effect=prepare) as prepared:
            result = cpu_startup.prepare(self.frozen, 'qwen36_27b', 8, shared_frames=True)
        prepared.assert_called_once_with(self.frozen, 'qwen36_27b', 8, cpu_startup.LABEL)
        pin = binding(self.frozen / 'startup_receipt.json')
        self.assertEqual(result['startup_receipt'], pin)
        self.assertEqual(result['gpu_environment'], {'STUDENT_STARTUP_RECEIPT': pin['path'],
                                                   'STUDENT_STARTUP_RECEIPT_SHA256': pin['sha256']})
        self.assertEqual(len(result['inputs']), 8)
        self.assertFalse(result['gpu_admission'])

    def test_existing_receipt_still_passes_through_the_native_request_validator(self):
        (self.frozen / 'training.json.source_receipt.json').write_text('{}')
        with patch.object(cpu_startup, 'require_clean_checkout'), patch.object(cpu_startup, 'run', side_effect=ValueError('native receipt refusal')) as run:
            with self.assertRaisesRegex(ValueError, 'native receipt refusal'):
                cpu_startup.prepare(self.frozen, 'qwen36_27b', 8)
        self.assertEqual(run.call_args.args[0][5], 'lease-request-ddp')
        self.assertFalse((self.frozen / 'cpu_startup.json').exists())

    def test_refuses_gpu_allocations_before_running_preparation(self):
        for variable, value in (('SLURM_JOB_GPUS', '0-7'), ('SLURM_JOB_GPUS', '0'), ('SLURM_GPUS_ON_NODE', '8'), ('SLURM_STEP_GPUS', '0'), ('SLURM_STEP_GPUS', '2')):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: value}), patch.object(cpu_startup, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'CPU allocation'):
                    cpu_startup.prepare(self.frozen, 'qwen36_27b', 8)
                run.assert_not_called()

    def test_refuses_to_replace_existing_request(self):
        path = self.frozen / 'request.json'
        path.write_text('retained request')
        with patch.object(cpu_startup, 'require_clean_checkout'), patch.object(cpu_startup, 'run') as run:
            with self.assertRaises(ValueError):
                cpu_startup.prepare(self.frozen, 'qwen36_27b', 8)
            run.assert_not_called()
        self.assertEqual(path.read_text(), 'retained request')

    def test_refuses_missing_frozen_identity_or_invalid_world(self):
        for world in (0, 1, 9, 33):
            with self.subTest(world=world), patch.object(cpu_startup, 'require_clean_checkout'):
                with self.assertRaises(ValueError):
                    cpu_startup.prepare(self.frozen, 'qwen36_27b', world)
        with patch.object(cpu_startup, 'require_clean_checkout'), self.assertRaises(ValueError):
            cpu_startup.prepare(self.root / 'missing', 'qwen36_27b', 8)


if __name__ == '__main__':
    unittest.main()
