set -euo pipefail; umask 077; S=/project/community/jjyeung/okh7/813f42db/r10b; test ! -e $S; mkdir -m 700 $S
cat > $S/b.py <<'PYEOF'
"""Rebuild routed deliveries A and B with fresh tokens and an appending fill (runs on Orchard login).
Reads the placed reviewed deliveries, verifies their sha256, changes only: token (9.json, BATCH.sh,
0.json, CONFIG.json, PACKAGE.json), a/4.py slot line (append the preparation archive), and derived
hashes. Writes new delivery dirs and a staging report. Places nothing."""
import ast, gzip, hashlib, io, json, os, re, sys, tarfile, difflib
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


def bundle_of(batch):
    lines = [l for l in batch.decode().splitlines() if l.startswith('b=bytes.fromhex(')]
    assert len(lines) == 1
    return lines[0], bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))


def rebatch(batch, told, tnew, old_pub, new_pub, operator):
    line, raw = bundle_of(batch)
    items = read_tar(raw)
    assert sorted(m.name for m, _ in items) == ['0.json', '0.py', '7.py']
    out = []
    for m, d in items:
        if m.name == '0.json':
            assert d == old_pub; d = new_pub
        elif m.name == '7.py':
            assert d == operator
        out.append((m, d))
    newline = 'b=bytes.fromhex(%r)' % write_tar(out).hex()
    text = batch.decode(); assert text.count(line) == 1
    text = text.replace(line, newline).encode()
    text = replace_once(text, told, tnew, 'BATCH.sh token line')
    return wrap_batch(text, tnew.decode())


HEAD_OLD = "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\n"
def wrap_batch(text, tok):
    # ORCH ANSWER 0318Z item 2: node-local log, EXIT trap copies node line + exit code + last 60 lines to the package's a/x<job>;
    # USR1 (stop margin) is forwarded to the reader; a failed copy never changes the exit code. #SBATCH exclude: item 3.
    t = text.decode(); assert t.startswith(HEAD_OLD) and t.endswith('\nA\n') and t.count('\nA\n') == 1
    head = ("#!/bin/bash\n#SBATCH --exclude=orchard-community-2\nset -uo pipefail\n"
            "P=/project/community/jjyeung/okh7/a15_cot_ap" + tok + "\nL=/tmp/a${SLURM_JOB_ID:-0}.l\nR=$P/a/x${SLURM_JOB_ID:-0}\n"
            "fin(){ rc=$?; { head -n 1 \"$L\"; echo \"exit $rc\"; tail -n 60 \"$L\"; } > \"$R\" 2>/dev/null || true; exit $rc; }\n"
            "trap fin EXIT\n"
            "echo \"node $(hostname -s) tmp_free_kb $(df -Pk /tmp | awk 'NR==2{print $4}') gpus $(nvidia-smi -L 2>/dev/null | wc -l) cvd ${CUDA_VISIBLE_DEVICES:-none}\" > \"$L\" 2>/dev/null\n"
            "/usr/bin/python3 -I -s -B - >>\"$L\" 2>&1 <<'A' &\n")
    tail = "\nA\nPID=$!\ntrap 'kill -USR1 $PID 2>/dev/null' USR1\nwhile true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done\nexit $rc\n"
    return (head + t[len(HEAD_OLD):-len('\nA\n')] + tail).encode()


def sweep(delivery, old_ids, X):
    # No old identity may survive anywhere: raw members, payload members, the embedded bundle.
    blobs = []
    for m, d in read_tar(delivery):
        blobs.append((m.name, d))
        if m.name == '0.tgz': blobs += [('0.tgz/'+pm.name, pd) for pm, pd in read_tar(d)]
        if m.name == 'BATCH.sh':
            blobs += [('BATCH.sh/bundle/'+bm.name, bd) for bm, bd in read_tar(bundle_of(d)[1])]
    for name, d in blobs:
        for v in old_ids:
            for form in (v.encode(), v.encode().hex().encode()):
                assert form not in d, (X, name, v)
    f = dict(blobs)
    assert f['BATCH.sh/bundle/0.json'] == f['0.json'] and f['BATCH.sh/bundle/7.py'] == f['a/6.py']
    pub = json.loads(f['0.json']); pk = json.loads(f['PACKAGE.json'])
    assert pub['payload_sha256'] == sha(f['0.tgz']) and pub['payload_bytes'] == len(f['0.tgz']) and f['CONFIG.json'] == f['0.json']
    assert all(sha(f[n]) == h for n, h in pk['files'].items()) and pk['token'] == pub['token'] == json.loads(f['0.tgz/9.json'])['token']
    assert re.fullmatch('[a-f][0-9a-f]{10,15}', pub['token'])
    assert ("'a'+j+%r" % pub['token']).encode() in f['BATCH.sh']
    if BIND is not None:
        eb = json.loads(f['0.tgz/9.json'])['export_binding']
        assert eb == {k: BIND[k] for k in KEYS}
        for name, val in (('REVIEWED_OBJECT', repr(BIND['object'])), ('REVIEWED_ARCHIVE_BYTES', str(BIND['archive_bytes'])), ('REVIEWED_ARCHIVE_SHA256', repr(BIND['archive_sha256']))):
            assert ('%s = %s\n' % (name, val)).encode() in f['a/4.py']


