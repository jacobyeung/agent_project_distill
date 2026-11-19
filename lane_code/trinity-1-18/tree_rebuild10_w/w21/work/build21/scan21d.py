from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from naming21 import scan_decoded,PROVENANCE_FIELDS
scan=scan_decoded(B/'kits/q');J.write(D/'SCAN.json',scan)
J.write(D/'ALLOWLIST.json',PROVENANCE_FIELDS)
start=J.load(D/'START.json');kit=B/'kits/q'
files={str(p.relative_to(kit)):dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in kit.rglob('*') if p.is_file()}
assert files==start['kit_files'],'Kit bytes changed'
assert J.seal(kit)==start['kit_seal']
J.write(D/'KIT_CHECK.json',dict(status='PASS',files=len(files),before=start['kit_seal'],after=J.seal(kit),byte_identical=True))
print(json.dumps(dict(status=scan['status'],checked_strings=scan['checked_strings'],maps=len(scan['decoded_maps']),
    environments=len(scan['environment_sinks']),kit_seal=J.seal(kit))))
