from pathlib import Path
import json, os
L=Path(__file__).resolve().parents[2]; B=L/'work/build18'
def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
B.mkdir(exist_ok=True)
(B/'STORAGE_START.json').write_text(json.dumps(dict(bytes=size(L),temporary_bytes=size(L/'work/tmp')),indent=2))
(B/'STATUS.md').write_text('Build 18: GO=false. The native mode-q fixture is being assembled. No combined admission is claimed.\n')
raw=(L/'work/build17/test17.py').read_text().replace("B=L/'work/build17'", "B=L/'work/build18'").replace("'B17_PROOF'","'B18_PROOF'")
raw=raw.replace("str(L/'work/build16')]", "str(L/'work/build16'),str(L/'work/build17')]")
(B/'test18.py').write_text(raw)
