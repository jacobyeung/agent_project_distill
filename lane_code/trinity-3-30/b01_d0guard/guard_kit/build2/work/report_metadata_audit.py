from pathlib import Path
import json,sys,hashlib
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work';sys.path.insert(0,str(B/'out/guard_kit'))
from guard_core import read,write,sha
root=W/'d0closure';records=[]
for line in (root/'CLOSURE_FILES.sha256').read_text().splitlines():
 h,name=line.split(maxsplit=1);name=name.lstrip('*');p=root/'x'/name.removeprefix('./')
 if not p.is_file():p=root/name
 if not p.is_file():raise ValueError('Per-file closure inventory cannot resolve '+name)
 records.append(dict(file=str(p),expected=h,actual=sha(p),equal=h==sha(p)))
write(B/'out/CLOSURE_FILES_AUDIT.json',dict(status='PASS' if all(r['equal'] for r in records) else 'FAIL',files=records))
print(len(records))
