"""Regression contracts for review findings 4/5 and the production adoption rule."""
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import io, json, os, sys, tempfile, unittest
import torch

torch.set_num_threads(8)
L = Path(__file__).resolve().parents[1]
tempfile.tempdir = os.environ['TMPDIR']
REPORT = (L/'out/REPORT.md').read_text()
NOTE = (L/'out/NOTE_FOR_TREE_REBUILD.md').read_text()
HELPER_CODE = (L/'work/measure_modep.py').read_text()


class ReviewContracts(unittest.TestCase):
    def test_savings_claim_is_bounded_and_explicitly_estimated(self):
        for text in (REPORT, NOTE):
            self.assertIn('≤18.5 min, estimated (possibly 0)', text)
            self.assertNotIn('10–20 minute', text)
        self.assertIn('0.264 * OFF phase_resources.frames.seconds', NOTE)

    def test_scope_exact_switch_lines_and_job_ledger_are_documented(self):
        self.assertIn('Both switches have process-wide scope.', NOTE)
        self.assertIn('generated `<kit>/b/r.sh`', NOTE)
        self.assertIn('export S1_PREP_FAST_PATHS=0', NOTE)
        self.assertIn('export S1_PREP_SELECT_SQL=0', NOTE)
        self.assertIn('both values beside the job ID in `<kit>/o/modep_switches.jsonl`', NOTE)

    def test_real_store_gate_and_comparison_files_are_documented(self):
        for text in (REPORT, NOTE):
            self.assertIn("Both switches OFF on N's first launch.", text)
            self.assertIn('ON from the next launch only after one production launch shows parity on real stores.', text)
            self.assertIn('Review round 1: finding -> fix -> test', text)
        for name in ('frame_inventory.sqlite', 'frames.json', 'vqa_indices.json',
                     'pose_scene_order.json', 'data_receipt.json', 'phase_frames.complete.json'):
            self.assertIn(name, NOTE)

    def test_measurement_helper_uses_off_frame_seconds(self):
        root = Path(tempfile.mkdtemp(prefix='modep_measure_review_'))
        for phase, seconds in [('prepare', 7000), ('frames', 1000)]:
            output = root/phase
            output.mkdir()
            payload = output/'result.json'
            payload.write_text(json.dumps({'resources': {'seconds': seconds, 'peak_rss_kib': 1}}))
            (root/f'phase_{phase}.complete.json').write_text(json.dumps({'payload': {'path': str(payload)}}))
        (root/'prepare/config.json').write_text('{}')
        (root/'frames/frames.json').write_text(json.dumps({'sources': {'vqa': dict(
            rows=1, frame_references=32, unique_frames=32, hash_sample=[{}]*8)}}))
        stdout = io.StringIO()
        with patch.object(sys, 'argv', ['measure_modep.py', str(root)]), redirect_stdout(stdout):
            exec(compile(HELPER_CODE, str(L/'work/measure_modep.py'), 'exec'), {'__name__': '__main__'})
        value = json.loads(stdout.getvalue())
        self.assertEqual(value['estimated_path_saving_seconds'], 264.0)
        self.assertIn('OFF phase_resources.frames.seconds', value['estimate_basis'])


if __name__ == '__main__':
    if '--mutations' not in sys.argv:
        unittest.main(verbosity=2)
    else:
        cases = [
            ('inflated_headline', 'REPORT', REPORT.replace('≤18.5 min, estimated (possibly 0)', '10–20 minutes'),
             'test_savings_claim_is_bounded_and_explicitly_estimated'),
            ('wrong_multiplier', 'HELPER_CODE', HELPER_CODE.replace('0.264*', '0.3*'),
             'test_measurement_helper_uses_off_frame_seconds'),
            ('missing_scope', 'NOTE', NOTE.replace('Both switches have process-wide scope.', ''),
             'test_scope_exact_switch_lines_and_job_ledger_are_documented'),
            ('missing_sql_line', 'NOTE', NOTE.replace('export S1_PREP_SELECT_SQL=0', ''),
             'test_scope_exact_switch_lines_and_job_ledger_are_documented'),
            ('missing_ledger', 'NOTE', NOTE.replace('<kit>/o/modep_switches.jsonl', ''),
             'test_scope_exact_switch_lines_and_job_ledger_are_documented'),
            ('premature_enable', 'NOTE', NOTE.replace("Both switches OFF on N's first launch.",
                                                    "Enable switches on N's first launch."),
             'test_real_store_gate_and_comparison_files_are_documented'),
        ]
        results = []
        for name, variable, value, method in cases:
            with patch.object(sys.modules[__name__], variable, value):
                log = L/'out/tests'/('review1_contract_mutant_'+name+'.log')
                with log.open('w') as stream:
                    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
                        unittest.TestSuite([ReviewContracts(method)]))
            assert len(result.failures) == 1 and not result.errors, name
            results.append(dict(mutation=name, failures=len(result.failures), errors=len(result.errors), log=str(log)))
            print('CONTRACT_MUTATION_CAUGHT '+name+' failures=1 errors=0', flush=True)
        (L/'out/tests/review1_contract_mutations.json').write_text(json.dumps(results, indent=2)+'\n')
