#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aac85ad201020f3.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ac85ad201020f
cd "$P"
(set -C; : > a/2.lock)
job=$(cat a/8.txt); [[ "$job" =~ ^[0-9]+$ ]]
squeue -u jjyeung -h -o '%i' > a/3.txt
if grep -Fxq "$job" a/3.txt; then exit 1; fi
test ! -e a/f
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,runpy,subprocess,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]); job=sys.argv[2]; pub=json.loads((p/'0.json').read_text())
auth=runpy.run_path(str(p/'a/7.py'))
for name,h in json.loads((p/'PACKAGE.json').read_text())['files'].items():
    if auth['digest'](p/name)!=h:raise ValueError('package differs')
with tarfile.open(p/'0.tgz') as t:plan=json.load(t.extractfile('9.json'))
digest=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
if digest!=pub['plan_sha256']:raise ValueError('plan differs')
token=pub['token']+format(int(job),'08x'); source=Path(plan['pool'])/token
ex=json.loads((source/'EXIT.json').read_text()); receipt=json.loads((source/'RETURN_RECEIPT.json').read_text())
auth['validate_exit'](ex,source/'result.tar.gz',digest,token)
if str(ex['job'])!=job:raise ValueError('job differs')
auth['validate_receipt'](receipt,ex,source/'EXIT.json',source/'result.tar.gz',digest,token)
subprocess.run(['/usr/bin/python3','-I','-s','-B',str(p/'3.py'),'fetch','--return-token',token,'--out',str(p/'a/f')],check=True)
dest=p/'a/f'; got=json.loads((dest/'EXIT.json').read_text())
auth['validate_exit'](got,dest/'0.tgz',digest,token)
auth['validate_receipt'](json.loads((dest/'RETURN_RECEIPT.json').read_text()),got,dest/'EXIT.json',dest/'0.tgz',digest,token)
with tarfile.open(dest/'0.tgz') as t:
    names=t.getnames()
    if len(names)!=len(set(names)):raise ValueError('duplicate return member')
    rid=json.load(t.extractfile('metadata/RETURN_ID.json'))
    if rid['token']!=token or str(rid['job'])!=job:raise ValueError('inner identity differs')
    for name in ('CAPTURE.json','PARITY.json'):
        raw=t.extractfile('metadata/'+name).read()
        with (dest/name).open('xb') as f:f.write(raw)
        print(name);print(raw.decode())
PY
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 < /dev/null &
printf 'pid=%s log=%s\n' "$!" "$S.log"
