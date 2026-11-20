import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import common
common.J=z
source=(L/'work/build24m4n/recorder_tests.py').read_text()
# Add strict native-loader coverage to the existing real CPU recorder fixture.
source=source.replace("evidence=J.load(root/'f1.json') if (root/'f1.json').exists() else None", "from student_pilot.p3_provenance import load as strict_load\n  evidence=strict_load(root/'f1.json') if (root/'f1.json').exists() else None")
source=source.replace("self.assertEqual(r['finite'],not nonfinite)","self.assertEqual(r['finite'],not nonfinite)\n     if nonfinite:\n      self.assertEqual(r['loss'],'NaN')\n      self.assertIn('/loss',r['nonfinite_values'])")
(D/'recorder_tests.py').write_text(source)
exec(compile(source,str(D/'recorder_tests.py'),'exec'))
