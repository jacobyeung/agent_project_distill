from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path[:0]=[str(L/'work/build24f'),str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from kit24f import reseal
from launch_r1.build import verify
rows={}
for name in ('q','n','n_go'):
    k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
    for n in ('BUILD.json','SHA256SUMS.txt'):
        p=k/n;raw=p.read_bytes();old=L/'attic/build24h'/p.relative_to(L)
        old.parent.mkdir(parents=True,exist_ok=True)
        if not old.exists():p.rename(old)
        p.write_bytes(raw)
    seal=reseal(k);assert verify(k)==seal
    rows[name]=dict(kit_seal=seal,GO=J.load(k/'k/a.json')['GO'])
    assert rows[name]['GO']==(name=='n_go')
J.write(D/'KIT.json',rows)
print(rows)
