import json,hashlib,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1];S=Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l');seal=S/'out24j/TREE24J_SEAL.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
v=json.loads(seal.read_text());assert v['tree_sha256']=='189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710';assert digest(v['files'])==v['tree_sha256']
result={'inputs':[{'path':str(seal),'sha256':sha(seal)},{'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__))}], 'seal':v['tree_sha256'],'file_count':len(v['files']),'mismatches':[]}
for name,h in v['files'].items():
 p=S/'work/tree_r1'/name;actual=sha(p)
 if actual!=h:result['mismatches'].append({'file':name,'expected':h,'actual':actual})
 for tree in ('live_base','live_new'):
  dest=W/'work'/tree/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
patch=Path('/scratch/jjyeung/orch_n30/fb_pack/prior2/out/PATCH_PRIOR.patch');shutil.copyfile(patch,W/'out/PATCH_PRIOR.patch');result['inputs'].append({'path':str(patch),'sha256':sha(patch)})
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(W/'work/live_new'),'-i',str(W/'out/PATCH_PRIOR.patch')],capture_output=True,text=True)
result.update(patch_returncode=r.returncode,patch_output=r.stdout+r.stderr,status='PASS' if not result['mismatches'] and r.returncode==0 else 'FAIL')
(W/'out/LIVE_PATCH.json').write_text(json.dumps(result,indent=2)+'\n')
(W/'STATUS.md').write_text('The live tree seal 189df6ac is available at tree_rebuild15_w24l/out24j/TREE24J_SEAL.json. Its inventory and PATCH_PRIOR application have been checked; LIVE_PATCH.json records any mismatch. Production population inputs are incomplete zero-count placeholders. Independent source filtering and prepared-receipt tooling remain in progress.\n')
print(json.dumps({k:v for k,v in result.items() if k!='inputs'},indent=2))
