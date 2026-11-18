"""Audit nested producer inputs without deriving any operand from response text."""
from pathlib import Path
from collections import Counter
import json,itertools
L=Path(__file__).resolve().parents[2];N=L.parent;B=L/'work/build10'
def walk(value,path=''):
    if isinstance(value,dict):
        for k,v in value.items():
            q=path+'.'+k if path else k
            yield q,k,v
            yield from walk(v,q)
    elif isinstance(value,list):
        for v in value:yield from walk(v,path+'[]')
rows=[]
for p in sorted((N/'work/rows_slices').rglob('*.jsonl')):
    fields=Counter();examples={};count=0
    with p.open() as f:
        for line in itertools.islice(f,2000):
            count+=1
            for path,key,value in walk(json.loads(line)):
                if any(s in key.lower() for s in ('pose','rotation','depth','fov','matrix','camera','xyz','head_input')):
                    fields[path]+=1
                    examples.setdefault(path,str(value)[:240])
    rows.append(dict(source=str(p),rows=count,potential_operand_fields=dict(fields),examples=examples))
out=dict(files=rows,scope='Every nested key in each bound slice row; original rows remain in place. Field names are evidence of available metadata, not a claim that producer inputs are reconstructible.')
(B/'proofs/parity/NESTED_OPERANDS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'files':len(rows),'potential_fields':sorted({k for r in rows for k in r['potential_operand_fields']})}))
