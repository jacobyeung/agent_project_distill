"""Expose the actual source-bound receipt from the native synthetic packet run."""
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
read=lambda p:json.loads(p.read_text())
proof=read(L/'out/B3_NATIVE_JOB_PROOF.json')
pin=proof['packet'];path=Path(pin['path'])
if hashlib.sha256(path.read_bytes()).hexdigest()!=pin['sha256']:
    raise ValueError('Fixture packet hash differs')
packet=read(path);result=path.parent/packet['output']/'0.json'
value=read(result)
(L/'out/B3_HOST_STATEMENT_PROOF.json').write_text(json.dumps(dict(synthetic=True,full_store=False,
    packet=pin,result={'path':str(result),'sha256':hashlib.sha256(result.read_bytes()).hexdigest()},
    statements=value['statements']),indent=2)+'\n')
