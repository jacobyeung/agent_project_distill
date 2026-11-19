from pathlib import Path
import json,sqlite3,os
L=Path(__file__).resolve().parents[2]
for p in (L/'work/build19/proofs/native').glob('*/rows.sqlite'):
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as c:
        print(p.relative_to(L),p.stat().st_size,c.execute('select length(row) from rows limit 1').fetchone())
sizes=[]
for p in L.iterdir():
    for x in p.iterdir():
        if x.is_dir():sizes.append((sum(z.stat().st_size for z in x.rglob('*') if z.is_file() and not z.is_symlink()),str(x.relative_to(L))))
        else:sizes.append((x.stat().st_size,str(x.relative_to(L))))
print(sorted(sizes,reverse=True)[:18])
E=L.parent/'ext/pwrap'
for n in ('k/0.json','k/launch.json'):
    print(n,(E/n).read_text()[:5000])
