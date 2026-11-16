"""Refresh evidence without changing packaged job sources."""
from pathlib import Path
import hashlib
import sys
import tarfile
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
from adapter import dump,load,pin,sha
family=load(B/'out/FAMILY.json');package=load(B/'out/PACKAGE.json')
assert sha(B/'out/c.tar')==family['code']['sha256']==package['code']['sha256']
assert sha(B/'out/FAMILY.json')==package['family']['sha256']
with tarfile.open(B/'out/c.tar') as stream:
    members=stream.getmembers()
    for member in members:
        assert member.isfile()
        assert hashlib.sha256(stream.extractfile(member).read()).hexdigest()==sha(B/'code'/member.name)
for name,value in family['code_sources'].items():assert sha(B/'code'/name)==value
config=load(B/'out/packet/CONFIG.json')
assert config['family']['sha256']==sha(B/'out/FAMILY.json')
assert config['assets']['sha256']==sha(B/'out/ASSETS.json')
dump(B/'out/PACKAGE_VERIFICATION.json',dict(passed=True,members=len(members),code=pin(B/'out/c.tar'),family=pin(B/'out/FAMILY.json'),packet=pin(B/'out/packet/PACKET.json')))
cli='work/rh_cli_complete'
for name in ('REPORT.json','REPORT.md'):(B/name).write_bytes((B/cli/'report'/name).read_bytes())
for source,target in [('work/rh_final/RESULT.json','out/rehearsal/LOGIC_RESULT.json'),(cli+'/RESULT.json','out/rehearsal/CLI_RESULT.json'),('work/rh_final/PROOF.json','out/PROOF_CPU.json')]:
    (B/target).write_bytes((B/source).read_bytes())
tests=load(B/'out/TESTS.json');tests['new']['log']=pin(B/'out/tests/final_verified.log');tests['proof_comparator']=pin(B/'out/PROOF_CPU.json')
dump(B/'out/TESTS.json',tests)
owned=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not p.is_symlink())
dump(B/'out/STORAGE.json',dict(owned_bytes=owned,limit_bytes=8000000000,passed=owned<8000000000))
print('Package, source and packet hashes verified; evidence refreshed.')
