"""Job-side check of a derived kit's new staging entries before b/r.sh stages them (stdlib only).
c.sh tk_stage_tars extracts every member of an archive and verifies only the listed ones, and tk_stage_small places the
sealed small tar e00 first, so later entries could overwrite its members. This script reads the actual bytes:
- every tar entry of KIT/k/0.json that is not byte-identical to an entry of the sealed k/0.json is streamed from its parts;
  each member must be a regular file (no directory, link or device entries) with a safe, unique name, listed in `files`
  or named by a listed full_weights.json manifest, and match that sha256; every listed or manifest-named file must be
  present, and files and manifest must not pin different bytes for one name; if the entry carries a
  whole-stream sha256, the stream must match it;
- no new tar member and no new extra destination may land on a member of e00 (verified against its pin) or on a path a
  sealed entry places.
Prints a JSON summary; exits 3 on any refusal.
Usage: vt.py KIT_DIR SEALED_0_JSON [SEALED_0_SHA256]"""
import hashlib, io, json, sys, tarfile
from pathlib import Path

SEALED_0_SHA = '620a7ed162cd2f9722724be13ef09bae4123b2aba70ea3147fcc25ce91eced83'  # k/0.json of sealed kit 07ca49df
AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
AL = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
X_REL = 'ap/8865619b/'


def refuse(why):
    print(json.dumps(dict(status='REFUSED', reason=why)), flush=True)
    raise SystemExit(3)


def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'))


def safe(n): return isinstance(n, str) and not n.startswith('/') and all(x not in ('', '.', '..') for x in n.split('/'))


def rel(path):
    for prefix in (AS, AL, AS[1:], AL[1:]):
        if path.startswith(prefix): return path[len(prefix):]
    return None


def union_dest(path):
    """Where c.sh hp() puts an extra: AS/X goes into the per-job kit root (not the union), AS and AL into the union."""
    if path.startswith(AS + X_REL): return None
    return rel(path)


class Parts(io.RawIOBase):
    def __init__(self, parts): self.files, self.f, self.h, self.n = list(parts), None, hashlib.sha256(), 0
    def readable(self): return True
    def readinto(self, buf):
        while True:
            if self.f is None:
                if not self.files: return 0
                self.f = open(self.files.pop(0), 'rb')
            data = self.f.read(len(buf))
            if data:
                buf[:len(data)] = data; self.h.update(data); self.n += len(data)
                return len(data)
            self.f.close(); self.f = None


def stream_check(entry, protected):
    raw = Parts(entry['parts']); stream = io.BufferedReader(raw, 8 << 20)
    files, seen, manifests = entry['files'], {}, {}
    with tarfile.open(fileobj=stream, mode='r|') as tin:
        for m in tin:
            if not safe(m.name.rstrip('/')): refuse('unsafe member name ' + m.name)
            if not m.isfile(): refuse('non-regular member (new archives carry regular files only) ' + m.name)
            if m.name in seen: refuse('duplicate member ' + m.name)
            if m.name in protected: refuse('member lands on a sealed placement or e00 member: ' + m.name)
            h, keep = hashlib.sha256(), m.name.endswith('/full_weights.json') and m.name in files
            buf, f = [], tin.extractfile(m)
            for block in iter(lambda: f.read(8 << 20), b''):
                h.update(block)
                if keep: buf.append(block)
            seen[m.name] = h.hexdigest()
            if keep: manifests[m.name] = b''.join(buf)
        stream.read()
    allowed = dict(files)
    for name, data in manifests.items():
        if seen[name] != files[name]: refuse('manifest differs from its pin: ' + name)
        spec, d = json.loads(data.decode()), name.rsplit('/', 1)[0]
        for item in [spec['index']] + spec['files']:
            if not safe(item['name']) or '/' in item['name']: refuse('manifest names a nested path: ' + name)
            k = d + '/' + item['name']
            if k in allowed and allowed[k] != item['sha256']: refuse('files and the manifest pin different bytes for ' + k)
            allowed[k] = item['sha256']
    unexpected = sorted(set(seen) - set(allowed))
    if unexpected: refuse('archive holds members neither listed nor named by a listed manifest: ' + ', '.join(unexpected[:5]))
    absent = sorted(set(allowed) - set(seen))
    if absent: refuse('listed or manifest-named files absent from the archive: ' + ', '.join(absent[:5]))
    wrong = sorted(n for n, v in seen.items() if allowed[n] != v)
    if wrong: refuse('member sha256 differs: ' + ', '.join(wrong[:5]))
    whole = raw.h.hexdigest()
    if entry.get('sha256') and entry['sha256'] != whole: refuse('archive stream differs from its pin: ' + entry['parts'][0])
    return dict(parts=entry['parts'], members=len(seen), bytes=raw.n, sha256=whole)


def main(kit, sealed0, sealed_sha=SEALED_0_SHA):
    if hashlib.sha256(Path(sealed0).read_bytes()).hexdigest() != sealed_sha: refuse('sealed k/0.json differs from its pin')
    cur, base = json.loads((Path(kit) / 'k/0.json').read_text()), json.loads(Path(sealed0).read_text())
    if cur['small'] != base['small']: refuse('the small tar entry changed')
    e00 = Path(cur['small']['file'])
    if hashlib.sha256(e00.read_bytes()).hexdigest() != cur['small']['sha256']: refuse('e00 differs from its pin')
    protected = set()
    with tarfile.open(str(e00), 'r:*') as t:
        for m in t:
            r = rel('/' + m.name.lstrip('/')) if not m.isdir() else None
            if r: protected.add(r)
    for src, dst in (('ap/244cdf20/k/932c0c4e.json', 'ap/f1a2c7e9/k/932c0c4e.json'), ('ap/244cdf20/k/99e6eed6.json', 'ap/f1a2c7e9/k/99e6eed6.json')):
        if src in protected: protected.add(dst)
    base_entries = {enc(e) for e in base.get('tars', []) + base.get('extra', [])}
    for e in base.get('extra', []) + [base['a1rows']]:
        r = union_dest(e['dest'])
        if r: protected.add(r)
    for t in base.get('tars', []): protected |= set(t['files'])
    if enc(cur['a1rows']) != enc(base['a1rows']): refuse('the a1rows entry changed')
    report = dict(status='PASS', protected_paths=len(protected), tars=[], extras=0)
    new_extra = [e for e in cur.get('extra', []) if enc(e) not in base_entries]
    for e in new_extra:
        r = union_dest(e['dest'])
        if r is None or r in protected: refuse('new extra lands on a sealed placement, e00 member or the kit root: ' + e['dest'])
    report['extras'] = len(new_extra)
    for t in cur.get('tars', []):
        if enc(t) in base_entries: continue
        report['tars'].append(stream_check(t, protected))
    print(json.dumps(report, sort_keys=True), flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:])
