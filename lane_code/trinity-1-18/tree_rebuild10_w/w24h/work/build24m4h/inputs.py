import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from copy import deepcopy
(D/"inputs").mkdir()
p=J.load(input_file("5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af"))
m=J.load(input_file(p["manifest"]["sha256"]))
print("P manifest",p["manifest"],"sets",len(m["sets"]))
old=deepcopy(m)
for s in m["sets"]:
 if s["name"] in ("ROUTE_direct","SCENE_room","T0_room","T1H1_room"):s["status"]="deferred"
mp=save_input(m);seed=deepcopy(p);seed["manifest"]=mp
# This is a preparation seed, not a receipt claiming to have been prepared by C.
seed["scope"]="configuration-seed-requires-native-preparation"
sp=save_input(seed)
J.write(D/"CONFIG_INPUTS.json",dict(manifest=mp,selection=sp,original_manifest=p["manifest"],statuses={n:v["status"] for n,v in p["sources"].items()}))
base={n:{str(f.relative_to(kit(n))):dict(sha256=J.sha(f),bytes=f.stat().st_size,mode=f.stat().st_mode&511) for f in kit(n).rglob("*") if f.is_file()} for n in NAMES}
J.write(D/"ORIGINAL_KITS.json",base)
for n in NAMES:
 k=kit(n);spec=J.load(k/"k/p.json")
 new=[(mp["sha256"],input_file(mp["sha256"]).stat().st_size),(sp["sha256"],input_file(sp["sha256"]).stat().st_size),("e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536",9963520)]
 for h,size in new:
  assert not any(x["sha256"]==h for x in spec["uploads"])
  spec["uploads"].append(dict(sha256=h,bytes=size,opaque_name="u/"+h));spec["pin_paths"][h]=spec["namespace"]+"/u/"+h
 spec["uploads"].sort(key=lambda r:r["sha256"]);cap(k/"k/p.json",spec)
 for fn in ("k/c.json","k/n.json"):
  cfg=J.load(k/fn);cfg["s1_routing"]["selection"]=sp
  # P supplies U and its augmented manifest/index closure; keep all N inputs too.
  for h in p.get("catalog",{}):pass
  pc=J.load(input_file("b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad"))
  for h in pc["s1_routing"]["catalog"]:cfg["s1_routing"]["catalog"].setdefault(h,"u/"+h)
  cfg["s1_routing"]["catalog"].update({mp["sha256"]:"u/"+mp["sha256"],sp["sha256"]:"u/"+sp["sha256"]})
  cfg["r1_training"]["p_tree"]=dict(path="u/"+new[-1][0],sha256=new[-1][0])
  cap(k/fn,cfg)
J.write(L/"out/ORCHARD_COPIES_24M4H.json",[dict(source="/project/community/jjyeung/okh7/x_ee227714/k/t_b83a8a35d420815b.tar",sha256=new[-1][0],size=9963520,destination="/project/community/jjyeung/okh7/x_22c714e1/u/"+new[-1][0],basis="P source seal, launch, run binding, pin map, inventory; not in supplied 24m4e staging inventory")])
print("INPUTS",mp,sp)
