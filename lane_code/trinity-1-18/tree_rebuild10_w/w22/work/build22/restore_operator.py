"""Carry the named build-21 operator metadata required to regenerate kit q."""
from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path.insert(0,str(L/'work/build21'))
import joblib as J
p=D/'FIXTURE_PREREQUISITES.json';items=json.loads(p.read_text())
for leaf in ('REQUEST_TEMPLATE.json','STAGING.json'):
 name='work/build17/proofs/operator/'+leaf;source=L.parent/'w21'/name;target=L/name
 raw=source.read_bytes();assert len(raw)<5_000_000
 if leaf=='REQUEST_TEMPLATE.json':assert json.loads(raw)==J.load(L/'work/build21/kits/q/k/r.json')
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 items.append(dict(path=name,source=str(source),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
p.write_text(json.dumps(items,indent=2)+'\n');print('Restored operator prerequisites')
