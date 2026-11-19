import json,tarfile,hashlib,gzip
from pathlib import Path
p=Path('work/metadata_registry.json');r=json.loads(p.read_text());bad=set(a for a in Path('work/compressed_archives.txt').read_text().splitlines() if a.endswith('.tar'))
original=hashlib.sha256(p.read_bytes()).hexdigest(); wanted={a:set() for a in bad}
for h,e in list(r['files'].items()):
 keep=[]
 for loc in e['locations']:
  a,sep,n=loc.partition('::')
  if a in bad and sep:wanted[a].add(n)
  else:keep.append(loc)
 if keep:e['locations']=keep
 else:del r['files'][h]
for a,names in sorted(wanted.items()):
 with tarfile.open(a,'r|gz') as t:
  for m in t:
   if m.name not in names:continue
   data=t.extractfile(m).read();h=hashlib.sha256(data).hexdigest();loc=a+'::'+m.name
   if h in r['files']:r['files'][h]['locations'].append(loc);continue
   kind='jsonl' if '.jsonl' in m.name else 'json' if '.json' in m.name else 'text'
   raw=gzip.decompress(data) if m.name.endswith('.gz') else data
   out=Path('work/blobs')/(h+'.'+kind);out.write_bytes(raw)
   r['files'][h]=dict(locations=[loc],bytes=len(data),uncompressed_bytes=len(raw),kind=kind,blob=str(out),sha256=h)
 print(a,len(names),flush=True)
r['inputs'][str(p.resolve())]={'sha256':original};r['command']='/usr/bin/python3 work/repair_metadata.py'
Path('work/metadata_fixed.json').write_text(json.dumps(r,indent=2)+'\n')
Path('STATUS.md').write_text('Capture reproduction and direct row scans are saved. The metadata cache now handles gzip archives with .tar names correctly in work/metadata_fixed.json; the original cache is retained. Lineage pins, scene indices, pool filters, and evaluation joins remain in progress.\n')
