from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix'
sizes={}
for folder in ('work/tree_r1','work/base','fixtures','work/contracts_r6','work/n1fix','work/rows_slices','out','work/tmp'):
    root=L/folder;sizes[folder]=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
(B/'STORAGE.json').write_text(json.dumps(sizes,indent=2)+'\n');print(json.dumps(sizes))
