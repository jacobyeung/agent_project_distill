date -u
nice -n 10 env CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 python3 -I -s -B - <<'PY'
from pathlib import Path
import base64, hashlib, json, sys
root = Path("/project/community/jjyeung/okh7/e6fc152498/p446")
total = 0
for rel in (".", "items", "items_sources", "a"):
    folder = root / rel
    if not folder.is_dir():
        print("UNRESOLVED_DIRECTORY " + str(folder), file=sys.stderr)
        continue
    for p in sorted(folder.iterdir()):
        if p.is_symlink() or not p.is_file() or p.suffix not in (".json", ".jsonl"):
            continue
        size = p.stat().st_size
        if size > 8*1024*1024 or total+size > 16*1024*1024:
            print("SIZE_LIMIT " + str(p), file=sys.stderr)
            continue
        b=p.read_bytes(); total += len(b)
        print(json.dumps({"path":str(p), "bytes":len(b), "sha256":hashlib.sha256(b).hexdigest(), "base64":base64.b64encode(b).decode()}))
PY
