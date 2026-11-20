from pathlib import Path
import json,hashlib,tarfile,os
J=Path.cwd();W=J/'work/enospc';O=J/'out'
required=[O/'ENOSPC_24M4Z.md',O/'ENOSPC_24M4Z.json',O/'jn2.sh',O/'KIT_CHANGE_24M4Z.patch',O/'BUILD24M4Z_REPORT.md']
# Inventory test artifacts before building the archive. Preserve every test failure.
files=required+sorted(p for p in W.rglob('*') if p.is_file())
assert not any(p.is_symlink() for p in files)
assert not any(p.name=='fill' for p in files)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
manifest={str(p.relative_to(J)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in files}
m=W/'package_members.json';m.write_text(json.dumps(manifest,indent=2)+'\n');files.append(m)
pending=O/'tree_rebuild_b24m4z_pending.tar'
with tarfile.open(pending,'w',format=tarfile.PAX_FORMAT) as t:
 for p in files:t.add(p,arcname=str(p.relative_to(J)),recursive=False)
# Verify the entire tar against the exact member payloads before the final rename/checksum.
with tarfile.open(pending) as t:
 members=t.getmembers();assert len(members)==len(files)
 for member in members:
  p=J/member.name;assert member.isfile() and member.size==p.stat().st_size
  h=hashlib.sha256()
  with t.extractfile(member) as f:
   for b in iter(lambda:f.read(1<<20),b''):h.update(b)
  assert h.hexdigest()==digest(p),member.name
h=digest(pending);target=O/('tree_rebuild_b24m4z_'+h[:8]+'.tar');assert not target.exists();os.rename(pending,target)
# The checksum is deliberately the last filesystem write in this build.
(target.with_name(target.name+'.sha256')).write_text(h+'  '+target.name+'\n')
print(json.dumps(dict(package=str(target),sha256=h,bytes=target.stat().st_size,members=len(files),verified=True)))
