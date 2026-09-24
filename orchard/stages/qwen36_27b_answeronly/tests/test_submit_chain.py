import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / 'scripts'))
from stage_lib import TRAINER_COMMIT, sha256


def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(0o755)
    return path


class SubmitChainTests(unittest.TestCase):
    def setUp(self):
        reference = os.environ.get('AO_REFERENCE_DEPLOYMENT')
        if not reference:
            self.skipTest('Set AO_REFERENCE_DEPLOYMENT to the staged, read-only arm C deployment inputs')
        self.reference = Path(reference)
        self.root = Path(tempfile.mkdtemp(prefix='qwen27b_ao_chain_'))
        self.stage = self.root / 'stage'
        shutil.copytree(STAGE, self.stage)
        self.base = self.root / 'orchard/code/deployment_433d8a1'
        scripts = self.base / 'scripts/orchard'
        for name in ('submit_train.sh', 'run_train.sh', 'train_job.py', 'configs/qwen36_27b.json'):
            write(scripts / name, (self.reference / name).read_text())
        write(self.base / 'slurm/train_qwen36_27b.slurm', (self.reference / 'slurm/train_qwen36_27b.slurm').read_text())
        write(scripts / 'common.sh', ':\n')
        write(scripts / 'stage_model.py', 'raise SystemExit("CPU fixture must never stage a model")\n')
        self.dataset = self.root / 'dataset with spaces'
        self.index = write(self.dataset / 'candidate_index.jsonl', '{"fixture": true}\n')
        self.split = write(self.dataset / 'split_trainer.json', '{}\n')
        value = json.loads((self.stage / 'manifest.json').read_text())
        for identity in value['datasets'].values():
            identity['sha256'] = {self.index.name: sha256(self.index), self.split.name: sha256(self.split)}
            identity['rows'] = {'total': 1, 'train': 1, 'heldout': 0}
        write(self.stage / 'manifest.json', json.dumps(value))
        self.bin = self.root / 'bin'
        write(self.bin / 'git', '#!/usr/bin/env bash\nset -eu\ncase "$*" in\n  *"rev-parse HEAD") printf "%s\\n" "${MOCK_GIT_HEAD:-' + TRAINER_COMMIT + '}";;\n  *"status --porcelain"*) printf "%s" "${MOCK_GIT_DIRTY:-}";;\n  *) exit 99;;\nesac\n', executable=True)
        write(self.bin / 'sbatch', '#!' + sys.executable + '\nimport json, os, sys\nkeys = ("ORCH_DEPLOY", "SPLIT_RECORD", "WORLD_SIZE", "PARTITION", "QOS", "TRAINER_COMMIT", "STUDENT", "PARALLEL", "STUDENT_FRAME_ROOT_MAP")\nwith open(os.environ["MOCK_SBATCH_LOG"], "a") as output:\n    output.write(json.dumps({"argv": sys.argv[1:], "env": {key: os.environ.get(key) for key in keys}}) + "\\n")\nif "--test-only" in sys.argv and os.environ.get("MOCK_SBATCH_REJECT"):\n    raise SystemExit(7)\nprint("test-only accepted" if "--test-only" in sys.argv else "123456")\n', executable=True)
        self.calls = self.root / 'sbatch_calls.jsonl'
        model_manifest = write(self.root / 'model_sha256_meta.json', '{}\n')
        self.env = {
            'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
            'HOME': str(self.root), 'TMPDIR': os.environ.get('TMPDIR', str(self.root)),
            'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
            'ORCH': str(self.root / 'orchard'), 'ORCH_DEPLOY': str(self.base),
            'MODEL_MANIFEST': str(model_manifest), 'SPLIT_RECORD': str(self.split),
            'STAGE_MODEL_REVIEWED_SHA256': sha256(scripts / 'stage_model.py'),
            'ROOMFIX_GATE': 'cpu_fixture_not_a_real_verdict', 'STAGE_PYTHON': sys.executable,
            'MOCK_SBATCH_LOG': str(self.calls),
        }

    def launch(self, variant='setH', run_id='cpu_run', **env):
        return subprocess.run(['bash', str(self.stage / 'submit_train_ao.sh'), variant, str(self.dataset), run_id],
                              env={**self.env, **env}, text=True, capture_output=True)

    def records(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_each_variant_uses_original_submitter_and_separate_frozen_config(self):
        for variant, epochs in (('setH', 3), ('setH_e1', 1), ('fullpool', 1)):
            with self.subTest(variant=variant):
                result = self.launch(variant, 'run_' + variant, DEPENDENCY='afterany:98765')
                self.assertEqual(result.returncode, 0, result.stderr)
                records = self.records()[-2:]
                self.assertEqual([record['argv'][0] for record in records], ['--test-only', '--parsable'])
                deploy = Path(records[-1]['env']['ORCH_DEPLOY'])
                self.assertNotEqual(deploy, self.base)
                config = json.loads((deploy / 'scripts/orchard/configs/qwen36_27b.json').read_text())
                self.assertEqual(config['epochs'], epochs)
                self.assertEqual(config['max_microbatch_size'], 8)
                for record in records:
                    self.assertEqual(record['env']['STUDENT'], 'qwen36_27b')
                    self.assertEqual(record['env']['WORLD_SIZE'], '4')
                    self.assertEqual(record['env']['SPLIT_RECORD'], str(self.split))
                    self.assertIn('--partition=advanced', record['argv'])
                    self.assertIn('--qos=adv_4gpu_qos', record['argv'])
                    self.assertIn('--gres=gpu:4', record['argv'])
                    self.assertIn('--no-requeue', record['argv'])
                    self.assertIn('--dependency=afterany:98765', record['argv'])
                    self.assertEqual(record['argv'][-3:], [str(deploy / 'slurm/train_qwen36_27b.slurm'), str(self.dataset), 'run_' + variant])
                self.assertEqual((deploy / 'scripts/orchard/submit_train.sh').read_bytes(), (self.reference / 'submit_train.sh').read_bytes())
                self.assertIn(str(self.root / 'orchard/runs' / ('run_' + variant) / 'publication') + '/', result.stdout)
        self.assertEqual(json.loads((self.base / 'scripts/orchard/configs/qwen36_27b.json').read_text())['epochs'], 1)

    def test_supported_preempt_override(self):
        result = self.launch('fullpool', PARTITION='preempt', QOS='preempt_qos', WORLD_SIZE='8')
        self.assertEqual(result.returncode, 0, result.stderr)
        for record in self.records():
            self.assertIn('--gres=gpu:8', record['argv'])
            self.assertIn('--requeue', record['argv'])
            self.assertIn('--time=2-00:00:00', record['argv'])
            self.assertIn('--cpus-per-task=64', record['argv'])
            self.assertIn('--mem=512G', record['argv'])
            self.assertEqual(record['env']['WORLD_SIZE'], '8')

    def test_prepare_only_never_calls_scheduler(self):
        result = self.launch(PREPARE_ONLY='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.records(), [])
        self.assertTrue((self.root / 'orchard/code/deployment_433d8a1_ao27b_setH_cpu_run/answeronly_stage.json').exists())

    def test_dry_only_tests_scheduling(self):
        result = self.launch(DRY='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.records()), 1)
        self.assertIn('--test-only', self.records()[0]['argv'])
        self.assertNotIn('--parsable', self.records()[0]['argv'])

    def test_failed_scheduler_probe_does_not_submit(self):
        result = self.launch(MOCK_SBATCH_REJECT='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.records()), 1)
        self.assertIn('--test-only', self.records()[0]['argv'])

    def test_invalid_scheduler_or_recipe_fails_before_scheduler(self):
        for overrides in ({'WORLD_SIZE': '8'}, {'PARALLEL': 'ddp'}, {'SMOKE_TRAIN': '1'}, {'CHECKPOINT_EVERY_STEPS': '1'}, {'TRAINER_COMMIT': 'wrong'}):
            with self.subTest(overrides=overrides):
                self.assertNotEqual(self.launch(**overrides).returncode, 0)
                self.assertEqual(self.records(), [])

    def test_changed_index_fails_before_scheduler(self):
        with self.index.open('a') as output:
            output.write('changed\n')
        self.assertNotEqual(self.launch().returncode, 0)
        self.assertEqual(self.records(), [])

    def test_changed_split_fails_before_scheduler(self):
        with self.split.open('a') as output:
            output.write('changed\n')
        self.assertNotEqual(self.launch().returncode, 0)
        self.assertEqual(self.records(), [])

    def test_unreviewed_stage_model_or_dirty_trainer_fails_before_scheduler(self):
        for overrides in ({'STAGE_MODEL_REVIEWED_SHA256': ''}, {'STAGE_MODEL_REVIEWED_SHA256': '0' * 64}, {'MOCK_GIT_DIRTY': ' M changed.py'}, {'MOCK_GIT_HEAD': 'wrong'}, {'ROOMFIX_GATE': ''}):
            with self.subTest(overrides=overrides):
                self.assertNotEqual(self.launch(**overrides).returncode, 0)
                self.assertEqual(self.records(), [])

    def test_published_run_is_refused(self):
        write(self.root / 'orchard/runs/cpu_run/publication/PUBLISHED.json', '{}\n')
        self.assertEqual(self.launch().returncode, 5)
        self.assertEqual(self.records(), [])

    def test_bad_variant_and_run_id_are_refused(self):
        for variant, run_id in (('qwen36_27b_ao_setH', 'cpu_run'), ('setH', '../unsafe')):
            with self.subTest(variant=variant, run_id=run_id):
                self.assertEqual(self.launch(variant, run_id).returncode, 2)
                self.assertEqual(self.records(), [])


if __name__ == '__main__':
    unittest.main()
