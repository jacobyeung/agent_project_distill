import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_intake import intake
_,report=intake(L/'work/tmp/r2_k123nbad/T0_room/MANIFEST.json')
print(json.dumps(report['refusals'],indent=2))
