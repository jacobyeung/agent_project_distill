"""Local review regressions shared by the report suite and mutation runner."""
import unittest

def suite(module):
    class ReviewReport(unittest.TestCase):
        def test_missing_candidate_pin_reports_required_input(self):
            # A missing CONFIG pin must be diagnosed before comparing identities.
            fixture=module.Fixture()
            candidate=fixture.write('candidate.json',fixture.cand)
            baseline=fixture.write('baseline.json',fixture.base)
            with self.assertRaisesRegex(module.G.Refusal,'candidate artifact sha256 is required'):
                module.G.analyze(candidate,baseline,module.LIST,module.LIST_SHA,module.TASKS,
                    module.PARSER,module.PARSER_SHA,candidate_artifact=None)
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReviewReport)
