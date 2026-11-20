import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
import sys
if len(sys.argv)>1 and sys.argv[1] in ('check','submit'):
    for flag,value in (('--gpus','1'),('--time','05:00:00')):
        matches=[i for i,x in enumerate(sys.argv) if x==flag or x.startswith(flag+'=')]
        if not matches:sys.argv.extend([flag,value]);continue
        if len(matches)!=1:raise ValueError('duplicate '+flag)
        i=matches[0];got=sys.argv[i].split('=',1)[1] if '=' in sys.argv[i] else sys.argv[i+1]
        if got!=value:raise ValueError('requires '+flag+' '+value)
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
