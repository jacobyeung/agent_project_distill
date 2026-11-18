from pathlib import Path
import sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
base=inventory(L/'work/base/tree_b01ce449');fixtures=inventory(L/'fixtures')
original=L/'work/build9fix/test_runner.py';current=B/'test_runner.py'
assert original.read_text().replace('work/build9fix','work/n1fix2')==current.read_text()
checks=[]
for group in ('generator','legacy','r2'):
    path=B/'inherited/suite_base'/group/'GROUP_RECEIPT.json';v=json.loads(path.read_text())
    assert v['inputs']['source']==base
    assert v['inputs']['fixtures']==fixtures
    assert v['inputs']['runner_sha256']==hashlib.sha256(original.read_bytes()).hexdigest()
    checks.append(dict(group=group,receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),complete=v['complete']))
(B/'BASE_RESUME_PREFLIGHT.json').write_text(json.dumps(dict(verified=True,groups=checks),indent=2))
print('All base resume inputs match.')
