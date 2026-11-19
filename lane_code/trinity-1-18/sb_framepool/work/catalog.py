import tarfile,json,hashlib
from pathlib import Path
from collections import Counter
entries=[]
for a in Path('work/tars.txt').read_text().splitlines():
 with tarfile.open(a) as t:
  for m in t:
   if m.isfile():entries.append(dict(archive=a,name=m.name,size=m.size,offset=m.offset_data))
Path('work/archive_catalog.json').write_text(json.dumps({'inputs':{str(Path('work/tars.txt').resolve()):{'sha256':hashlib.sha256(Path('work/tars.txt').read_bytes()).hexdigest()}},'entries':entries}))
for a in Path('work/tars.txt').read_text().splitlines():
 es=[e for e in entries if e['archive']==a and (e['name'].endswith(('.sqlite','.jsonl.gz')) or any(n in e['name'] for n in ('scene_index','scene_map','training_scenes')))]
 print(Path(a).parent.name,Path(a).name,'members',sum(e['archive']==a for e in entries),'data',len(es));print('\n'.join(str((e['name'],e['size'])) for e in es[:12]))