BIND = json.loads(Path(sys.argv[3]).read_text()) if len(sys.argv) > 3 else None
KEYS = ('base_identity', 'config_sha256', 'frame_layout', 'lineage', 'member_directory', 'object', 'preparation_sha256', 'run', 'step')


def rebind_plan(d, told, tnew):
    # 9.json is single-line sort_keys JSON; rebuild it in the same format with the new binding.
    v = json.loads(d); assert json.dumps(v, sort_keys=True).encode() == d
    v['token'] = tnew.decode()
    if BIND is not None:
        assert set(v['export_binding']) == set(KEYS)
        v['export_binding'] = {k: BIND[k] for k in KEYS}
    return json.dumps(v, sort_keys=True).encode()


def rebind_fill(d):
    if BIND is None: return d
    old = json.loads(BINDING_OLD)
    for name, a, b in (('REVIEWED_OBJECT', repr(old['object']), repr(BIND['object'])),
                       ('REVIEWED_ARCHIVE_BYTES', str(old['archive_bytes']), str(BIND['archive_bytes'])),
                       ('REVIEWED_ARCHIVE_SHA256', repr(old['archive_sha256']), repr(BIND['archive_sha256']))):
        d = replace_once(d, ('%s = %s\n' % (name, a)).encode(), ('%s = %s\n' % (name, b)).encode(), name)
    return d


BINDING_OLD = json.dumps(dict(object='q8/8865619b/673bc60f_m200.tar', archive_bytes=21583032320,
                              archive_sha256='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'))
