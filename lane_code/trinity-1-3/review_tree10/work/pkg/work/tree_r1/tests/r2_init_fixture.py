from pathlib import Path
import os
from student_pilot.p3_provenance import load, file_pin
ROOT = Path(os.environ.get('R2_FIXTURES', Path(__file__).resolve().parents[3]/'fixtures'))
PIN = file_pin(ROOT/'work/build6/INIT_INPUT.json')
INIT = load(ROOT/'work/build6/INIT_INPUT.json')['identity']
def binding(): return dict(r2_identity=dict(init=INIT))
