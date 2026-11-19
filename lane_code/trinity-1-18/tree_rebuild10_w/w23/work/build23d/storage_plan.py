from pathlib import Path
import json,os
L=Path(__file__).resolve().parents[2];D=L/'work/build23d'
items=[]
for root,dirs,files in os.walk(L):
 if Path(root)==L/'work':dirs[:]=[n for n in dirs if n!='build23b']
 if Path(root)==L/'attic':dirs[:]=[n for n in dirs if n!='tr13']
 for n in files:
  p=Path(root)/n
  if p.is_symlink():continue
  size=p.stat().st_size
  if size>3_000_000 and p.suffix=='.json' and '/work/tree_r1/' not in str(p):items.append(dict(name=str(p.relative_to(L)),bytes=size))
items.sort(key=lambda x:-x['bytes'])
(D/'STORAGE_CANDIDATES.json').write_text(json.dumps(items,indent=2)+'\n')
print(json.dumps(items[:45],indent=2))