report = {}; diff_lines = []
for X, o in OLD.items():
    if X not in sys.argv[2].split(','): continue
    raw = o['delivery'].read_bytes()
    assert sha(raw) == o['sha'], X
    while True:
        tok = os.urandom(7).hex()[:13]
        if not (K/('a15_cot_ap'+tok)).exists() and re.fullmatch('[a-f][0-9a-f]{10,15}', tok): break
    told, tnew = o['token'].encode(), tok.encode()
    items = read_tar(raw); new = []; changed = {}
    files = {m.name: d for m, d in items}
    pay = read_tar(files['0.tgz']); pay_new = []
    for m, d in pay:
        if m.name == '9.json':
            assert d.count(told) == 1
            nd = rebind_plan(d, told, tnew)
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
            nd = b'PENDING'
        elif n == 'a/4.py':
            nd = rebind_fill(replace_once(d, OLD_SLOT.encode(), NEW_SLOT.encode(), 'slot'))
        elif n == 'PACKAGE.json':
            nd = None
        else:
            assert told not in d, n
            nd = d
        new.append([m, nd])
    newfiles = {m.name: d for m, d in new if d is not None}
    oldpub = json.loads(files['0.json'])
    newfiles['BATCH.sh'] = rebatch(files['BATCH.sh'], told, tnew, files['0.json'], newfiles['0.json'], files['a/6.py'])
    for e in new:
        if e[0].name == 'BATCH.sh': e[1] = newfiles['BATCH.sh']
    pk_old_sha = sha(files['PACKAGE.json'])
    pk = json.loads(files['PACKAGE.json']); assert jd(pk) == files['PACKAGE.json'] and pk['token'] == o['token']
    for name in pk['files']:
        assert sha(files[name]) == pk['files'][name], name
        pk['files'][name] = sha(newfiles[name])
    pk['token'] = tok
    for e in new:
        if e[0].name == 'PACKAGE.json': e[1] = jd(pk)
    newfiles['PACKAGE.json'] = jd(pk)
    delivery = write_tar([tuple(e) for e in new])
    old_ids = [o['token'], oldpub['payload_sha256'], oldpub['plan_sha256'], sha(files['0.json']), pk_old_sha]
    if BIND is not None: old_ids += [json.loads(BINDING_OLD)['archive_sha256'], json.loads(BINDING_OLD)['object']]
    sweep(delivery, old_ids, X)
    # Diff of every delivery member and every payload member.
    diff_lines.append('=== %s: old token %s -> new token %s\n' % (X, o['token'], tok))
    for m, d in items:
        nd = newfiles[m.name]
        if d == nd: continue
        changed[m.name] = [sha(d), sha(nd)]
        if m.name == '0.tgz':
            for (pm, pd), (_, pn) in zip(pay, pay_new):
                if pd != pn:
                    ja, jb = json.loads(pd), json.loads(pn)
                    for k in sorted(set(ja) | set(jb)):
                        if ja.get(k) != jb.get(k):
                            diff_lines.append('--- payload %s key %s\n-%s\n+%s\n' % (pm.name, k, json.dumps(ja.get(k), sort_keys=True), json.dumps(jb.get(k), sort_keys=True)))
            diff_lines.append('payload members changed: %s\n' % [pm.name for (pm, pd), (_, pn) in zip(pay, pay_new) if pd != pn])
        elif m.name == 'BATCH.sh':
            ol = [l if not l.startswith('b=bytes.fromhex(') else l[:90]+'...' for l in d.decode().splitlines(True)]
            nl = [l if not l.startswith('b=bytes.fromhex(') else l[:90]+'...' for l in nd.decode().splitlines(True)]
            diff_lines += list(difflib.unified_diff(ol, nl, 'old/BATCH.sh', 'new/BATCH.sh', n=0))
            _, ob = bundle_of(d); _, nb = bundle_of(nd)
            for (bm, bd), (_, bn) in zip(read_tar(ob), read_tar(nb)):
                if bd != bn: diff_lines += list(difflib.unified_diff(bd.decode().splitlines(True), bn.decode().splitlines(True), 'old/BATCH.sh/bundle/'+bm.name, 'new/BATCH.sh/bundle/'+bm.name, n=0))
            diff_lines.append('bundle members changed: %s\n' % [bm.name for (bm, bd), (_, bn) in zip(read_tar(ob), read_tar(nb)) if bd != bn])
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
cat > $S/bind.json <<'JEOF'
{"archive_bytes": 21583032320, "archive_sha256": "dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5", "base_identity": "c202236235762e1c871ad0ccb60c8ee5ba337b9a", "config_sha256": "9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4", "frame_layout": "duplicate", "lineage": "SFT", "member_directory": "m400", "object": "q8/8865619b/6ed2c7aa_m400.tar", "preparation_sha256": {"config": "b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad", "data_receipt": "03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47", "receipt": "a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda"}, "run": "6ed2c7aa", "step": 400}
JEOF
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
PYEOF
cat > $S/d2.py <<'PYEOF'
"""Login-node reproduction of the pure-Python checks of a/5.py and the GPU path that need no staged
environment. Usage: dry2.py PACKAGE WORKDIR. Prints one JSON report; exit 1 on any failure."""
import ast, hashlib, io, json, runpy, sys, tarfile
from pathlib import Path

