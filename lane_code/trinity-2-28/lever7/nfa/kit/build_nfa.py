"""Build the NF-A package from package b9ef552934627 (local copy of its placed files).

Reused unchanged: every payload file except 9.json (the plan, which carries the token), the
bootstrap 0.py, 3.py, SUBMIT.cmd, INPUTS.example.json, a/1.json (inputs already on Orchard) and
a/export.json. New: token, 9.json, 0.json, CONFIG.json, BATCH.sh (bundles the new operator as 7.py),
PACKAGE.json, a/5.py (CPU check) and a/6.py (operator).
`--token b9ef552934627 --operator <parent a/6.py> --cpu <parent a/5.py>` must reproduce the parent.
"""
import argparse
import base64
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN_RE = '[a-f][0-9a-f]{10,15}'
SMALL = ('0.json', '3.py', 'BATCH.sh', 'CONFIG.json', 'INPUTS.example.json', 'PACKAGE.json', 'SUBMIT.cmd')
PRIVATE = ('a/1.json', 'a/5.py', 'a/6.py', 'a/export.json')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def tar_bytes(files):
    sys.path.insert(0, str(HERE.parent / 'ref/payload/orchard_h10/vendor'))
    import orchard_launcher
    return orchard_launcher.tar_bytes(files)


def write_json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def render_operator(items_path):
    d = json.loads(Path(items_path).read_text())
    text = (HERE / 'src/op.py.in').read_text()
    wrapper = (HERE / 'src/w.py').read_text()
    for key, value in (('@IDX@', json.dumps(d['forward_indices'])), ('@FSHA@', d['forward_ids_sha256']),
                       ('@RSHA@', d['reverse_ids_sha256']), ('@WRAPPER@', repr(wrapper))):
        if text.count(key) != 1:
            raise ValueError('template slot differs: ' + key)
        text = text.replace(key, value)
    return text.encode()


def build(parent, token, operator, cpu, out):
    parent = Path(parent)
    if not re.fullmatch(TOKEN_RE, token):
        raise ValueError('token form differs')
    raw = (parent / '0.tgz').read_bytes()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        files = {e.name: archive.extractfile(e).read() for e in archive if e.isfile()}
    if tar_bytes(files) != raw:
        raise ValueError('parent payload is not reproducible')
    cfg = json.loads(files['9.json'])
    if files['9.json'] != json.dumps(cfg, sort_keys=True).encode():
        raise ValueError('plan encoding differs')
    holders = [n for n, v in files.items() if cfg['token'].encode() in v]
    if holders != ['9.json']:
        raise ValueError('token appears outside the plan: %r' % holders)
    cfg['token'] = token
    files['9.json'] = json.dumps(cfg, sort_keys=True).encode()
    payload = tar_bytes(files)
    public = dict(payload_bytes=len(payload), payload_sha256=sha(payload), plan_sha256=canonical(cfg), token=token)
    zero = (json.dumps(public, sort_keys=True) + '\n').encode()
    batch_old = (parent / 'BATCH.sh').read_text()
    m = re.search(r"bytes\.fromhex\('([0-9a-f]+)'\)", batch_old)
    with tarfile.open(fileobj=io.BytesIO(bytes.fromhex(m.group(1)))) as archive:
        bundle_old = {e.name: archive.extractfile(e).read() for e in archive}
    if set(bundle_old) != {'0.py', '0.json', '7.py'}:
        raise ValueError('parent bundle inventory differs')
    bundle = tar_bytes({'0.py': bundle_old['0.py'], '0.json': zero, '7.py': operator})
    old_token = json.loads(bundle_old['0.json'])['token']
    head, tail = batch_old[:m.start(1)], batch_old[m.end(1):]
    if tail.count("+'%s')" % old_token) != 1:
        raise ValueError('batch token slot differs')
    batch = head + bundle.hex() + tail.replace("+'%s')" % old_token, "+'%s')" % token)
    placed = {'0.tgz': payload, '0.json': zero, 'CONFIG.json': write_json(public), 'BATCH.sh': batch.encode(),
              '3.py': (parent / '3.py').read_bytes(), 'SUBMIT.cmd': (parent / 'SUBMIT.cmd').read_bytes(),
              'INPUTS.example.json': (parent / 'INPUTS.example.json').read_bytes(),
              'a/1.json': (parent / 'a/1.json').read_bytes(), 'a/export.json': (parent / 'a/export.json').read_bytes(),
              'a/5.py': cpu, 'a/6.py': operator}
    pins = {n: sha(placed[n]) for n in ('0.json', '0.tgz', '3.py', 'BATCH.sh', 'CONFIG.json', 'a/5.py', 'a/6.py')}
    placed['PACKAGE.json'] = write_json(dict(files=pins, token=token))
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=False)
        for name, data in placed.items():
            path = out / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return placed, public


def place_script(placed, token):
    """One self-checking transfer: refuses an existing package, writes, re-hashes, prints placed bytes."""
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz', format=tarfile.USTAR_FORMAT) as t:
        for name in sorted(placed):
            info = tarfile.TarInfo(name)
            info.size = len(placed[name]); info.mode = 0o700 if name == 'BATCH.sh' else 0o600; info.mtime = 0
            t.addfile(info, io.BytesIO(placed[name]))
    encoded = base64.b64encode(archive.getvalue()).decode()
    sums = {n: sha(v) for n, v in placed.items()}
    total = sum(len(v) for v in placed.values())
    text = """#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/%s
test ! -e "$P"
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import base64,hashlib,io,json,os,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);sums=json.loads(%r);total=%d
raw=base64.b64decode(%r)
p.mkdir(mode=0o700);(p/'a').mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
    for e in t:
        if not e.isfile() or e.name not in sums or '..' in Path(e.name).parts:raise SystemExit('E61')
        data=t.extractfile(e).read()
        if hashlib.sha256(data).hexdigest()!=sums[e.name]:raise SystemExit('E62')
        fd=os.open(p/e.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o700 if e.name=='BATCH.sh' else 0o600)
        with os.fdopen(fd,'wb') as f:f.write(data)
got={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in sums}
if got!=sums:raise SystemExit('E63')
print(sum((p/n).stat().st_size for n in sums) if sum((p/n).stat().st_size for n in sums)==total else 'E64')
PY
""" % (token, json.dumps(sums, sort_keys=True), total, encoded)
    return text, total


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', required=True); p.add_argument('--token', required=True)
    p.add_argument('--items'); p.add_argument('--operator'); p.add_argument('--cpu')
    p.add_argument('--out'); p.add_argument('--place')
    a = p.parse_args()
    operator = Path(a.operator).read_bytes() if a.operator else render_operator(a.items)
    cpu = Path(a.cpu).read_bytes() if a.cpu else (HERE / 'src/c.py').read_bytes()
    placed, public = build(a.parent, a.token, operator, cpu, a.out)
    if a.place:
        text, total = place_script(placed, a.token)
        Path(a.place).write_text(text)
    print(json.dumps(dict(public=public, files={n: sha(v) for n, v in sorted(placed.items())},
                          bytes=sum(len(v) for v in placed.values())), indent=1, sort_keys=True))
