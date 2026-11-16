D=/scratch/jjyeung/k1/m544_parts
ls -la $D
cat > /tmp/k1ops6_tl.py <<'PY'
import sys, tarfile, json
names=sys.argv[1:]
class Cat:
    def __init__(s,f): s.f=[open(x,'rb') for x in f]; s.i=0
    def read(s,n=-1):
        out=b''
        while s.i<len(s.f) and (n<0 or len(out)<n):
            b=s.f[s.i].read(n-len(out) if n>=0 else -1)
            if not b: s.i+=1; continue
            out+=b
        return out
rows=[]; fw=None
with tarfile.open(fileobj=Cat(names), mode='r|') as t:
    for m in t:
        rows.append(dict(name=m.name,size=m.size,type=m.type.decode() if isinstance(m.type,bytes) else m.type))
        if m.name.endswith('full_weights/full_weights.json') or m.name.endswith('.json') and m.size<2000000:
            f=t.extractfile(m)
            if f is not None:
                rows[-1]['content']=f.read().decode('utf-8','replace')
print(json.dumps(rows))
PY
python3 /tmp/k1ops6_tl.py $D/*part00* $D/*part01* $D/*part02* $D/*part03* > /tmp/k1ops6_export_list.json 2>/tmp/k1ops6_tl.err; echo py_rc=$?; cat /tmp/k1ops6_tl.err | tail -3
wc -c /tmp/k1ops6_export_list.json
cat /tmp/k1ops6_export_list.json | timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cat > /scratch/jjyeung/orch_n30/k1_ops6/work/export_list.json && echo COPY_OK"
