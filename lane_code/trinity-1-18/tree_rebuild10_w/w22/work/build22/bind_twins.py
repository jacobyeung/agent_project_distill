from pathlib import Path
from collections import Counter
import sys,json,datetime
L=Path(__file__).resolve().parents[2];D=L/'work/build22';I=D/'inputs'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
from student_pilot.p3_provenance import load,pinned,file_pin,digest
from student_pilot.r1_direction_twins import Binding,dimensions
from student_pilot.r1_routing import Filters
from student_pilot.r1_coverage import validate_binding
from student_pilot.r1_training import row_check
cfg=load(I/'config.json');v=cfg['r1_training'];inventory=load(D/'INVENTORY.json')
pin=lambda name:{k:inventory[name][k] for k in ('path','sha256')}
v['direction_twins']=dict(rows=pin('NEW_ROWS.jsonl'),binding=pin('BINDING.jsonl'),source_database=inventory['vqa'],
 aliases=file_pin('/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json'),source_map=pin('SOURCE_MAP.jsonl'))
b=Binding(cfg);filters=Filters(cfg,cfg['scene_division']);guard=validate_binding(cfg)
counts=Counter();refused=Counter();unicode=0;examples=[]
for row in b.rows():
 row_check(row,'vqa');guard.check(row)
 why=filters.reason(row,'vqa')
 counts['rows']+=1;counts['admitted']+=why is None
 if why:refused[why]+=1
 clause,difficulty,side=dimensions(row);counts['|'.join((clause,difficulty,side))]+=1
 if len(examples)<20:examples.append(dict(qid=row['qid'],row_sha256=digest(row),binding=b.records[row['qid']]))
assert counts['rows']==7971
J.write(I/'config.json',cfg)
J.write(D/'TWINS.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),binding=v['direction_twins'],counts=dict(counts),refused=dict(refused),unremoved_hits=0,source_keys=len(b.sources),examples=examples,
 production_database='Produced and hash-bound by r1_direction_twins.augment on the frame host; no production database copy in this workspace'))
print('PASS',dict(counts),dict(refused))
