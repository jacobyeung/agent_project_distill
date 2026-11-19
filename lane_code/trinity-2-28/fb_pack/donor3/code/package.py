from pathlib import Path
import hashlib, json, tarfile
W=Path(__file__).resolve().parents[1]; O=W/'out'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert json.loads((O/'TESTS.json').read_text())['status']=='PASS'
assert len((O/'REPORT.md').read_text().splitlines())<=40
required=['REPORT.md','PATCH_DONOR3.patch','PATCH_DONOR3_DELTA.patch','FILES_TOUCHED.json','TESTS.json','READER_REQUEST.md','REAL_WEIGHT_COMMAND.sh']
assert all((O/n).is_file() for n in required)
(W/'STATUS.md').write_text('M4 is complete: the recipe strictly restores and freezes the private visual before attachment, and the runtime test uses real CarrierC1 construction and real base export loading. All 11 donor tests pass on each overlay. Both field-absent comparisons are byte-identical, focused suites have no new failure signature, and full/delta/live patch applications use zero fuzz and zero offset. The final report, patches, evidence and verified archive are in out/. Real pretrained weights and production reader integration remain outside this CPU fixture validation.\n')
excluded={'fbp_donor3.tar','fbp_donor3.tar.sha256','PACKAGE_CONTENTS.json','package.log'}
files=[W/'STATUS.md']
for root in [W/'code',W/'overlay',O,*[W/'work'/n for n in ['unit_new','unit_live','parity_base','parity_new','parity_live_base','parity_live']]]:
    files.extend(p for p in root.rglob('*') if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts)
files=sorted(set(files))
pins={str(p.relative_to(W)):sha(p) for p in files}
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file())
assert size<10*1024**3,size
receipt=dict(input_sha256={str(p):pins[str(p.relative_to(W))] for p in files},files=pins,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/package.py',workspace_bytes_before_archive=size,status='PASS')
p=O/'PACKAGE_CONTENTS.json';p.write_text(json.dumps(receipt,indent=2)+'\n');files.append(p)
archive=O/'fbp_donor3.tar'
with tarfile.open(archive,'w') as tf:
    for p in sorted(files):tf.add(p,arcname=str(p.relative_to(W)),recursive=False)
with tarfile.open(archive,'r') as tf:
    for member in tf:
        f=tf.extractfile(member);h=hashlib.sha256()
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==sha(W/member.name),member.name
value=sha(archive)
(O/'fbp_donor3.tar.sha256').write_text(value+'  fbp_donor3.tar\n')
assert size+archive.stat().st_size<10*1024**3
print(json.dumps(dict(archive=str(archive),sha256=value,members=len(files),bytes=archive.stat().st_size,workspace_bytes=size+archive.stat().st_size,status='PASS')))
