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
    return replace_once(text, told, tnew, 'BATCH.sh token line')


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
            nd = b'PENDING'
        elif n == 'a/4.py':
            nd = replace_once(d, OLD_SLOT.encode(), NEW_SLOT.encode(), 'slot')
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
                    a = pd.decode(); b = pn.decode(); i = a.index(o['token'])
                    diff_lines.append('--- payload %s (single-line JSON; only differing span)\n-%r\n+%r\n' % (pm.name, a[i-40:], b[i-40:]))
            diff_lines.append('payload members changed: %s\n' % [pm.name for (pm, pd), (_, pn) in zip(pay, pay_new) if pd != pn])
        elif m.name == 'BATCH.sh':
            ol, nl = d.decode().splitlines(), nd.decode().splitlines()
            assert len(ol) == len(nl)
            for i, (a, b) in enumerate(zip(ol, nl)):
                if a != b: diff_lines.append('--- BATCH.sh line %d\n-%s...\n+%s...\n' % (i+1, a[:90], b[:90]))
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
