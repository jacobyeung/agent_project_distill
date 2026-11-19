from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path[:0]=[str(D),str(L/"work/build24"),str(L/"work/tree_r1")]
import joblib as J
from launch_r2.build import capsule_json
p=D/"patch24e.py";s=p.read_text().replace("return {key:relocate(x) for key,x in v.items()}","return {key:(x if key in (\x27p_run\x27,\x27init_artifact\x27) else relocate(x)) for key,x in v.items()}")
p.write_text(s)
from patch24e import upgrade
for name in ("q","n","n_go"):
 k=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 old=L/"attic/build24e"/k.relative_to(L)
 for fn in ("c.json","n.json"):
  v=J.load(k/"k"/fn);before=J.load(old/"k"/fn)
  v["r1_training"]["p_run"]=before["r1_training"]["p_run"];v["init_artifact"]=before["init_artifact"]
  (k/"k"/fn).write_bytes(capsule_json(v))
 print(name,upgrade(k))
