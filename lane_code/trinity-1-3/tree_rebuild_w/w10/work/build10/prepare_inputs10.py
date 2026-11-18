"""Stage bounded harness metadata and preserve every source receipt."""
from pathlib import Path
import hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build10';F=L.parent/'w9f'
copies=[]
for p in (L/'work/build9fix/inputs').rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    if p.suffix not in ('.json','.md','.txt','.yaml','.yml','.jsonl'):continue
    if p.stat().st_size>10_000_000:raise ValueError('Metadata copy exceeds bounded size: '+str(p))
    target=B/'inputs'/p.relative_to(L/'work/build9fix/inputs')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(p.read_bytes())
    copies.append(dict(source=str(p),target=str(target),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
rows=json.loads((B/'PACKET_INPUTS.json').read_text())
for row in rows:
    target=L/row['target'];source=L/row['target'].replace('work/build10/','work/build9fix/')
    if not source.exists():source=F/row['source']
    if not source.exists():raise ValueError('Missing packet input '+str(source))
    raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    row['source']=str(target.relative_to(L))
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2)+'\n')
# Paths in copied inputs are local; hashes are refreshed only for local metadata.
for p in (B/'inputs').rglob('*'):
    if p.is_file() and p.suffix in ('.json','.md','.yaml','.txt'):
        text=p.read_text().replace(str(F),str(L)).replace('work/build9fix','work/build10')
        p.write_text(text)
def bind(value):
    if isinstance(value,list):return [bind(v) for v in value]
    if not isinstance(value,dict):return value
    out={k:bind(v) for k,v in value.items()}
    if isinstance(out.get('path'),str) and out.get('sha256'):
        p=Path(out['path'])
        if p.is_absolute() and p.is_relative_to(B/'inputs') and p.is_file():out['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return out
for _ in range(3):
    for p in sorted((B/'inputs').glob('*.json')):
        old=json.loads(p.read_text());new=bind(old)
        if new!=old:p.write_text(json.dumps(new,indent=2)+'\n')
(B/'INPUT_STAGING.json').write_text(json.dumps(copies,indent=2)+'\n')
print(json.dumps(dict(metadata_files=len(copies),packet_inputs=len(rows))))
