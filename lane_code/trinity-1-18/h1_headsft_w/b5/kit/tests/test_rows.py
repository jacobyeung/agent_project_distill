import json
from pathlib import Path
import unittest
from rows.expected_calls import expected_calls,actual_calls
from rows.faithful_check import check
from rows.mix_h1 import build,NEEDS_64
from tests.fixtures import K

class Rows(unittest.TestCase):
    def test_expected_calls(self):
        n=0
        for name in ('camera_fixtures.jsonl','a0_units.jsonl'):
            for s in (K/'rows'/name).read_text().splitlines():
                r=json.loads(s);self.assertEqual(expected_calls(r['question'],r['question_type']),actual_calls(r));n+=1
        self.assertEqual(n,14)
    def test_configs_keep_d0(self):
        base,outputs=build()
        for c in outputs.values():
            self.assertEqual(c['streams'],base['streams']);self.assertEqual(c['init_artifact'],base['init_artifact'])
            self.assertEqual(c['recipe']['mix'],base['recipe']['mix']);self.assertEqual(c['recipe']['seed'],17)
            self.assertEqual(c['recipe']['steps'],1000);self.assertEqual(c['recipe']['milestones'],[100,200])
        with self.assertRaisesRegex(ValueError,'64 frames refused'):build(64)
        self.assertEqual(len(NEEDS_64),7)
    def test_checker_refusal_denominator(self):
        r=json.loads((K/'rows/camera_fixtures.jsonl').read_text().splitlines()[0])
        report=check([r,{**r,'trace_revision':'unsupported'}])
        self.assertEqual(report['identity_rate'],.5);self.assertEqual(report['refusal_reasons'],{'invalid_trace_revision':1})
