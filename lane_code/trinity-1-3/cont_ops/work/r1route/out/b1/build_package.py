"""Reseal reviewed payload bytes, changing only the token in the plan."""
from pathlib import Path
import hashlib,json,sys,tarfile
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O/'src'))
from orchard_h10.common import canonical,sha,template,valid_token,write
from orchard_h10.build import batch
template(O/'src/orchard_h10/vendor')
import orchard_launcher as L
P=O/'package';token=valid_token((O/'TOKEN').read_text().strip())
with tarfile.open(O/'original/0.tgz') as archive:
    payload={m.name:archive.extractfile(m).read() for m in archive}
cfg=json.loads(payload['9.json']);cfg['token']=token
payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
raw=L.tar_bytes(payload)
(P/'0.tgz').write_bytes(raw);(O/'0.tgz').write_bytes(raw)
(O/'src/9.json').write_bytes(payload['9.json'])
public=dict(token=token,payload_sha256=sha(P/'0.tgz'),payload_bytes=len(raw),plan_sha256=canonical(cfg))
(P/'0.json').write_text(json.dumps(public,sort_keys=True)+'\n')
write(P/'CONFIG.json',public)
manifest=json.loads((P/'PACKAGE.json').read_text());manifest['token']=token
manifest['files']={name:sha(P/name) for name in manifest['files']}
write(P/'PACKAGE.json',manifest)
write(O/'BUILD.json',dict(token=token,code_bytes=len(raw),plan=canonical(cfg),
                        changed_payload_members=['9.json'],operator_path='7.py'))
print(json.dumps(public,sort_keys=True))
