"""Check report freshness against recorded real-Git hook evidence."""
from pathlib import Path
import sys
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()


class ReportEvidenceTests(unittest.TestCase):
    def test_f5_report_names_passed_hook_run_and_current_upgrade(self):
        text = (ROOT / 'REPORT.md').read_text()
        self.assertTrue(text.startswith('VERDICT: DONE '))
        self.assertIn('Review round 4: finding -> fix -> test', text)
        self.assertIn('realgit4_by_swarm_opt', text)
        self.assertIn('3 tests, 0 skips', text)
        self.assertIn('realgit5_by_swarm_opt', text)
        self.assertNotIn('await authorized Git execution', text)
        self.assertNotIn('hook cases remain unverified', text)
        self.assertIn('Only `land_kit.py` changes', text)


if __name__ == '__main__':
    unittest.main()
