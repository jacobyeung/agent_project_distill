import hashlib,json,shutil
from pathlib import Path
W=Path.cwd(); R=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24'); src=R/'work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=R/'out/TREE_FILES.sha256'; seal=R/'out/TREE_SEAL.json'
inventory={n:h for h,n in (line.split('  ',1) for line in manifest.read_text().splitlines())}
tree_sha=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert tree_sha=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
lines=manifest.read_text().splitlines(); assert len(lines)==json.loads(seal.read_text())['files']
for line in lines:
 h,n=line.split('  ',1); p=src/n; assert sha(p)==h,(n,'seal mismatch')
 for name in ('base','new'):
  dest=W/'work'/name/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
result={'status':'PASS','tree_sha256':tree_sha,'files':len(lines),'inputs':[{'path':str(p),'sha256':sha(p)} for p in (manifest,seal,Path(__file__))]}
(W/'out/BASE_SEAL.json').write_text(json.dumps(result,indent=2)+'\n')
(W/'STATUS.md').write_text('The base seal matches 57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7 across all 939 files. Verified copies are in work/base and work/new. Production population reconstruction and the opt-in draw patch are in progress.\n')
print(result)
