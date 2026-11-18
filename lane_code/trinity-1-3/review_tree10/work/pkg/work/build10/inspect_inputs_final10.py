from pathlib import Path
import json,collections,hashlib
L=Path(__file__).resolve().parents[2];N=L.parent;B=L/'work/build10'
result={}
for reader in ('gf1','c8r'):
    root=N/'work/build7/proofs/eat1'/reader
    items=[json.loads(s) for s in (root/'items.jsonl').read_text().splitlines()]
    outcomes=[json.loads(s) for s in (root/'run/ITEMS.jsonl').read_text().splitlines()]
    result[reader]={'items':items,'outcome_keys':list(outcomes[0]),'first_outcome':outcomes[0],
        'weights_bytes':(root/'artifact/weights.pt').stat().st_size}
paths=collections.Counter();examples={}
def inspect(value,path=''):
    if isinstance(value,dict):
        for key,v in value.items():
            q=path+'.'+key if path else key
            paths[q]+=1
            if any(w in key.lower() for w in ('pose','geometry','rotation','depth','fov','head','point','xyz')):
                examples.setdefault(q,str(v)[:300])
            inspect(v,q)
    elif isinstance(value,list) and value:inspect(value[0],path+'[]')
for p in sorted((N/'work/rows_slices').rglob('*.jsonl')):
    with p.open() as f:inspect(json.loads(next(f)))
result['nested_first_row_keys']=dict(paths);result['potential_operands']=examples
(B/'proofs/parity/INPUT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{'keys':v['outcome_keys'],'weights_bytes':v['weights_bytes'],'first_outcome':str(v['first_outcome'])[:1200]} for k,v in result.items() if k in ('gf1','c8r')},indent=2))
print(json.dumps(examples,indent=2))
