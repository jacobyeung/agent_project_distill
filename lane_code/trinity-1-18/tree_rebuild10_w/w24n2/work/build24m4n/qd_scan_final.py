from common import *
from support import scan
import gzip
full=scan(kit('qd'),'qd');raw=json.dumps(full,sort_keys=True).encode();target=D/'SCAN_qd.json.gz';target.write_bytes(gzip.compress(raw,mtime=0))
J.write(D/'SCAN_qd.json',dict(status=full['status'],kit_seal=J.seal(kit('qd')),full_report=str(target.relative_to(L)),uncompressed_sha256=hashlib.sha256(raw).hexdigest()))
print('qd full decoded/name/environment scan PASS')
