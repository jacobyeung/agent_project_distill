"""Package this task's bounded outputs; write the archive checksum last."""
import hashlib
import json
from pathlib import Path
import tarfile

J=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14')
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
paths=sorted(p for root in (J/'out',J/'work') for p in root.rglob('*'))
assert all(not p.is_symlink() for p in paths)
assert not any(p.suffix=='.tar' or p.name.endswith('.tar.sha256') for p in paths)
files=[p for p in paths if p.is_file()]
size=sum(p.stat().st_size for p in files)
assert size<16_000_000, ('Unexpected package size; stop before bulk IO',size)
manifest=J/'out/PACKAGE_CONTENTS.json'
assert not manifest.exists()
manifest.write_text(json.dumps(dict(schema='admit-test-package-v1',
    excludes='The archive and its checksum cannot include themselves. This manifest hashes every other packaged file.',
    files={str(p.relative_to(J)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}),indent=2,sort_keys=True)+'\n')
files.append(manifest)
planned={str(p.relative_to(J)):sha(p) for p in files}
temporary=J/'out/.build24m4z14_package.tar'
with tarfile.open(temporary,'x',format=tarfile.PAX_FORMAT) as t:
    for directory in sorted({J/'out',J/'work',*(p for p in paths if p.is_dir())}):
        t.add(directory,arcname=str(directory.relative_to(J)),recursive=False)
    for p in sorted(files): t.add(p,arcname=str(p.relative_to(J)),recursive=False)
observed={}
with tarfile.open(temporary,'r') as t:
    for member in t:
        if member.isdir():continue
        assert member.isfile()
        with t.extractfile(member) as f: observed[member.name]=hashlib.file_digest(f,'sha256').hexdigest()
assert observed==planned, 'Package content verification failed'
h=sha(temporary)
final=J/'out'/('tree_rebuild_b24m4z14_'+h[:8]+'.tar')
assert not final.exists()
temporary.rename(final)
checksum=Path(str(final)+'.sha256')
assert not checksum.exists()
# No file writes follow this checksum.
checksum.write_text(h+'  '+final.name+'\n')
print(json.dumps(dict(archive=str(final),sha256=h,checksum=str(checksum),
                     members=len(planned),archive_bytes=final.stat().st_size,content_verified=True),indent=2))
