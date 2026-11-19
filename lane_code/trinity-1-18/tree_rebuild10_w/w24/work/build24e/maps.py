from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/"work/build24"));import joblib as J
for n in ("l","p","c","n"):
 v=J.load(L/"work/build24/kits/q/k"/(n+".json"));(L/"work/build24e"/(n+"_decoded.json")).write_text(json.dumps(v,indent=2))
