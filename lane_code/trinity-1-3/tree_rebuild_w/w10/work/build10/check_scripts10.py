from pathlib import Path
import ast,hashlib,json
B=Path(__file__).resolve().parent;rows=[]
for p in sorted(B.glob('*10.py')):
    raw=p.read_bytes();ast.parse(raw,filename=str(p))
    rows.append(dict(file=p.name,sha256=hashlib.sha256(raw).hexdigest(),syntax='PASS'))
(B/'SCRIPT_SYNTAX.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Current build scripts parse successfully.')
