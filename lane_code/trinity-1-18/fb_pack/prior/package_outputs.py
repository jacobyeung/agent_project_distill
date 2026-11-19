"""Package reviewable artifacts and verify their bytes, without external writes."""
import hashlib,json,tarfile
from pathlib import Path
W=Path(__file__).resolve().parent;O=W/'out'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
files=['census_source.py','parse_direction.py','analyze_prior.py','loader_boundary.py','finalize.py','package_outputs.py','manual_review.py',
 'out/REPORT.md','out/PRIOR_DELTA.json','out/PRIOR_DELTA.json.sha256','out/CENSUS.json','out/CENSUS.json.sha256',
 'out/SOURCE_CENSUS.json','out/LOADER_BOUNDARY.json','out/READ40.md','out/READ40_KEYS.tsv','out/MANUAL_REVIEW.json',
 'out/EVIDENCE_PIN.json','out/EVIDENCE_S400.md','out/DIRECTION_ROWS.tsv.gz','out/PARSED_ROWS.tsv.gz','out/SOURCE_SCAN.log','out/ANALYSIS.log']
assert all((W/p).is_file() for p in files)
records=[dict(path=str(W/p),archive_path=p,sha256=sha(W/p),bytes=(W/p).stat().st_size) for p in files]
assert sum(r['bytes'] for r in records)<400_000_000
manifest={'schema':'fbp-prior-package-v1','status':'BLOCKED_TREE_CHANGE_REQUIRED','inputs':records,'production_delta_runnable':False,'native_draw_verification':'MISSING'}
(O/'PACKAGE.json').write_text(json.dumps(manifest,indent=2)+'\n')
files.append('out/PACKAGE.json')
archive=O/'fbp_prior.tar'
with tarfile.open(archive,'w') as tar:
 for name in files:tar.add(W/name,arcname=name,recursive=False)
with tarfile.open(archive,'r') as tar:
 assert tar.getnames()==files
 for rec in records:
  f=tar.extractfile(rec['archive_path']);h=hashlib.sha256()
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
  assert h.hexdigest()==rec['sha256'],rec['archive_path']
h=sha(archive)
(O/'fbp_prior.tar.sha256').write_text(h+'  fbp_prior.tar\n')
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file())
assert size<1_000_000_000,size
(W/'STATUS.md').write_text('Final stage: Packaged the authenticated source census, 40 manually reviewed rows, option comparison, blocked delta, code-line change specification, and reproducible scripts in out/fbp_prior.tar. Verified every archived member and wrote the archive SHA256; the workspace remains under 1 GB. The sealed loader cannot express the selected policy, and its bound population is incomplete, so native before/after draw verification and an executable delta remain MISSING. No external files, tree, config, jobs, or sessions changed.\n')
print(json.dumps(dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,workspace_bytes=size,members=len(files))))
