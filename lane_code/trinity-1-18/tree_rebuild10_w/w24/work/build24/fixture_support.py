from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';O=D/'proofs/capacity';sys.path.insert(0,str(D));import joblib as J
base=J.load(L/'work/build22/FIXTURE_PREREQUISITES.json');rows={x['path']:dict(x) for x in base}
for folder in (O/'model',O/'600/export',O/'600/checkpoint_000600',O/'final/400/export'):
 for p in folder.rglob('*'):
  if p.is_file():rows[str(p.relative_to(L))]=dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=J.sha(p),role='native tiny-model fixture support')
for p in (O/'source.tar',O/'final/source.tar',O/'f.png',O/'mask.npz'):
 if p.is_file():rows[str(p.relative_to(L))]=dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=J.sha(p),role='native fixture support')
value=list(rows.values());total=sum(x['bytes'] for x in value)
assert total<60_000_000,total
J.write(D/'FIXTURE_PREREQUISITES.json',value);print(len(value),'files',total,'bytes')