P = Path(sys.argv[1]); W = Path(sys.argv[2]); W.mkdir(mode=0o700, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
R = {}; bad = []
def check(name, ok, detail=None):
    R[name] = dict(ok=bool(ok), **({'detail': detail} if detail is not None else {}))
    if not ok: bad.append(name)

pub = json.loads((P/'0.json').read_text()); pk = json.loads((P/'PACKAGE.json').read_text())
payload = (P/'0.tgz').read_bytes()
# a/5.py main, before stage
check('5.payload_sha', sha(payload) == pub['payload_sha256'])
check('5.package_descriptor', all(sha((P/n).read_bytes()) == h for n, h in pk['files'].items()))
check('5.sequence_is_a6', pk['files']['a/6.py'] == sha((P/'a/6.py').read_bytes()))
with tarfile.open(fileobj=io.BytesIO(payload)) as t:
    pay = {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
for n, d in pay.items():
    if n.startswith('orchard_h10/'):
        f = W/'pay'/n; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(d)
sys.path.insert(0, str(W/'pay'))
cfg = json.loads(pay['9.json'])
check('5.plan_sha', sha(json.dumps(cfg, sort_keys=True, separators=(',', ':')).encode()) == pub['plan_sha256'])
for rel, pin in cfg['payload_pins'].items():
    if sha(pay[rel]) != pin['sha256']: bad.append('payload_pin ' + rel)
check('stage.payload_pins', not [b for b in bad if b.startswith('payload_pin')], len(cfg['payload_pins']))
inputs = json.loads((P/'a/1.json').read_text())
from orchard_h10 import export_pins
try:
    pins = export_pins.load(inputs, P); check('5.export_pins_load_validate', True)
except Exception as e:
    pins = json.loads((P/'a/export.json').read_text()); check('5.export_pins_load_validate', False, repr(e))
check('prepare.no_optional', not inputs.get('optional'))
check('prepare.types_all_five', inputs.get('types') == cfg['order'], inputs.get('types'))
# stage slot 5: preparation files must exist under d/ (else prepare falls back to the 544 META copies and refuses)
prep_arch = inputs['archives'][-1]
raw = Path(prep_arch['parts'][0]['path']).read_bytes()
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    prep = {m.name: t.extractfile(m).read() for m in t.getmembers()}
want = {s['path']: s for s in pins['preparation'].values()}
check('prepare.prep_members', set(prep) == set(want), sorted(prep))
check('prepare.prep_pins', all(sha(prep[p]) == s['sha256'] and len(prep[p]) == s['bytes'] for p, s in want.items() if p in prep))
check('prepare.prep_vs_binding', all(pins['preparation'][k]['sha256'] == v for k, v in cfg['export_binding']['preparation_sha256'].items()))
check('admit.export_binding', all(pins.get(k) == cfg['export_binding'][k] for k in ('run', 'step', 'member_directory', 'lineage', 'object')))
import re as _re
_rev = _re.search(r"^REVIEWED_ARCHIVE_SHA256 = '([0-9a-f]{64})'$", (P/'a/4.py').read_text(), _re.M).group(1)
check('admit.archive0', pins.get('archive_sha256') == inputs['archives'][0]['sha256'] == _rev, _rev[:8])
# stage policy scripts against ORCHARD_ASSETS, read from the a3.tar slot
assets = json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
a3 = [a for a in inputs['archives'] if a['sha256'].startswith('05dc8f79')]
check('stage.a3_slot_present', len(a3) == 1)
with tarfile.open(a3[0]['parts'][0]['path']) as t:
    q = {m.name.lstrip('./'): t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
check('stage.vnice_sha', sha(q['q/vnice.sh']) == assets['vnice_sha256'])
check('stage.terminator_sha', sha(q['q/terminator.sh']) == assets['terminator_sha256'])
pol = json.loads(q['q/policy.json'])
check('stage.policy_receipt', pol.get('vnice') == inputs['policy']['vnice'] and pol.get('terminator') == inputs['policy']['terminator'] and pol.get('authorized') is True)
env = json.loads(q['q/env.json'])
R['prepare.env_receipt_versions'] = dict(ok=True, detail=env.get('versions'))
# bundle guard (a/5.py check_bundle_guard) and bundle 0.py
batch = (P/'BATCH.sh').read_text()
lines = [l for l in batch.splitlines() if l.startswith('b=bytes.fromhex(')]
braw = bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(braw)) as t:
    bm = {m.name: t.extractfile(m).read() for m in t.getmembers()}
check('guard.inventory', len(lines) == 1 and set(bm) == {'0.py', '0.json', '7.py'})
check('guard.descriptor', json.loads(bm['0.json']) == pub)
check('guard.operator', bm['7.py'] == (P/'a/6.py').read_bytes())
check('guard.tmp_token', ("'a'+j+%r" % pub['token']) in batch)
# post-prepare settings check in a/5.py and a/6.py prepare (settings come from 9.json via prepare.run)
s = dict(stage1_select_rule=cfg.get('stage1_select_rule', 'null_argmax'), perception_memo=cfg.get('perception_memo', 'off'),
         perception_memo_modules=cfg['perception_memo_modules'], perception_memo_verify_ids=cfg.get('perception_memo_verify_ids', []))
check('5.settings_rule', s['stage1_select_rule'] == 'candidates_argmax' and s['perception_memo'] == 'on'
      and s['perception_memo_modules'] == ['g3t'] and s['perception_memo_verify_ids'] == [], s)
op = runpy.run_path(str(P/'a/6.py'), run_name='dry')
check('6.rule_in_RULES', s['stage1_select_rule'] in op['RULES'])
d = op['descriptors'](str(P))
check('6.descriptor', len(d) == 1 and d[0]['stage1_select_rule'] == 'candidates_argmax' and d[0]['perception_memo'] == 'on' and d[0]['expected'] == 636)
mem = op['memory_bound']()
check('6.memory_fits', mem['fits'] is True and mem['basis'] == 'fixed_g3t_shapes' and mem['sam_measurement_required'] is False)
items = json.loads(pay['items/devs1_routed.json'])['items']
from collections import Counter
c = Counter(r['question_type'] for r in items)
check('6.items_636', sum(c.values()) == 636 and c['object_abs_distance'] == 150 and c['room_size_estimation'] == 36
      and all(c[k] == 150 for k in ('camera_displacement', 'camera_rotation', 'camera_movement_direction')), dict(c))
check('6.types_order', [cfg['order'][t] for t in d[0]['types']] == ['object_abs_distance'] + cfg['order'][:3] + ['room_size_estimation'])
# GPU submission path (8.py submit -> BATCH.sh -> bundle 0.py -> job.main): pins it reads
check('sub.job_name', ("a15_cot_ap" + pub['token']) in json.loads((P/'2.json').read_text())['argv'][-1] if (P/'2.json').exists() else False)
R['failed'] = bad; R['passed'] = not bad
print(json.dumps(R, indent=1, sort_keys=True))
sys.exit(0 if not bad else 1)
PYEOF
cat > $S/d2b.py <<'PYEOF'
"""B (room) variant. Login-node reproduction of the pure-Python checks of a/5.py and the GPU path that need no staged
environment. Usage: dry2.py PACKAGE WORKDIR. Prints one JSON report; exit 1 on any failure."""
import ast, hashlib, io, json, runpy, sys, tarfile
from pathlib import Path

P = Path(sys.argv[1]); W = Path(sys.argv[2]); W.mkdir(mode=0o700, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
R = {}; bad = []
def check(name, ok, detail=None):
    R[name] = dict(ok=bool(ok), **({'detail': detail} if detail is not None else {}))
    if not ok: bad.append(name)

pub = json.loads((P/'0.json').read_text()); pk = json.loads((P/'PACKAGE.json').read_text())
payload = (P/'0.tgz').read_bytes()
# a/5.py main, before stage
check('5.payload_sha', sha(payload) == pub['payload_sha256'])
check('5.package_descriptor', all(sha((P/n).read_bytes()) == h for n, h in pk['files'].items()))
check('5.sequence_is_a6', pk['files']['a/6.py'] == sha((P/'a/6.py').read_bytes()))
with tarfile.open(fileobj=io.BytesIO(payload)) as t:
    pay = {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
for n, d in pay.items():
    if n.startswith('orchard_h10/'):
        f = W/'pay'/n; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(d)
sys.path.insert(0, str(W/'pay'))
cfg = json.loads(pay['9.json'])
check('5.plan_sha', sha(json.dumps(cfg, sort_keys=True, separators=(',', ':')).encode()) == pub['plan_sha256'])
for rel, pin in cfg['payload_pins'].items():
    if sha(pay[rel]) != pin['sha256']: bad.append('payload_pin ' + rel)
check('stage.payload_pins', not [b for b in bad if b.startswith('payload_pin')], len(cfg['payload_pins']))
inputs = json.loads((P/'a/1.json').read_text())
from orchard_h10 import export_pins
try:
    pins = export_pins.load(inputs, P); check('5.export_pins_load_validate', True)
except Exception as e:
    pins = json.loads((P/'a/export.json').read_text()); check('5.export_pins_load_validate', False, repr(e))
check('prepare.no_optional', not inputs.get('optional'))
check('prepare.types_room', inputs.get('types') == ['room_size_estimation'], inputs.get('types'))
# stage slot 5: preparation files must exist under d/ (else prepare falls back to the 544 META copies and refuses)
prep_arch = inputs['archives'][-1]
raw = Path(prep_arch['parts'][0]['path']).read_bytes()
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    prep = {m.name: t.extractfile(m).read() for m in t.getmembers()}
want = {s['path']: s for s in pins['preparation'].values()}
check('prepare.prep_members', set(prep) == set(want), sorted(prep))
check('prepare.prep_pins', all(sha(prep[p]) == s['sha256'] and len(prep[p]) == s['bytes'] for p, s in want.items() if p in prep))
check('prepare.prep_vs_binding', all(pins['preparation'][k]['sha256'] == v for k, v in cfg['export_binding']['preparation_sha256'].items()))
check('admit.export_binding', all(pins.get(k) == cfg['export_binding'][k] for k in ('run', 'step', 'member_directory', 'lineage', 'object')))
import re as _re
_rev = _re.search(r"^REVIEWED_ARCHIVE_SHA256 = '([0-9a-f]{64})'$", (P/'a/4.py').read_text(), _re.M).group(1)
check('admit.archive0', pins.get('archive_sha256') == inputs['archives'][0]['sha256'] == _rev, _rev[:8])
# stage policy scripts against ORCHARD_ASSETS, read from the a3.tar slot
assets = json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
a3 = [a for a in inputs['archives'] if a['sha256'].startswith('05dc8f79')]
check('stage.a3_slot_present', len(a3) == 1)
with tarfile.open(a3[0]['parts'][0]['path']) as t:
    q = {m.name.lstrip('./'): t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
check('stage.vnice_sha', sha(q['q/vnice.sh']) == assets['vnice_sha256'])
check('stage.terminator_sha', sha(q['q/terminator.sh']) == assets['terminator_sha256'])
pol = json.loads(q['q/policy.json'])
check('stage.policy_receipt', pol.get('vnice') == inputs['policy']['vnice'] and pol.get('terminator') == inputs['policy']['terminator'] and pol.get('authorized') is True)
env = json.loads(q['q/env.json'])
R['prepare.env_receipt_versions'] = dict(ok=True, detail=env.get('versions'))
# bundle guard (a/5.py check_bundle_guard) and bundle 0.py
batch = (P/'BATCH.sh').read_text()
lines = [l for l in batch.splitlines() if l.startswith('b=bytes.fromhex(')]
braw = bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(braw)) as t:
    bm = {m.name: t.extractfile(m).read() for m in t.getmembers()}
check('guard.inventory', len(lines) == 1 and set(bm) == {'0.py', '0.json', '7.py'})
check('guard.descriptor', json.loads(bm['0.json']) == pub)
check('guard.operator', bm['7.py'] == (P/'a/6.py').read_bytes())
check('guard.tmp_token', ("'a'+j+%r" % pub['token']) in batch)
# post-prepare settings check in a/5.py and a/6.py prepare (settings come from 9.json via prepare.run)
s = dict(stage1_select_rule=cfg.get('stage1_select_rule', 'null_argmax'), perception_memo=cfg.get('perception_memo', 'off'),
         perception_memo_modules=cfg['perception_memo_modules'], perception_memo_verify_ids=cfg.get('perception_memo_verify_ids', []))
s['types'] = inputs.get('types')
check('5.settings_rule', s['stage1_select_rule'] == 'candidates_argmax' and s['perception_memo'] == 'on'
      and s['types'] == ['room_size_estimation'] and s['perception_memo_modules'] == ['g3t'] and s['perception_memo_verify_ids'] == [], s)
op = runpy.run_path(str(P/'a/6.py'), run_name='dry')
check('6.rule_in_RULES', s['stage1_select_rule'] in op['RULES'])
d = op['descriptors'](str(P))
check('6.descriptor', len(d) == 1 and d[0]['stage1_select_rule'] == 'candidates_argmax' and d[0]['perception_memo'] == 'on' and d[0]['expected'] == 134 and d[0]['types'] == [4])
mem = op['memory_bound']()
check('6.memory_fits', mem['fits'] is True and mem['basis'] == 'fixed_g3t_shapes' and mem['sam_measurement_required'] is False)
items = json.loads(pay['items/room134.json'])['items']
from collections import Counter
c = Counter(r['question_type'] for r in items)
check('6.items_134', sum(c.values()) == 134 and c['room_size_estimation'] == 134, dict(c))
check('6.full_reader_items_in_payload', all(n in pay for n in ('items/room134.json',)))
# GPU submission path (8.py submit -> BATCH.sh -> bundle 0.py -> job.main): pins it reads
check('sub.job_name', ("a15_cot_ap" + pub['token']) in json.loads((P/'2.json').read_text())['argv'][-1] if (P/'2.json').exists() else False)
R['failed'] = bad; R['passed'] = not bad
print(json.dumps(R, indent=1, sort_keys=True))
sys.exit(0 if not bad else 1)
PYEOF
/usr/bin/python3 -I -s -B $S/b.py $S A $S/bind.json > $S/build.out 2>&1
/usr/bin/python3 -c "import json;b=json.load(open('$S/BUILD.json'));[print(k,v['token'],v['delivery_dir'],v['delivery_sha256']) for k,v in b.items()]"
