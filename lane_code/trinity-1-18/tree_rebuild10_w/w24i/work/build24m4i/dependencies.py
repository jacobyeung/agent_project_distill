import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
cfg=J.load(kit("n")/"k/c.json");hs={v["sha256"] for v in cfg["r2_sampling"].values() if isinstance(v,dict)}
def visit(v,path):
 if isinstance(v,dict):
  for k,x in v.items():
   if any(h in k for h in hs):print("KEY",path+"/"+k,str(x)[:350])
   visit(x,path+"/"+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):visit(x,path+"/"+str(i))
 elif isinstance(v,str) and any(h in v for h in hs):print(path,v[:160])
for p in sorted((kit("n")/"k").glob("*.json")):
 try:v=J.load(p)
 except ValueError:continue
 visit(v,p.name)
s=J.load(kit("n")/"k/s.json")
for h in hs:
 print("EMBED",h,json.dumps(s["entries"].get("u/"+h))[:700])
p=J.load(D/"P_CONFIG.json");print("P prep",p.get("preparation"))
print("P receipt",J.load(W/"work/sel24/evidence/p_preparation.json").keys())
t=J.load(W/"work/sel24/evidence/p_type_mix.json");print("P type mix",list(t));print("P counts",{s:{k:len(v) for k,v in groups.items()} for s,groups in t["populations"].items()});print("P tables",t.get("tables"))
