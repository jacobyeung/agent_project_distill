from pathlib import Path
import hashlib,json,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out';archive=O/'sb_fhalias2.tar'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
for label in ('before','after'):
 for line in (O/('TREE_'+label.upper()+'.sha256')).read_text().splitlines():
  h,name=line.split('  ',1);assert sha(W/'work'/('tree_'+label)/name)==h,name
count=0
with tarfile.open(archive,'r:') as tar:
 for member in tar:
  assert not member.issym() and not member.islnk(),member.name
  if member.isfile():
   count+=1
   with tar.extractfile(member) as f:
    h=hashlib.sha256()
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
   assert h.hexdigest()==sha(W/member.name),member.name
assert len((O/'FHALIAS2_REPORT.md').read_text().splitlines())<=30
assert sha(archive)==(O/'sb_fhalias2.tar.sha256').read_text().split()[0]
for p in O.glob('*.json'):
 data=json.loads(p.read_text());assert data.get('input_sha256'),str(p)
text=f'PASS: {count} archived regular files match their workspace bytes. Report length and SHA-256 sidecar verified. All review evidence JSON includes input_sha256.\n'
(O/'ARCHIVE_CHECK2.txt').write_text(text)
print(text,end='');print('sha256',sha(archive));print('bytes',archive.stat().st_size)
