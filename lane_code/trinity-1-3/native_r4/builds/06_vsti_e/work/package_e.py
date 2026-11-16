"""Package the proof-first wrapper while preserving the reference archive."""
from pathlib import Path
import hashlib,sys,tarfile,json
B=Path(__file__).resolve().parents[1];S=B.parent/'04_vsti_d'
sys.path.append(str(B/'code'))
from adapter import dump,load,pin,sha
import engine
expected='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f'
assert sha(B/'out/d.tar')==sha(S/'out/d.tar')==expected
with tarfile.open(B/'out/c.tar','w') as archive:
    for p in sorted((B/'code').rglob('*')):
        if not p.is_file():continue
        info=tarfile.TarInfo(str(p.relative_to(B/'code')))
        info.size=p.stat().st_size;info.mtime=0;info.mode=p.stat().st_mode&0o777
        with p.open('rb') as stream:archive.addfile(info,stream)
family=load(S/'out/FAMILY.json');family['code']=pin(B/'out/c.tar');family['code_sources']=engine.source_pins()
family['added']['c'].update(sha256=sha(B/'out/c.tar'),bytes=(B/'out/c.tar').stat().st_size)
dump(B/'out/FAMILY.json',family);dump(B/'out/ADDITIONS.pending.json',family['added'])
dump(B/'out/PACKAGE.json',dict(code=pin(B/'out/c.tar'),reference=pin(B/'out/d.tar'),family=pin(B/'out/FAMILY.json'),launch_ready=family['launch_ready']))
with tarfile.open(B/'out/c.tar') as archive:
    assert {m.name for m in archive if m.isfile()}=={str(p.relative_to(B/'code')) for p in (B/'code').rglob('*') if p.is_file()}
    for member in archive:
        if member.isfile():assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==sha(B/'code'/member.name)
changes=[k for k,v in family['code_sources'].items() if load(S/'out/FAMILY.json')['code_sources'].get(k)!=v]
assert changes==['o.py']
dump(B/'out/PACKAGE_VERIFY.json',dict(passed=True,package=pin(B/'out/PACKAGE.json'),source_pins_equal=True,archive_members_verified=True,changed_production_files=changes,reference_byte_identical=True,reference_source=pin(S/'out/d.tar')))
print(json.dumps(load(B/'out/PACKAGE.json'),indent=2))
