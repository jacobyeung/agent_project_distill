"""Verify all D400/D544 differences against the permitted fields and byte pins."""
import hashlib
import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parent.parent
sys.path.insert(0, str(ROOT / 'dbuild'))
from build_support import read_tar

sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda path: json.loads(path.read_text())
reports = {s: read(WORK / ('actual%d/BUILD.json' % s))['D'] for s in (400, 544)}
deliveries, payloads, plans, publics, packages = {}, {}, {}, {}, {}
headers = {}
for step, report in reports.items():
    raw = (Path(report['delivery_dir']) / '1.tgz').read_bytes()
    assert sha(raw) == report['delivery_sha256'] and len(raw) == report['delivery_bytes']
    members = read_tar(raw)
    d = deliveries[step] = {m.name: data for m, data in members}
    pay_members = read_tar(d['0.tgz'])
    p = payloads[step] = {m.name: data for m, data in pay_members}
    assert len(d) == len(members) and len(p) == len(pay_members)
    headers[step] = [(m.name, m.mode, m.uid, m.gid, m.uname, m.gname, m.mtime,
                      m.type, m.linkname, m.pax_headers) for m, data in members + pay_members]
    plan = plans[step] = json.loads(p['9.json'])
    pub = publics[step] = json.loads(d['0.json'])
    package = packages[step] = json.loads(d['PACKAGE.json'])
    assert d['0.json'] == d['CONFIG.json']
    assert pub['token'] == package['token'] == plan['token'] == report['token']
    assert pub['payload_bytes'] == len(d['0.tgz'])
    assert pub['payload_sha256'] == sha(d['0.tgz']) == report['payload_sha256']
    assert pub['plan_sha256'] == sha(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()) == report['plan_sha256']
    assert all(pin == dict(bytes=len(p[name]), sha256=sha(p[name]))
               for name, pin in plan['payload_pins'].items())
    assert all(sha(d[name]) == pin for name, pin in package['files'].items())
    items = json.loads(p['items/dist580.json'])
    assert items['count'] == len(items['items']) == 580
    assert p['items/dist580.json'] == (ROOT / 'dbuild/evidence/items/dist580.json').read_bytes()
    assert report['walltime'] == '04:00:00' and report['budget_fits'] is False
    assert report['budget_gpu_seconds'] == 19595
    assert plan['stop_margin'] == 1800
    assert report['source_sha256'] == sha((ROOT / 'in/B5_1.tgz').read_bytes())

assert headers[400] == headers[544], 'Archive metadata differs'
assert deliveries[400].keys() == deliveries[544].keys()
assert payloads[400].keys() == payloads[544].keys()
assert publics[400].keys() == publics[544].keys() == {'token', 'payload_bytes', 'payload_sha256', 'plan_sha256'}
assert packages[400].keys() == packages[544].keys() == {'token', 'files'}
assert packages[400]['files'].keys() == packages[544]['files'].keys()
assert {name for name in payloads[400] if payloads[400][name] != payloads[544][name]} == {'9.json'}
assert {k: v for k, v in plans[400].items() if k not in ('token', 'export_binding')} == {
    k: v for k, v in plans[544].items() if k not in ('token', 'export_binding')}
for key in ('items_sha256', 'walltime', 'budget_fits', 'budget_gpu_seconds', 'timing', 'source_sha256'):
    assert reports[400][key] == reports[544][key], key

checks = dict(passed=True, steps=[400, 544], delivery_members=len(deliveries[400]),
              payload_members=len(payloads[400]), items=580, walltime='04:00:00',
              budget_fits=False, budget_gpu_seconds=19595,
              archive_metadata_unchanged=True, all_payload_pins_verified=True,
              public_fields_all_derived=True, package_fields_all_derived=True,
              source_sha256=reports[400]['source_sha256'],
              operator_sha256=sha(deliveries[400]['a/6.py']),
              items_sha256=sha(payloads[400]['items/dist580.json']),
              settings_sha256=sha(deliveries[400]['a/0.json']),
              builds={str(s): dict(token=r['token'], delivery_sha256=r['delivery_sha256'],
                                  build=str(WORK / ('actual%d/BUILD.json' % s))) for s, r in reports.items()})
(WORK / 'DIFF_CHECKS.json').write_text(json.dumps(checks, sort_keys=True, indent=2) + '\n')
diff = ROOT / 'DIFF_D400_VS_D544.txt'
assert diff.read_text().startswith('PASS: step 400 versus step 544;')
with diff.open('a') as out:
    out.write('\nAdditional D checks: %d delivery members and %d payload members; archive metadata unchanged.\n' % (checks['delivery_members'], checks['payload_members']))
    out.write('0.json and CONFIG.json contain only verified token, payload length/hash and plan hash; PACKAGE.json contains only verified token and member hashes.\n')
    out.write('Every payload pin and delivery pin matches the actual bytes.\n')
    out.write('Items: 580; walltime: 04:00:00; budget: 19595 + 1800 stop-margin seconds; budget_fits=false in both.\n')
    for key in ('source_sha256', 'operator_sha256', 'items_sha256', 'settings_sha256'):
        out.write('%s: %s\n' % (key, checks[key]))
    for step in (400, 544):
        out.write('D%d BUILD.json: %s\n' % (step, checks['builds'][str(step)]['build']))
print(json.dumps(checks, sort_keys=True, indent=2))
