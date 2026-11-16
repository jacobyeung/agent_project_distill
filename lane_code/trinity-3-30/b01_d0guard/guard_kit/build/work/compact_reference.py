from pathlib import Path
import json,hashlib,sys
B=Path(__file__).resolve().parents[1];sys.path.insert(0,str(B/'out/guard_kit'))
from guard_core import read,write,identity_record,sha
p=B/'out/inputs/reference.json';rows=read(p)
compact=[]
for row in rows:
 x={k:row[k] for k in ('key','arm','question_type','question_unit','checkpoint_sha256','no_answer','scores','room','stratum','called')}
 x['decode']={k:row['decode'][k] for k in ('tokens','text','finish')}
 x['decode']['calls']=[{k:c[k] for k in ('call','kind','response','at_token','forced_tokens','spec_version','spec_revision') if k in c} for c in row['decode']['calls']]
 assert identity_record(x)==identity_record(row);compact.append(x)
write(p,compact)
opaque=read(B/'out/TRINITY_KEY_MAP.json');write(B/'out/inputs/opaque_reference.json',[dict(r,key=opaque[r['key']]) for r in compact])
selection=read(B/'out/ITEM_SELECTION.json');selection['reference_sha256']=sha(p);write(B/'out/ITEM_SELECTION.json',selection)
write(B/'out/REFERENCE_EXTRACTION.json',dict(source=str(B.parents[1]/'work/ret544/native/R1.json'),arm='unflagged',items=len(compact),selection='out/ITEM_SELECTION.json',reference_sha256=sha(p),identity_fields_equal=True,omitted='Large head tensors, geometry arrays, timing and audit detail; tokens, ordered calls, responses and full answer text are exact.'))
