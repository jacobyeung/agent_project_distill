import json
from pathlib import Path
import sys
for name in sys.argv[1:]:
    value=json.loads(Path(name).read_text())
    print(name)
    print({k:len(v) if isinstance(v,list) else v for k,v in value.items() if k!='fatal'})
    for field in ('failures','errors'):
        for test, error in value.get(field,[]):
            print(test, error[-5000:])
