from pathlib import Path
import json,shutil
L=Path(__file__).resolve().parents[2]
value={"bytes":sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()),"free":shutil.disk_usage('/scratch').free}
(L/'work/build23b/SPACE.json').write_text(json.dumps(value));print(value)
