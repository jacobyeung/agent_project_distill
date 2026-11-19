from pathlib import Path
import json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1')]
from runtime import harden_kit
from patch import reseal
import joblib as J
records=J.load(D/'KIT.json')
for name in ('q','n'):
 k=L/'work/build24/kits'/name
 a=L/'attic/build24c/revision1'/name;a.parent.mkdir(parents=True,exist_ok=True)
 k.rename(a);shutil.copytree(a,k)
 harden_kit(k);records[name]['kit_seal']=reseal(k)
 v=J.load(D/('UPLOADS_'+name+'.json'))
 for x in v['files']:
  p=Path(x['local_path']);x.update(bytes=p.stat().st_size,sha256=J.sha(p))
 J.write(D/('UPLOADS_'+name+'.json'),v)
J.write(D/'KIT.json',records)
