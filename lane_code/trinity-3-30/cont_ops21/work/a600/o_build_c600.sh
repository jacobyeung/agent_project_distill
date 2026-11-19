#!/bin/bash
set -euo pipefail
umask 077
S=/project/community/jjyeung/okh7/813f42db/c21a600
test ! -e "$S"
mkdir -m 700 "$S"
cat > "$S/b.py" <<'C600_EOF'
"""Rebuild routed A for 450 camera items with a fresh token and export binding.
Verify the original delivery, restrict the operator and input types, append preparation
without replacing the policy slot, and reseal all derived hashes. Preserve the payload
item registry, settings, serving pins, and USR1 wrapper. Write a delivery and build report.
"""
import ast, gzip, hashlib, io, json, os, re, sys, tarfile, difflib
from pathlib import Path

K = Path('/project/community/jjyeung/okh7')
S = Path(sys.argv[1])
assert sys.argv[2] == 'A', 'Camera build supports A only'
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


def rebatch(batch, told, tnew, old_pub, new_pub, operator, new_operator):
    line, raw = bundle_of(batch)
    items = read_tar(raw)
    assert sorted(m.name for m, _ in items) == ['0.json', '0.py', '7.py']
    out = []
    for m, d in items:
        if m.name == '0.json':
            assert d == old_pub; d = new_pub
        elif m.name == '7.py':
            assert d == operator; d = new_operator
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


def camera_operator(d):
    d = replace_once(d, b'COUNTS=(150,150,150,150,36)', b'COUNTS=(150,150,150,0,0)', 'COUNTS')
    d = replace_once(d, b'SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4))', b'SCHEDULE=((0,0),(0,1),(0,2))', 'SCHEDULE')
    d = replace_once(d, b'types=[3,0,1,2,4]', b'types=[0,1,2]', 'descriptor types')
    assert d.count(b'636') == 4, 'descriptor/rehearsal/completion counts'
    return d.replace(b'636', b'450')


