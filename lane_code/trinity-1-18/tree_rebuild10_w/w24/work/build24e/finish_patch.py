from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path[:0]=[str(D),str(L/"work/build24")]
from patch24e import preserve
p=L/"work/build24/joblib.py";preserve(p);s=p.read_text()
s=s.replace("    paths.update(spec[\x27pin_paths\x27])","    paths.update(spec[\x27pin_paths\x27])\n    paths.update(spec.get(\x27host_paths\x27,{}))")
s=s.replace("    paths.update(expected_paths)","    paths.update(expected_paths)\n    paths.update(spec.get(\x27host_paths\x27,{}))")
p.write_text(s)
p=D/"patch24e.py";s=p.read_text();s=s.replace("replacements.update(closure[\"host_pins\"])","replacements.update({h:\"u/\"+h for h in closure[\"host_pins\"]})\n spec[\"host_paths\"]=closure[\"host_pins\"]")
s=s.replace(" k=Path(k);spec=", " k=Path(k)\n (k/\"b/z.py\").write_bytes((L/\"work/build24/joblib.py\").read_bytes())\n spec=")
p.write_text(s)
import importlib,patch24e;importlib.reload(patch24e)
for k in (L/"work/build24/kits/q",L/"work/build24/kits/n",L/"out/kit_n_go"):print(k.name,patch24e.upgrade(k))
