set -euo pipefail; umask 077; S=/project/community/jjyeung/okh7/813f42db; test ! -e $S; mkdir -m 700 $S
cat > $S/b.py <<'PYEOF'
"""Rebuild routed deliveries A and B with fresh tokens and an appending fill (runs on Orchard login).
Reads the placed reviewed deliveries, verifies their sha256, changes only: token (9.json, BATCH.sh,
0.json, CONFIG.json, PACKAGE.json), a/4.py slot line (append the preparation archive), and derived
hashes. Writes new delivery dirs and a staging report. Places nothing."""
import gzip, hashlib, io, json, os, sys, tarfile, difflib
from pathlib import Path

K = Path('/project/community/jjyeung/okh7')
S = Path(sys.argv[1])
OLD = {
    'A': dict(token='d72cdcff1e22a', delivery=K/'a15_cot_ap1f6dfa8874e49e1e/1.tgz',
              sha='ca977dd2bc6feb1c14c7c03023eefe7b5e2b67b1cabe838d34effbafd003c765'),
    'B': dict(token='b9188e9225a85', delivery=K/'a15_cot_ap5e8d1fa8216c469d/1.tgz',
              sha='be1f4dec0a2607e0590f0392ef1f7b6c44e3f60c34a06ad6b6a3f3cd551ea3ad'),
}
OLD_SLOT = ("    inputs['archives'][4]=dict(destination=archive['destination'],parts=[prep_archive],\n"
            "                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values())))\n")
NEW_SLOT = ("    inputs['archives'].append(dict(destination=archive['destination'],parts=[prep_archive],\n"
            "                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values()))))\n")
sha = lambda b: hashlib.sha256(b).hexdigest()
jd = lambda v: (json.dumps(v, indent=2, sort_keys=True) + '\n').encode()


def read_tar(raw):
    t = tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz')
    out = [(m, t.extractfile(m).read()) for m in t.getmembers()]
    assert all(m.isfile() for m, _ in out)
    return out


def write_tar(items):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=9, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as t:
            for m, data in items:
                info = tarfile.TarInfo(m.name)
                info.size = len(data); info.mode = m.mode; info.mtime = m.mtime
                info.uid = m.uid; info.gid = m.gid; info.uname = m.uname; info.gname = m.gname
                t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def replace_once(data, old, new, what):
    assert data.count(old) == 1, (what, data.count(old))
    return data.replace(old, new)


report = {}; diff_lines = []
for X, o in OLD.items():
    raw = o['delivery'].read_bytes()
    assert sha(raw) == o['sha'], X
    while True:
        tok = os.urandom(7).hex()[:13]
        if not (K/('a15_cot_ap'+tok)).exists() and tok[0] in '0123456789abcdef': break
    told, tnew = o['token'].encode(), tok.encode()
    items = read_tar(raw); new = []; changed = {}
    files = {m.name: d for m, d in items}
    pay = read_tar(files['0.tgz']); pay_new = []
    for m, d in pay:
        if m.name == '9.json':
            nd = replace_once(d, told, tnew, '9.json')
            assert json.loads(nd)['token'] == tok
            plan = json.loads(nd)
        else:
            assert told not in d, m.name
            nd = d
        pay_new.append((m, nd))
    # Sanity: rebuilding the old payload must change nothing but bytes of 9.json.
    payload = write_tar(pay_new)
    plan_sha = sha(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode())
    for m, d in items:
        n = m.name
        if n == '0.tgz':
            nd = payload
        elif n in ('0.json', 'CONFIG.json'):
            v = json.loads(d); assert jd(v) == d and v['token'] == o['token']
            v.update(token=tok, payload_bytes=len(payload), payload_sha256=sha(payload), plan_sha256=plan_sha)
            nd = jd(v)
        elif n == 'BATCH.sh':
            nd = replace_once(d, told, tnew, 'BATCH.sh')
        elif n == 'a/4.py':
            nd = replace_once(d, OLD_SLOT.encode(), NEW_SLOT.encode(), 'slot')
        elif n == 'PACKAGE.json':
            nd = None
        else:
            assert told not in d, n
            nd = d
        new.append([m, nd])
    newfiles = {m.name: d for m, d in new if d is not None}
    pk = json.loads(files['PACKAGE.json']); assert jd(pk) == files['PACKAGE.json'] and pk['token'] == o['token']
    for name in pk['files']:
        assert sha(files[name]) == pk['files'][name], name
        pk['files'][name] = sha(newfiles[name])
    pk['token'] = tok
    for e in new:
        if e[0].name == 'PACKAGE.json': e[1] = jd(pk)
    newfiles['PACKAGE.json'] = jd(pk)
    delivery = write_tar([tuple(e) for e in new])
    # Diff of every delivery member and every payload member.
    diff_lines.append('=== %s: old token %s -> new token %s\n' % (X, o['token'], tok))
    for m, d in items:
        nd = newfiles[m.name]
        if d == nd: continue
        changed[m.name] = [sha(d), sha(nd)]
        if m.name == '0.tgz':
            for (pm, pd), (_, pn) in zip(pay, pay_new):
                if pd != pn:
                    a = pd.decode(); b = pn.decode(); i = a.index(o['token'])
                    diff_lines.append('--- payload %s (single-line JSON; only differing span)\n-%r\n+%r\n' % (pm.name, a[i-40:], b[i-40:]))
            diff_lines.append('payload members changed: %s\n' % [pm.name for (pm, pd), (_, pn) in zip(pay, pay_new) if pd != pn])
        else:
            diff_lines += list(difflib.unified_diff(d.decode().splitlines(True), nd.decode().splitlines(True),
                                                    'old/'+m.name, 'new/'+m.name, n=0))
    D = K/('a15_cot_ap'+os.urandom(8).hex())
    assert not D.exists(); D.mkdir(mode=0o700)
    (D/'1.tgz').write_bytes(delivery)
    report[X] = dict(old_token=o['token'], token=tok, package=str(K/('a15_cot_ap'+tok)), delivery_dir=str(D),
                     delivery_sha256=sha(delivery), delivery_bytes=len(delivery), payload_sha256=sha(payload),
                     payload_bytes=len(payload), plan_sha256=plan_sha, a4_sha256=sha(newfiles['a/4.py']),
                     changed_members=changed)

