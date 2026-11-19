from pathlib import Path
import json
B=Path(__file__).resolve().parent
for step in ('400','600'):
    root=B/'proofs/capacity'/step/'q'
    p=root/'RESULT.json'
    if not p.exists():continue
    value=json.loads(p.read_text())
    print(step,value.get('status'),value.get('refusal'))
    if value.get('status')=='ADMIT':
        rows=json.loads((root/'f.json').read_text())['records']
        print('first_losses',{rank:next(r['loss'] for r in rows if r['rank']==rank) for rank in range(4)})
        print('forwarded_rows',len(rows),'finite',all(r['finite'] for r in rows))
        twins=root.parent/'TWINS.json'
        if twins.exists():print('twins',{k:r.get('refusal') for k,r in json.loads(twins.read_text()).items()})
