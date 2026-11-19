from pathlib import Path
import datetime,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
r=D/'proofs/400/q/p'
print(json.dumps({str(p.relative_to(r)):p.stat().st_size for p in r.glob('prepare_*/*/rows.sqlite')}))
for p in (D/'proofs/400/q/RESULT.json',D/'CAPACITY.json'):
 if p.exists():
  v=json.loads(p.read_text());print(str(p),v.get('status'),v.get('refusal'))
