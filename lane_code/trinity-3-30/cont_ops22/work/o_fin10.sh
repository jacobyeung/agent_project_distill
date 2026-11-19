set -euo pipefail; umask 077
P=/project/community/jjyeung/okh7/a15_cot_apdd982cd5c4b25
test ! -e $P/a/10.json; test ! -e $P/a/1.txt
/usr/bin/python3 -B - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('/project/community/jjyeung/okh7/a15_cot_apdd982cd5c4b25')
d=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
c=json.loads((p/'2.json').read_text()); assert c['passed'] is True and c['time']=='04:00:00'
par=Path('/project/community/jjyeung/okh7/a15_cot_apdc863c3e6b41d/a/10.json'); pv=json.loads(par.read_text())
print('inputs',d(p/'a/1.json'),'2.json inputs',c['inputs'])
print('export',d(p/'a/export.json'),'parent export',pv['export_sha256'])
(p/'a/10.json').write_text(json.dumps(dict(passed=True,inputs_sha256=d(p/'a/1.json'),export_sha256=d(p/'a/export.json')))+'\n')
(p/'a/1.txt').write_text('0\n')
print(open(p/'a/10.json').read())
PY
