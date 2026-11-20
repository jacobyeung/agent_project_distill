"""Render opaque, streamed Orchard scripts for the sealed delivery."""
import base64
import json
from pathlib import Path
from build import ROOT, jd


def background(token, number, body):
    return '''#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aTOKENNUMBER.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/TOKEN
BODYTEXT
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 < /dev/null &
printf 'pid=%s log=%s\\n' "$!" "$S.log"
'''.replace('BODYTEXT', body).replace('TOKEN', token).replace('NUMBER', number)


def render():
    info = json.loads((ROOT/'out/BUILD.json').read_text()); token = info['token']
    b64 = base64.b64encode((ROOT/'out/delivery.tgz').read_bytes()).decode()
    meta = base64.b64encode(jd(info)).decode()
    body = '''/usr/bin/python3 -I -s -B - <<'PY'
import base64,hashlib,io,json,os,tarfile
from pathlib import Path
raw=base64.b64decode('DELIVERY')
build_raw=base64.b64decode('DESCRIPTOR'); build=json.loads(build_raw)
p=Path(build['package'])
if p.exists():raise ValueError('destination exists')
if hashlib.sha256(raw).hexdigest()!=build['delivery_sha256']:raise ValueError('delivery differs')
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    members=t.getmembers()
    if len(members)!=len(build['files']) or {m.name for m in members}!=set(build['files']):raise ValueError('inventory differs')
    total=len(raw)+len(build_raw)+sum(m.size for m in members)
    if total>50_000_000:raise ValueError('placement exceeds 50 MB')
    for m in members:
        if not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts:raise ValueError('unsafe member')
        if hashlib.sha256(t.extractfile(m).read()).hexdigest()!=build['files'][m.name]:raise ValueError('file differs')
    with tarfile.open(fileobj=io.BytesIO(t.extractfile('0.tgz').read())) as inner:
        contents=inner.getmembers()
        if len(contents)!=len(build['payload_files']) or {m.name for m in contents}!=set(build['payload_files']):raise ValueError('payload inventory differs')
        for m in contents:
            if not m.isfile() or hashlib.sha256(inner.extractfile(m).read()).hexdigest()!=build['payload_files'][m.name]:raise ValueError('payload member differs')
        plan=json.load(inner.extractfile('9.json'))
        if hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=build['plan_sha256']:raise ValueError('plan differs')
    p.mkdir(mode=0o700)
    for m in members:
        path=p/m.name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with path.open('xb') as f:f.write(t.extractfile(m).read())
    (p/'BUILD.json').write_bytes(build_raw)
    for n,h in build['files'].items():
        with (p/n).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=h:raise ValueError('installed file differs')
print(json.dumps(dict(package=str(p),verified=True,added_bytes=total)))
PY'''.replace('DELIVERY',b64).replace('DESCRIPTOR',meta)
    (ROOT/'orchard/o_place.sh').write_text(background(token,'0',body))
    body = '''cd "$P"
(set -C; : > a/0.lock)
test ! -e a/c
test ! -e a/4.txt
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
reply=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --job-name=a15_cot_apTOKEN --cpus-per-task=8 --mem=200G --time=05:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\\n' "$job" > a/4.txt
cat a/4.txt'''.replace('TOKEN',token)
    (ROOT/'orchard/o_cpu.sh').write_text(background(token,'1',body))
    body = '''cd "$P"
(set -C; : > a/1.lock)
test ! -e a/8.txt
/usr/bin/python3 -I -s -B a/9.py "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
squeue -u jjyeung -p general -h > a/9.txt
test ! -s a/9.txt
reply=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\\n' "$job" > a/8.txt
cat a/8.txt'''
    (ROOT/'orchard/o_check_sub.sh').write_text(background(token,'2',body))
    body = '''cd "$P"
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
PY'''
    (ROOT/'orchard/o_fetch.sh').write_text(background(token,'3',body))
    return token


if __name__ == '__main__': print(render())
