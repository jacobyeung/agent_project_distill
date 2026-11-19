from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def walk(x):
    if isinstance(x,dict):
        if set(x)=={'path','sha256'}:yield x
        for v in x.values():yield from walk(v)
    if isinstance(x,list):
        for v in x:yield from walk(v)
rows=[]
for name in ('work/build14/inputs/config.json','work/n1fix2/inputs/config.json','work/n1fix2/inputs/row_sources.json','work/n1fix2/inputs/v7_receipt.json'):
    for pin in walk(json.loads((L/name).read_text())):
        p=Path(pin['path']);rows.append(dict(owner=name,**pin,exists=p.is_file()))
(B/'INPUT_AVAILABILITY.json').write_text(json.dumps(rows,indent=2))
print(json.dumps([x for x in rows if not x['exists']],indent=2))
for g in ('generator','legacy','r2'):
    p=L/'work/build14/proofs/final/suite_tree'/g/'results.json'
    v=json.loads(p.read_text())
    print(g,{k:len(v[k]) if isinstance(v.get(k),list) else v.get(k) for k in ('tests','passed','failures','errors','skips','complete')})
