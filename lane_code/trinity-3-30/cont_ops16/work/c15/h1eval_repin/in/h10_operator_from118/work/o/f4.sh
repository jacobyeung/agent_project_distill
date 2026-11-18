T=/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar; ls -la $T
nice -n 19 python3 - <<'P'
import tarfile,gzip,json
t=tarfile.open('/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar')
ms=t.getmembers(); print(len(ms), [ (m.name,m.size) for m in ms[:40]])
for m in ms:
    if m.name.endswith('.jsonl.gz'):
        f=gzip.open(t.extractfile(m),'rt'); r=json.loads(f.readline())
        def sk(o,d=0):
            return {k:(sk(v,d+1) if isinstance(v,dict) and d<2 else type(v).__name__) for k,v in o.items()} if isinstance(o,dict) else type(o).__name__
        print(m.name, json.dumps(sk(r))[:900]); break
P
