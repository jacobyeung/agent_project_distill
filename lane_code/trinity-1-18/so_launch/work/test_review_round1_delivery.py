"""Regression contracts for the review's claims, coverage and packaged artifacts."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TREE = Path(os.environ.get('REVIEW_TREE', ROOT / 'work/tree'))
OUT = ROOT / 'out'


class ReviewDeliveryTests(unittest.TestCase):
    def test_finding_1_production_claim_and_cross_run_design(self):
        for name in ('REPORT.md', 'NOTE_FOR_TREE_REBUILD.md'):
            text = (OUT / name).read_text()
            self.assertFalse(re.search(r'\b120\b', text), name + ': unsupported preparation saving')
            self.assertTrue('01 stays OFF' in text, name + ': keep patch 01 OFF')
            self.assertTrue('cannot hit in the production topology' in text, name + ': production topology warning')
        design = (OUT / 'CROSS_RUN_STORE_DESIGN.md').read_text()
        for required in ('content-addressed', 'every Orchard node', 'field recorder',
                         'unkeyed', 'request.json', 'config.json', 'source seal',
                         'data_receipt.json', 'checkpoint', 'two-node', 'independent',
                         '140.57', '145.27', 'estimate', 'output', 'run_key', 'preparation_output'):
            self.assertIn(required, design)
        self.assertLessEqual(len(design.split()), 1150)

    def test_finding_3_resume_estimate_and_four_call_sites(self):
        for name in ('REPORT.md', 'NOTE_FOR_TREE_REBUILD.md'):
            text = (OUT / name).read_text()
            self.assertTrue(re.search(r'(?i)estimate[^\n]*4[–-]10 min', text), name + ': resume saving estimate missing')
            self.assertIn('03, 04, 02', text)
            self.assertIn('four', text)
        report = (OUT / 'REPORT.md').read_text()
        for required in ('job.sh', 'g.py', 'persistent_launch', 'complete()',
                         'recursive', 'parent', '675', '86', '11-minute'):
            self.assertIn(required, report)

    def test_finding_5_real_stage_and_guard_integration_are_in_delivery(self):
        wrapper = (TREE / 'tests/test_prepared_cache_wrapper.py').read_text()
        self.assertTrue('class RealStageTests' in wrapper, 'real tk_stage integration test is missing')
        self.assertIn('source "$TK_KIT_HOME/b/c.sh"', wrapper)
        memo = (TREE / 'tests/test_checkpoint_verify_memo.py').read_text()
        self.assertIn('test_four_resume_verifications_through_real_guard_and_chooser_processes', memo)

    def test_finding_7_native_gate_selects_all_relevant_modules(self):
        runner = Path(os.environ.get('REVIEW_GATE', ROOT / 'work/run_native_regression.py')).read_text()
        module = ast.parse(runner)
        names = next(ast.literal_eval(node.value) for node in module.body
                     if isinstance(node, ast.Assign) and any(
                         isinstance(t, ast.Name) and t.id == 'names' for t in node.targets))
        for required in ('tests.test_s1_launch_kit', 'tests.test_s1_production_imports',
                         'tests.test_s1_checkpoint_buffers'):
            self.assertIn(required, names)

    def test_finding_8_cache_environment_and_json_names_are_generic(self):
        module = ast.parse((TREE / 'launch_s1/b/pc.py').read_text())
        names = next(ast.literal_eval(node.value) for node in module.body
                     if isinstance(node, ast.Assign) and any(
                         isinstance(t, ast.Name) and t.id == 'ENVIRONMENT' for t in node.targets))
        self.assertEqual(names, ('S1_CPU_REHEARSAL', 'SLURM_CPUS_PER_TASK', 'PYTHONHASHSEED'))
        tests = (TREE / 'tests/test_prepared_input_cache.py').read_text()
        self.assertIn('test_irrelevant_environment_is_absent_from_key_and_written_json_names', tests)

    def test_finding_8_patches_and_manifest_include_review_regressions(self):
        manifest = json.loads((OUT / 'patches/manifest.json').read_text())
        expected = {
            '01_prepared_input_cache.diff': ('test_partial_native_journal_survives_same_path_miss',
                'test_recursive_resume_with_symlinked_parent', 'class RealStageTests'),
            '03_checkpoint_verify_memo.diff': ('test_four_resume_verifications_through_real_guard',),
            '04_launch_phase_timing.diff': ('test_missing_output_directory_does_not_abort',
                'run_p_launch_guard_start'),
        }
        for name, needles in expected.items():
            path = OUT / 'patches' / name
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), manifest[name]['sha256'])
            self.assertEqual(len(data), manifest[name]['bytes'])
            for needle in needles:
                self.assertTrue(needle in data.decode(), name + ': missing ' + needle)
        self.assertIn('launch_s1/b/r.sh', manifest['04_launch_phase_timing.diff']['files'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
