from pathlib import Path
import hashlib,json,difflib,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/base';NEW=ROOT/'work/new'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
setup=json.loads((ROOT/'out/SETUP.json').read_text());base_files=setup['base_plus_patchA_files']
inputs={str(ROOT/'out/SETUP.json'):sha(ROOT/'out/SETUP.json'),str(Path(__file__)):sha(Path(__file__))}
protected=set()
for p in [ROOT.parent/'donor/out/FILES_TOUCHED.json',ROOT.parent/'prior2/out/FILES_TOUCHED.json']:
 inputs[str(p)]=sha(p);protected.update(r['path'] for r in json.loads(p.read_text())['files'])
new_files={str(p.relative_to(NEW)):sha(p) for p in sorted(NEW.rglob('*')) if p.is_file() and 'artifacts' not in p.relative_to(NEW).parts and '__pycache__' not in p.parts}
assert set(base_files)<=set(new_files)
files=[];parts=[]
for name,h in sorted(new_files.items()):
 before=base_files.get(name)
 if before==h:continue
 assert name not in protected,name
 p=NEW/name;inputs[str(p)]=h
 if before:assert sha(BASE/name)==before;inputs[str(BASE/name)]=before
 a=(BASE/name).read_text().splitlines(keepends=True) if before else []
 parts.extend(difflib.unified_diff(a,p.read_text().splitlines(keepends=True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
 files.append(dict(path=name,base_sha256=before,new_sha256=h,bytes=p.stat().st_size))
patch=ROOT/'out/PATCH_CAMFORM.patch';patch.write_text(''.join(parts))
applied=ROOT/'work/applied';applied.mkdir(exist_ok=False)
for name in base_files:
 p=applied/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,p)
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=applied,check=True)
actual={str(p.relative_to(applied)):sha(p) for p in applied.rglob('*') if p.is_file()}
assert actual==new_files
value=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/build_patch.py',base_tree_sha256=setup['base_tree_sha256'],base_plus_patchA_tree_sha256=hashlib.sha256(json.dumps(base_files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),patchA_sha256=setup['input_sha256'][str(ROOT.parent/'patchA/out/PATCH_A.patch')],files=files,protected_paths=sorted(protected),overlap_with_donor_or_prior2=[],patch_sha256=sha(patch),apply_verified=True,verified_files=len(actual))
(ROOT/'out/FILES_TOUCHED.json').write_text(json.dumps(value,indent=2)+'\n')
print(dict(files=[f['path'] for f in files],verified_files=len(actual),patch_sha256=sha(patch)))
