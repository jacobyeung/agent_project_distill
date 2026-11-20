from common import *
import tarfile
r=J.load(L/'work/build24m4j/resolver/resolved_n.json')
p=Path(r['archive']['path'].replace(str(W/'w24j'),str(L)))
assert J.sha(p)==r['archive']['sha256']
found={}
with tarfile.open(p) as archive:
 for h,v in r['small_files'].items():
  raw=archive.extractfile(v['member']).read()
  assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==h
  dest=D/'inputs'/h
  if not dest.exists():dest.write_bytes(raw)
  found[h]=str(dest)
J.write(D/'METADATA_RECOVERY.json',dict(archive=J.sha(p),members=found,scope='Member hashes verified; rewritten fixture member hashes are not original missing production pins'))
print('recovered',len(found),'authenticated archive members')
