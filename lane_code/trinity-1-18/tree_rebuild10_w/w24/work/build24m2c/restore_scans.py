"""Reconstruct full decoded scan reports from the package's lossless bundle."""
import json,hashlib,sys
from pathlib import Path

def expand(bundle,name):
 base=bundle['base']
 if name=='q':value=base
 else:
  value=dict(base)
  for key,edit in bundle['deltas'][name].items():
   if 'replace' in edit:value[key]=edit['replace']
   else:
    out=[]
    for step in edit['sequence']:
     if 'copy' in step:
      start,count=step['copy'];out.extend(base[key][start:start+count])
     else:out.extend(step['insert'])
    value[key]=out
 raw=json.dumps(value,sort_keys=True).encode()
 assert hashlib.sha256(raw).hexdigest()==bundle['sha256'][name]
 return raw

if __name__=='__main__':
 source=Path(sys.argv[1]);target=Path(sys.argv[2]);target.mkdir(parents=True,exist_ok=True)
 bundle=json.loads(source.read_text())
 for name in ('q','n','n_go','qd'):
  with (target/('SCAN_full_'+name+'.json')).open('xb') as f:f.write(expand(bundle,name))
