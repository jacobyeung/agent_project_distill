from pathlib import Path
import os
D=Path(__file__).resolve().parent
L=D.parents[1]
R=Path(os.environ.get('REHEARSAL_K2_ROOT',str(D/'rehearsal_k2'))).resolve()
if R not in (D/'rehearsal_k2',D/'rehearsal_k2_probe'):
    raise ValueError('Only the two authorized rehearsal directories are writable')
NS='/tmp/q_22c714e1'

def reseal(kit):
    import json,hashlib,base64
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    files={str(f.relative_to(kit)):sha(f) for f in kit.rglob('*') if f.is_file() and f.name not in ('BUILD.json','SHA256SUMS.txt')}
    (kit/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
    doc=json.loads((kit/'BUILD.json').read_text());value=json.loads(base64.b64decode(doc['payload']))
    value['kit_sha256']=sha(kit/'SHA256SUMS.txt')
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
    (kit/'BUILD.json').write_text(json.dumps(doc))
    return value['kit_sha256']
