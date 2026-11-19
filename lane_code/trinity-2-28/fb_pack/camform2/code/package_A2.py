"""Package on authenticated PATCH_A2 only when its SHA256 companion exists."""
from pathlib import Path
import hashlib,json,difflib,subprocess,shutil,re,datetime,tarfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';directory=ROOT.parent/'patchA2/out';patch=directory/'PATCH_A2.patch'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p) for p in (Path(__file__),OUT/'SETUP.json',OUT/'PATCH_CAMFORM2.patch')}
expected=directory/'PATCH_A2.patch.sha256';companions=[]
for p in sorted(directory.glob('*')):
    if p.is_file() and ('sha256' in p.name.lower() or p.name=='SHA256SUMS'):
        text=p.read_text()
        for line in text.splitlines():
            fields=line.split()
            if fields and re.fullmatch('[a-f0-9]{64}',fields[0]) and ((len(fields)==1 and p.name in ('PATCH_A2.patch.sha256','PATCH_A2.sha256')) or (len(fields)>1 and Path(fields[-1].lstrip('*')).name=='PATCH_A2.patch')):
                companions.append((p,fields[0]))
archive_authentication=None
archive=directory/'fbp_patchA2.tar';archive_sha=directory/'fbp_patchA2.tar.sha256'
if not companions and patch.is_file() and archive.is_file() and archive_sha.is_file():
    entries=[line.split() for line in archive_sha.read_text().splitlines()]
    matches=[entry[0] for entry in entries if len(entry)>1 and Path(entry[-1].lstrip('*')).name==archive.name]
    assert len(matches)==1 and sha(archive)==matches[0],'A2 archive SHA256 differs'
    with tarfile.open(archive) as bundle:
        members=[m for m in bundle.getmembers() if m.name=='out/PATCH_A2.patch' and m.isfile()]
        assert len(members)==1,'A2 archive patch is missing or ambiguous'
        archived=bundle.extractfile(members[0]).read()
    assert archived==patch.read_bytes(),'A2 archive patch differs from delivered patch'
    patch_hash=hashlib.sha256(archived).hexdigest()
    companions.append((archive_sha,patch_hash))
    inputs[str(archive)]=matches[0]
    archive_authentication=dict(mode='sha256_sealed_archive_and_exact_patch_member',archive=str(archive),archive_sha256=matches[0],sha256_file=str(archive_sha),member='out/PATCH_A2.patch',patch_sha256=patch_hash)
result=dict(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/package_A2.py')
if not patch.is_file() or not companions:
    if patch.is_file():inputs[str(patch)]=sha(patch)
    result.update(status='MISSING',expected_patch=str(patch),expected_sha256_companion=str(expected),reason='The conditional A2 overlay requires the patch and an accompanying authenticated SHA256 entry.')
else:
    actual=sha(patch);inputs[str(patch)]=actual
    for p,h in companions:assert h==actual,(p,h,actual);inputs[str(p)]=sha(p)
    ro=ROOT.parent/'ro/orch_n30/tree_rebuild10_w/w24';manifest=ro/'out/TREE_FILES.sha256';inputs[str(manifest)]=sha(manifest)
    base=ROOT/'work/baseA2';new=ROOT/'work/newA2';names=[]
    for line in manifest.read_text().splitlines():
        h,name=line.split('  ',1);p=ro/'work/tree_r1'/name;assert sha(p)==h
        dest=base/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);names.append(name)
    def apply(tree,p,log):
        proc=subprocess.run(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(p)],cwd=tree,text=True,capture_output=True)
        (OUT/log).write_text(proc.stdout+proc.stderr);assert proc.returncode==0,(proc.stdout,proc.stderr)
    apply(base,patch,'patch_apply_baseA2.log');shutil.copytree(base,new);apply(new,OUT/'PATCH_CAMFORM2.patch','patch_apply_camform_A2.log')
    names=sorted({str(p.relative_to(new)) for p in new.rglob('*') if p.is_file()});chunks=[];files=[]
    for name in names:
        a=base/name;b=new/name;old=a.read_text() if a.exists() else '';fresh=b.read_text()
        if old!=fresh:
            chunks.extend(difflib.unified_diff(old.splitlines(keepends=True),fresh.splitlines(keepends=True),fromfile='a/'+name if a.exists() else '/dev/null',tofile='b/'+name))
            files.append(dict(path=name,base_sha256=sha(a) if a.exists() else None,new_sha256=sha(b)))
    overlay=OUT/'PATCH_CAMFORM2_ON_A2.patch';overlay.write_text(''.join(chunks));inputs[str(overlay)]=sha(overlay)
    verified=ROOT/'work/applied_A2';shutil.copytree(base,verified);apply(verified,overlay,'patch_apply_A2.log')
    for name in names:assert (verified/name).read_bytes()==(new/name).read_bytes(),name
    inputs.update({str(p):sha(p) for p in sorted(base.rglob('*')) if p.is_file()});inputs.update({str(p):sha(p) for p in sorted(new.rglob('*')) if p.is_file()})
    result.update(status='PASS',authentication=archive_authentication or {'mode':'patch_sha256_companion'},files=files,applies_with_fuzz_zero=True,verified_result_files=len(names),patch_sha256=actual,overlay_sha256=sha(overlay))
(OUT/'A2_PACKAGING.json').write_text(json.dumps(result,indent=2)+'\n')
p=OUT/'FILES_TOUCHED.json';v=json.loads(p.read_text());v['A2']={k:val for k,val in result.items() if k!='input_sha256'};v['input_sha256'][str(OUT/'A2_PACKAGING.json')]=sha(OUT/'A2_PACKAGING.json');p.write_text(json.dumps(v,indent=2)+'\n')
print(result['status'])
