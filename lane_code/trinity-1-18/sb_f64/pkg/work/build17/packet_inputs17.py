"""Bind the packet's existing local fixtures by their supplied hashes."""
from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build17';rows=json.loads((L/'work/build14/PACKET_INPUTS.json').read_text())
for r in rows:
    p=L/r['target'];assert p.is_file()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    r['source']=r['target'];r['target']=r['target'].replace('work/build14/proofs/final','work/build17/proofs/final')
    q=L/r['target'];q.parent.mkdir(parents=True,exist_ok=True)
    if not q.exists():q.symlink_to(p)
    assert hashlib.sha256(q.read_bytes()).hexdigest()==r['sha256']
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2))
print('Bound packet fixtures:',len(rows))
