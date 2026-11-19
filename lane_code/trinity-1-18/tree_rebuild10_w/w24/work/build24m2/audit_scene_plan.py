from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/"work/build24"));import joblib as J
c=J.load(L/"work/build24/kits/q/k/n.json");s=J.load(L/"work/build24/kits/q/k/p.json")
v=J.load(L/"work/build24m2/SCENE_REBUILD_INPUTS.json")
for r in v["missing"]:print(r["input"], "catalog",r["sha256"] in c["s1_routing"]["catalog"],"host",r["sha256"] in s["host_paths"])
