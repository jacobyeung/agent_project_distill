"""Run the delivered full envelope with native intake and its mandatory local limit."""
from common import *
seen=start('run_packaged_intake.py')
from student_pilot.r1_persisted import scope
from student_pilot.r2_intake import intake
os.chdir(ROOT)
paths={p.name:str(p) for p in (ROOT/'u').iterdir() if p.is_file()}
for h,p in paths.items():pin(p,h)
p=ROOT/'out/envelopes/camera_wording.json';pin(p)
with scope(paths):items,report=intake(p,limit=2000)
capture(seen)
write('out/PACKAGED_INTAKE.json',report)
print(report['counts'])
