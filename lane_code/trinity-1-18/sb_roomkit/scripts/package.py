"""Package the CPU delivery, excluding caches and recursive inclusion of the archive."""
from common import *
import tarfile
files=[]
for top in ['scripts','configs','tests','vendor','evidence','review','out']:
 for p in sorted((W/top).rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  if p.name.startswith('sb_roomkit.tar') or p.name=='DELIVERY_SHA256.txt':continue
  files.append(p)
for name in ['OPERATOR.md','KIT_SPEC_room_pricing.md','STATUS.md']:
 files.append(W/name)
ledger=W/'out/DELIVERY_SHA256.txt';ledger.write_text(''.join(f'{sha(p)}  {p.relative_to(W)}\n' for p in sorted(files)))
archive=W/'out/sb_roomkit.tar'
with tarfile.open(archive,'w') as tar:
 for p in sorted(files)+[ledger]:tar.add(p,arcname=str(p.relative_to(W)),recursive=False)
h=sha(archive);(W/'out/sb_roomkit.tar.sha256').write_text(h+'  sb_roomkit.tar\n')
# Verify archive contents against the delivery ledger without extracting anything.
with tarfile.open(archive) as tar:
 for line in ledger.read_text().splitlines():
  expected,name=line.split('  ',1);member=tar.extractfile(name);actual=hashlib.sha256(member.read()).hexdigest();assert actual==expected,name
print(h,archive,archive.stat().st_size,'bytes; all member digests verified')
