import sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from student_pilot.p3_provenance import load
from student_pilot.r1_persisted import scope
from student_pilot.r2_scene_bindings import rebuild
v=load(sys.argv[1])
with scope(v['paths']):rebuild(v['spec'],v['config'],v['output'])
