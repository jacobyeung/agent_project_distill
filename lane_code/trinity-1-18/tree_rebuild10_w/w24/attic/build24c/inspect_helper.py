from pathlib import Path
import base64,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
for name in ('q','n'):
 k=L/'work/build24/kits'/name
 raw=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload'])
 (D/('j_'+name+'_before.sh')).write_bytes(raw)
 print(name,'bytes',sum(p.stat().st_size for p in k.rglob('*') if p.is_file()),'seal',J.seal(k))
