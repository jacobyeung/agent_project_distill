"""Authenticate and unpack a fetched return under this workspace; retain partial status."""
import argparse,hashlib,json,tarfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--exit',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 O=Path(__file__).resolve().parent;W=O.parent
 dest=Path(a.out).resolve()
 if not dest.is_relative_to(W):raise ValueError('Output must stay inside W2')
 raw=Path(a.archive);receipt=json.loads(Path(a.exit).read_text());public=json.loads((O/'package/0.json').read_text())
 with raw.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 if receipt.get('synthetic') is not False or receipt.get('plan_sha256')!=public['plan_sha256']:raise ValueError('Return provenance differs')
 if digest!=receipt.get('archive_sha256') or raw.stat().st_size!=receipt.get('archive_bytes'):raise ValueError('Return bytes differ')
 dest.mkdir(parents=True,exist_ok=False);seen=set();total=0
 with tarfile.open(raw) as tar:
  for m in tar:
   path=Path(m.name);total+=m.size
   if path.is_absolute() or '..' in path.parts or not m.isfile() or m.name in seen or total>512*1024**2:raise ValueError('Unsafe or oversized return')
   seen.add(m.name);target=dest/path;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as f:f.write(tar.extractfile(m).read())
 from sys import path as imports
 imports.insert(0,str(O/'src'))
 from orchard_h10.common import canonical,sha
 identity=json.loads((dest/'metadata/IDENTITY.json').read_text())
 inputs=json.loads((O/'inputs_tower.json').read_text())
 if (identity['plan']!=public['plan_sha256'] or identity['cards']!=1 or identity['inputs']!=canonical({k:v for k,v in inputs.items() if k!='resume'})
     or identity['operator_sha256']!=sha(O/'tower_sequence.py')):raise ValueError('Read identity differs')
 print(json.dumps(dict(output=str(dest),complete=receipt['complete'],status=receipt['status'],sha256=digest)))

if __name__=='__main__':main()
