from pathlib import Path
import sys,json,base64,hashlib
L=Path(__file__).resolve().parents[2]; W=L.parent
sys.path[:0]=[str(L/"work/build24m4d"),str(L/"work/tree_r1")]
import joblib as J
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
print("tree",digest(inventory(L/"work/tree_r1")))
for n,rel in (("q","work/build24/kits/q"),("n","work/build24/kits/n"),("n_go","out/kit_n_go"),("qd","out/kit_qd")):
 print("kit",n,verify(L/rel))
v=J.load(W/"ext/pwrap/k/0.json")
print("P MAP KEYS",list(v))
for k in v:
 if "train" in k or "tree" in k or "code" in k:print("MAP",k,v[k])
p=J.load(W/"w24g/work/build24m4g/inputs/b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad")
print("P CFG KEYS",list(p))
for k in ("code","source","run_id","s1_routing"):print("P",k,p.get(k))
print("PK FILES",[str(x.relative_to(W/"ext/pk")) for x in (W/"ext/pk").glob("*")][:60])
print("PWRAP TARS",[str(x) for x in (W/"ext/pwrap/k").glob("t_*")])
n=J.load(L/"work/build24/kits/n/k/c.json")
print("N ROUTING",n["s1_routing"])
print("N train keys",list(n["r1_training"]))
