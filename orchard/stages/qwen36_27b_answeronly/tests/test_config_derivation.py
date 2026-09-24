import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / 'scripts'))
VARIANTS = {'setH': 3, 'setH_e1': 1, 'fullpool': 1, 'setH_mb4': 3}
FIXTURES = {
    'setH': {
        'rows': {'total': 9232, 'train': 7684, 'heldout': 1548},
        'sha256': {
            'candidate_index.jsonl': '5797eac24b659eb9c5ac7f41242f842a345e231b5cd7ed7135758cc85de97cca',
            'split_trainer.json': 'eec29d981c5c30b6217c72938bfbb1c0cbd13842ff651767a2c657125092cb27',
        },
    },
    'fullpool': {
        'rows': {'total': 29399, 'train': 25164, 'heldout': 4235},
        'sha256': {
            'candidate_index.jsonl': 'b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446',
            'split_trainer.json': '46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70',
        },
    },
}


class ConfigDerivationTests(unittest.TestCase):
    def test_only_epochs_differ_from_arm_c_template(self):
        baseline = json.loads((STAGE / 'configs/qwen36_27b.json').read_text())
        for variant in ('setH', 'setH_e1', 'fullpool'):
            with self.subTest(variant=variant):
                path = STAGE / 'configs' / ('qwen36_27b_ao_' + variant + '.json')
                actual = json.loads(path.read_text())
                self.assertEqual(set(actual), set(baseline))
                self.assertEqual(actual, {**baseline, 'epochs': VARIANTS[variant]})

    def test_setH_mb4_derives_exact_bytes_from_arm_c_template(self):
        from stage_lib import validate_config, variant_spec
        baseline = (STAGE / 'configs/qwen36_27b.json').read_bytes()
        expected = baseline.replace(b'"epochs": 1', b'"epochs": 3', 1).replace(
            b'"max_microbatch_size": 8', b'"max_microbatch_size": 4', 1)
        actual = (STAGE / 'configs/qwen36_27b_ao_setH_mb4.json').read_bytes()
        self.assertEqual(actual, expected)
        self.assertEqual((STAGE / 'frozen_configs/setH_mb4/configs/qwen36_27b.json').read_bytes(), expected)
        self.assertEqual(validate_config('setH_mb4', json.loads(actual)), json.loads(expected))
        self.assertEqual(variant_spec('setH_mb4')['run_id'], 'qwen36_27b_ao_setH_mb4_20260924')

    def test_variant_override_declarations_cannot_widen_gate(self):
        from stage_lib import variant_spec
        manifest = json.loads((STAGE / 'manifest.json').read_text())
        for variant, epochs in VARIANTS.items():
            expected = {'epochs': epochs}
            if variant == 'setH_mb4':
                expected['max_microbatch_size'] = 4
            with self.subTest(variant=variant):
                self.assertEqual(variant_spec(variant)['config_overrides'], expected)
            for key, value in (('learning_rate', 0.001), ('max_microbatch_size', 8 if variant == 'setH_mb4' else 4)):
                changed = copy.deepcopy(manifest)
                changed['variants'][variant]['config_overrides'][key] = value
                with self.subTest(variant=variant, key=key), mock.patch('stage_lib.manifest', return_value=changed):
                    with self.assertRaises(ValueError):
                        variant_spec(variant)

    def test_setH_mb4_rejects_every_undeclared_field(self):
        from stage_lib import validate_config
        config = json.loads((STAGE / 'configs/qwen36_27b_ao_setH_mb4.json').read_text())
        validate_config('setH_mb4', config)
        for key in sorted(set(config) - {'epochs', 'max_microbatch_size'} | {'dataset_root'}):
            with self.subTest(key=key):
                changed = copy.deepcopy(config)
                changed[key] = {'unexpected': True}
                with self.assertRaises(ValueError):
                    validate_config('setH_mb4', changed)
        for key, value in (('epochs', 1), ('max_microbatch_size', 8)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config('setH_mb4', {**config, key: value})

    def test_matched_training_fields(self):
        for variant, epochs in VARIANTS.items():
            with self.subTest(variant=variant):
                config = json.loads((STAGE / 'configs' / ('qwen36_27b_ao_' + variant + '.json')).read_text())
                self.assertEqual(config['epochs'], epochs)
                self.assertEqual(config['world_size'], 4)
                self.assertEqual(config['effective_batch_size'], 32)
                self.assertEqual(config['max_microbatch_size'], 4 if variant == 'setH_mb4' else 8)
                self.assertEqual(config['microbatch_size'], 'auto')
                self.assertEqual(config['parallel'], 'fsdp')
                self.assertNotIn('dataset_root', config)
                self.assertNotIn('split_record', config)

    def test_dataset_rows_hashes_and_filenames(self):
        manifest = json.loads((STAGE / 'manifest.json').read_text())
        self.assertEqual(set(manifest['variants']), set(VARIANTS))
        for variant, epochs in VARIANTS.items():
            with self.subTest(variant=variant):
                selection = manifest['variants'][variant]
                dataset = manifest['datasets'][selection['dataset']]
                fixture = FIXTURES['fullpool' if variant == 'fullpool' else 'setH']
                self.assertEqual(selection['epochs'], epochs)
                self.assertEqual(selection['config'], 'qwen36_27b_ao_' + variant + '.json')
                self.assertEqual(dataset['rows'], fixture['rows'])
                self.assertEqual(dataset['sha256'], fixture['sha256'])
                self.assertEqual(Path(dataset['split_record']).name, 'split_trainer.json')
                self.assertEqual(dataset['rows']['train'] + dataset['rows']['heldout'], dataset['rows']['total'])

    def test_fixture_identity_checks_accept_pins(self):
        from stage_lib import dataset_identity, verify_identity
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                fixture = FIXTURES['fullpool' if variant == 'fullpool' else 'setH']
                verify_identity(dataset_identity(variant), fixture['sha256'], fixture['rows']['total'])

    def test_fixture_identity_checks_reject_each_changed_hash(self):
        from stage_lib import dataset_identity, verify_identity
        for variant in VARIANTS:
            fixture = FIXTURES['fullpool' if variant == 'fullpool' else 'setH']
            for filename in fixture['sha256']:
                with self.subTest(variant=variant, filename=filename):
                    hashes = {**fixture['sha256'], filename: '0' * 64}
                    with self.assertRaises(ValueError):
                        verify_identity(dataset_identity(variant), hashes, fixture['rows']['total'])

    def test_fixture_identity_checks_reject_wrong_rows_and_names(self):
        from stage_lib import dataset_identity, verify_identity
        for variant in VARIANTS:
            fixture = FIXTURES['fullpool' if variant == 'fullpool' else 'setH']
            with self.subTest(variant=variant):
                with self.assertRaises(ValueError):
                    verify_identity(dataset_identity(variant), fixture['sha256'], fixture['rows']['total'] - 1)
                with self.assertRaises(ValueError):
                    verify_identity(dataset_identity(variant), {'other.jsonl': '0' * 64}, fixture['rows']['total'])

    def test_recipe_checker_rejects_microbatch_or_extra_fields(self):
        from stage_lib import validate_config
        config = json.loads((STAGE / 'configs/qwen36_27b_ao_setH.json').read_text())
        for key, value in (('max_microbatch_size', 4), ('dataset_root', '/not/a/training/field')):
            with self.subTest(key=key):
                changed = copy.deepcopy(config)
                changed[key] = value
                with self.assertRaises(ValueError):
                    validate_config('setH', changed)

    def test_publication_identity_and_readme_contract(self):
        identity = json.loads((STAGE / 'manifest.json').read_text())['publication_identity']
        self.assertEqual(identity, {
            'schema': 'student-publication-v1',
            'protocol_version': 'vlm-lora-ddp-v2',
            'base': {'repo_id': 'Qwen/Qwen3.6-27B', 'revision': '6a9e13bd6fc8f0983b9b99948120bc37f49c13e9'},
            'student': 'qwen36_27b',
            'trained_module_families': ['vision', 'merger', 'language'],
            'result_status': 'diagnostic, provisional',
            'provisional_diagnostic': 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW',
            'benchmark_improvement_claim': False,
            'score_nomination_allowed': False,
            'provenance': {'commit': '433d8a117bf94bcd8214de9a6d6e149ff6f5f74f'},
        })
        readme = (STAGE / 'README.md').read_text()
        for literal in (
            '≈9.3h', '≈3.1h', '≈10h upper bound',
            'schema=student-publication-v1', 'protocol_version=vlm-lora-ddp-v2',
            'base.repo_id=Qwen/Qwen3.6-27B',
            'base.revision=6a9e13bd6fc8f0983b9b99948120bc37f49c13e9',
            'student=qwen36_27b', 'trained_module_families=[vision,merger,language]',
            'result_status="diagnostic, provisional"',
            'provisional_diagnostic=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW',
            'benchmark_improvement_claim=false', 'score_nomination_allowed=false',
            'provenance.commit=433d8a117bf94bcd8214de9a6d6e149ff6f5f74f',
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, readme)


if __name__ == '__main__':
    unittest.main()
