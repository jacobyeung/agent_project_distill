import hashlib,json,tarfile,sys
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
if len(sys.argv)>1 and sys.argv[1]=='fetch':
    raw=(p/'a/7.py').read_bytes()
    manifest=json.loads((p/'PACKAGE.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=manifest['files']['a/7.py']:
        raise ValueError('Fetch helper differs')
    sys.argv[1:]=['--package',str(p)]+sys.argv[2:]
    exec(compile(raw,str(p/'a/7.py'),'exec'),dict(__name__='__main__',__file__=str(p/'a/7.py')))
    raise SystemExit(0)
if len(sys.argv)>1 and sys.argv[1] in ('check','submit'):
    for flag,value in (('--gpus','1'),('--time','01:23:45')):
        matches=[i for i,x in enumerate(sys.argv) if x==flag or x.startswith(flag+'=')]
        if not matches:sys.argv.extend([flag,value]);continue
        if len(matches)!=1:raise ValueError('Duplicate '+flag)
        i=matches[0];got=sys.argv[i].split('=',1)[1] if '=' in sys.argv[i] else sys.argv[i+1]
        if got!=value:raise ValueError('H requires '+flag+' '+value)
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
