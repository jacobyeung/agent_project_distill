"""Verify every latest round-4 encoded artifact without restoring it to disk."""
from pathlib import Path
import hashlib,json,os,resource,sys
sys.path.insert(0,str(Path(__file__).parent))
import decode_artifact as D
resource.setrlimit(resource.RLIMIT_AS,(28*1024**3,28*1024**3))
if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:8]))
r=Path(__file__).resolve().parent;root=r.parents[1]
rows={x['path']:x for x in json.loads((r/'STORAGE.json').read_text())['files']};total=0
for path,row in rows.items():
    raw=D.decode(root/path)
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],path
    total+=len(raw)
result=dict(passed=True,encoded_artifacts=len(rows),decoded_bytes_checked=total)
(r/'STORAGE_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
