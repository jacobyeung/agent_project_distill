"""Make a six-file overlay, apply it to a sealed copy, and check every resulting file."""
import json,hashlib,difflib,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1];B=W/'work/base';N=W/'work/new'
RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/out')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest=RO/'TREE_FILES.sha256';inventory={n:h for h,n in (line.split('  ',1) for line in manifest.read_text().splitlines())}
assert digest(inventory)=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
for n,h in inventory.items():assert sha(B/n)==h,('BASE CHANGED',n)
paths=set(inventory)|{'student_pilot/r1_direction_prior.py','tests/test_r1_direction_prior.py'}
changed=[];chunks=[];new_inventory={}
for n in sorted(paths):
 p=N/n;new_inventory[n]=sha(p)
 if inventory.get(n)==new_inventory[n]:continue
 old=(B/n).read_text().splitlines(True) if n in inventory else []
 new=p.read_text().splitlines(True)
 chunks.extend(difflib.unified_diff(old,new,fromfile='a/'+n if n in inventory else '/dev/null',tofile='b/'+n))
 changed.append(dict(path=n,before_sha256=inventory.get(n),after_sha256=new_inventory[n],bytes=p.stat().st_size))
patch=W/'out/PATCH_PRIOR.patch';patch.write_text(''.join(chunks))
check=W/'work/patchcheck_final';assert not check.exists()
for n in inventory:
 p=check/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/n,p)
result=subprocess.run(['patch','--batch','-p1','-d',str(check),'-i',str(patch)],text=True,capture_output=True)
(W/'out/PATCH_APPLY.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result
for n,h in new_inventory.items():assert sha(check/n)==h,('PATCH DIFFERS',n)
record={'status':'PASS','base_tree_sha256':digest(inventory),'new_tree_sha256':digest(new_inventory),'files':changed,'overlap_with_declared_fbp_patchA_scope':[],'overlap_with_declared_fbp_donor_scope':[],'overlap_basis':'Task-declared file scopes; other lanes actual patch manifests were not supplied.','inputs':[pin(manifest),pin(RO/'TREE_SEAL.json'),pin(__file__)]+[pin(N/v['path']) for v in changed],'patch':pin(patch),'patch_apply_verified_files':len(new_inventory),'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python scripts/make_patch.py'}
(W/'out/FILES_TOUCHED.json').write_text(json.dumps(record,indent=2)+'\n')
print('Changed files',len(changed),'verified files',len(new_inventory),'new seal',digest(new_inventory),flush=True)
