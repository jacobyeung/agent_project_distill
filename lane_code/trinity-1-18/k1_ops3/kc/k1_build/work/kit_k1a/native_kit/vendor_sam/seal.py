"""Check a kit seal with no imports from its implementation."""
import sys,json,hashlib
from pathlib import Path
root=Path(sys.argv[1]).resolve()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
seal=json.loads((root/'SEAL.json').read_text())
if sha(root/'SHA256SUMS')!=seal['sha256sums_sha256']:raise SystemExit('Seal manifest mismatch')
count=0
for line in (root/'SHA256SUMS').read_text().splitlines():
 h,name=line.split('  ',1);p=(root/name).resolve()
 if not p.is_relative_to(root) or sha(p)!=h:raise SystemExit('Pin mismatch: '+name)
 count+=1
if count!=seal['files']:raise SystemExit('Seal count mismatch')
print('Verified',count,'files')
