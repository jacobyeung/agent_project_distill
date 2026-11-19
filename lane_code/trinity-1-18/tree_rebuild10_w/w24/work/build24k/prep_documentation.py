from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for filename in ('PREP_FIELDS.json','PREP_FIELDS.md'):
 p=L/'out'/filename;s=p.read_text().replace('launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run','launch_r1/production_proof.py:run; launch_r1/entry.py:admit; b/h.py; b/rv.py:run').replace('b/a.py:q -> b/i.py:refresh','b/pl.py:plan_payload; b/i.py:refresh')
 p.write_text(s)
p=L/'work/build24k/REHEARSAL_K.md';p.write_text(p.read_text().replace('milestones 2/4','milestone 2 and the step-4 budget-stop export'))
print('Updated source references; preparation allowlist unchanged')
