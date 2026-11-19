"""Dry stage resolution of a filled inputs list (no extraction): every archive's parts exist with
pinned sizes, every archive's tar headers read, and every pinned file and policy script resolves to
exactly one regular member of the declared size. Usage: dryres.py INPUTS.json [BASE.json] [PREP_SHA]"""
import io, json, os, sys, tarfile
from pathlib import Path

LOG = '/scratch/jjyeung/'


class Cat(io.RawIOBase):
    def __init__(self, parts):
        self.parts = [(p['path'], p['bytes']) for p in parts]; self.size = sum(n for _, n in self.parts)
        self.pos = 0; self.fh = {}
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos
    def readinto(self, b):
        want = len(b); got = 0; start = 0
        for path, n in self.parts:
            if self.pos < start + n and want > got:
                f = self.fh.get(path) or self.fh.setdefault(path, open(path, 'rb'))
                f.seek(self.pos - start); chunk = f.read(min(want - got, start + n - self.pos))
                b[got:got + len(chunk)] = chunk; got += len(chunk); self.pos += len(chunk)
            start += n
        return got


def norm(name):
    while name.startswith('./'): name = name[2:]
    return name.rstrip('/')


def main():
    inputs = json.loads(Path(sys.argv[1]).read_text())
    base = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else None
    out = dict(archives=[], problems=[])
    owners = {}
    for i, a in enumerate(inputs['archives']):
        for p in a['parts']:
            if os.stat(p['path']).st_size != p['bytes']: out['problems'].append('size %d %s' % (i, p['path']))
        t = tarfile.open(fileobj=Cat(a['parts']), mode='r:')
        n = 0
        for m in t:
            n += 1
            key = norm(str(Path(LOG) / Path(a['destination']).relative_to('sj') / norm(m.name)))
            if m.isfile() and key in owners and owners[key][0] != i:
                out['problems'].append('duplicate member %s in archives %d and %d' % (key[1], owners[key][0], i))
            if key not in owners or m.isfile(): owners[key] = (i, m.type, m.size, m.linkname)
        out['archives'].append(dict(slot=i, sha256=a['sha256'][:8], members=n,
                                    parts=[os.path.basename(os.path.dirname(p['path'])) + '/' + os.path.basename(p['path']) for p in a['parts']]))
    def resolve(logical):
        return owners.get(norm(str(Path(logical))))
    found = {}
    for name, f in sorted(inputs['files'].items()):
        o = resolve(f['path'])
        if o is None: out['problems'].append('missing file %s %s' % (name, f['path'])); continue
        slot, typ, size, link = o
        if typ != tarfile.REGTYPE and typ != tarfile.AREGTYPE:
            out['problems'].append('not regular %s type %r link %s' % (name, typ, link))
        elif size != f['bytes']: out['problems'].append('size differs %s %d != %d' % (name, size, f['bytes']))
        found[name] = slot
    for name in ('vnice', 'terminator'):
        o = resolve(inputs['policy'][name])
        if o is None: out['problems'].append('missing policy script ' + name)
        else: found['policy.' + name] = o[0]
    for key in ('python', 'frames_root', 'sam_source'):
        o = resolve(inputs[key]); found[key] = None if o is None else o[0]
    out['resolved_slot'] = found
    pf = inputs['files'][inputs['policy_receipt']]; o = resolve(pf['path'])
    if o is not None:
        a = inputs['archives'][o[0]]; t = tarfile.open(fileobj=Cat(a['parts']), mode='r:')
        pre = Path(LOG) / Path(a['destination']).relative_to('sj')
        m = [m for m in t.getmembers() if norm(str(pre / norm(m.name))) == norm(pf['path'])][-1]
        pol = json.loads(t.extractfile(m).read())
        if pol.get('vnice') != inputs['policy']['vnice'] or pol.get('terminator') != inputs['policy']['terminator'] or pol.get('authorized') is not True:
            out['problems'].append('policy receipt does not authorize the scripts')
        out['policy_receipt_ok'] = not out['problems'] or 'policy receipt' not in out['problems'][-1]
    if base is not None:
        n = len(base['archives'])
        for i in range(1, n):
            if inputs['archives'][i] != base['archives'][i]: out['problems'].append('base slot %d changed' % i)
        if len(inputs['archives']) != n + 1: out['problems'].append('expected %d archives, got %d' % (n + 1, len(inputs['archives'])))
    if len(sys.argv) > 3 and inputs['archives'][-1]['sha256'] != sys.argv[3]:
        out['problems'].append('last slot is not the preparation archive')
    out['passed'] = not out['problems']
    print(json.dumps(out, indent=1, sort_keys=True))
    sys.exit(0 if out['passed'] else 1)


main()