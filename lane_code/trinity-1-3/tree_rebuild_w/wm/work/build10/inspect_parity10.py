from pathlib import Path
import json,hashlib,itertools
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
out=L/'work/merge11/proofs/parity';out.mkdir(parents=True,exist_ok=True)
rows=[]
for p in sorted((N/'work/rows_slices').rglob('*.jsonl')):
    with p.open() as stream:
        first=json.loads(next(stream))
    def shape(v,depth=0):
        if depth>2:return type(v).__name__
        if isinstance(v,dict):return {k:shape(w,depth+1) for k,w in v.items()}
        if isinstance(v,list):return dict(length=len(v),first=shape(v[0],depth+1) if v else None)
        return type(v).__name__
    rows.append(dict(path=str(p),bytes=p.stat().st_size,shape=shape(first)))
(out/'INPUT_SHAPES.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows[:2],indent=2))
