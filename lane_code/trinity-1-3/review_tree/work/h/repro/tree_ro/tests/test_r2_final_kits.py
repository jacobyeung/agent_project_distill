"""Stage the final deliverable directories through the real bounded kit builder."""
import runpy
import unittest
from student_pilot.p3_provenance import load
from tests.test_r2_data_path import LANE


class FinalKits(unittest.TestCase):
    def test_deliverable_staging(self):
        runpy.run_path(str(LANE/'work/build3/finish_kits.py'),run_name='__main__')
        results=load(LANE/'out/B3_KITS.json')
        self.assertEqual({r['connector'] for r in results},{'none','gf1'})
        self.assertEqual(len({r['source_sha256'] for r in results}),1)
        self.assertTrue(all(r['tmp_before']==r['tmp_after'] and r['tmp_after']<=200000000 for r in results))
        self.assertTrue(all(not r['admission'] for r in results))
