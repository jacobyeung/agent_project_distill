from pathlib import Path
import sys,json,hashlib
L=Path(__file__).resolve().parents[2];sys.path[:0]=[str(L/"work/tree_r1c"),str(L/"work/build24/kits/n/b")]
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
kits={n:L/("out/kit_"+n if n in ("n_go","qd") else "work/build24/kits/"+n) for n in ("q","n","n_go","qd")}
s={n:verify(p) for n,p in kits.items()};expected=json.loads((L/"work/build24m4j/SEALS.json").read_text());assert s==expected,(s,expected)
t=digest(inventory(L/"work/tree_r1c"));assert t=="0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de",t
v=dict(tree=t,kits=s,files={n:{str(p.relative_to(k)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob("*") if p.is_file()} for n,k in kits.items()})
(L/"work/build24m4l/BASELINE.json").write_text(json.dumps(v,indent=2)+"\n");print(t,s)
