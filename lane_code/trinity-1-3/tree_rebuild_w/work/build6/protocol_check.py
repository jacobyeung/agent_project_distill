"""Read the room-program protocol selected by each staged kit."""
import json
import sys
from pathlib import Path
L=Path(__file__).resolve().parents[2]
B=L/'work/build6'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load
rows=[]
for name in ('a2','a0'):
    root=B/'kits'/name
    launch=load(root/'k/launch.json')
    path=root/launch['config']['file']
    cfg=load(path)
    rows.append(dict(kit=name,trace_program_version=cfg.get('trace_program_version'),
                     source=str(path.relative_to(L))))
(B/'KIT_PROTOCOLS.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
