"""Verify archive bytes, members, and current validation-source hashes."""
from pathlib import Path
import hashlib
import tarfile
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1];P.sha(__file__)
package=P.load(root/'out/PACKAGE.json')
archive=P.checked(dict(path=package['archive'],sha256=package['sha256']))
with tarfile.open(archive) as tar:
    members=tar.getmembers()
    assert sorted(m.name for m in members)==sorted(package['members'])
    for member in members:
        assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
        assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==P.sha(root/member.name),member.name
checked=0
for name in ('TEST_RESULTS','CPU_PROOF','PARITY','GATE_CHECK','REMOVE_CHECK','SERVING_CHECK'):
    receipt=P.load(root/'out'/f'{name}.json')
    for path,sha in receipt['input_sha256'].items():
        # Source/input hashes must match the code and fixtures used in this delivery.
        P.checked(dict(path=path,sha256=sha));checked+=1
P.write(root/'out/DELIVERY_CHECK.json',dict(status='PASS',archive=package['sha256'],members=len(members),
    dependency_hash_checks=checked,command='PYTHONPATH=overlay python -B scripts/verify_package.py'))
print('Archive members and validation dependencies verified:',len(members),checked)
