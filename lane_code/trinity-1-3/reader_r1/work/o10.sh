set -euo pipefail
P=/project/community/jjyeung/c3cc59fb4aae0
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['full_reader_passed'] is True
assert c['full_reader']['passed'] is True and c['full_reader']['device']=='cpu'
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('dev-S1','room_scene0155_00'),('R0-dev','r0_015bd4aaf6870d79bade')]
assert all(r['passed'] is True and r['record']['complete'] is True and r['record']['output']['finish']=='eos' for r in rows)
print('full_reader_passed=true')
for r in rows:print(r['set'],r['item'],r['record']['output']['finish'],r['ground_truth_score']['score'])
print('CPU.json sha', sha(p/'a/c/CPU.json'))
PYCODE
