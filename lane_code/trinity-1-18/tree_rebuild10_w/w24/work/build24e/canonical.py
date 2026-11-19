from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";p=D/"patch24e.py";s=p.read_text().replace("spec[\"uploads\"]=list(uploads.values())","spec[\"uploads\"]=[uploads[h] for h in sorted(uploads)]");p.write_text(s)
sys.path.insert(0,str(D));from patch24e import upgrade
for k in (L/"work/build24/kits/q",L/"work/build24/kits/n",L/"out/kit_n_go"):print(k.name,upgrade(k))
