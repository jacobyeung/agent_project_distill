# BUILD.json of the fixed kit: the original bytes with only the seal (and the payload/sha256 that encode it) replaced.
import sys,json,base64,hashlib
from pathlib import Path
old,new_kit=Path(sys.argv[1]),Path(sys.argv[2])
seal=hashlib.sha256((new_kit/'SHA256SUMS.txt').read_bytes()).hexdigest()
t=old.read_text();o=json.loads(t);raw=base64.b64decode(o['payload'])
d=json.loads(raw);s0=d['kit_sha256'];assert raw.count(s0.encode())==1
raw2=raw.replace(s0.encode(),seal.encode());p2=base64.b64encode(raw2).decode()
assert t.count(o['payload'])==1 and t.count(o['sha256'])==1 and hashlib.sha256(raw).hexdigest()==o['sha256']
t2=t.replace(o['payload'],p2).replace(o['sha256'],hashlib.sha256(raw2).hexdigest())
(new_kit/'BUILD.json').write_text(t2);print('BUILD seal',s0[:8],'->',seal[:8])
