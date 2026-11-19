"""Check current direct input hashes without dereferencing unavailable inherited sources."""
import json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1];RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro');O=W/'out';seen={}
def sha(p):
 p=Path(p)
 if p not in seen:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  seen[p]=h.hexdigest()
 return seen[p]
files=['BASE_SEAL.json','INPUT_LOCATIONS.json','CAPSULE_RECOVERY.json','MISSING_INPUTS.json','TOWARD_HARD_WEIGHTS.json','WEIGHT_BUILD.json','CENSUS_LOADER.json','FILES_TOUCHED.json','CPU_FINAL_base.json','CPU_FINAL_new.json','TESTS.json']
checked=[];absent=[];mismatch=[]
for name in files:
 p=O/name
 if not p.is_file():absent.append(name);continue
 value=json.loads(p.read_text());assert value.get('inputs'),name
 for item in value['inputs']:
  path=Path(item['path'])
  if not path.is_absolute():path=W/path
  assert path.is_relative_to(W) or path.is_relative_to(RO),path
  actual=sha(path)
  if actual!=item['sha256']:mismatch.append(dict(output=name,input=str(path),expected=item['sha256'],actual=actual))
 checked.append(dict(path=str(p),sha256=sha(p)))
seal=json.loads((O/'BASE_SEAL.json').read_text())
manifest=Path(seal['inputs'][0]['path'])
base_files={n:h for h,n in (line.split('  ',1) for line in manifest.read_text().splitlines())}
new_files=dict(base_files)
for row in json.loads((O/'FILES_TOUCHED.json').read_text())['files']:new_files[row['path']]=row['after_sha256']
for tree,files in [('base',base_files),('new',new_files)]:
 for n,h in files.items():
  actual=sha(W/'work'/tree/n)
  if h!=actual:mismatch.append(dict(tree=tree,path=n,expected=h,actual=actual))
result=dict(trees_checked=dict(base=len(base_files),new=len(new_files)),status='PASS' if not absent and not mismatch else 'PENDING' if absent and not mismatch else 'FAIL',missing_outputs=absent,mismatches=mismatch,unique_direct_inputs_checked=len(seen),scope='Current direct input pins only; unavailable inherited filtering inputs remain MISSING.',inputs=checked+[dict(path=str(Path(__file__).resolve()),sha256=sha(Path(__file__).resolve()))])
(O/'EVIDENCE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='inputs'})
assert not mismatch,mismatch
