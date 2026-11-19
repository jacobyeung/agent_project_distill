"""Small recorder/store protocol fixture, explicitly not native preparation."""
from pathlib import Path
import json
import os
import sys

L = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(L / 'work/tree'))
from student_pilot.preparation_reads import Recorder, canonical
from student_pilot.preparation_store import Store, receipt

output = Path(sys.argv[1])
output.mkdir(mode=0o700)
source = output / 'input.txt'
source.write_bytes(b'row-b\nrow-a\n')
files = {'rows': source, 'fixture-code': Path(__file__)}
for name in ('preparation_reads.py', 'preparation_store.py'):
    files['code/' + name] = L / 'work/tree/student_pilot' / name
r = Recorder({'sort': True}, files=files, environment={'RULE': 'lexical-v1'})
with r.python_io_guard():
    for role in files:
        if role != 'rows':
            r.read_file(role)
    rows = r.read_file('rows').decode().splitlines()
    assert r.environment('RULE') == 'lexical-v1'
    if r.config['sort']:
        rows.sort()
key = r.key
store = Store(output / 'store', create=True)
payload = store.put_bytes(canonical(rows))
metadata = store.put_bytes(receipt({'schema': 'protocol-fixture-only', 'rows': {'object': payload['sha256']}}), kind='receipt')
root = store.publish(key, [{'name': 'rows.json', **payload}, {'name': 'receipt.json', **metadata}])
result = dict(scope='protocol fixture only; NOT native prepare-only', root_digest=root, key=key,
              store=str(store.path), hostname=os.environ.get('HOSTNAME'), tmpdir=os.environ.get('TMPDIR'))
(output / 'telemetry.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
