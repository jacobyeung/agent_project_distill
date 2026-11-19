"""Archive the deliverables; write the archive digest to the adjacent report."""
import hashlib,json,tarfile
from pathlib import Path
out=Path(__file__).resolve().parent
report=out/'ALIAS_AUDIT_REPORT.md'
lines=report.read_text().splitlines()
assert len(lines)<=80
files=sorted(p for p in out.iterdir() if p.is_file() and p.name!='sb_alias.tar')
for p in files:
 if p.suffix=='.json':
  v=json.loads(p.read_text());assert v['status']=='MISSING' and v['inputs'] and not v['complete']
with tarfile.open(out/'sb_alias.tar','w') as t:
 for p in files:t.add(p,arcname='out/'+p.name,recursive=False)
h=hashlib.sha256()
with (out/'sb_alias.tar').open('rb') as f:
 for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
digest=h.hexdigest()
lines=[f'Archive SHA256: `{digest}` (`out/sb_alias.tar`).' if s.startswith('Archive SHA256:') else s for s in lines]
report.write_text('\n'.join(lines)+'\n')
with tarfile.open(out/'sb_alias.tar','r:') as t:
 for p in files:
  data=t.extractfile('out/'+p.name).read()
  if p!=report:assert hashlib.sha256(data).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest()
status=out.parent/'STATUS.md'
status.write_text(status.read_text().rstrip()+f' The output package is out/sb_alias.tar, SHA256 {digest}; all archived JSON bytes were verified against the adjacent files.\n')
print(json.dumps({'archive_sha256':digest,'files':len(files),'report_lines':len(lines),'bytes':(out/'sb_alias.tar').stat().st_size}))
