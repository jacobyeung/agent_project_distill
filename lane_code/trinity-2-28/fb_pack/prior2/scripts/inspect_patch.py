from pathlib import Path
import difflib
B=Path('work/base');N=Path('work/new')
for p in sorted(N.rglob('*')):
 if not p.is_file() or '/artifacts/' in str(p):continue
 q=B/p.relative_to(N)
 if not q.exists() or q.read_bytes()!=p.read_bytes():
  print(str(p.relative_to(N)))
  if q.exists():print(''.join(difflib.unified_diff(q.read_text().splitlines(True),p.read_text().splitlines(True),n=2)))
