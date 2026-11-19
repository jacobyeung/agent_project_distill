set -euo pipefail; umask 077; S=/project/community/jjyeung/okh7/813f42db/r6; test ! -e $S; mkdir -m 700 $S
cat > $S/b.py <<'PYEOF'
"""Rebuild routed deliveries A and B with fresh tokens and an appending fill (runs on Orchard login).
Reads the placed reviewed deliveries, verifies their sha256, changes only: token (9.json, BATCH.sh,
0.json, CONFIG.json, PACKAGE.json), a/4.py slot line (append the preparation archive), and derived
hashes. Writes new delivery dirs and a staging report. Places nothing."""
import gzip, hashlib, io, json, os, re, sys, tarfile, difflib
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
/usr/bin/python3 -I -s -B $S/b.py $S A > $S/build.out 2>&1; cat $S/BUILD.json; sha256sum $S/b.py
