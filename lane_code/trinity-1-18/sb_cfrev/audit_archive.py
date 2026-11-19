from pathlib import Path
import hashlib, io, json, tarfile

ROOT = Path(__file__).resolve().parent
BUILD = Path('/scratch/jjyeung/orch_n30/sb_cachefix')
pins = {}
def read(p):
    b = p.read_bytes()
    pins[str(p)] = hashlib.sha256(b).hexdigest()
    return b
read(Path(__file__))
archive = read(BUILD/'out/sb_cachefix.tar')
checks = {}
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    names = [m.name for m in tar.getmembers() if m.isfile()]
    for suffix in ('out/cachefix.patch','out/CACHEFIX_REPORT.md','review/REVIEW.md','work/test_cachefix.py'):
        matches = [n for n in names if n == suffix or n.endswith('/'+suffix)]
        assert len(matches) == 1, (suffix,matches)
        data = tar.extractfile(matches[0]).read()
        expected = read(BUILD/suffix)
        checks[suffix] = dict(member=matches[0],sha256=hashlib.sha256(data).hexdigest(),matches=data==expected)
        assert data == expected
result = dict(input_sha256=pins,regular_files=len(names),checks=checks)
(ROOT/'evidence/archive.json').write_text(json.dumps(result,indent=2)+'\n')
print('Archive patch, report, review, and tests match the reviewed files.')
