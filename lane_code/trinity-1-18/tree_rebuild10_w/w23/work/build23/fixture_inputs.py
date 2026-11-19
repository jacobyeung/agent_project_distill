from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2]
source=L.parent/'w21/work/build16/proofs/traces/units.jsonl'
with source.open() as f:raw=next(f)
value=json.loads(raw);assert 'native_row' in value
target=L/'work/build16/proofs/traces/units.jsonl';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(raw)
(L/'work/build23/FIXTURE_INPUTS.json').write_text(json.dumps(dict(source=str(source),selection='first line only',path=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()),indent=2))
