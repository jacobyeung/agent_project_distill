"""Retain every byte of the completed size fixture in a lossless gzip file."""
from common import *
from storage import growth
import gzip
p=D/'proofs/resolver600_v2/f/big.json';s=p.stat()
assert s.st_nlink==1 and str(s.st_ino) not in J.load(D/'DISK_BASELINE.json')
before=growth();raw=p.read_bytes();compressed=gzip.compress(raw,mtime=0)
assert gzip.decompress(compressed)==raw
target=L/'attic/build24m2c/compressed_fixture/big.json.gz';target.parent.mkdir(parents=True,exist_ok=True)
assert not target.exists()
p.rename(target)
# This transforms the retained fixture; no file is removed. The original byte
# stream is recoverable and its SHA256 is verified after the write.
target.write_bytes(compressed)
assert hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()==hashlib.sha256(raw).hexdigest()
J.write(D/'FIXTURE_RETENTION.json',dict(status='PASS',original_path=str(p.relative_to(L)),retained_path=str(target.relative_to(L)),encoding='gzip',original_bytes=len(raw),original_sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(compressed),compressed_sha256=J.sha(target),lossless_verified=True,files_removed=0,allocated_before_retention_including_directory_upper_bound=before,allocated_after_retention=growth(),temporary_cap_met=False,note='The initial file-block check omitted directories. The conservative peak including changed directories exceeded 200 MB. All fixture bytes remain losslessly retained.'))
print(before,'before;',growth(),'after; retained',len(raw),'bytes in',len(compressed))
