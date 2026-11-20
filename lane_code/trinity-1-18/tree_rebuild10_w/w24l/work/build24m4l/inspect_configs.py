from pathlib import Path
import json,base64,hashlib,sys
L=Path(__file__).resolve().parents[2];D=Path(__file__).parent
sys.path[:0]=[str(L/"work/tree_r1c"),str(L/"work/build24m4h")]
import joblib as J
from launch_r1.build import verify
for n,k in [("q",L/"work/build24/kits/q"),("n",L/"work/build24/kits/n"),("n_go",L/"out/kit_n_go"),("qd",L/"out/kit_qd")]:
 print("SEAL",n,verify(k))
 for p in sorted((k/"k").glob("*.json")):
  try:v=J.load(p)
  except (ValueError,UnicodeError) as e: print("SKIP",p.name,str(e));continue
  if n=="n_go":
   dest=D/"decoded"/p.name;dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(v,indent=2)+"\n")
  print(n,p.name, list(v)[:35])
for p in (L.parent/"inputs/p_configs").glob("*.json"):
 v=J.load(p);print("P",p.name,list(v)[:35]);(D/("P_"+p.name)).write_text(json.dumps(v,indent=2)+"\n")
