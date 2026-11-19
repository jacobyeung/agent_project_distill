"""Hash and inspect local metadata, without treating fixtures or receipts as training rows."""
import json,hashlib,gzip,re,tarfile
from pathlib import Path
from collections import Counter
ROOT=Path.cwd();files=Path('work/files.txt').read_text().splitlines()
# Expand archive member inventory to all surviving mirror archives.
archives=sorted(p for p in files if '/n30_mirror/' in p and p.endswith(('.tar','.tgz','.tar.gz')))
entries=[];errors=[]
for a in archives:
 try:
  with tarfile.open(a) as t:
   for m in t:
    if m.isfile():entries.append(dict(archive=a,name=m.name,size=m.size,offset=m.offset_data,compressed=not a.endswith('.tar')))
 except Exception as e:errors.append(dict(path=a,error=str(e)))
 print('catalog',a,flush=True)
Path('work/all_archive_catalog.json').write_text(json.dumps(dict(inputs={str(ROOT/'work/files.txt'):dict(sha256=hashlib.sha256(Path('work/files.txt').read_bytes()).hexdigest())},entries=entries,errors=errors)))
# Index every non-image metadata payload in mirror and W; exclude copied source trees and ephemeral tests.
def wanted(p):
 if not p.endswith(('.json','.jsonl','.json.gz','.jsonl.gz','.tsv','.csv')):return False
 if any(x in p for x in ('/tmp/','/tests/','/vendor/','/g3t_vendor/','/tokenizer','/caps_raw/','/caps/','/rasters/')):return False
 if 'frame_map' in p or 'frame_plan' in p:return False
 if '/n30_mirror/' in p:return True
 return any(x in p for x in ('/inputs/','/ext/','/fixtures/work/','/proofs/rooms/','/proofs/components/')) or any(x in Path(p).name for x in ('scene_indices','pool_indices','pool_exclusion','remove_'))
local=[dict(path=p,size=Path(p).stat().st_size) for p in files if wanted(p) and Path(p).is_file()]
arch=[e for e in entries if wanted('/n30_mirror/'+e['name'])]
Path('work/blobs').mkdir(exist_ok=True)
registry={};skipped=[]
def ingest(e,data):
 h=hashlib.sha256(data).hexdigest();loc=e.get('path') or e['archive']+'::'+e['name']
 if h in registry:registry[h]['locations'].append(loc);return
 name=e.get('path',e.get('name'));kind='jsonl' if '.jsonl' in name else 'json' if '.json' in name else 'text'
 try:raw=gzip.decompress(data) if name.endswith('.gz') else data
 except Exception as x:skipped.append(dict(location=loc,error=str(x)));return
 out=Path('work/blobs')/(h+'.'+kind);out.write_bytes(raw)
 registry[h]=dict(locations=[loc],bytes=len(data),uncompressed_bytes=len(raw),kind=kind,blob=str(out),sha256=h)
for e in local:
 if e['size']>350_000_000:skipped.append(dict(location=e['path'],reason='large payload; row scanner handles SQLite/JSONL separately'));continue
 try:ingest(e,Path(e['path']).read_bytes())
 except Exception as x:skipped.append(dict(location=e['path'],error=str(x)))
for a in archives:
 es=[e for e in arch if e['archive']==a]
 if a.endswith('.tar'):
  with open(a,'rb') as f:
   for e in es:
    if e['size']>350_000_000:skipped.append(dict(location=a+'::'+e['name'],reason='large metadata payload'));continue
    f.seek(e['offset']);ingest(e,f.read(e['size']))
 else:
  with tarfile.open(a) as t:
   for e in es:
    if e['size']<=350_000_000:ingest(e,t.extractfile(e['name']).read())
 print('metadata',a,flush=True)
Path('work/metadata_registry.json').write_text(json.dumps(dict(inputs={str(ROOT/'work/files.txt'):dict(sha256=hashlib.sha256(Path('work/files.txt').read_bytes()).hexdigest()),str(ROOT/'work/all_archive_catalog.json'):dict(sha256=hashlib.sha256(Path('work/all_archive_catalog.json').read_bytes()).hexdigest())},files=registry,skipped=skipped),indent=2))
print('DONE',len(registry),'locations',sum(len(e['locations']) for e in registry.values()),'skipped',len(skipped),flush=True)
