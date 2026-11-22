"""Write kit/o_patch.sh: replace only the files fix 1 changed under the placed package, keeping each old
file as <name>.pre1 (never deleting), and move the old CPU receipt 2.json (bound to the old PACKAGE.json)
to 2.json.pre1 so o_check.sh can write a fresh one."""
import base64, gzip, hashlib, json, sys
from pathlib import Path
NFA = Path('/scratch/jjyeung/orch_n30/lever7/nfa')
OLD, NEW = NFA / 'fix1/pre/pkg', NFA / 'kit/pkg'
TOKEN = (NFA / 'kit/TOKEN').read_text().strip()
sha = lambda b: hashlib.sha256(b).hexdigest()
NAMES = ('a/6.py', 'BATCH.sh', 'PACKAGE.json')   # PACKAGE.json last
files = {}
for n in NAMES:
    old, new = (OLD / n).read_bytes(), (NEW / n).read_bytes()
    assert old != new, n
    files[n] = dict(old=sha(old), new=sha(new), mode=0o700 if n == 'BATCH.sh' else 0o600,
                    b64=base64.b64encode(gzip.compress(new, mtime=0)).decode())
pins = json.loads((NEW / 'PACKAGE.json').read_text())['files']
for n, h in pins.items():
    assert sha((NEW / n).read_bytes()) == h, n
spec = json.dumps({n: {k: v for k, v in f.items() if k != 'b64'} for n, f in files.items()}, sort_keys=True)
data = '{' + ','.join("%r:base64.b64decode('%s')" % (n, f['b64']) for n, f in files.items()) + '}'
text = """#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/%s
test -e "$P/PACKAGE.json"
test ! -e "$P/a/70.txt"
q=$(squeue -u jjyeung -h -o '%%j' | grep '^a15_cot_ap%s' || true)
test -z "$q"
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import base64,gzip,hashlib,json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);spec=json.loads(%r);h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
order=%r
blobs=%s
for n in order:
    if h(p/n)!=spec[n]['old']:raise SystemExit('E81 '+n+' is not the placed pre-fix file')
    if os.path.lexists(str(p/n)+'.pre1'):raise SystemExit('E82 '+n+'.pre1 exists')
if os.path.lexists(str(p/'2.json')+'.pre1'):raise SystemExit('E82 2.json.pre1 exists')
for n in order:
    data=gzip.decompress(blobs[n])
    if hashlib.sha256(data).hexdigest()!=spec[n]['new']:raise SystemExit('E83 '+n)
    os.rename(p/n,str(p/n)+'.pre1')
    fd=os.open(p/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL,spec[n]['mode'])
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    got=h(p/n)
    if got!=spec[n]['new'] or h(Path(str(p/n)+'.pre1'))!=spec[n]['old']:raise SystemExit('E84 '+n)
    print(n,got,'kept',n+'.pre1',spec[n]['old'])
if (p/'2.json').exists():
    os.rename(p/'2.json',str(p/'2.json')+'.pre1');print('2.json moved to 2.json.pre1; run o_check.sh next')
pins=json.loads((p/'PACKAGE.json').read_text())['files']
bad=[n for n,v in pins.items() if h(p/n)!=v]
if bad:raise SystemExit('E85 pins differ: '+' '.join(bad))
print('pins ok',len(pins))
PY
""" % (TOKEN, TOKEN, spec, list(NAMES), data)
out = NFA / 'kit/o_patch.sh'
out.write_text(text)
print(out, len(text.encode()), 'bytes', {n: (v['old'][:12], v['new'][:12]) for n, v in files.items()})
