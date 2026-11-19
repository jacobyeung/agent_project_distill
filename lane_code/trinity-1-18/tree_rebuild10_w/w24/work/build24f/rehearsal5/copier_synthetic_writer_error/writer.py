import json,sys
from pathlib import Path
sessions=json.loads(Path(sys.argv[2]).read_text())
assert all(sys.argv[3]+f.part{i:02d}-of-04 in sessions for i in range(4))
import hashlib,json,sys
from pathlib import Path
s,key,p=sys.argv[2:5];raw=Path(p).read_bytes();width=(len(raw)+3)//4
out=Path(s).parent/'objects';out.mkdir(exist_ok=True)
with Path(s+'.receipts.jsonl').open('a') as f:
 for i in range(4):
  part=raw[i*width:(i+1)*width];name=key+f'.part{i:02d}-of-04'
  (out/name.replace('/','_')).write_bytes(part)
  f.write(json.dumps(dict(name=name,bytes=len(part),offset=i*width,sha256=hashlib.sha256(part).hexdigest(),generation=str(i+1)))+'\n')