def camera_inputs(d):
    v = json.loads(d)
    assert v['types'] == ['camera_displacement','camera_rotation','camera_movement_direction',
                          'object_abs_distance','room_size_estimation']
    v['types'] = v['types'][:3]
    return jd(v)


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
        elif n == 'a/6.py':
            nd = camera_operator(d)
        elif n == 'a/0.json':
            nd = camera_inputs(d)
        elif n == 'PACKAGE.json':
            nd = None
        else:
            assert told not in d, n
            nd = d
        new.append([m, nd])
    newfiles = {m.name: d for m, d in new if d is not None}
    oldpub = json.loads(files['0.json'])
    newfiles['BATCH.sh'] = rebatch(files['BATCH.sh'], told, tnew, files['0.json'], newfiles['0.json'], files['a/6.py'], newfiles['a/6.py'])
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
sim['types'] = sim['types'][:3]
(S/'SIM_A_1.json').write_text(json.dumps(sim, indent=2, sort_keys=True) + '\n')
(S/'BUILD.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
(S/'DIFF.txt').write_text(''.join(diff_lines))
print(json.dumps(report, indent=1, sort_keys=True)); print(''.join(diff_lines))

C600_EOF
cat > "$S/bind.json" <<'C600_EOF'
{"archive_bytes": 21583032320, "archive_sha256": "673c147c46bd5a64a991e023307b6e2676f1c2cb96c564ca236ab7c914e2c430", "base_identity": "c202236235762e1c871ad0ccb60c8ee5ba337b9a", "config_sha256": "9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4", "frame_layout": "duplicate", "lineage": "SFT", "member_directory": "m600", "object": "q8/8865619b/6ed2c7aa_m600.tar", "preparation_sha256": {"config": "b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad", "data_receipt": "03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47", "receipt": "a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda"}, "run": "6ed2c7aa", "step": 600}
C600_EOF
cat > "$S/read_plan.py" <<'C600_EOF'
"""Bind the scoring plan to the actual freshly built package; Python 3.6 stdlib."""
import hashlib
import json
import runpy
import sys
import tarfile
from pathlib import Path

def make(package, binding, template):
    p=Path(package)
    public=json.loads((p/'0.json').read_text())
    with tarfile.open(str(p/'0.tgz')) as archive:
        cfg=json.load(archive.extractfile('9.json'))
        items=json.load(archive.extractfile('items/devs1_routed.json'))['items']
    op=runpy.run_path(str(p/'a/6.py'),run_name='read_plan')
    assert op['COUNTS']==(150,150,150,0,0) and op['SCHEDULE']==((0,0),(0,1),(0,2))
    for k,v in cfg['export_binding'].items():
        assert binding[k]==v,k
    ids={i['id'] for i in items if i['question_type'] in cfg['order'][:3]}
    assert len(ids)==450
    plan=json.loads(json.dumps(template))
    plan.update(token=public['token'],plan_sha256=public['plan_sha256'],
        operator_sha256=hashlib.sha256((p/'a/6.py').read_bytes()).hexdigest(),
        expected=[450],read_settings=op['descriptors'](str(p)),sequence=[list(x) for x in op['SCHEDULE']],
        walltime='03:00:00',export_binding={k:binding[k] for k in plan['export_binding']},
        export_identity_seal='PACKAGE.json pins the operator and fill helper; payload 9.json seals the step-600 export binding.',
        operations_file='REPORT_A600C.md',item_sets={'dev-S1':450})
    plan['item_ids_in_execution_order']=[i for i in plan['item_ids_in_execution_order'] if i in ids]
    assert len(plan['item_ids_in_execution_order'])==450
    return plan

if __name__=='__main__':
    package,binding,template,output=sys.argv[1:]
    plan=make(package,json.loads(Path(binding).read_text()),json.loads(Path(template).read_text()))
    Path(output).write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')

C600_EOF
cat > "$S/read_plan_template.json" <<'C600_EOF'
{
  "arms": [
    "tower"
  ],
  "cpu_check": {
    "bootstrap_sha256": "76036ed94db2dcb7b6ffb7997d855ac06f50fa5e59d9acc828c65fac1cbae2b3",
    "cpus": 8,
    "exclude": "orchard-flame-[0-31]",
    "gpus": 0,
    "helper_sha256": "e4648e671c719e3b1cb56618a7442ea3ec97e549562add9492603c56ebe0776a",
    "memory": "200G",
    "partition": "preempt",
    "required_flags": [
      "passed",
      "bundle_guard_passed",
      "entry_sequence_passed"
    ],
    "results": "a/c/CPU.json",
    "walltime": "04:00:00"
  },
  "expected": [
    636
  ],
  "export_binding": {
    "archive_bytes": 21583032320,
    "archive_sha256": "dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5",
    "base_identity": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
    "config_sha256": "9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4",
    "frame_layout": "duplicate",
    "lineage": "SFT",
    "member_directory": "m400",
    "object": "q8/8865619b/6ed2c7aa_m400.tar",
    "preparation_sha256": {
      "config": "b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad",
      "data_receipt": "03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47",
      "receipt": "a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda"
    },
    "run": "6ed2c7aa",
    "step": 400
  },
  "export_identity_seal": "Delivery PACKAGE.json pins a/4.py; payload 9.json remains byte-identical.",
  "item_ids_in_execution_order": [
    "vsi590k_042574",
    "vsi590k_042581",
    "vsi590k_042584",
    "vsi590k_042588",
    "vsi590k_042597",
    "vsi590k_042604",
    "vsi590k_042608",
    "vsi590k_042612",
    "vsi590k_042613",
    "vsi590k_042627",
    "vsi590k_042632",
    "vsi590k_042644",
    "vsi590k_042645",
    "vsi590k_042656",
    "vsi590k_042674",
    "vsi590k_042690",
    "vsi590k_042715",
    "vsi590k_042717",
    "vsi590k_044593",
    "vsi590k_044597",
    "vsi590k_044622",
    "vsi590k_045538",
    "vsi590k_045546",
    "vsi590k_045785",
    "vsi590k_045786",
    "vsi590k_046210",
    "vsi590k_046212",
    "vsi590k_047592",
    "vsi590k_050188",
    "vsi590k_050630",
    "vsi590k_155738",
    "vsi590k_155745",
    "vsi590k_161427",
    "vsi590k_161567",
    "vsi590k_161571",
    "vsi590k_161734",
    "vsi590k_161796",
    "vsi590k_161799",
    "vsi590k_161806",
    "vsi590k_161807",
    "vsi590k_161821",
    "vsi590k_161825",
    "vsi590k_161826",
    "vsi590k_161827",
    "vsi590k_161828",
    "vsi590k_161830",
    "vsi590k_161832",
    "vsi590k_161834",
    "vsi590k_161836",
    "vsi590k_161841",
    "vsi590k_163060",
    "vsi590k_163069",
    "vsi590k_163082",
    "vsi590k_163091",
    "vsi590k_163095",
    "vsi590k_163157",
    "vsi590k_163169",
    "vsi590k_163172",
    "vsi590k_163271",
    "vsi590k_163641",
    "vsi590k_163643",
    "vsi590k_163648",
    "vsi590k_163659",
    "vsi590k_163662",
    "vsi590k_163777",
    "vsi590k_163778",
    "vsi590k_163785",
    "vsi590k_163788",
    "vsi590k_163793",
    "vsi590k_163796",
    "vsi590k_163797",
    "vsi590k_163799",
    "vsi590k_163811",
    "vsi590k_163813",
    "vsi590k_163814",
    "vsi590k_163815",
    "vsi590k_164325",
    "vsi590k_164334",
    "vsi590k_164335",
    "vsi590k_164340",
    "vsi590k_164348",
    "vsi590k_164354",
    "vsi590k_164784",
    "vsi590k_164785",
    "vsi590k_164801",
    "vsi590k_164817",
    "vsi590k_164821",
    "vsi590k_165296",
    "vsi590k_165307",
    "vsi590k_165318",
    "vsi590k_165323",
    "vsi590k_165343",
    "vsi590k_165350",
    "vsi590k_165357",
    "vsi590k_166609",
    "vsi590k_168046",
    "vsi590k_168055",
    "vsi590k_168067",
    "vsi590k_168070",
    "vsi590k_169291",
    "vsi590k_169295",
    "vsi590k_169442",
    "vsi590k_169469",
    "vsi590k_251447",
    "vsi590k_251449",
    "vsi590k_251452",
    "vsi590k_251453",
    "vsi590k_251454",
    "vsi590k_251506",
    "vsi590k_251515",
    "vsi590k_251702",
    "vsi590k_251912",
    "vsi590k_251919",
    "vsi590k_251923",
    "vsi590k_251924",
    "vsi590k_251925",
    "vsi590k_251927",
    "vsi590k_251965",
    "vsi590k_251967",
    "vsi590k_252278",
    "vsi590k_252280",
    "vsi590k_252282",
    "vsi590k_252283",
    "vsi590k_252491",
    "vsi590k_252493",
    "vsi590k_252496",
    "vsi590k_252497",
    "vsi590k_252500",
    "vsi590k_252505",
    "vsi590k_253035",
    "vsi590k_253038",
    "vsi590k_253039",
    "vsi590k_253040",
    "vsi590k_253042",
    "vsi590k_253230",
    "vsi590k_253354",
    "vsi590k_253363",
    "vsi590k_253783",
    "vsi590k_253784",
    "vsi590k_254132",
    "vsi590k_254285",
    "vsi590k_254594",
    "vsi590k_254604",
    "vsi590k_255374",
    "vsi590k_255402",
    "vsi590k_255407",
    "vsi590k_255863",
    "vsi590k_255865",
    "vsi590k_256028",
    "vsi590k_256516",
    "devs1cam-0020d0cefc26c693abeb6c4e5951cc07",
    "devs1cam-07b1a63813a4733a042538e350e265eb",
    "devs1cam-088f1e3c275fb323293f10b356d740a2",
    "devs1cam-0adb11f9bb13b47d9d937ab72f8e2eea",
    "devs1cam-0baec18afce655dae16a404906102533",
    "devs1cam-0bbc754c75556e9403d471951304183b",
    "devs1cam-0c0b001891172c79b9b8caa6fef84bda",
    "devs1cam-1142c5ca6feafd58d27489b2166b42ba",
    "devs1cam-13e0fc3df819bbe48fd3e13644508b18",
    "devs1cam-17e826c7e7031b84a5d88c7ce16623a6",
    "devs1cam-1976e69d628ad042a97c896d57221682",
    "devs1cam-19baad91803f182449ea525bb1c95521",
    "devs1cam-1a2a6eee4de7efd195338e9547b105c4",
    "devs1cam-1d60e77e9e48d47d63d61c2e735686a9",
    "devs1cam-1e82b04d17a1e723669d4385fef93ebe",
    "devs1cam-229e7bdf910b966f2218a59c4d1e1273",
    "devs1cam-252cc74fcb20a299b88bb5a7ceee5d60",
    "devs1cam-25d7016a7ea1bf023f76948fdd9deaeb",
    "devs1cam-27bac7d0c462e80b3395e5923e3bdcd3",
    "devs1cam-2d2f184399fce90f8ef087a67303096a",
    "devs1cam-2d6247bfc8f1ff68196e8e0321a20c6d",
    "devs1cam-2d770696a926df52f2f9e3414a53efd8",
    "devs1cam-2f4c478745e39b6f1e29fd1706ed5bf0",
    "devs1cam-2f6b04a35cb285aebf8a567c9422fd65",
    "devs1cam-30f0f38919466d58f06d53f632cdd2a1",
    "devs1cam-311f577252a264592c0d796210ee8cb0",
    "devs1cam-31d9eac811eb11717a53fffe9583f9f0",
    "devs1cam-348a9e022f27ac67031f55b8b0167ba3",
    "devs1cam-35f6b028403fc915f5ee1839ac0fc7e8",
    "devs1cam-389218694a6e46678a1f993e09e0bfec",
    "devs1cam-3c209557bfc86a182a9952f28e04221a",
    "devs1cam-3d1603b2e5b652d907876bdb15597177",
    "devs1cam-3d52edf5468c4207061fa53bfbf09c1c",
    "devs1cam-3db00ce69e697a9d3abeac27819a3ae6",
    "devs1cam-3fa79d1a487810e1b48b4c30ddda88a5",
    "devs1cam-4162d0dbfce5adfc5875d80199370621",
    "devs1cam-44076714b5ef1e416bb5e9f7140d2a09",
    "devs1cam-45ed5c9e944f8f16079231feb6c2d941",
    "devs1cam-49dbcdf686b199381d65e13d07b1e14e",
    "devs1cam-50b26c5a65f68c7184c6827117eb3145",
    "devs1cam-53d3069b9da4533486ef2527d1c5483f",
    "devs1cam-53fb8eb60d82ce1054bc4bfe900bdd5c",
    "devs1cam-54062ce87aa7bd7a3d1f520e657648b4",
    "devs1cam-542eb42026788cc63df9e5a0ed9aae46",
    "devs1cam-578e23b84ba6a586db309e68eff43d9e",
    "devs1cam-584ed12038aeaf7de02484f2d59de464",
    "devs1cam-58b41f71b4e5883894beae8dccb7e99e",
    "devs1cam-5a3b79130e94e0a9727ae3ec32d04ce8",
    "devs1cam-5ba10abff65a66ad9d955a50fc844d8c",
    "devs1cam-5c4f40c19d29304493a4e340e2fbdb11",
    "devs1cam-63862a6912ad716a4e4fd35af9b591f9",
    "devs1cam-642f7803436e63d24fbe54a14b784cb5",
    "devs1cam-648c86f02e008d0d922da63705103589",
    "devs1cam-662b57eea66bab52aa22d0c26a468735",
    "devs1cam-67088ff4bd269377c9afbe466856c732",
    "devs1cam-67f88213f397025d9200d63060fd70bf",
    "devs1cam-72122469350c4004d5c1cce4394722af",
    "devs1cam-722dd024e09eee0569da63edd89933fd",
    "devs1cam-754534997c26e60a298a7e9b3c14f9c1",
    "devs1cam-7aee247756391afad52f2faf1ca75d68",
    "devs1cam-7d06df8bee5bd530275ee62b8af089ca",
    "devs1cam-836877f1f5add3cc5e175256967ba7b0",
    "devs1cam-86480cf65f2e27b317973b8c0995db69",
    "devs1cam-8698caaa9bc45e7b762ed3b06bd47d45",
    "devs1cam-877888c6735f1dca76c43a86f44fdeb5",
    "devs1cam-8a500999c75d8a1d9a4f4fcb634b7a97",
    "devs1cam-8a979b3abff030d4a45889283b52c26e",
    "devs1cam-8ae5a8537ccbc40da4a1269c70ad77cc",
    "devs1cam-8b5fb9cf2e866f24465310d36b052dd9",
    "devs1cam-8bc385e109ce53b6b828c4da3d0f8b44",
    "devs1cam-8db8694dd3b4430f5ad37380ce39afed",
    "devs1cam-8dede8264b43be4f9f76a97b23d18b30",
    "devs1cam-8e055c12febdfa30413dca6695fd8d1d",
    "devs1cam-8f077d15a9fdf6662a13eaba1630dadf",
    "devs1cam-8f44d7b34e2d8851d196827f07fbafe1",
    "devs1cam-8fbc98f7b2d368f156a7d6c76691dcfe",
    "devs1cam-97f274f7f0bd32bf78617f293b8cb48c",
    "devs1cam-98614fb5fa4dd5824d01b2ab23272e57",
    "devs1cam-994081a40cb48cd70def7d6b287f057b",
    "devs1cam-9e1614f93d7fa3db779b02f3a7bae138",
    "devs1cam-a022bdd0062041f4998af564f26e2658",
    "devs1cam-a08dbb43caecc161222571b94b872637",
    "devs1cam-a128d5e1f4fc12687b094f2f3ac91c77",
    "devs1cam-a15a5901d91b07cc930c9e63063047d6",
    "devs1cam-a3ad5639a615a77b2076c44c717e66db",
    "devs1cam-a4cfd20ab9eafeb380aea46db14905bb",
    "devs1cam-a50984da46e25527d043c1dc766ed2c6",
    "devs1cam-a7f6edf87afda6c66b9a7670dfd81fae",
    "devs1cam-ae9942a32cf70b6bc62a81dc0ad56e27",
    "devs1cam-b04b4afb81c8062ee3609f1d1e4283f6",
    "devs1cam-b7308a02db220b9af980441da794dab8",
    "devs1cam-b8a55a66c62e190d02c9968212f55e2a",
    "devs1cam-bcb5ad45947af16e5f28d5fb11829252",
    "devs1cam-bcebf4406284f42f489c41fde2b8492a",
    "devs1cam-bcf12b2b29a3f76524d2acac38f02dd1",
    "devs1cam-bd699ff6855744603df5f827438c8574",
    "devs1cam-bd84646412253bf82c56b1d3592480c8",
    "devs1cam-bd999ce1a3ae47d5142d31260572f81d",
    "devs1cam-be04857120531d0a040f49624d6115ff",
    "devs1cam-be90bb00bc0b2b91577a66c49c42d3a3",
    "devs1cam-c02304abe5f819346c1cfe2679a33ec3",
    "devs1cam-c091a064bdedc2c3e9d92e889414e87e",
    "devs1cam-c0d6bf6233776e576b54167dc3b56d50",
    "devs1cam-c0e184986fa119c320bc18c2a5f53f60",
    "devs1cam-c14129ee262a91322510c7ee032de73f",
    "devs1cam-c17b484fd3023c3131badd6bbc0a828f",
    "devs1cam-c2b87ae00c3ef9d9da947e3cb0198700",
    "devs1cam-c2ceb11cca4363c296e93d58a69e766b",
    "devs1cam-c488362d0fc8f14d7c48076137ede89d",
    "devs1cam-c54e0849a9b9f57617f0142b9eb86e37",
    "devs1cam-c76d6ddb4a5ff5c2f30a83312ecbcb04",
    "devs1cam-c7d09a143d8c4ee2fdbcc59021bd2966",
    "devs1cam-cbd5f4f015b2707411ded4fcff760b6d",
    "devs1cam-cd1a6c238bd3746ed63aa88735ca1895",
    "devs1cam-cf7a8adb59908e74396b0305caf22413",
    "devs1cam-cf9d3b7294f89a136f222539ba3fcc15",
    "devs1cam-d0b6bbe0d485f3f2852954fa8439cedb",
    "devs1cam-d287ebc02c4771de8f876c98e1b7e943",
    "devs1cam-d61cbbbcbd424e472b55b899d5718e05",
    "devs1cam-d77b61105f335c59d7bd989a6bc77faf",
    "devs1cam-d7a9e07bd64f8c2b232d81a29efa8a6b",
    "devs1cam-d83525f8e677da756548de53980eb813",
    "devs1cam-d8ba81eeeddadf155e8fc2638bf6bb3a",
    "devs1cam-d9daa469f216857cc67fa0530e8c59c3",
    "devs1cam-d9f6ae3d729e9a4e8f9b97b2af31c886",
    "devs1cam-dcfbbe69be4976aa9ecfb01d3e1080dd",
    "devs1cam-de9ca21f755fe6cafd89f1ce84afbe37",
    "devs1cam-e1acae6d43db0cd60bea9f785550a87b",
    "devs1cam-e2d492243567a18de496c869a59cd6ac",
    "devs1cam-e2f99f9b04a4a94201fc44bee78e176c",
    "devs1cam-e6fac49a6443a6005fecc3b0375abb7e",
    "devs1cam-e768057b0752ef4fde738baf13a0e68d",
    "devs1cam-ea07ae4210e3abdee120f9305aba7b46",
    "devs1cam-ead1b4fb5b95c572595cc95c9a6e0989",
    "devs1cam-eae874a60413349d42a8dd93f3336205",
    "devs1cam-eb07a132caaeb7be8b0910119cb386bc",
    "devs1cam-eb0f179e32e0587081d84f8ea3150c5b",
    "devs1cam-ecb9db6f1302b6413b9e6ca015c38be4",
    "devs1cam-edca804cd923f7acd0bcb078605dcd07",
    "devs1cam-ee982c1184f51e77828bf37cc21b8b48",
    "devs1cam-efec944324efe0b3eb395fb1367e4e66",
    "devs1cam-f1347e043f5205a845097b758b9abff2",
    "devs1cam-f2bfd0d329f9fa309be7773930e66c55",
    "devs1cam-f2e015f3b14dc875780f4c647d173695",
    "devs1cam-f326e38622edbe6109879dc0784f965f",
    "devs1cam-f33cc892a4ba2bcfec746800b01a4e9a",
    "devs1cam-f36d481f33de9f69054a5b08a5b25c24",
    "devs1cam-f478a182c77d9392d78cc110d970b5d6",
    "devs1cam-fe35bce39404594f56ea20f44a491977",
    "devs1cam-ff3ba6316a032c274ffed6542abba64c",
    "devs1cam-02240d9bcaf9703226aa03c98e9f2d6e",
    "devs1cam-05eff7f66869bc50118d2e0d84d927df",
    "devs1cam-069c4a4fb2b94413b432b3abc2d66ac2",
    "devs1cam-0a369d6600f61cc6c3e15cb9e954e689",
    "devs1cam-0ab1b7c5ac60d3d2550706a3cdce8b29",
    "devs1cam-0cdcb2a08007772ca78ae5d7a6c9b886",
    "devs1cam-0d0cf0791c32f428cfacf34bc5b66f6a",
    "devs1cam-138cccbfe6d3bb26b10f50e1cae6a0d4",
    "devs1cam-13c1d6e42464ff095b5000e82d782009",
    "devs1cam-15f434c2d7e5cabf4baa6425706378c0",
    "devs1cam-164f3c63246cf1801e39bd68179b25c6",
    "devs1cam-16c216a1c82e3d8e6ac2410cb5a6356b",
    "devs1cam-198336f8bdf6985012b777f57d49cced",
    "devs1cam-1a33fc17ab1eb437d771e9f981ea8832",
    "devs1cam-1b7ba80e4a37097641e4c6abd2387e07",
    "devs1cam-1c639bff1680ba444816cdfe4a391af9",
    "devs1cam-1dcd9643f274d9b9cfa4c80b4ce59652",
    "devs1cam-1e32b030462621630cc2f907576af887",
    "devs1cam-1ed3c6004b63451bde7ffa3c6c12e2e4",
    "devs1cam-2145b0bdf8607a7d4c289b00ca7fb16a",
    "devs1cam-23e4a31e0df1e0b06b7c9f43c1a5d641",
    "devs1cam-24fc408c05e4d666b6fb1e89d218f5d9",
    "devs1cam-25d51266f56ad4b02b7d8ed70c27ce52",
    "devs1cam-28efb0393e32b223347815cfe18adec4",
    "devs1cam-29773f44cdd54eeee982a0498d024951",
    "devs1cam-2a2cb97664b1c93f39fbb6153c07d305",
    "devs1cam-2c3e51248e313ee107d8bf9a312a0212",
    "devs1cam-2c8c72894ccbffdc9d46321f66ec8090",
    "devs1cam-2cd565588214cafe7715bfa386c15341",
    "devs1cam-2de4909ee3577f17c78c77a2e9e29317",
    "devs1cam-2ea3d5c02118a891bfc300d2f2f28ca7",
    "devs1cam-2fa02399c753a95355ec261aa49813ff",
    "devs1cam-36625cf9ab3cf88b534b4385238f2f12",
    "devs1cam-3b06cb0a2e8face562911a02f71d8623",
    "devs1cam-3b299b26636d3d0b30d139a507bbaa96",
    "devs1cam-3f22bf92384123d71d26d8c6811ceb35",
    "devs1cam-3f4559da4d4b5f856fcce3cc817c55dc",
    "devs1cam-40263b40dfc3078be2ba9eb3258bf439",
    "devs1cam-42142c541ad2b875c1539f5e85e69feb",
    "devs1cam-453f94505fe0f14d25cb80c5088e6f72",
    "devs1cam-4a315b8a07d782753f8625a1dc0439ae",
    "devs1cam-4a3ee8096e8a2d087746a7e9bb45bc7d",
    "devs1cam-4b4e285c9b22b922af7ed6684d129445",
    "devs1cam-4d34ad1ab67f1406fb84bf183d091ef7",
    "devs1cam-4e15e17068eec1a23a601e9615dc2c77",
    "devs1cam-4faed4682687658d4cce9053ce6ae9e6",
    "devs1cam-504a8f836ec9b59ff4a1b3722de9e280",
    "devs1cam-5243d62cb1b1e112d1c18b3bca988c57",
    "devs1cam-5640abcbd1882f1be581ed84194b82a1",
    "devs1cam-5972b10244779f08bf3dde7bf43c3074",
    "devs1cam-5a35be901ad65075a70c92ebe3fea1db",
    "devs1cam-5b8fb5dd49158ebeb45c42704076caa5",
    "devs1cam-5bd21da4b35e5360f27e75d6cdadf114",
    "devs1cam-5dc99fae7c27b2ad92d5788691ebc75f",
    "devs1cam-5df62da4b1dd2e6e77486bb2cdf8d769",
    "devs1cam-61abc3d389b77c34d7e311fbdbba54fa",
    "devs1cam-6548f6320506db01af213699ff2d37cd",
    "devs1cam-6746124474529d17b5c54c12a6f11bba",
    "devs1cam-67fb535eff3949310860344b8d417f5c",
    "devs1cam-6b16d62bb25ecc085fc34bf292e5a8f4",
    "devs1cam-6b828505f5f98c36f314bfacca685227",
    "devs1cam-6bd803a39f1f3b9b0f22b07f2906bd8a",
    "devs1cam-6c2df6f4b136eaf1d44ef60046c31e04",
    "devs1cam-6c7aa5901a2b980ee21e95fff59f4296",
    "devs1cam-6e76bb165adcd84edb46017714a037d5",
    "devs1cam-7193e21f1a9eeaec75015548a004359c",
    "devs1cam-74c691e368949b8aff63b2c299f5e942",
    "devs1cam-78ba8145f465ba79adecb27f98f1c30e",
    "devs1cam-79eb89f229322d338df859f4691cb570",
    "devs1cam-7b08cbabe7f9cc91e2b634fcf4610d92",
    "devs1cam-803a7700708aa95fe7c980788f127009",
    "devs1cam-83376579376807594d1593c8cc8d31cb",
    "devs1cam-839fd8c5c222121513aadda01f2d6fdf",
    "devs1cam-87133eab18a146643bf0823c7a56fac7",
    "devs1cam-896d7dcb29a66ee249548d14a1ad2841",
    "devs1cam-899c9025299cf495fd3d0ca818be1fb7",
    "devs1cam-89c5d2617b98a34e3302dd594c411a7f",
    "devs1cam-89edf130515f36979b854b48d33a14c6",
    "devs1cam-8a1a8eedbf21529f89091896157a9057",
    "devs1cam-8d91efa63427b4f81a306eb2996d5126",
    "devs1cam-8e333863432f4c41ffdef8d842e977d7",
    "devs1cam-8f0ea0e0500274e8f5a60aa02c3dd496",
    "devs1cam-8f70bd517ed5842308a80e7f87cd0e55",
    "devs1cam-90c5871835bc55d15c21223041175ee8",
    "devs1cam-9130fc1cb6d80cd810105090d0d59d6d",
    "devs1cam-915e8acafcc568f1b7e1780d3c93bf3c",
    "devs1cam-9277f3e7669b809af590bc9ed02ea652",
    "devs1cam-9578f4adc786b5c30c669d2d3d0c62c3",
    "devs1cam-96dee7cb2c5327d13ac81ccfcd57893f",
    "devs1cam-9797e3726c7d48572d8387e9a3f962d1",
    "devs1cam-98f2007812e37ec2e25b8438c785d12d",
    "devs1cam-99ed25e0197022edda2c4fa4364a72fd",
    "devs1cam-9a01d0e6ce1042faa18a1102ae3c6e47",
    "devs1cam-9a8db608ee976f7e0e36134398cb85f5",
    "devs1cam-9c8aa16bc3b251e715bf8e1f0a342d3c",
    "devs1cam-9dac19f69a1b6bf75e5e445adb6882bf",
    "devs1cam-a10b71d7b53e916fe720fcff88336188",
    "devs1cam-a1544413e4257cabdfd2926fdb1fad9b",
    "devs1cam-a17deabef59ec32bfe7813f347d1a308",
    "devs1cam-a38aed53757373f4a0e905af32a1741c",
    "devs1cam-a6e71784fc1347d454ef4ecc0c6d552e",
    "devs1cam-a7b0535f9cb3ed3d9188f14ed5098b3e",
    "devs1cam-aa6402ccf7186ad8cf004ba57a2b8941",
    "devs1cam-ac602d365aeacdf8a179a8f70d9156af",
    "devs1cam-b10e322ca231fa7d49daaccb14a6a665",
    "devs1cam-b4ad41ef3a5a10d99b546fa01e68584c",
    "devs1cam-b6078b1b9d92f479af60834f947ecba8",
    "devs1cam-ba394adb360a86fed821893368e4cd2a",
    "devs1cam-bbbddf93cb397bd48f24a0448e6e4225",
    "devs1cam-bcf65905224204490afeb430b3337ec9",
    "devs1cam-bdf1c5b5f7ee6f3b810b36fccd2a145a",
    "devs1cam-be2a8b7bef757f07626b031fa0e3a02c",
    "devs1cam-be83a9feec4e630a532ff2330331b6e8",
    "devs1cam-be91c3a8f6ff92085d42f5b9e09fbb90",
    "devs1cam-c0644be078f1db2cafd487bfa5a7b088",
    "devs1cam-c302a46ccf165208796597c2510f4647",
    "devs1cam-c5a0a17b179942f374329af010828248",
    "devs1cam-c79e5c0edd19a9a8035e1fd969f6f76f",
    "devs1cam-c7aab39b4f06c2219e4632690dc7e393",
    "devs1cam-ca64af6a5b4ea0363cb456202ae2e0f4",
    "devs1cam-caf201fee4a2125022f292aba9e095e9",
    "devs1cam-ccc9f6278b17c1f708090d91ae274443",
    "devs1cam-cce660785a67b4dca971187eab6f4b18",
    "devs1cam-cdb99fe782379f91617eb469aa3f3a4a",
    "devs1cam-d035183ef78c43cf01beca9637368c2b",
    "devs1cam-d4cf651b885608710d311ad0b7758073",
    "devs1cam-d4d8c67ba13a53bd6cb7305e78745d3c",
    "devs1cam-d57c2366f6f5c0ca64b2a22da074e197",
    "devs1cam-d635240eed1b2d1cf522a83aa43c05bf",
    "devs1cam-d7d4eb0b26a31f804d5dc4dd6094fbe3",
    "devs1cam-d8dc34d4d85be6038b2d39b3634e4f24",
    "devs1cam-da1309eaed7df2d6a30c2e624c2d5383",
    "devs1cam-da88cc894e4c2c65e71c88fed6771996",
    "devs1cam-dab03f358476674236311cd3b829a165",
    "devs1cam-dd019294f91678c9fd3e25379ce46e90",
    "devs1cam-e6d8b6e07437be2b74ef1e73758fea22",
    "devs1cam-e6f5d3735e2244d40cd2dc7c7d49d453",
    "devs1cam-e7196b6467f78124d993bb8999122eb4",
    "devs1cam-e802fa5b7b2918a44efb44fc77a1ac6a",
    "devs1cam-ed6b77db243a54d1381c3dd00bdca8da",
    "devs1cam-ed84c61dbde5ab68aeab5a005a791a9e",
    "devs1cam-edfc5278137c4b51a9ba99a7b87ed25d",
    "devs1cam-eec45efdcef279db3166cce92751ad4d",
    "devs1cam-ef0396683f20d945e6898535e381ad21",
    "devs1cam-f1a2ba15c47cc6fdb336d2c63be79da0",
    "devs1cam-f472c425b295f1620576f307364be5ab",
    "devs1cam-f845406344eee35d8e87003a3737fd89",
    "devs1cam-fae38610f0ddd1c022d8079537d9bc25",
    "devs1cam-fd61e009146cb6d72ef89f6ac1269b42",
    "devs1cam-fe04c49911ec5a773f3e5975dd1df75a",
    "devs1cam-00729c5db90fc5d0c5281ed7ce889dca",
    "devs1cam-05ce2ad29e7353ab8b808abe3df89f0d",
    "devs1cam-0d4180723a5d9942daa277d9466db301",
    "devs1cam-0d591bfbb81d0bac9261869201786807",
    "devs1cam-0e6c9965c28858ab6a0d70649e9f7801",
    "devs1cam-0f41e5b96a3bf8f5c9d748d663448c88",
    "devs1cam-0f558e8f2f579ecce0a2173b1505584d",
    "devs1cam-1054354c3c441728e37e87dc7bbd6a68",
    "devs1cam-14bd1afd2f3737fcb8c72811b82dbcd1",
    "devs1cam-1a0cee7f65e591a5590179ec2b8cdfa9",
    "devs1cam-1a1863a10468af67b7244bdebd30b073",
    "devs1cam-1b61a955e284dbebb14768fdd95ebc9b",
    "devs1cam-1c4baf0dcb39c0575ae19014ac6fade7",
    "devs1cam-227f221890b5efcf2a6517ff68226723",
    "devs1cam-23f04fb2b67c5c545d592b39d8d52c97",
    "devs1cam-247c686a26ebecb5097ee688577ec62a",
    "devs1cam-25a2d02602e3865726da5f94f1043f19",
    "devs1cam-25b79a6f4a93cac75556e6f4dfcb243e",
    "devs1cam-261616c5055d35a90c5d584eb897193c",
    "devs1cam-27da9a85bf26dc4dbd9f9d0c6e40f59d",
    "devs1cam-28389a5db258677ec602acb20f27840e",
    "devs1cam-287a70b200cc988bdc196baddcfba2ee",
    "devs1cam-295b5a2706d771d9bea92573137194ce",
    "devs1cam-2a80598ada0b258686ce5f8c24257ae6",
    "devs1cam-2caddcb84c0bc23b0d89ba3003bfba57",
    "devs1cam-2f76f5acd2a8a198a57edc57900b21a5",
    "devs1cam-2fd5bd894c6b7ae7098f6e7f8a0c88d4",
    "devs1cam-2fe8882e1b6e7b4bd3f9230e9add461c",
    "devs1cam-31cffb00c5dba885767d5428b673bdfb",
    "devs1cam-332f6cace3baf8c061dc536c7a4dd243",
    "devs1cam-369e6305542730f6ae91fb214dc1fbd1",
    "devs1cam-38cae6cbe5a8ef1abb1ff04b2cd51dc5",
    "devs1cam-3a9f05dfb4de4e999fcfa728533858e2",
    "devs1cam-3b3bd31478f32ba1744edd3c3dbea8aa",
    "devs1cam-3e82dd97532a1b9786af2d973c1c39f5",
    "devs1cam-3ea4d987de4dbedecb40ca902d836b1f",
    "devs1cam-41f0ee22c9b241d8d745406680121021",
    "devs1cam-44476730608f5c7d6a8a8340713399df",
    "devs1cam-48807cbe2a627252c8d48966af2ac778",
    "devs1cam-4aaef73ef8f7374b3318805e5788836a",
    "devs1cam-4c8b8d552a6c0ed8f7c575d9fe34b0f7",
    "devs1cam-4db02514fa675dbd1ed5cbcfb84f1130",
    "devs1cam-50d8b3491b4136fe011ab45a48ddc79d",
    "devs1cam-55215ec664298583c3cfb0e2873a86a0",
    "devs1cam-55737eb70f6647fb31984bebad82c03f",
    "devs1cam-5603d546987bf298034c320fd4030fe0",
    "devs1cam-56637b6125f18410bdfca24073fd453e",
    "devs1cam-58775077eff086d079ffdaf4a2a85443",
    "devs1cam-59ab36f70477becdd652ee11b3366880",
    "devs1cam-5b98ada09a663b4e3ec06701022acee6",
    "devs1cam-5f9724339c1393d9cbdc605c301b0b26",
    "devs1cam-60346f2b71cd2003c082cc86d8a56989",
    "devs1cam-64b76ac73df298f7222625e1fdd2e222",
    "devs1cam-655b1f6a401470c178e86c28210edb22",
    "devs1cam-675db7e44fe82f9f9992ea3065e1a44f",
    "devs1cam-683a58e40f41330cd8faab0a1ba43314",
    "devs1cam-6d17e8458230e869232ce05dea93ff52",
    "devs1cam-6db650f1c078b92c5a9ac29d3b1755b9",
    "devs1cam-6e2f23250f0779a47f0347d7494c9207",
    "devs1cam-70b09cedb470e097dab042ba3d1dc86a",
    "devs1cam-715bf3e476665c3a94cd862f3204c1e6",
    "devs1cam-73693cd3f25013c7da3bf6b681fc6e05",
    "devs1cam-7443c515b1e413fba39cc56a95d39d9d",
    "devs1cam-752c972e1103bed700d1279c626b7621",
    "devs1cam-7604ce99934dabc0732e2db012fd3368",
    "devs1cam-76a1b5c5f08da424b5aae4b83b7bdecc",
    "devs1cam-76ac56c75f3c0612917bbcc8193c5339",
    "devs1cam-7882ba6c97c8fe2bca5b6c5a7859ae36",
    "devs1cam-79b7b96a0b66bba534f8e06655fefe13",
    "devs1cam-7f07649a2d141fe6a25250b34684f48a",
    "devs1cam-7f258b080002196edab46a1629700ee6",
    "devs1cam-808b952b36da29869b042c89222ae4a2",
    "devs1cam-81a416f5577ee7e64931331ee6750357",
    "devs1cam-82a124293066cf01de27789b77e5f14b",
    "devs1cam-866e98051dedeb27cf7a85fecc6d0a32",
    "devs1cam-88349b7b0fdd2ae5a317a78c9550e623",
    "devs1cam-88905f96578b8cadfc92ea93883406b8",
    "devs1cam-8d14e744f2d40c6cfc8e5f75b3036a10",
    "devs1cam-8d2cb8065776ea262e1fb5aad990f894",
    "devs1cam-8e028611da6bce81d51ab169d47cb65c",
    "devs1cam-8f71fc95b94aaab9d94531279ac76859",
    "devs1cam-90cb36e22bff724116fb8461a7c00f12",
    "devs1cam-92efe2a3d563d6b53f8cd9650717afc3",
    "devs1cam-942bceec79ef54ad20361ca882815728",
    "devs1cam-9483a565716d53e6a31e555cd9e30d56",
    "devs1cam-9601384c89c2e4ded9eb6990e85e7264",
    "devs1cam-983fddb8247c02b3514fd6441dbd3f83",
    "devs1cam-99e244ce603d96012829f0ea549bd620",
    "devs1cam-9bf8cf0a716ea3739829502dfbb622e3",
    "devs1cam-a21dcc11af700ec9bb93ef1a71b5111c",
    "devs1cam-a581bbf0fbb9921793ec8240d0be05ec",
    "devs1cam-a5a3052d28bf12a3f318770f86240d18",
    "devs1cam-a6d2d6e14e58b0e148285184e6863ae6",
    "devs1cam-a8279221abbed044f088f87619dae21a",
    "devs1cam-a8fd6af8498a492331057d060923265e",
    "devs1cam-a925b6df0a21afb65b31df518a977f29",
    "devs1cam-aa4801358eaaac23def499d7a066409a",
    "devs1cam-aad4281c9228c5bc6a95d66e895a875f",
    "devs1cam-ac1cb26f09606e41818c376f03366a0f",
    "devs1cam-af59a069d7fb19829009f25797beb8c5",
    "devs1cam-af66a215b0599f56af4bbc4f68f7aae9",
    "devs1cam-af9e2c6598e4e3944755997d465fc8b9",
    "devs1cam-b6e5cfa5d9307989012d53f63d0e305c",
    "devs1cam-ba129771ad9baaa801f45fca42f880bb",
    "devs1cam-ba4560899e77e3d6f3f4ef27d20acf3d",
    "devs1cam-bd00f72b51c8224819d9dada1f8eff9c",
    "devs1cam-bd57333c31970bf4d95adf75850578cc",
    "devs1cam-bda1eceab340255c9c67d42c196b4076",
    "devs1cam-bf82c2868bf1894ce38228169a29e265",
    "devs1cam-bfa2caee438ea33ca07f51b380966266",
    "devs1cam-c03882737ec55c4ba239bfe8a4a95278",
    "devs1cam-c1752a9c772503e6b52b66d507f4b710",
    "devs1cam-c7411f83c967792a369a613a0e71511b",
    "devs1cam-c85cb7657c0dec4e6d4f51df247d985b",
    "devs1cam-ca8a0fc19426e77e2e7cf760981d30be",
    "devs1cam-cb5bfe5b6afe21cc05ee8e06282dee85",
    "devs1cam-ccb86e47081baeb174c08933507d44fb",
    "devs1cam-ce5446131af04c8eb1ca90e9e5f8f214",
    "devs1cam-d037c8d92af32b28ed26504704f4b33e",
    "devs1cam-d0b8b9bf6b6de8790f0709bafb42c2b2",
    "devs1cam-d0f62f1ec0cd67b34be909bc51db97f5",
    "devs1cam-d29d99c3728e911fcf2d237ac6f3113e",
    "devs1cam-d32079e013ae11d12b8be4f23fb5338d",
    "devs1cam-d475f752e4f7ccf449345cfd8c5d4440",
    "devs1cam-d66246db6d6ba5e4bbed4ede2f23a74b",
    "devs1cam-d6c3ef6e54b2dffe79d5bfd3f5b7cc57",
    "devs1cam-d8429ebaf1ea0993d6e9ace70be838fd",
    "devs1cam-dbf4361fe48a8f8ace48b072266c8b4a",
    "devs1cam-dd869b302fe111dbab9d483ff02e3055",
    "devs1cam-dde36abd8d32ffefeaca1fd2415cd604",
    "devs1cam-dfd2a8c8eb0a21e58167b86cd8e5ba6a",
    "devs1cam-e882b7a8629fa59bc04033b7c50688ef",
    "devs1cam-e9606e946eecd710a9e6bbfeae0e998b",
    "devs1cam-eb07e274e83b0f461a684eb0ffd13b5b",
    "devs1cam-eb34518c1a090ab0e9cdd6c48c707ace",
    "devs1cam-ec6c00e232c56dc8415132f6c24afb7b",
    "devs1cam-ed73545308ead79f95c7a9bb74d497da",
    "devs1cam-edac661ee29d27f72c954830838ec6e3",
    "devs1cam-ee19c17d529a785abf6218ee9fb48be5",
    "devs1cam-f0595ffa3a586b8d8a5b2c0b2dca14e9",
    "devs1cam-f07715e99a6cc7726d3e26a85bfd645e",
    "devs1cam-f18f720d2784ed810397fb2361d3c679",
    "devs1cam-f4417b403fffaabe50bac4af4c77976c",
    "devs1cam-f5316bf5ff16257d9587548f1c67ec83",
    "devs1cam-f866ae99d3db5c3590d990d6d621f6cc",
    "devs1cam-f9f52c52e877443c3053641748c4cdaf",
    "devs1cam-fa07df6af6ef47bc3b83baeaf44badb1",
    "devs1cam-fa38ceae7d5be6c02b695fa308ffd1b1",
    "devs1cam-faaa1fab79082817dacb8bb7b32c4519",
    "devs1cam-fcd098dd942c2ded6599bec14bccaf36",
    "room_scene0155_00",
    "room_scene0155_02",
    "room_scene0166_02",
    "room_scene0261_02",
    "room_scene0320_00",
    "room_scene0320_01",
    "room_scene0320_02",
    "room_scene0380_02",
    "room_scene0401_00",
    "room_scene0475_00",
    "room_scene0475_01",
    "room_scene0475_02",
    "room_scene0515_00",
    "room_scene0515_01",
    "room_scene0515_02",
    "room_scene0587_00",
    "room_scene0587_01",
    "room_scene0587_02",
    "vsi590k_058413",
    "vsi590k_058414",
    "vsi590k_058415",
    "vsi590k_058460",
    "vsi590k_058535",
    "vsi590k_058599",
    "vsi590k_058764",
    "vsi590k_059181",
    "vsi590k_059182",
    "vsi590k_059183",
    "vsi590k_059475",
    "vsi590k_059477",
    "vsi590k_059493",
    "vsi590k_059494",
    "vsi590k_059495",
    "vsi590k_059529",
    "vsi590k_059530",
    "vsi590k_059531"
  ],
  "item_manifest_sha256": "2849206e3eb66f40b3e2fba49cfe84abe3c0465a318f85aaeaeca6ff6f26fe21",
  "item_order_matches_baseline_read0": true,
  "item_sets": {
    "dev-S1": 636
  },
  "memo_scope": "one worker per read",
  "modes": [
    "none"
  ],
  "operations_file": "OPERATIONS_R1ROUTE.md",
  "operator_path": "7.py",
  "operator_sha256": "97c8e6dfe33e7fd2988dc44e740f7a3b19627259b8f86827598ed368e1659e22",
  "plan_sha256": "a44d88c837053e42ab670a56c518eadff1221b54b134593126642945a86eaf18",
  "read_settings": [
    {
      "arm": "tower",
      "expected": 636,
      "modes": [
        "none"
      ],
      "perception_memo": "on",
      "perception_memo_modules": [
        "g3t"
      ],
      "perception_memo_verify_ids": [],
      "save_own_depth": false,
      "stage1_select_rule": "candidates_argmax",
      "types": [
        3,
        0,
        1,
        2,
        4
      ]
    }
  ],
  "return_margin": 1200,
  "rules": [
    "candidates_argmax"
  ],
  "save_own_depth": false,
  "sequence": [
    [
      0,
      3
    ],
    [
      0,
      0
    ],
    [
      0,
      1
    ],
    [
      0,
      2
    ],
    [
      0,
      4
    ]
  ],
  "stop_margin": 1800,
  "token": "dc76460c3a164",
  "walltime": "05:00:00"
}
C600_EOF
cat > "$S/d.py" <<'C600_EOF'
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

C600_EOF
cat > "$S/d2.py" <<'C600_EOF'
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
check('prepare.types_camera', inputs.get('types') == cfg['order'][:3], inputs.get('types'))
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
check('6.descriptor', len(d) == 1 and d[0]['stage1_select_rule'] == 'candidates_argmax' and d[0]['perception_memo'] == 'on' and d[0]['expected'] == 450)
mem = op['memory_bound']()
check('6.memory_fits', mem['fits'] is True and mem['basis'] == 'fixed_g3t_shapes' and mem['sam_measurement_required'] is False)
items = json.loads(pay['items/devs1_routed.json'])['items']
from collections import Counter
c = Counter(r['question_type'] for r in items)
check('6.items_636', sum(c.values()) == 636 and c['object_abs_distance'] == 150 and c['room_size_estimation'] == 36
      and all(c[k] == 150 for k in ('camera_displacement', 'camera_rotation', 'camera_movement_direction')), dict(c))
check('6.types_order', [cfg['order'][t] for t in d[0]['types']] == cfg['order'][:3])
# GPU submission path (8.py submit -> BATCH.sh -> bundle 0.py -> job.main): pins it reads
check('sub.job_name', ("a15_cot_ap" + pub['token']) in json.loads((P/'2.json').read_text())['argv'][-1] if (P/'2.json').exists() else False)
R['failed'] = bad; R['passed'] = not bad
print(json.dumps(R, indent=1, sort_keys=True))
sys.exit(0 if not bad else 1)

C600_EOF
/usr/bin/python3 -I -s -B "$S/b.py" "$S" A "$S/bind.json" > "$S/build.out" 2>&1
cat "$S/BUILD.json"
