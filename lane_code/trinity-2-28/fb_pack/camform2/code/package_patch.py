"""Create reviewable unified overlays and verify clean zero-fuzz application."""
from pathlib import Path
import hashlib,json,difflib,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';base=ROOT/'work/base';new=ROOT/'work/new'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
setup=json.loads((OUT/'SETUP.json').read_text());names=set(setup['base_plus_patchA_files'])|{'configs/r1_camera_trace_form_v1.json','student_pilot/r1_camera_trace_form.py','tests/test_r1_camera_trace_form.py','tests/test_r1_camera_trace_form2.py'}
def emit(before,after,target):
    chunks=[];files=[]
    for name in sorted(names):
        a=before/name;b=after/name
        old=a.read_text() if a.exists() else '';fresh=b.read_text() if b.exists() else ''
        if old==fresh:continue
        assert b.exists(),'Deletion is out of scope'
        chunks.extend(difflib.unified_diff(old.splitlines(keepends=True),fresh.splitlines(keepends=True),fromfile='a/'+name if a.exists() else '/dev/null',tofile='b/'+name))
        files.append(dict(path=name,base_sha256=sha(a) if a.exists() else None,new_sha256=sha(b)))
    target.write_text(''.join(chunks));return files
files=emit(base,new,OUT/'PATCH_CAMFORM2.patch')
verified=ROOT/'work/applied_A';shutil.copytree(base,verified)
proc=subprocess.run(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(OUT/'PATCH_CAMFORM2.patch')],cwd=verified,text=True,capture_output=True);(OUT/'patch_apply_A.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0
for name in names:assert (verified/name).read_bytes()==(new/name).read_bytes(),name
inputs={str(p):sha(p) for p in (Path(__file__),OUT/'SETUP.json',OUT/'PATCH_CAMFORM2.patch',ROOT.parent/'camformrev/REVIEW_VERDICT.md',ROOT.parent/'camform/out/PATCH_CAMFORM.patch')}
inputs.update({str(new/f['path']):f['new_sha256'] for f in files});inputs.update({str(base/f['path']):f['base_sha256'] for f in files if f['base_sha256']})
result=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/package_patch.py',files=files,file_count=len(files),applies_with_fuzz_zero=True,verified_result_files=len(names),A2='PENDING packaging-time SHA256 availability check')
(OUT/'FILES_TOUCHED.json').write_text(json.dumps(result,indent=2)+'\n')
print(len(files),sha(OUT/'PATCH_CAMFORM2.patch'))
