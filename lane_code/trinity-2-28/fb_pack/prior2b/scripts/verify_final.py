"""Verify final archive members, checksum, runtime proof, and workspace size."""
from pathlib import Path
import json,hashlib,tarfile,os
W=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p))
archive=W/'out/fbp_prior2b.tar';package=W/'out/PACKAGE.json';checksums=W/'out/fbp_prior2b.tar.sha256';members=json.loads(package.read_text())['members']
expected=checksums.read_text().split()[0];actual=sha(archive);assert actual==expected
seen=set();count=0
with tarfile.open(archive,'r|') as tar:
 for member in tar:
  assert member.isfile(),member.name
  assert member.name not in seen;seen.add(member.name)
  h=hashlib.sha256();f=tar.extractfile(member)
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  wanted=sha(package) if member.name=='out/PACKAGE.json' else members[member.name]['sha256']
  assert h.hexdigest()==wanted,member.name;count+=1
assert seen==set(members)|{'out/PACKAGE.json'}
for name,item in members.items():assert sha(W/name)==item['sha256'],name
report=W/'out/REPORT.md';assert len(report.read_text().splitlines())<=80
proof=json.loads((W/'out/PROOF.json').read_text());tests=json.loads((W/'out/TESTS.json').read_text())
assert proof['verdict']=='NO_GO' and proof['production_all_cell_gate']=='MISSING'
assert proof['fixture']['cells_tested']==31 and proof['fixture']['status']=='PASS'
assert all(v['production_status']=='MISSING' for v in proof['cells'].values())
assert all(v['status']=='PASS' for v in tests['added_tests']) and not tests['worsened_existing_tests']
current_script=sha(W/'out/prove_on_prepared.py')
for p in [W/'work/final_gate/RESULT.json',W/'out/CHECKER_NEGATIVE_TESTS.json']:
 data=json.loads(p.read_text());matches=[v for v in data['inputs'] if v['path']==str(W/'out/prove_on_prepared.py')]
 assert matches and matches[0]['sha256']==current_script,p
size=0;files=0
for root,dirs,names in os.walk(W,followlinks=False):
 dirs[:]=[d for d in dirs if d not in ('.git','__pycache__') and not (Path(root)/d).is_symlink()]
 for name in names:
  p=Path(root)/name
  if p.is_file() and not p.is_symlink():size+=p.stat().st_size;files+=1
assert size<30*1024**3,size
result=dict(status='PASS',archive_sha256=actual,archive_bytes=archive.stat().st_size,members_verified=count,workspace_file_bytes=size,workspace_files=files,report_lines=len(report.read_text().splitlines()),
 command='OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python scripts/verify_final.py',
 inputs=[pin(p) for p in [Path(__file__),archive,package,checksums,W/'out/PROOF.json',W/'out/TESTS.json',report,W/'out/prove_on_prepared.py',W/'work/final_gate/RESULT.json',W/'out/CHECKER_NEGATIVE_TESTS.json']])
(W/'out/ARCHIVE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','command')},indent=2))
