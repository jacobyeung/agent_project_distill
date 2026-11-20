from pathlib import Path
import sys,runpy,json,hashlib
L=Path.cwd(); D=L/"work/build24m4w"; V=L.parent/"w24v"
a=runpy.run_path(str(V/"out/apply_24m4v.py")); data=a["DATA"]
sys.path.insert(0,str(L/"work/tree_r1c"))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
r={}
for name,root,expected,kexpected in [("u",L,data["base_tree"],data["base_kits"]),("v",V,data["tree"],data["kits"])]:
 tree=digest(inventory(root/"work/tree_r1c")); assert tree==expected,(name,tree,expected)
 seals={k:verify(root/p) for k,p in data["kit_paths"].items()};assert seals==kexpected,(name,seals,kexpected)
 stated=json.loads((root/("work/build24m4u/SEALS.json" if name=="u" else "work/build24m4v/SEALS.json")).read_text())
 assert seals==(stated if name=="u" else stated["kits"])
 for k,p in data["kit_paths"].items():
  assert a["load"](root/p/"BUILD.json")["source_seal"]==tree
 r[name]=dict(tree=tree,kits=seals)
r["helpers_before"]={p.name:a["sha"](p) for p in (L/"out/rcj").iterdir() if p.is_file()}
r["apply_files"]={n:dict(expected_before=v["before"],actual_before=a["sha"](L/n)) for n,v in data["files"].items()}
r["job173754"]=dict(path=str(L.parent/"work/d173754"),exists=(L.parent/"work/d173754").exists())
r["census"]={str(p.relative_to(L)):a["sha"](p) for p in (L/"out").glob("*CENSUS*") if p.is_file()}
(D/"PREFLIGHT.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps(r,indent=2))
