"""Check installed packet hashes and the lane's size without reading large assets."""
import hashlib,json,os,subprocess
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
manifest=json.loads((L/'out/PATCH_MANIFEST_R6.json').read_text())
checks=[]
for rel,item in manifest['files'].items():
    for arm,key in [('r6_base','base_sha256'),('r6_applied','patched_sha256')]:
        path=(L/'work/base/work/base/tree_b01ce449' if arm=='r6_base' else L/'work/trees'/arm)/rel
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        checks.append(dict(source_path=str(path),expected=item[key],actual=actual,pass_check=actual==item[key]))
total=int(subprocess.run(['du','-sk',str(L)],capture_output=True,text=True,check=True).stdout.split()[0])*1024
out=dict(source_path=str(L),lane_allocated_bytes=total,limit_bytes=3_900_000_000,under_limit=total<3_900_000_000,
         patch_manifest_path=str(L/'out/PATCH_MANIFEST_R6.json'),all_hashes_match=all(c['pass_check'] for c in checks),checks=checks)
(W/'integrity.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
