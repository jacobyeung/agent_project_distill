"""Read-only validation of the delivered archive and its evidence inventory."""
import hashlib, json, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()
archive=OUT/'fbp_pointD.tar'
sidecar=OUT/'fbp_pointD.tar.sha256'
expected,name=sidecar.read_text().split()
assert name==archive.name and sha(archive)==expected
manifest=json.loads((OUT/'PACKAGE.json').read_text())
expected_members=set(manifest['archive_members'])|{'out/PACKAGE.json'}
with tarfile.open(archive,'r') as tf:
    members=tf.getmembers()
    assert len(members)==len(expected_members)
    assert {p.name for p in members}==expected_members
    for p in members:
        assert p.isfile() and not Path(p.name).is_absolute() and '..' not in Path(p.name).parts
        raw=tf.extractfile(p).read()
        assert hashlib.sha256(raw).hexdigest()==sha(ROOT/p.name)
        if p.name!='out/PACKAGE.json':
            assert hashlib.sha256(raw).hexdigest()==manifest['input_sha256'][str(ROOT/p.name)]
report=OUT/'REPORT.md'
assert len(report.read_text().splitlines())<=80
used=sum(p.stat().st_size for p in ROOT.rglob('*') if not p.is_symlink() and p.is_file())
assert used<10_000_000_000,used
result=dict(command='bash code/run.sh check_delivery',
    input_sha256={str(p):sha(p) for p in (archive,sidecar,OUT/'PACKAGE.json',report,Path(__file__))},
    status='PASS',archive_bytes=archive.stat().st_size,archive_members=len(expected_members),
    report_lines=len(report.read_text().splitlines()),workspace_file_bytes=used)
(OUT/'DELIVERY_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
