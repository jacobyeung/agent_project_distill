from pathlib import Path
import json,hashlib,sys
L=Path(__file__).resolve().parents[2];W=L.parent
v=json.loads((W/"ext/pwrap/k/7.json").read_text());found={};reports=[]
roots=[W/"ext/r1_ops/work"/a/b for a in ("snap_6a5c7d00","snap_fac07052") for b in ("work/tree","work/reference/tree")]+[L/"work/tree_r1"]
for root in roots:
 matches=[]
 for n,h in v["files"].items():
  p=root/n
  if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h:found.setdefault(n,str(p));matches.append(n)
 reports.append(dict(root=str(root),matches=len(matches),pool="student_pilot/s1_pool.py" in matches,routing="student_pilot/s1_routing.py" in matches))
missing=[n for n in v["files"] if n not in found]
(L/"work/build24m4h/TREE_LOCATIONS.json").write_text(json.dumps(dict(roots=reports,found=found,missing=missing),indent=2)+"\n")
print(json.dumps(dict(roots=reports,missing=missing),indent=2))
