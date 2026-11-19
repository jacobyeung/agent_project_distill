"""Authenticate and unpack a fetched return under this workspace; retain partial status."""
import argparse,hashlib,json,tarfile,re
from fetch_return import digest as file_digest, validate_exit
from pathlib import Path

def validate_journals(dest):
 root=Path(dest)
 # A read start proves a worker was launched, even if it failed before type setup.
 for steps in (root/'metadata/reads').glob('*/STEPS.jsonl'):
  if any(json.loads(line).get('event')=='start' for line in steps.read_text().splitlines()):
   if not list(steps.parent.glob('metadata/journals/*/*/items.jsonl')):
    raise ValueError('Started read has no journal: '+str(steps.parent))
 for started in (root/'metadata/reads').glob('*/metadata/journals/*/*/STARTED.json'):
  if not (started.parent/'items.jsonl').is_file():
   raise ValueError('Started segment has no journal: '+str(started.parent))
  if not (started.parent/'environment.json').is_file():
   raise ValueError('Started segment has no environment: '+str(started.parent))
 if not list((root/'metadata/reads').glob('*/metadata/journals/*/*/items.jsonl')):
  raise ValueError('Return has no journals')


def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--exit',required=True);p.add_argument('--out',required=True);p.add_argument('--baseline',action='store_true');p.add_argument('--package',type=Path);p.add_argument('--return-token');a=p.parse_args()
 O=Path(__file__).resolve().parent;W=O.parent
 if a.package and not a.baseline:raise ValueError('--package requires registered --baseline')
 if a.baseline:O=(a.package or W/'bases'/'b2').resolve()
 dest=Path(a.out).resolve()
 if not dest.is_relative_to(W):raise ValueError('Output must stay inside W6')
 raw=Path(a.archive);receipt=json.loads(Path(a.exit).read_text());public=json.loads((O/'package/0.json').read_text())
 digest=file_digest(raw)
 token=receipt.get('token','')
 if not re.fullmatch(re.escape(public['token'])+'[0-9a-f]{8}',token):raise ValueError('Return token differs')
 if a.return_token and token!=a.return_token:raise ValueError('Requested return token differs')
 validate_exit(receipt,raw,public['plan_sha256'],token)
 if str(receipt.get('job'))!=str(int(token[-8:],16)):raise ValueError('Return job differs')
 if a.baseline and (token!='f40065df28aa30002a1a8' or digest!='e3f32cb12debd95004e466d6664041a152bb207f5ae8dc98bb72a3f00c60c230'):
  raise ValueError('Registered baseline differs')
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
 inputs=json.loads(((O/'package/a/1.json') if a.baseline else (dest/'metadata/INPUTS.json')).read_text())
 from orchard_h10.common import read_config
 from orchard_h10.export_pins import validate,admit
 admit(inputs,read_config(O/'package'),validate(json.loads(((O/'package/a/export.json') if a.baseline else (dest/'metadata/EXPORT_PIN.json')).read_text())))
 if (identity['plan']!=public['plan_sha256'] or identity['cards']!=1 or identity['inputs']!=canonical({k:v for k,v in inputs.items() if k!='resume'})
     or identity['operator_sha256']!=sha(O/'tower_sequence.py')):raise ValueError('Read identity differs')
 validate_journals(dest)
 print(json.dumps(dict(output=str(dest),complete=receipt['complete'],status=receipt['status'],sha256=digest)))

if __name__=='__main__':main()
