import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / 'scripts'))
from prepare_deployment import CHAIN_FILES, prepare_deployment
from stage_lib import STUDENT, freeze_config, load_student_config, sha256, verify_dataset


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='qwen27b_ao_deploy_'))
        self.base = self.root / 'armc'
        self.deploy = self.root / 'answeronly'
        self.dataset = self.root / 'dataset'
        self.split = write(self.root / 'split_trainer.json', '{}\n')
        for relative in CHAIN_FILES:
            write(self.base / relative, ':\n' if relative.endswith('.sh') else 'raise SystemExit(99)\n')
        write(self.base / 'scripts/orchard/configs/qwen36_27b.json', (STAGE / 'configs/qwen36_27b.json').read_text())
        write(self.base / 'slurm/train_qwen36_27b.slurm', '#!/usr/bin/env bash\nexit 99\n')
        self.reviewed = sha256(self.base / 'scripts/orchard/stage_model.py')

    def prepare(self, variant='setH', deploy=None, **kwargs):
        values = dict(base=self.base, deploy=deploy or self.deploy, variant=variant,
                      run_id='unit_run', dataset=self.dataset, split=self.split,
                      reviewed_sha256=self.reviewed)
        values.update(kwargs)
        return prepare_deployment(**values)

    def test_selected_config_uses_literal_student_filename(self):
        for variant, epochs in (('setH', 3), ('setH_e1', 1), ('fullpool', 1), ('setH_mb4', 3)):
            with self.subTest(variant=variant):
                here = self.root / variant
                target = freeze_config(variant, here)
                self.assertEqual(target.name, 'qwen36_27b.json')
                self.assertEqual(load_student_config(here)['epochs'], epochs)
                self.assertEqual(load_student_config(here)['max_microbatch_size'], 4 if variant == 'setH_mb4' else 8)
                with self.assertRaises(ValueError):
                    load_student_config(here, 'qwen36_27b_ao_' + variant)

    def test_existing_variants_freeze_to_pinned_dry_run_bytes(self):
        pins = {
            'setH': '6c8357817494a4df4388d1de1ac39c9eefc571321cfc2e24e7d3e78ce760a565',
            'setH_e1': '50d39dfd2b4b314bc5f25d8c1f54a62d1bdf5fb8af37bcbc7b5c107f225b9ecf',
            'fullpool': '50d39dfd2b4b314bc5f25d8c1f54a62d1bdf5fb8af37bcbc7b5c107f225b9ecf',
        }
        for variant, expected in pins.items():
            with self.subTest(variant=variant):
                self.assertEqual(sha256(freeze_config(variant, self.root / variant)), expected)

    def test_separate_deployment_preserves_source_and_quarantines_copies(self):
        source = self.base / 'scripts/orchard/configs/qwen36_27b.json'
        original = source.read_bytes()
        receipt = self.prepare()
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual((self.deploy / '_quarantine/answeronly_stage/scripts/orchard/configs/qwen36_27b.json').read_bytes(), original)
        self.assertEqual(load_student_config(self.deploy / 'scripts/orchard')['epochs'], 3)
        self.assertEqual(receipt['student'], STUDENT)
        for relative in CHAIN_FILES:
            self.assertEqual((self.base / relative).read_bytes(), (self.deploy / relative).read_bytes())

    def test_variants_do_not_change_each_others_queued_config(self):
        self.prepare()
        selected = self.deploy / 'scripts/orchard/configs/qwen36_27b.json'
        frozen = selected.read_bytes()
        self.prepare('setH_e1', self.root / 'fallback')
        self.prepare('setH_mb4', self.root / 'mb4')
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertEqual(load_student_config(self.root / 'fallback/scripts/orchard')['epochs'], 1)
        self.assertEqual(load_student_config(self.root / 'mb4/scripts/orchard')['max_microbatch_size'], 4)

    def test_identical_reuse_does_not_rewrite_config_or_receipt(self):
        receipt = self.prepare()
        paths = [self.deploy / 'answeronly_stage.json', self.deploy / 'scripts/orchard/configs/qwen36_27b.json']
        before = [path.stat().st_mtime_ns for path in paths]
        self.assertEqual(self.prepare(), receipt)
        self.assertEqual([path.stat().st_mtime_ns for path in paths], before)

    def test_changed_variant_or_run_id_is_refused(self):
        self.prepare()
        with self.assertRaises(ValueError):
            self.prepare('setH_e1')
        with self.assertRaises(ValueError):
            self.prepare(run_id='different_run')

    def test_changed_frozen_config_or_code_is_refused(self):
        for relative in ('scripts/orchard/configs/qwen36_27b.json', 'scripts/orchard/train_job.py', 'slurm/train_qwen36_27b.slurm'):
            with self.subTest(relative=relative):
                deploy = self.root / ('changed_' + Path(relative).name)
                self.prepare(deploy=deploy)
                write(deploy / relative, 'changed\n')
                with self.assertRaises(ValueError):
                    self.prepare(deploy=deploy)

    def test_unknown_existing_directory_is_not_overwritten(self):
        marker = write(self.deploy / 'keep.txt', 'retained\n')
        with self.assertRaises((ValueError, OSError)):
            self.prepare()
        self.assertEqual(marker.read_text(), 'retained\n')
        self.assertFalse((self.deploy / 'scripts').exists())

    def test_source_and_nested_destinations_are_refused(self):
        for deploy in (self.base, self.base / 'nested', self.root):
            with self.subTest(deploy=deploy), self.assertRaises(ValueError):
                self.prepare(deploy=deploy)

    def test_unreviewed_model_stager_is_refused(self):
        for value in ('', '0' * 64):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.prepare(reviewed_sha256=value)
        self.assertFalse(self.deploy.exists())

    def test_file_hash_and_row_verification_with_retained_cpu_fixture(self):
        index = write(self.dataset / 'candidate_index.jsonl', '{"fixture": 1}\n{"fixture": 2}\n')
        expected = {'sha256': {index.name: sha256(index), self.split.name: sha256(self.split)}, 'rows': {'total': 2}}
        with mock.patch('stage_lib.dataset_identity', return_value=expected):
            self.assertEqual(verify_dataset('setH', self.dataset, self.split), (expected['sha256'], 2))
            write(index, '{"fixture": 3}\n')
            with self.assertRaises(ValueError):
                verify_dataset('setH', self.dataset, self.split)

    def test_slurm_wrapper_passes_literal_student_and_arguments(self):
        write(self.base / 'scripts/orchard/run_train.sh', 'printf "%s\\n" "$@" "$WORLD_SIZE"\n')
        env = {**os.environ, 'ORCH_DEPLOY': str(self.base), 'WORLD_SIZE': '4', 'PYTHONDONTWRITEBYTECODE': '1'}
        result = subprocess.run(['bash', str(STAGE / 'slurm/train_qwen36_27b_ao.slurm'), str(self.dataset), 'unit_run'],
                                env=env, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), [STUDENT, str(self.dataset), 'unit_run', '4'])


if __name__ == '__main__':
    unittest.main()