# Pre-placement dry slot check: rebuild old A's filled inputs with the fixed slot rule.
old_filled = json.loads((K/'a15_cot_apd72cdcff1e22a/a/1.json').read_text())
base = json.loads((K/'a15_cot_apd72cdcff1e22a/a/0.json').read_text())
sim = json.loads(json.dumps(old_filled))
sim['archives'][4] = base['archives'][4]
sim['archives'].append(old_filled['archives'][4])
(S/'SIM_A_1.json').write_text(json.dumps(sim, indent=2, sort_keys=True) + '\n')
(S/'BUILD.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
(S/'DIFF.txt').write_text(''.join(diff_lines))
print(json.dumps(report, indent=1, sort_keys=True)); print(''.join(diff_lines))
PYEOF
cat > $S/d.py <<'PYEOF'
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
            key = (a['destination'], norm(m.name))
            if m.isfile() and key in owners and owners[key][0] != i:
                out['problems'].append('duplicate member %s in archives %d and %d' % (key[1], owners[key][0], i))
            if key not in owners or m.isfile(): owners[key] = (i, m.type, m.size, m.linkname)
        out['archives'].append(dict(slot=i, sha256=a['sha256'][:8], members=n,
                                    parts=[os.path.basename(os.path.dirname(p['path'])) + '/' + os.path.basename(p['path']) for p in a['parts']]))
    dest = {a['destination'] for a in inputs['archives']}
    assert len(dest) == 1; dest = dest.pop()
    def resolve(logical):
        rel = norm(str(Path(logical).relative_to(Path(LOG) / Path(dest).relative_to('sj'))))
        return owners.get((dest, rel))
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
        rel = norm(str(Path(pf['path']).relative_to(Path(LOG) / Path(dest).relative_to('sj'))))
        m = [m for m in t.getmembers() if norm(m.name) == rel][-1]
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
PYEOF
cat > $S/r.sh <<'SHEOF'
set -euo pipefail
S=$1; A=/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a
/usr/bin/python3 -I -s -B $S/b.py $S > $S/build.out 2>&1
PREP=$(/usr/bin/python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['archives'][4]['sha256'])" $A/a/1.json)
/usr/bin/python3 -I -s -B $S/d.py $S/SIM_A_1.json $A/a/0.json $PREP > $S/dry_sim.out 2>&1 && echo DRYPASS > $S/done.txt || echo DRYFAIL > $S/done.txt
SHEOF
nohup bash $S/r.sh $S </dev/null > $S/r.log 2>&1 &
echo started $S; sha256sum $S/b.py $S/d.py
