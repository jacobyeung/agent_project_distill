W=/project/community/jjyeung/okh7/e6fc152498; T=b01ec87a6f29b00029ad2; S=$W/r2/sj/h10sub3_$T
python3 - <<'X' >&2
import tarfile,hashlib
t=tarfile.open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ad2/result.tar.gz')
a=hashlib.sha256(t.extractfile('metadata/journals/3/0/items.jsonl').read()).hexdigest()
b=hashlib.sha256(open('/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10ret_b01ec87a6f29b00029ad2/metadata/journals/3/0/items.jsonl','rb').read()).hexdigest()
print('ret_items_match', a==b, a[:16])
import json
r=json.loads(open('/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl').readline())
def sk(o,d=0,p=''):
    if isinstance(o,dict):
        for k,v in o.items(): 
            if isinstance(v,(dict,list)): print('  '*d+k, type(v).__name__, len(v)); sk(v,d+1) if d<3 else None
            else: print('  '*d+k, '=', repr(v)[:150])
    elif isinstance(o,list) and o: sk(o[0],d+1)
sk(r)
X
tar cf - -C $S curve.json report.md
