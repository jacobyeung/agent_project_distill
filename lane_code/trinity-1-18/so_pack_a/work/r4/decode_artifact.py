"""Decode a preserved scratch artifact to stdout; validate its recorded SHA256."""
from pathlib import Path
import gzip,hashlib,json,sys
from functools import lru_cache
root=Path(__file__).resolve().parents[2]
entries={}
for name in ('work/r3/STORAGE.json','work/r4/STORAGE.json'):
    p=root/name
    if p.exists():
        for row in json.loads(p.read_text())['files']:entries[row['path']]=row
@lru_cache(maxsize=32)
def block(key):
    value=gzip.decompress((root/'work/r4/blocks'/(key+'.gz')).read_bytes())
    assert hashlib.sha256(value).hexdigest()==key
    return value
@lru_cache(maxsize=16)
def decode(path):
    p=Path(path).resolve();key=str(p.relative_to(root));row=entries.get(key);raw=p.read_bytes()
    if raw.startswith(b'PACKLINES1\n'):row=json.loads(raw.split(b'\n',1)[1])
    elif raw.startswith(b'{'):
        try:
            spec=json.loads(raw)
            if isinstance(spec,dict) and spec.get('encoding')=='PACKREF1':row=spec
        except ValueError:pass
    if row:
        if row['encoding']=='PACKREF1':raw=decode(root/row['reference'])
        elif row['encoding']=='gzip in place':raw=gzip.decompress(raw)
        elif row['encoding']=='PACKLINES1':
            spec=json.loads(raw.split(b'\n',1)[1]);pieces=[]
            for line in spec['lines']:
                if 'text' in line:pieces.append(line['text'].encode('utf-8'))
                else:
                    pieces.append(block(line['block']))
            raw=b''.join(pieces)
        else:raise ValueError('Unknown encoding: '+row['encoding'])
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],key
    return raw
if __name__=='__main__':sys.stdout.buffer.write(decode(sys.argv[1]))
