import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_scene_bindings import merge
from student_pilot.p3_provenance import file_pin, encoded
dev=file_pin(L/'work/kit07ca49df_meta/m/k/dev_scene_exclusions.json')
rooms=file_pin(L/'work/shared/WITHHELD_ROOMS_80.json')
value=merge(dev,rooms)
p=L/'work/tree_r1/student_pilot/r2_dev_merged.json'
p.write_text(encoded(value)+'\n')
(L/'out/B3B_MERGED_BINDING.json').write_text(json.dumps(dict(inputs=[dev,rooms],merged=file_pin(p)),indent=2)+'\n')
print(json.dumps(file_pin(p)))
