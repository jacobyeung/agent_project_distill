"""Promote completed temporary products to immutable, indexed proof artifacts."""
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
dest=L/'work/build4'/sys.argv[1]
dest.mkdir(parents=True,exist_ok=False)
mapping={}
for p in sorted((L/'work/tmp').iterdir()):
    q=dest/p.name
    p.rename(q)
    mapping[str(p)]=str(q)
(dest/'LOCATIONS.json').write_text(json.dumps(mapping,indent=2)+'\n')
print(json.dumps(dict(artifacts=len(mapping),destination=str(dest))))
