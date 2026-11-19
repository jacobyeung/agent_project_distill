from pathlib import Path
import json,hashlib,sys,collections
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1';N=L/'work/n1fix2'
O=B/'proofs/preservation';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(N),str(T)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.p3_provenance import load,pinned
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
cfg=load(N/'inputs/config.json');remove=[p for p in cfg['remove_files'] if p['sha256']=='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'];division=cfg['scene_division']
assert len(remove)==1
rows=[];pins=[]
for pin in remove:
    p=pinned(pin);raw=p.read_bytes();pins.append(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest()))
    for line in raw.splitlines():
        row=json.loads(line);dataset,scene=row['scene'].split('/',1)
        rows.append(dict(qid=row['row_key'],dataset=dataset,scene=scene))
assert len(rows)==601
try:check_rows(rows,division)
except ValueError as exc:refusal=str(exc)
else:raise AssertionError('Absent scenes admitted without their exclusion list')
got=check_rows(rows,division,removals=Removals(remove))
assert got['removed']==601 and got['outside']==0
inherited=N/'inherited/proofs/extent_admission/RESULT.json'
record=dict(keys=len(rows),pins=pins,division=division,without_list=refusal,with_list=got,
    inherited_repaired_counts=json.loads(inherited.read_text()),inherited_source=str(inherited.relative_to(L)),
    inherited_sha256=hashlib.sha256(inherited.read_bytes()).hexdigest(),
    limitation='Full repaired-family and production VQA censuses were not rerun. Local proof verifies the exact exclusion list and division refusal only.')
(O/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');monitor.save(O)
print(json.dumps(dict(keys=len(rows),without_list=refusal,with_list=got)))
