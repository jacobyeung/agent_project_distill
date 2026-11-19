from pathlib import Path
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
RO=ROOT.parent/'ro/orch_n30'
TREE=RO/'tree_rebuild10_w/w24/work/tree_r1'
MAN=RO/'tree_rebuild10_w/w24/out/TREE_FILES.sha256'
SEAL=RO/'tree_rebuild10_w/w24/out/TREE_SEAL.json'
PATCH=ROOT.parent/'patchA/out/PATCH_A.patch'
sha=lambda b:hashlib.sha256(b).hexdigest()
files={}
for line in MAN.read_text().splitlines():
 h,rel=line.split('  ',1);data=(TREE/rel).read_bytes();assert sha(data)==h,rel
 files[rel]=h
seal=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())
assert seal==json.loads(SEAL.read_text())['tree_sha256']=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7',seal
assert sha(PATCH.read_bytes())=='b95c1c618659a17b123b0d4d079fdf9ad53667f715e7362f43df0078bf6de477'
for rel in files:
 p=ROOT/'work/base'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(TREE/rel,p)
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(PATCH)],cwd=ROOT/'work/base',check=True)
shutil.copytree(ROOT/'work/base',ROOT/'work/new')
inputs={str(p):sha(p.read_bytes()) for p in [MAN,SEAL,PATCH,Path(__file__)]}
for p in [ROOT.parent/'donor/out/FILES_TOUCHED.json',ROOT.parent/'prior2/out/FILES_TOUCHED.json',RO/'fb_pack/cam/work/build.py',RO/'fb_pack/cam/work/common.py',RO/'fb_pack/camrev/REVIEW_VERDICT.md']:
 inputs[str(p)]=sha(p.read_bytes())
result=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/setup.py',base_tree_sha256=seal,verified_files=len(files),base_plus_patchA_files={str(p.relative_to(ROOT/'work/base')):sha(p.read_bytes()) for p in sorted((ROOT/'work/base').rglob('*')) if p.is_file()})
(ROOT/'out/SETUP.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 1: Verified all 939 files against the pinned tree seal and applied the authenticated PATCH_A with zero fuzz. work/base holds the comparison baseline; work/new holds the editable overlay. The camera rewrite helper resides in common.py and build.py supplies its event/render integration. Donor and prior2 paths are protected.\n')
print(seal,len(files))
