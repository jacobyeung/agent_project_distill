cd /project/community/jjyeung/cp4tk_fr/k6tk && tar xOf bin.tar plan/PLAN.json.gz | python3 -c "
import gzip,sys,json
d=json.loads(gzip.decompress(sys.stdin.buffer.read()))
print(type(d).__name__, list(d)[:10] if isinstance(d,dict) else len(d))
for k in (list(d)[:6] if isinstance(d,dict) else []):
    v=d[k]; print(k, type(v).__name__, (len(v) if hasattr(v,'__len__') else ''), json.dumps(v)[:700])
"
tar xOf bin.tar bin/wa.py | head -40
