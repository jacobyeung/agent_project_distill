X=/project/community/jjyeung/okh7/x_22c714e1; Q=$X/qp_11386117; D=$X/qd; TZ=UTC date +%TZ; df -h /project/community | tail -1
sha256sum $Q/SHA256SUMS.txt $D/SHA256SUMS.txt
(cd $Q && sha256sum -c --quiet SHA256SUMS.txt && echo "qp sums all match")
(cd $D && sha256sum -c --quiet SHA256SUMS.txt && echo "qd sums all match")
diff <(sort -k2 $D/SHA256SUMS.txt) <(sort -k2 $Q/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'
diff <(cd $D && find . -type f | sort) <(cd $Q && find . -type f | sort) | head
nice -n 10 python3 -I -s -B - <<'PY'
import json,base64,hashlib
X='/project/community/jjyeung/okh7/x_22c714e1'
def dec(p):
    v=json.load(open(p))
    if isinstance(v,dict) and 'payload' in v: return json.loads(base64.b64decode(v['payload']))
    return v
def walk(x,y,p=''):
    if isinstance(x,dict) and isinstance(y,dict):
        for k in sorted(set(x)|set(y)): walk(x.get(k,'<absent>'),y.get(k,'<absent>'),p+'/'+str(k))
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+'['+str(i)+']')
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:300],'->',json.dumps(y)[:300])
for f in ('h.json','r.json','p.json','a.json'):
    print('##',f); walk(dec(X+'/qd/k/'+f),dec(X+'/qp_11386117/k/'+f))
u=X+'/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73'
import os; print('u a49f117f exists',os.path.exists(u), os.path.exists(u) and hashlib.sha256(open(u,'rb').read()).hexdigest())
PY
ls $X/o/173964 2>&1 | head -30
