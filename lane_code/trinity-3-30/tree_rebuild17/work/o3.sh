X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
python3 - <<'P'
import json,base64,gzip,zlib
d=json.load(open('qd/k/j.json')); print(d['encoding'])
b=d['payload'].encode()
for f in (lambda x: base64.b64decode(x), lambda x: gzip.decompress(base64.b64decode(x)), lambda x: zlib.decompress(base64.b64decode(x))):
    try: t=f(b).decode(); break
    except Exception: pass
L=t.splitlines()
for i,l in enumerate(L,1):
    if any(k in l for k in ('trap','TERM','cleanup','_exit','finish')): print(i,l[:200])
for i in range(140,162): print(i+1,L[i][:220])
P
