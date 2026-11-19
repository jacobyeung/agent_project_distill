from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1]
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l')
p=S/'out24j/TREE24J_SEAL.json';seal=json.loads(p.read_text());files=seal['files'];errors=[]
for n,h in files.items():
 q=S/'work/tree_r1_base'/n;raw=q.read_bytes();actual=hashlib.sha256(raw).hexdigest()
 if h!=actual:errors.append(n)
 d=W/'work/live_base'/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(raw)
 d=W/'work/live'/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(raw)
actual=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert not errors and actual==seal['tree_sha256']=='189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
r=dict(input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest(),**{str(S/'work/tree_r1_base'/n):h for n,h in files.items()},str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},status='PASS',tree_sha256=actual,files=len(files),command='python code/stage_live.py',mapped_location='MISSING',verified_location=str(S/'work/tree_r1_base'))
(W/'out/LIVE_VERIFY.json').write_text(json.dumps(r,indent=2)+'\n')
print(actual,len(files))
