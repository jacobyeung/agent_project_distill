from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
source=B/'inputs/extents.json';retained=L/'work/build12/proofs/text/retained_extents.json'
expected=json.loads((B/'inputs/config.json').read_text())['extent_receipt']['sha256']
assert not source.exists() and hashlib.sha256(retained.read_bytes()).hexdigest()==expected
retained.rename(source)
