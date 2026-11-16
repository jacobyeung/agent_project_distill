from pathlib import Path
import json, tarfile, hashlib
B=Path(__file__).resolve().parents[1]
W=B.parents[1]/'work'
f=json.loads((W/'p9/metadata/FAMILY.json').read_text())
print('family keys', sorted(f))
print('assets keys', sorted(f['assets']))
for p in f['assets']['small_objects']:
    print('object', {k:v for k,v in p.items() if k!='members'}, 'members',len(p['members']), 'sample',list(p['members'].items())[:2])
print('contract', {k:v for k,v in f['worker_contract'].items() if k not in ('expected_keys','adapter_pins','geometry_captures')})
print('code pin count',len(f['code_pins']))
print('limit',f['limits'])
for name in ('metadata_e10fbb95487f3baf.tar','model_8005668fc14ce5ee.tar'):
    with tarfile.open(str(W/'obj'/name)) as t:
        names=t.getnames()
        print(name, 'members',len(names), 'sample', names[:6])
manifest=json.loads((W/'p9/native/geometry/GEOMETRY_MANIFEST.json').read_text())
print('geometry',len(manifest['records']),manifest['records'][0])
report=json.loads((W/'p9/native/probe/PILOT_REPORT.json').read_text())
print('report item',report['items'][0])
