from pathlib import Path
import sys,json,shutil,os,ast,hashlib
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path[:0]=[str(L/"work/build24c"),str(D),str(L/"work/build24"),str(L/"work/tree_r1")]
import joblib as J
from runtime import harden_kit
from patch24e import reseal
from student_pilot.source_seal import inventory
from launch_r1.build import verify
assert inventory(L/"work/tree_r1")==J.load(L/"work/build24b/TREE_FILES.json")
records={}
def cp(src,dst):
 if Path(src).suffix==".tar" or Path(src).name=="l.json":os.link(src,dst)
 else:shutil.copyfile(src,dst)
for name in ("q","n"):
 k=L/"work/build24/kits"/name;old=L/"attic/build24e/work/build24/kits"/name
 target=D/"generated"/name;target.parent.mkdir(exist_ok=True);shutil.copytree(old,target,copy_function=cp)
 harden_kit(target);reseal(target)
 assert J.seal(target)==J.seal(k),(name,J.seal(target),J.seal(k))
 before={str(p.relative_to(target)):J.sha(p) for p in target.rglob("*") if p.is_file()};harden_kit(target);reseal(target)
 assert before=={str(p.relative_to(target)):J.sha(p) for p in target.rglob("*") if p.is_file()}
 def norm(v):
  if isinstance(v,dict):return {key:norm(x) for key,x in v.items() if not (key=="path" and "sha256" in v)}
  if isinstance(v,list):return [norm(x) for x in v]
  return v
 for fn in ("c.json","n.json","r.json","h.json"):
  assert norm(J.load(k/"k"/fn))==norm(J.load(old/"k"/fn))
 assert J.load(k/"k/n.json")["r1_training"]["p_run"]==J.load(old/"k/n.json")["r1_training"]["p_run"]
 records[name]=dict(seal=verify(k),regeneration_identical=True,idempotent=True,config_semantics_and_pin_hashes_unchanged=True)
old=ast.parse((L/"attic/build24e/work/build24/joblib.py").read_text());new=ast.parse((L/"work/build24/joblib.py").read_text())
for name in ("identities","export_identity","metadata_closure","receipt600","checkpoint600","bound400"):
 get=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(get(old))==ast.dump(get(new))
packages={p.name:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in (L/"out").glob("tree_rebuild_b24*.tar")}
previous=J.load(L/"out/DELIVERY_24D.json");assert packages[Path(previous["package"]).name]["sha256"]==previous["sha256"]
J.write(D/"INVARIANTS.json",dict(status="PASS",tree_byte_identical=True,resolver_identity_checks_identical=True,kits=records,packages=packages));print("PASS")
