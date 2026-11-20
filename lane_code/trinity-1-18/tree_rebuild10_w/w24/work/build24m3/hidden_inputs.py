from common import *
import gzip,lzma,shutil
F=D/'hidden'
available=J.load(L/'work/build24m2c/PIN_AUDIT.json')['available']
retained={}
for record in J.load(L/'work/build24m2d/RETENTION_XZ.json')['records']:retained[record['original_sha256']]=L/record['retained']
resolved=J.load(F/'resolved.json');restored=[]
for h,item in resolved['small_files'].items():
 p=F/'inputs'/h
 if p.exists() and J.sha(p)==h:continue
 raw=None
 if h in retained:raw=lzma.decompress(retained[h].read_bytes())
 if raw is None and h in available:
  source=Path(available[h])
  if source.is_file() and J.sha(source)==h:raw=source.read_bytes()
 if raw is None:raise ValueError('Authenticated fixture metadata absent:'+h)
 assert hashlib.sha256(raw).hexdigest()==h and len(raw)==item['bytes']
 replace(p,raw);restored.append(h)
for name in ('q','n','n_go','qd'):
 k=F/name;replace(k/'b/cs.py',(kit(name)/'b/cs.py').read_bytes())
 for p in ('BUILD.json','SHA256SUMS.txt'):replace(k/p,(k/p).read_bytes())
 reseal(k)
J.write(D/'HIDDEN_RESTORED.json',dict(metadata_from_authenticated_original_or_lossless_retention=restored))
s=(D/'hidden_run.py').read_text().replace("+'_final'","+'_final3'")
(D/'hidden_run3.py').write_text(s)
