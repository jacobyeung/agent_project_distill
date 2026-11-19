from pathlib import Path
import sys,json,hashlib,ast,subprocess,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24m2";T=L/"work/tree_r1";X=L.parent/"work/x24l3_back"
sys.path[:0]=[str(L/"work/build24"),str(T)]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
kits={n:L/("out/kit_n_go" if n=="n_go" else "work/build24/kits/"+n) for n in ("q","n","n_go")}
base=dict(kits={n:{str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob("*") if p.is_file()} for n,k in kits.items()},packages={p.name:dict(sha256=J.sha(p),bytes=p.stat().st_size) for p in (L/"out").glob("tree_rebuild*.tar")},tree=dict(files=inventory(T)))
J.write(D/"BASELINE.json",base)
spec=J.load(X/"out/UNCHANGED24L3.json");seal=J.load(X/"out/TREE24L3_SEAL.json")
assert digest(base["tree"]["files"])==spec["before_tree_sha256"]
for n,v in spec["files"].items():assert base["tree"]["files"].get(n)==v["before"],n
patch=X/"out/HOST24LN3.patch"
p=subprocess.run(["patch","--dry-run","--fuzz=0","--batch","-p1","-i",str(patch)],cwd=T,capture_output=True,text=True)
(D/"patch_dry.log").write_text(p.stdout+p.stderr);assert p.returncode==0
for name in spec["changed"]:
 p=T/name
 if p.exists():
  old=L/"attic/build24m2"/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True);p.rename(old);p.write_bytes(old.read_bytes());p.chmod(old.stat().st_mode&511)
p=subprocess.run(["patch","--fuzz=0","--batch","-p1","-i",str(patch)],cwd=T,capture_output=True,text=True)
(D/"patch.log").write_text(p.stdout+p.stderr);assert p.returncode==0
actual=inventory(T);assert actual==seal["files"]
assert digest(actual)==spec["after_tree_sha256"]
for n,v in spec["files"].items():assert actual.get(n)==v["after"],n
protected={}
for key,v in spec["protected_functions"].items():
 name,fn=key.split(":");s=(T/name).read_text();node=next(n for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==fn)
 body=ast.get_source_segment(s,node)
 h=hashlib.sha256(body.encode()).hexdigest()
 # Compare exact functions to the unchanged base regardless of ledger newline convention.
 b=(X/"work/tree_r1_base"/name).read_text();bn=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name==fn)
 assert body==ast.get_source_segment(b,bn),key
 protected[key]=dict(identical=True,sha256=h)
J.write(D/"TREE_VERIFICATION.json",dict(status="PASS",tree_sha256=digest(actual),files=len(actual),changed=spec["changed"],protected=protected,fuzz=0))
for name in ("HOST24LN3.patch","TREE24L3_SEAL.json","UNCHANGED24L3.json"):(D/name).write_bytes((X/"out"/name).read_bytes())
print("Tree patch and unchanged ledger PASS",digest(actual),len(actual))
