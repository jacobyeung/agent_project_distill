import json,collections
from pathlib import Path
from scan_rows import sha
files=Path('work/files.txt').read_text().splitlines();entries=[]
for p in files:
 if '/tree_rebuild10_w/' not in p or not p.endswith('.sqlite'):continue
 try:
  with open(p,'rb') as f:head=f.read(160)
  entries.append(dict(path=p,sha256=sha(p),bytes=Path(p).stat().st_size,format='sqlite' if head.startswith(b'SQLite format 3') else 'LFS_POINTER' if head.startswith(b'version https://git-lfs') else 'not_SQLite',head=head.decode('utf8',errors='replace') if not head.startswith(b'SQLite') else None))
 except FileNotFoundError:entries.append(dict(path=p,status='MISSING'))
Path('work/local_store_inventory.json').write_text(json.dumps(dict(command='/usr/bin/python3 work/check_local_stores.py',inputs={'work/files.txt':{'sha256':sha('work/files.txt')}},files=entries),indent=2)+'\n')
print(collections.Counter(x.get('format',x.get('status')) for x in entries))
