from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';r=D/'proofs/400/q'
for n in ('p/phase_prepare.complete.json','p/phase_frames.complete.json','b/reader_filters.json','b/population.json','a/RESULT.json','h/config.json','f.json','RESULT.json'):
 p=r/n
 if p.exists():
  print(n,p.stat().st_size)
  if n=='RESULT.json':
   v=json.loads(p.read_text());print(v.get('status'),v.get('refusal'))
if (D/'CAPACITY.json').exists():print('CAPACITY',json.loads((D/'CAPACITY.json').read_text())['status'])
