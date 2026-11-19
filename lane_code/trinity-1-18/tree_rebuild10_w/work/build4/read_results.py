import json
import sys
from pathlib import Path
for name in sys.argv[1:]:
    p=Path(name)
    if not p.exists():
        continue
    r=json.loads(p.read_text())
    print(name, {k:len(v) if isinstance(v,list) else v for k,v in r.items() if k!='tmp_bytes'})
    for key in ('failures','errors'):
        for test, message in r.get(key,[]):
            print(test, '\n', message[-1800:])
