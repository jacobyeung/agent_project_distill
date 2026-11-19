from pathlib import Path
import json,sqlite3
L=Path(__file__).resolve().parents[2]
for s,p,n in [('pose','pose_store/pose.sqlite',16000),('vqa','vqa/rows.sqlite',32000),('pointing','pointing/rows.sqlite',8000),('routing','routing19/rows.sqlite',16000)]:
    path=L/'work/build20/proofs/native'/p
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:row,target=db.execute('SELECT row,target FROM rows LIMIT 1').fetchone()
    v=json.loads(row)
    def walk(v):
        if isinstance(v,dict):
            return {k:('/data2/f.png' if k=='path' and isinstance(x,str) and x.endswith('/f.png') else walk(x)) for k,x in v.items()}
        if isinstance(v,list):return [walk(x) for x in v]
        return v
    raw=json.dumps(walk(v));length=len(raw.encode())+len(target.encode())
    print(s,length,n,length*n,'page estimate',((length+4095)//4096)*4096*n)
