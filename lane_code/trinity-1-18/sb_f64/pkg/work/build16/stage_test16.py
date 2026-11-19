from pathlib import Path
import os,unittest
from launch_r1.production_proof import verify_staging
from student_pilot.p3_provenance import file_pin

class Staging(unittest.TestCase):
    def test_all_pins(self):
        root=Path(os.environ['R2_PROOFS']);root.mkdir(parents=True,exist_ok=True)
        p=root/'unreferenced.json';p.write_text('{}')
        pin=file_pin(p)
        self.assertEqual(verify_staging({'staged_pins':[pin]}),[pin])
        pin['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
            verify_staging({'staged_pins':[pin]})
