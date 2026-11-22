import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,room_report
sys.path.insert(0,sys.argv[1])
from student_pilot.r1_persisted import scope
r=load(sys.argv[2])
with scope(r['_paths']):room_report(load(sys.argv[3]),sys.argv[4])
