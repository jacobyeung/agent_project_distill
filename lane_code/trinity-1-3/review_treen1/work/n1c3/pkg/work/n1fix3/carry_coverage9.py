import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
source=L.parent/'work/build9/CHANGED_COVERAGE.json'
raw=source.read_bytes();target=B/'B9_CHANGED_COVERAGE.json';target.write_bytes(raw)
(B/'B9_COVERAGE_SOURCE.json').write_text(json.dumps(dict(path=str(source),sha256=hashlib.sha256(raw).hexdigest(),
    use='Only statements whose complete current file hash matches the original observation.'),indent=2)+'\n')
