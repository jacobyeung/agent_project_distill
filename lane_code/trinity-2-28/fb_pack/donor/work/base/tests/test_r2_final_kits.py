"""Stage the final deliverable directories through the real bounded kit builder."""
import json
import unittest
from student_pilot.p3_provenance import load
from tests.test_r2_data_path import PROOFS, LANE, directory


class FinalKits(unittest.TestCase):
    def test_deliverable_staging(self):
        from launch_r2 import build as B
        from tests.test_r2_build import inputs, dense
        root=directory();dp=dense(root);results=[]
        for name in ('none','gf1'):
            result=B.build(LANE/'work/kit07ca49df_meta/m',root/name,connector=name,records=inputs(),
                dense_manifest=dp if name=='gf1' else None, init_pin=INIT_PIN)
            results.append(dict(result,connector=name))
        self.assertEqual({r['connector'] for r in results},{'none','gf1'})
        self.assertEqual(len({r['source_sha256'] for r in results}),1)
        self.assertTrue(all(not r['admission'] for r in results))
        (PROOFS/'B3_KITS.json').write_text(json.dumps(results))

from tests.r2_init_fixture import PIN as INIT_PIN
