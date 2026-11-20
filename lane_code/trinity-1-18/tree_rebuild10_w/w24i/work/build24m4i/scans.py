from pathlib import Path
from common import *
from support import scan
import gzip
for name in ("q","n","n_go","qd"):
    full=scan(kit(name),name);raw=json.dumps(full,sort_keys=True).encode();target=D/("SCAN_"+name+".json.gz");target.write_bytes(gzip.compress(raw,mtime=0))
    J.write(D/("SCAN_"+name+".json"),dict(status=full["status"],kit_seal=J.seal(kit(name)),full_report=str(target.relative_to(L)),uncompressed_sha256=hashlib.sha256(raw).hexdigest()))
    print(name,"PASS",flush=True)
