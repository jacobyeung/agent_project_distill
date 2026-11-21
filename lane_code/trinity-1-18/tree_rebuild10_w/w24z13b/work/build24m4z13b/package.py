from pathlib import Path
import json,hashlib,tarfile,os,resource
J=Path(__file__).resolve().parents[2];W=J/'work/build24m4z13b'
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
assert os.nice(0)>=10
assert len(json.loads((W/'results.json').read_text()))==52
assert (W/'extra.log').read_text().endswith('PASS: 52 total cases\n')
assert json.loads((W/'fallback_bound/result.json').read_text())['PASS']
assert len((J/'out/BUILD24M4Z13B_REPORT.md').read_text().splitlines())<8
# Capture every regular output/work file, including the frozen logs and scripts.
manifest={str(p.relative_to(J)):hashlib.sha256(p.read_bytes()).hexdigest()
          for folder in ('out','work') for p in sorted((J/folder).rglob('*')) if p.is_file()}
# The manifest is outside the two trees being archived; use it to verify every member.
(J/'inputs/JN5_PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
tmp=J/'tmp/package.tar'
with tarfile.open(tmp,'w',format=tarfile.PAX_FORMAT) as t:
    for folder in ('out','work'):t.add(J/folder,arcname=folder)
seen=set()
with tarfile.open(tmp,'r') as t:
    for item in t:
        if item.isfile():
            assert item.name in manifest,item.name
            f=t.extractfile(item);h=hashlib.sha256()
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
            assert h.hexdigest()==manifest[item.name],item.name
            seen.add(item.name)
assert seen==set(manifest),(len(seen),len(manifest))
h=hashlib.sha256()
with tmp.open('rb') as f:
    for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
digest=h.hexdigest();name='tree_rebuild_b24m4z13b_'+digest[:8]+'.tar';final=J/'out'/name
tmp.rename(final)
# This checksum is the final filesystem write of the build.
(final.with_name(final.name+'.sha256')).write_text(digest+'  '+name+'\n')
print(json.dumps(dict(package=str(final),sha256=digest,files=len(seen),bytes=final.stat().st_size,verified=True)))
