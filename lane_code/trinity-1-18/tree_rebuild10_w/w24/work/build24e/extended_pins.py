from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";p=D/"patch24e.py";s=p.read_text().replace("if set(v)=={\"path\",\"sha256\"} and", "if \"path\" in v and \"sha256\" in v and");p.write_text(s)
sys.path.insert(0,str(D));from patch24e import upgrade
for k in (L/"work/build24/kits/q",L/"work/build24/kits/n",L/"out/kit_n_go"):print(k.name,upgrade(k))
p=D/"refresh_tests.py";s=p.read_text().replace("self.req=J.load(D/\x27go/r.json\x27)","self.req=J.load(L/\x27work/build24d/go/r.json\x27)");p.write_text(s)
