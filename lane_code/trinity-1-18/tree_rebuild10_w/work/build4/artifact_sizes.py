import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
groups=('work/tree_r1','fixtures','work/build4/kits','work/build4/rows_complete','work/tmp')
print(json.dumps({name:sum(p.stat().st_size for p in (L/name).rglob('*') if p.is_file() and not p.is_symlink()) for name in groups}))
