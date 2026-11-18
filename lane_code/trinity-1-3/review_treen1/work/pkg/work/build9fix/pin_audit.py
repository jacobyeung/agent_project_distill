from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix';bad=[]
def visit(value,source):
    if isinstance(value,dict):
        if set(value)=={'path','sha256'}:
            p=Path(value['path'])
            if p.is_relative_to(L) and p.is_file():
                actual=hashlib.sha256(p.read_bytes()).hexdigest()
                if actual!=value['sha256']:bad.append(dict(source=str(source),path=str(p),expected=value['sha256'],actual=actual))
        for v in value.values():visit(v,source)
    elif isinstance(value,list):
        for v in value:visit(v,source)
for p in (B/'inputs').glob('*.json'):visit(json.loads(p.read_text()),p)
(B/'PIN_AUDIT.json').write_text(json.dumps(bad,indent=2)+'\n');print(json.dumps(bad))
