from pathlib import Path
import sys,json,ast
L=Path.cwd();D=L/"work/build24m4x2";sys.path[:0]=[str(L/"work/tree_r1c"),str(L/"out/kit_qd/b")]
from student_pilot.r2_exclusions import SEALED
import z
wanted=set(SEALED.values());found={}
for file in (L/"work/build24m4u/PACKAGE_MANIFEST.json",L.parent/"w24v/work/build24m4v/PACKAGE_MANIFEST.json"):
 m=json.loads(file.read_text());root=L if "w24w" in str(file) else L.parent/"w24v"
 for n,v in m["files"].items():
  if v.get("sha256") in wanted and v["sha256"] not in found:
   p=root/n
   if p.is_file() and z.sha(p)==v["sha256"]:found[v["sha256"]]=str(p)
print(json.dumps({k:found.get(v) for k,v in SEALED.items()},indent=2))
(D/"FIXTURE_LOOKUP.json").write_text(json.dumps(found,indent=2)+"\n")
