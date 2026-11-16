"""CPU controller-record fixtures; no scheduler or device access."""
from contextlib import ExitStack
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from student_pilot import orchard_admission as admission


class StepAllocationTests(unittest.TestCase):
    def setUp(self):
        # Synthetic controller records. Actual captures can be replayed separately.
        self.job = ('JobId=42 JobState=RUNNING Account=av_alpamayo_aml UserId=jyeung(1234) '
                    'NumNodes=1 NodeList=pool0-0038 Partition=pool0 QOS=av_alpamayo_aml_normal '
                    'Nodes=pool0-0038 GRES=gpu:8(IDX:0-7)')
        self.step = ('StepId=42.0 State=RUNNING NodeList=pool0-0038 '
                     'TresPerNode=gres/gpu:8')
        self.pids = 'PID JOBID STEPID LOCALID GLOBALID\n4321 42 0 0 0'
        self.job_pids = self.pids
        self.calls = []
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {
            'STUDENT_ORCHARD': '1', 'STUDENT_SLURM_SITE': 'code-aws',
            'SLURM_JOB_ID': '42', 'SLURM_JOB_GPUS': '0,1,2,3,4,5,6,7',
            'SLURM_STEP_ID': '0', 'SLURM_STEP_GPUS': '0,1,2,3,4,5,6,7',
        }, clear=True))
        self.stack.enter_context(patch.object(admission.os, 'getuid', return_value=1234))
        self.stack.enter_context(patch.object(admission.os, 'getpid', return_value=4321))
        self.stack.enter_context(patch.object(admission.socket, 'gethostname', return_value='pool0-0038'))
        self.stack.enter_context(patch.object(Path, 'read_text', return_value='0::/fixture\n'))
        self.stack.enter_context(patch.object(admission, 'command', side_effect=self.controller))

    def controller(self, *args):
        self.calls.append(args)
        if args == ('scontrol', 'show', 'job', '-d', '-o', '42'):
            return self.job
        if args == ('scontrol', 'show', 'step', '-d', '-o', '42.0'):
            return self.step
        if args[:3] == ('scontrol', 'show', 'hostnames'):
            return {'pool0-0038': 'pool0-0038', 'pool0-0065': 'pool0-0065',
                    'pool0-[0038,0065]': 'pool0-0038\npool0-0065', '': ''}[args[3]]
        if args == ('scontrol', 'listpids', '42'):
            return self.job_pids
        if args == ('scontrol', 'listpids', '42.0'):
            return self.pids
        raise AssertionError(args)

    def test_full_allocation_without_step_indices_accepts_both_tres_forms(self):
        for separator in ('/', ':'):
            with self.subTest(separator=separator):
                self.step = self.step.replace('gres/gpu', 'gres:gpu') if separator == ':' else self.step
                result = admission.allocation()
                self.assertEqual(result, {
                    'job_id': '42', 'step_id': '0', 'host': 'pool0-0038', 'uid': 1234,
                    'gpu_indices': list(range(8)), 'partition': 'pool0',
                    'qos': 'av_alpamayo_aml_normal', 'restart_count': '0',
                })
                self.assertIn(('scontrol', 'listpids', '42.0'), self.calls)

    def test_no_indices_requires_exact_step_state_node_and_full_gpu_count(self):
        original = self.step
        changes = [('StepId=42.0', 'StepId=42.01'), ('StepId=42.0', 'StepId=142.0'),
                   ('State=RUNNING', 'State=RUNNING_BAD'), ('State=RUNNING', 'State=COMPLETED'),
                   ('NodeList=pool0-0038', 'NodeList=pool0-0065'),
                   ('NodeList=pool0-0038', 'NodeList=pool0-[0038,0065]'),
                   ('NodeList=pool0-0038', ''), ('TresPerNode=gres/gpu:8', ''),
                   ('gres/gpu:8', 'gres/gpu:4'), ('gres/gpu:8', 'gres/gpu:80'),
                   ('gres/gpu:8', 'gres/gpu:8,gres/gpu:8'),
                   ('gres/gpu:8', 'gres/gpu:8 GRES=gpu:8(IDX:unknown)')]
        for old, new in changes:
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.step = original.replace(old, new)
                admission.allocation()

    def test_no_indices_cannot_identify_subset_or_sibling_devices(self):
        for selected in ('0,1,2,3', '1,2,3,4,5,6,7,8'):
            with self.subTest(selected=selected), patch.dict(os.environ, SLURM_STEP_GPUS=selected):
                with self.assertRaises(ValueError):
                    admission.allocation()

    def test_explicit_indices_preserve_subset_behavior_and_are_authoritative(self):
        self.step += ' GRES=gpu:2(IDX:2-3)'
        with patch.dict(os.environ, SLURM_STEP_GPUS='2,3'):
            self.assertEqual(admission.allocation()['gpu_indices'], [2, 3])
        for selected in ('0,1', '0,1,2,3,4,5,6,7'):
            with self.subTest(selected=selected), patch.dict(os.environ, SLURM_STEP_GPUS=selected):
                with self.assertRaises(ValueError):
                    admission.allocation()
        self.step += ' GRES=gpu:2(IDX:2-3)'
        with patch.dict(os.environ, SLURM_STEP_GPUS='2,3'), self.assertRaises(ValueError):
            admission.allocation()

    def test_job_owner_state_qos_node_and_indices_still_required(self):
        original = self.job
        for old, new in [('JobId=42', 'JobId=43'), ('RUNNING', 'COMPLETED'),
                         ('jyeung(1234)', 'jyeung(1235)'), ('av_alpamayo_aml ', 'wrong '),
                         ('QOS=av_alpamayo_aml_normal', 'QOS=wrong'),
                         ('Partition=pool0', 'Partition=wrong'), ('NumNodes=1', 'NumNodes=9'),
                         ('NodeList=pool0-0038', 'NodeList=pool0-0065'), ('IDX:0-7', 'IDX:0-3')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.job = original.replace(old, new)
                admission.allocation()

    def test_process_must_belong_to_both_job_and_step(self):
        self.pids = 'PID JOBID STEPID LOCALID GLOBALID\n9999 42 0 0 0'
        with self.assertRaisesRegex(ValueError, 'claimed GPU step'):
            admission.allocation()
        self.job_pids = self.pids
        with self.assertRaisesRegex(ValueError, 'outside this Slurm allocation'):
            admission.allocation()

    def test_batch_and_no_step_gpu_environment_keep_existing_behavior(self):
        with patch.dict(os.environ, SLURM_STEP_ID='batch'):
            self.assertIsNone(admission.allocation()['step_id'])
        with patch.dict(os.environ, SLURM_STEP_GPUS=''):
            self.assertEqual(admission.allocation()['gpu_indices'], list(range(8)))
        self.assertNotIn(('scontrol', 'show', 'step', '-d', '-o', '42.0'), self.calls)

    def test_multinode_accepts_reference_tres_spellings(self):
        self.job = self.job.replace('NumNodes=1', 'NumNodes=2').replace(
            'pool0-0038', 'pool0-[0038,0065]')
        self.step = self.step.replace('pool0-0038', 'pool0-[0038,0065]')
        for separator in ('/', ':'):
            with self.subTest(separator=separator):
                self.step = self.step.replace('gres/gpu', 'gres:gpu') if separator == ':' else self.step
                result = admission.allocation()
                self.assertEqual(result['gpu_indices'], list(range(8)))
                self.assertEqual(result['nodes'], ['pool0-0038', 'pool0-0065'])
                self.assertEqual(result['node_rank'], 0)


if __name__ == '__main__':
    unittest.main()
