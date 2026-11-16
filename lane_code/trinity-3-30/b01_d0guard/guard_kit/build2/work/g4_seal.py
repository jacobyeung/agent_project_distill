"""Reseal the production inventory; never walk the operator's rehearsal outputs."""
from pathlib import Path
import hashlib,json,sys,tarfile
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
from transport import regular_tar

baseline=read(B/'work/G4_BASELINE.json');family=read(O/'FAMILY.json')
members=baseline['code_manifest']['members']
assert set(members)==set(family['code_pins'])
changed=[name for name,pin in members.items() if sha(K/name)!=pin['sha256']]
assert changed==['transport.py','worker.py'],changed
assert all(sha(K/name)==expected for name,expected in family['code_pins'].items())
assert all('rehearsal' not in Path(name).parts and not name.endswith('.g2_orig.py') for name in members)
identity=read(O/'SOURCE_IDENTITY.json')
for row in identity['files']:
    path=B/row['file']
    assert path.is_relative_to(K)
    assert sha(path)==row['sha256']==row['current_sha256']
assert identity['all_equal']

archive=O/'code_g2.tar';inventory={}
with tarfile.open(archive,'w',dereference=True) as stream:
    for name in sorted(members):
        path=K/name
        assert path.is_file() and not path.is_symlink()
        info=tarfile.TarInfo(name);info.size=path.stat().st_size
        info.mode=0o755 if path.suffix=='.sh' else 0o644
        with path.open('rb') as source:stream.addfile(info,source)
        inventory[name]=dict(bytes=info.size,sha256=sha(path))
regular_tar(archive)
write(O/'CODE_MANIFEST.json',dict(file='out/code_g2.tar',sha256=sha(archive),bytes=archive.stat().st_size,
      members=inventory,hard_links=0,regular_only=True,deterministic_metadata=True))
assert read(O/'INPUT_MANIFEST.json')==baseline['input_manifest']
assert sha(O/'inputs_g2.tar')==baseline['input_manifest']['sha256']
sizing=read(O/'SIZING.json');sizing['code_archive_bytes']=archive.stat().st_size
write(O/'SIZING.json',sizing)
write(O/'G4_SEAL.json',dict(status='PASS',changed_production_members=changed,
      member_inventory_unchanged=True,rehearsal_files_excluded=True,operator_backups_excluded=True,
      input_archive_unchanged=True,source_identity_matches_recorded_hashes=True,
      code_sha256=sha(archive),family_sha256=sha(O/'FAMILY.json')))
print(json.dumps(read(O/'G4_SEAL.json')))
