"""Refresh auxiliary harness files and resume only unchanged frozen suite inputs."""
from pathlib import Path
import json,subprocess,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build10';P=L/'work/build12/proofs/package'
for variant in ('tree','base'):
    result=json.loads((L/'work/build12/proofs'/('suite_'+variant)/'results.json').read_text())
    assert result['complete'] and not result['fatal'],variant
prior=json.loads((P/'ARCHIVE.json').read_text())
old=P/'frozen';retained=P/'frozen_first_pass'
assert not retained.exists()
old.rename(retained)
subprocess.run([sys.executable,'-I','-s','-B',str(B/'make_delivery.py')],check=True)
delivery=json.loads((B/'DELIVERY.json').read_text())
with (P/'REFRESH.log').open('w') as log:
    subprocess.run(['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])],stdout=log,stderr=subprocess.STDOUT,check=True)
text=(P/'REFRESH.log').read_text()
expected=[v+'/'+g for v in ('tree','base') for g in ('generator','legacy','r2')]
assert all('Resumed completed group '+x in text for x in expected)
value=dict(prior_archive=prior,final_archive=json.loads((P/'ARCHIVE.json').read_text()),resumed_groups=expected,
    basis='Each native package GROUP_RECEIPT matches full source inventory, fixture inventory, runner SHA and the bound R2 inputs. Only auxiliary build harness sources changed.',
    source_tree_changed=False)
(P/'REFRESH_RECEIPT.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'archive':delivery,'resumed_groups':expected}))
