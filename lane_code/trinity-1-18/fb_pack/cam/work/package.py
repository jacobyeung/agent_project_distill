from common import *
import tarfile,io
seen=start('package.py')
checks=load(ROOT/'out/CHECKS.json')
assert checks['status']=='PASS_WITH_EVAL_EXCLUSIONS'
# Hash the finalized deliverables, then include dependencies at their content-addressed u/ paths.
files=sorted(p for directory in ['work','out'] for p in (ROOT/directory).rglob('*') if p.is_file() and not p.is_symlink() and p.name not in ['fbp_cam.tar','fbp_cam.tar.sha256','PACKAGE.json'] and p.suffix!='.log')
files.append(ROOT/'STATUS.md')
inputs={str(p.relative_to(ROOT)):pin(p) for p in files}
u={p.name:p.resolve() for p in (ROOT/'u').iterdir() if p.is_file()}
for h,p in u.items():pin(p,h)
# Budget includes all files presently in the workspace and this uncompressed tar.
workspace=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
internal={p.resolve():str(p.relative_to(ROOT)) for p in files}
expected_payload=sum(p.stat().st_size for p in files)+sum(p.stat().st_size for p in u.values() if p not in internal)
assert workspace+expected_payload+3_000_000<300_000_000,(workspace,expected_payload)
out=ROOT/'out/fbp_cam.tar'
with tarfile.open(out,'w',format=tarfile.PAX_FORMAT) as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 for h,p in sorted(u.items()):
  name='u/'+h
  if p in internal:
   ti=tarfile.TarInfo(name);ti.type=tarfile.LNKTYPE;ti.linkname=internal[p];tar.addfile(ti)
  else:
   ti=tarfile.TarInfo(name);ti.size=p.stat().st_size;ti.mode=0o644
   with p.open('rb') as f:tar.addfile(ti,f)
archive_pin=pin(out)
(ROOT/'out/fbp_cam.tar.sha256').write_text(archive_pin['sha256']+'  out/fbp_cam.tar\n')
# Verify bytes directly in the archive; extraction would duplicate the package unnecessarily.
verified=0
with tarfile.open(out,'r') as tar:
 for name,entry in inputs.items():
  f=tar.extractfile(name);assert hashlib.file_digest(f,'sha256').hexdigest()==entry['sha256'];verified+=1
 for h in u:
  f=tar.extractfile('u/'+h);assert hashlib.file_digest(f,'sha256').hexdigest()==h;verified+=1
actual=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
assert actual<300_000_000,actual
write('out/PACKAGE.json',dict(status='PASS',archive=archive_pin,archive_bytes=out.stat().st_size,workspace_bytes_before_package_receipt=actual,verified_members=verified,files=inputs,content_addressed_dependencies={h:dict(source=str(p),sha256=h) for h,p in sorted(u.items())},scope='Rows, gzip shards, complete reports, code, and all active envelope metadata bytes are included. u/ entries for bundled outputs are tar hardlinks; external metadata are regular files. No RGB or raster bytes are included. Checksum sidecar and this receipt are outside the archive to avoid self-reference.'))
print(json.dumps(dict(archive=archive_pin,archive_bytes=out.stat().st_size,workspace_bytes=actual,verified_members=verified)),flush=True)
