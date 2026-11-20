"""Build a small installer that authenticates and links the placed frame archive."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'orchard_tower2x_b'
TOKEN = 'ae63d9b7124fc'
REMOTE = '/project/community/jjyeung/' + TOKEN
SOURCE = '/project/community/jjyeung/ac794e028b16f/8.tgz'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def put(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def main():
    oldpins = json.loads((OLD/'3.json').read_text())
    cfg = json.loads((OLD/'1.json').read_text())
    cfg.update(x0=TOKEN, xl=REMOTE+'/8')
    put(ROOT/'1.json', cfg)
    (ROOT/'BATCH.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexec /usr/bin/python3 -I -s -B '+REMOTE+'/9.py 1 '+REMOTE+'\n')
    small = ['0.py', '1.json', '2.py', '9.py', 'BATCH.sh']
    pins = {n: sha(ROOT/n) for n in small}
    pins['8.tgz'] = oldpins['8.tgz']
    put(ROOT/'3.json', pins)
    small.append('3.json')
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
        for name in small:
            raw = (ROOT/name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o600, 0
            archive.addfile(info, io.BytesIO(raw))
    blob = buffer.getvalue()
    script = '''#!/bin/bash
set -euo pipefail
umask 077
/usr/bin/python3 -I -s -B - <<'PY'
import base64,hashlib,io,json,os,sys,tarfile
from pathlib import Path
def install():
    p=Path(REMOTE)
    source=Path(SOURCE)
    blob=base64.b64decode(ASSETS,validate=True)
    if hashlib.sha256(blob).hexdigest()!=PIN:raise ValueError('E40')
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
        members=t.getmembers()
        if len(members)!=6 or set(m.name for m in members)!=set(NAMES) or any(not m.isfile() for m in members):raise ValueError('E41')
        data={m.name:t.extractfile(m).read() for m in members}
    pins=json.loads(data['3.json'])
    if set(pins)!=set(NAMES)-{'3.json'}|{'8.tgz'}:raise ValueError('E43')
    for n in NAMES:
        if n!='3.json' and hashlib.sha256(data[n]).hexdigest()!=pins[n]:raise ValueError('E43')
    if p.exists():raise ValueError('E44')
    if source.stat().st_size!=44374984:raise ValueError('E45')
    with source.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=pins['8.tgz']:raise ValueError('E46')
    p.mkdir(mode=0o700)
    os.link(source,p/'8.tgz')
    if not os.path.samefile(source,p/'8.tgz'):raise ValueError('E47')
    for n,b in data.items():
        with (p/n).open('xb') as f:f.write(b)
    print(sum(map(len,data.values())))
try:
    install()
except Exception as e:
    code=e.args[0] if e.args and isinstance(e.args[0],str) and e.args[0] in ('E40','E41','E43','E44','E45','E46','E47') else 'E49'
    print(code,file=sys.stderr)
    raise SystemExit(1)
PY
'''
    for key, value in [('REMOTE', REMOTE), ('SOURCE', SOURCE),
                       ('PIN', hashlib.sha256(blob).hexdigest()), ('NAMES', small),
                       ('ASSETS', base64.b64encode(blob).decode())]:
        script = script.replace(key, repr(value))
    (ROOT/'o_place.sh').write_text(script)
    assert len(script.encode()) < 1_000_000
    for name, prefix in [('o_cpu.sh','4'), ('o_check_sub.sh','5')]:
        text = (OLD/name).read_text().replace('ac794e028b16f', TOKEN).replace('--mem=20G', '--mem=200G')
        text = text.replace('--output=/dev/null --error=/dev/null', '--output="$P/'+prefix+'.out" --error="$P/'+prefix+'.stderr"')
        if name == 'o_cpu.sh':
            text = text.replace('$P/0.py 0 $P', '$P/9.py 0 $P')
        else:
            text = text.replace('/usr/bin/python3 -I -s -B "$P/0.py" 2 "$P"',
                                '/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P"')
            # Preflight and GPU use separate files; mode 2 is logged by the supervisor.
        (ROOT/name).write_text(text)
    text=(OLD/'o_fetch.sh').read_text().replace('ac794e028b16f', TOKEN)
    text=text.replace("for n in ('5.json','5.1.json'):t.add(p/n,arcname=n,recursive=False)",
        "for n in ('5.json','5.1.json','4.err','4.out','4.stderr','5.err','5.out','5.stderr','6.err'):\n        if (p/n).is_file():t.add(p/n,arcname=n,recursive=False)")
    (ROOT/'o_fetch.sh').write_text(text)
    (ROOT/'FORECAST.json').write_bytes((OLD/'FORECAST.json').read_bytes())
    reference=json.loads((ROOT.parent.parent/'cap/score_tower2x_b/REFERENCE.json').read_text())
    reference.update(token=TOKEN, input_sha256=sha(ROOT/'1.json'), decode_recording=True)
    put(ROOT/'REFERENCE.json', reference)
    put(ROOT/'BUILD.json', dict(token=TOKEN,path=REMOTE,source=SOURCE,small_files=small,
        bound_files=small+['8.tgz'],added_bytes=sum((ROOT/n).stat().st_size for n in small),
        transport_bytes=len(script.encode()),reused_bytes=44374984,reused_sha256=oldpins['8.tgz'],
        forecast_minutes=json.loads((ROOT/'FORECAST.json').read_text())['estimate_minutes']))
    print((ROOT/'BUILD.json').read_text())


if __name__ == '__main__':
    main()
